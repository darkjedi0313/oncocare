from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
import pandas as pd
import numpy as np

from api.deps import get_db, DataLoader
from api.schemas import SummaryResponse, CancerStat, PrioritySegment, PriorityResponse, PriorityItem, CompareResponse, FactorsResponse, FactorSegment, ChangeableFactor, FixedFactor, StrataRow, ActionResponse, ActionItem, SampleRequest, SampleResponse, RecordsResponse, CampaignRecordUpdateRequest

router = APIRouter(prefix="/api", tags=["Query"])

@router.get("/summary", response_model=SummaryResponse)
def get_summary(
    region: str = Query(..., description="지역 키 (예: '서울특별시|양천구')"),
    year: int = Query(..., description="연도 (예: 2024)"),
    scope: str = Query("sgg", description="조회 범위 (sgg 등)")
):
    db = get_db()
    df = db.expectation
    
    # 1. 해당 연도 데이터 필터
    df_year = df[df['연도'] == year].copy()
    if df_year.empty:
        raise HTTPException(status_code=404, detail=f"해당 연도({year})의 데이터가 없습니다.")
        
    # region 존재 여부 체크
    if region not in df_year['키'].values:
        raise HTTPException(status_code=404, detail=f"해당 지역({region})의 데이터를 찾을 수 없습니다.")
        
    # 2. 통합 수검률 및 전국 순위 계산
    # 시군구별 6대암 통합 수검률 산출
    sgg_total = df_year.groupby('키').agg(
        total_target=('대상자', 'sum'),
        total_screened=('수검자', 'sum')
    ).reset_index()
    sgg_total['통합수검률'] = sgg_total['total_screened'] / sgg_total['total_target'] * 100
    
    # 통합 수검률 기준 내림차순 랭킹 매기기 (높은 곳이 1등)
    sgg_total['rank'] = sgg_total['통합수검률'].rank(ascending=False, method='min')
    
    region_row = sgg_total[sgg_total['키'] == region]
    total_rate = float(region_row['통합수검률'].values[0])
    rank = int(region_row['rank'].values[0])
    total_sgg_count = len(sgg_total)
    
    # 미수검 인원
    target_sum = int(region_row['total_target'].values[0])
    screened_sum = int(region_row['total_screened'].values[0])
    unscreened_count = target_sum - screened_sum
    
    # 3. 암종별 현황 산출
    df_region = df_year[df_year['키'] == region]
    df_region_cancer = df_region.groupby('암종').agg(
        target=('대상자', 'sum'),
        screened=('수검자', 'sum')
    ).reset_index()
    
    # 전국 암종별 평균 수검률
    df_nat_cancer = df_year.groupby('암종').agg(
        nat_target=('대상자', 'sum'),
        nat_screened=('수검자', 'sum')
    ).reset_index()
    df_nat_cancer['전국_평균'] = df_nat_cancer['nat_screened'] / df_nat_cancer['nat_target'] * 100
    nat_cancer_map = df_nat_cancer.set_index('암종')['전국_평균'].to_dict()
    
    cancer_stats = []
    for r in df_region_cancer.itertuples():
        rate = float(r.screened / r.target * 100) if r.target > 0 else 0.0
        nat_avg = float(nat_cancer_map.get(r.암종, 0.0))
        cancer_stats.append(
            CancerStat(
                암종=r.암종,
                수검률=round(rate, 2),
                전국_평균=round(nat_avg, 2),
                대상자=int(r.target),
                수검자=int(r.screened)
            )
        )
        
    # 4. 우선 대상 Top 3 추출 (필터: 연령n < 11, 회복여지 >= 300)
    # AGENTS.md: MAX_AGE_IDX = 11 (연령n < 11), MIN_RECOVERY = 300 (회복여지 300명 미만 제외)
    # df_region에서 위 필터를 만족하는 것들 중 회복여지 내림차순 정렬 후 상위 3개
    p_df = df_region[(df_region['연령n'] < 11) & (df_region['회복여지'] >= 300)].copy()
    p_df = p_df.sort_values(by='회복여지', ascending=False)
    
    top3_segments = []
    for r in p_df.head(3).itertuples():
        top3_segments.append(
            PrioritySegment(
                성별=r.성별,
                연령=r.연령,
                암종=r.암종,
                대상자=int(r.대상자),
                수검률=round(float(r.수검률), 2),
                기대치=round(float(r.기대치), 2),
                잔차=round(float(r.잔차), 2),
                회복여지=int(np.round(r.회복여지))
            )
        )
        
    # 지역명 파싱 (시도|시군구 -> 시군구만 추출하여 사용자 친화적으로 반환)
    region_display = region.split('|')[1] if '|' in region else region
    
    return SummaryResponse(
        지역명=region_display,
        연도=year,
        통합_수검률=round(total_rate, 2),
        전국_순위=rank,
        전체_시군구수=total_sgg_count,
        미수검_인원=unscreened_count,
        암종별_현황=cancer_stats,
        우선_대상_top3=top3_segments
    )

@router.get("/priority", response_model=PriorityResponse)
def get_priority(
    region: Optional[str] = Query(None, description="특정 지역 필터 (예: '서울특별시|양천구')"),
    year: int = Query(..., description="연도 (예: 2024)")
):
    db = get_db()
    df = db.expectation
    
    # 1. 해당 연도 데이터 필터
    df_year = df[df['연도'] == year].copy()
    if df_year.empty:
        raise HTTPException(status_code=404, detail=f"해당 연도({year})의 데이터가 없습니다.")
        
    # 2. 전국 평균 조인
    df_nat = db.national_avg
    df_year = df_year.merge(df_nat, on=['연도', '성별', '연령', '암종'], how='left')
    
    # 3. 유사 지역 평균 조인
    df_sim = db.similar_rates
    df_year = df_year.merge(df_sim[['시도', '시군구', '성별', '연령', '암종', '연도', '유사_평균']], 
                             on=['시도', '시군구', '성별', '연령', '암종', '연도'], how='left')
    
    # 결측 보정
    df_year['전국_평균'] = df_year['전국_평균'].fillna(df_year['수검률'])
    df_year['유사_평균'] = df_year['유사_평균'].fillna(df_year['수검률'])
    
    # 특정 지역 지정 시 필터
    if region:
        if region not in df_year['키'].values:
            raise HTTPException(status_code=404, detail=f"해당 지역({region})의 데이터를 찾을 수 없습니다.")
        df_year = df_year[df_year['키'] == region]
        
    # 우선순위 필터 조건 적용 (MAX_AGE_IDX = 11, MIN_RECOVERY = 300)
    p_df = df_year[(df_year['연령n'] < 11) & (df_year['회복여지'] >= 300)].copy()
    
    # 회복여지 내림차순 정렬
    p_df = p_df.sort_values(by='회복여지', ascending=False)
    
    items = []
    for r in p_df.itertuples():
        items.append(
            PriorityItem(
                시도=r.시도,
                시군구=r.시군구,
                성별=r.성별,
                연령=r.연령,
                암종=r.암종,
                대상자=int(r.대상자),
                수검자=int(r.수검자),
                수검률=round(float(r.수검률), 2),
                기대치=round(float(r.기대치), 2),
                잔차=round(float(r.잔차), 2),
                회복여지=int(np.round(r.회복여지)),
                유사_평균=round(float(r.유사_평균), 2),
                전국_평균=round(float(r.전국_평균), 2)
            )
        )
        
    return PriorityResponse(
        연도=year,
        총_세그먼트수=len(items),
        목록=items
    )

@router.get("/compare", response_model=CompareResponse)
def get_compare(
    region: str = Query(..., description="지역 키 (예: '서울특별시|양천구')"),
    gender: str = Query(..., description="성별 ('남자' 또는 '여자')"),
    age: str = Query(..., description="연령대 (예: '65~69')"),
    cancer: str = Query(..., description="암종 (예: '대장암')"),
    year: int = Query(..., description="연도 (예: 2024)")
):
    db = get_db()
    
    # 1. 우리 지역 세그먼트 데이터 조회
    df_exp = db.expectation
    seg_row = df_exp[
        (df_exp['키'] == region) & 
        (df_exp['성별'] == gender) & 
        (df_exp['연령'] == age) & 
        (df_exp['암종'] == cancer) & 
        (df_exp['연도'] == year)
    ]
    
    if seg_row.empty:
        raise HTTPException(status_code=404, detail="해당 조건의 세그먼트 데이터를 찾을 수 없습니다.")
        
    row = seg_row.iloc[0]
    actual_rate = float(row['수검률'])
    expectation_rate = float(row['기대치'])
    residual = float(row['잔차'])
    
    # 2. 유사 지역 20곳 목록 조회
    similar_map = db.similar_regions
    if region not in similar_map:
        raise HTTPException(status_code=404, detail="유사 지역 매칭 목록이 존재하지 않습니다.")
    similar_list = similar_map[region]
    
    # 3. 유사 지역 20곳 통계치 조회
    df_sim = db.similar_rates
    sim_row = df_sim[
        (df_sim['시도'] == row['시도']) & 
        (df_sim['시군구'] == row['시군구']) & 
        (df_sim['성별'] == gender) & 
        (df_sim['연령'] == age) & 
        (df_sim['암종'] == cancer) & 
        (df_sim['연도'] == year)
    ]
    
    if sim_row.empty:
        # DB에 없을 경우 기본값으로 유사 지역 20곳 대상 직접 실시간 가공 처리
        # (similar_rates.parquet가 완벽하게 다 빌드되었다면 이 블록은 들어오지 않음)
        df_joined = df_exp[
            (df_exp['키'].isin(similar_list)) & 
            (df_exp['성별'] == gender) & 
            (df_exp['연령'] == age) & 
            (df_exp['암종'] == cancer) & 
            (df_exp['연도'] == year)
        ]
        if df_joined.empty:
            sim_avg, sim_min, sim_max, sim_se = 0.0, 0.0, 0.0, 0.0
        else:
            total_target = df_joined['대상자'].sum()
            total_screened = df_joined['수검자'].sum()
            sim_avg = total_screened / total_target * 100 if total_target > 0 else 0.0
            sim_min = df_joined['수검률'].min()
            sim_max = df_joined['수검률'].max()
            sim_std = df_joined['수검률'].std()
            sim_se = sim_std / np.sqrt(len(df_joined)) if len(df_joined) > 0 else 0.0
    else:
        s_row = sim_row.iloc[0]
        sim_avg = float(s_row['유사_평균'])
        sim_min = float(s_row['유사_최소'])
        sim_max = float(s_row['유사_최대'])
        sim_se = float(s_row['유사_SE'])
        
    region_display = region.split('|')[1] if '|' in region else region
    
    # 4. 전국 평균 계산
    df_nat = df_exp[
        (df_exp['성별'] == gender) & 
        (df_exp['연령'] == age) & 
        (df_exp['암종'] == cancer) & 
        (df_exp['연도'] == year)
    ]
    nat_avg = df_nat['수검자'].sum() / df_nat['대상자'].sum() * 100 if not df_nat.empty and df_nat['대상자'].sum() > 0 else 56.3
    
    # 유사 지역 목록도 사용자 친화적으로 파싱해서 반환 (시군구명만 표시)
    similar_list_display = [n.split('|')[1] if '|' in n else n for n in similar_list]
    
    return CompareResponse(
        연도=year,
        지역명=region_display,
        성별=gender,
        연령=age,
        암종=cancer,
        실제_수검률=round(actual_rate, 2),
        기대치=round(expectation_rate, 2),
        잔차=round(residual, 2),
        유사_평균=round(sim_avg, 2),
        유사_최소=round(sim_min, 2),
        유사_최대=round(sim_max, 2),
        유사_SE=round(sim_se, 2),
        전국_평균=round(nat_avg, 2),
        유사_지역목록=similar_list_display
    )

@router.get("/factors", response_model=FactorsResponse)
def get_factors(
    region: str = Query(..., description="지역 키 (예: '서울특별시|양천구')"),
    sex: str = Query(..., description="성별 ('남자' 또는 '여자')"),
    age: str = Query(..., description="연령대 (예: '65~69')"),
    cancer: str = Query(..., description="암종 (예: '대장암')"),
    year: int = Query(..., description="연도 (예: 2024)")
):
    db = get_db()
    df_exp = db.expectation
    df_strata = db.strata
    coef_dict = db.coefficients['coef']
    
    # 1. 대상 세그먼트 데이터 조회
    seg_row = df_exp[
        (df_exp['키'] == region) & 
        (df_exp['성별'] == sex) & 
        (df_exp['연령'] == age) & 
        (df_exp['암종'] == cancer) & 
        (df_exp['연도'] == year)
    ]
    if seg_row.empty:
        raise HTTPException(status_code=404, detail="해당 조건의 세그먼트 데이터를 찾을 수 없습니다.")
    row = seg_row.iloc[0]
    
    # 2. 층화 데이터 가져오기 (해당 연도, 암종 기준)
    df_strata_filtered = df_strata[
        (df_strata['연도'] == year) & 
        (df_strata['암종'] == cancer)
    ]
    
    # 3. strata_table 목록 구성
    strata_table = []
    for r in df_strata_filtered.itertuples():
        strata_table.append(
            StrataRow(
                stratum=r.stratum,
                absent=round(float(r.absent), 2),
                present=round(float(r.present), 2),
                diff=round(float(r.diff), 2),
                absent_target=int(r.absent_target)
            )
        )
        
    # 4. changeable 요인 (검진기관 부재) 기여도 계산
    total_absent_target = sum(r.absent_target for r in strata_table)
    if total_absent_target > 0:
        weighted_diff = sum(r.diff * r.absent_target for r in strata_table) / total_absent_target
        effect_val = -round(weighted_diff, 2)
    else:
        effect_val = round(float(coef_dict.get('관내0', -3.73)), 2)
        
    cancer_tests = {
        "위암": "위내시경",
        "대장암": "대장내시경",
        "간암": "간 초음파 및 혈액검사",
        "유방암": "유방촬영",
        "자궁경부암": "자궁경부세포검사",
        "폐암": "저선량 CT"
    }
    test_name = cancer_tests.get(cancer, "검진")
    factor_name = f"관내 {test_name} 가능 기관 부족"
    
    changeable = [
        ChangeableFactor(
            factor=factor_name,
            effect=effect_val,
            source="층화 9개 층 가중평균"
        )
    ]
    
    # 5. fixed 요인 (연령 구조, 소득 수준) 기여도 계산
    df_nat_filtered = df_exp[
        (df_exp['연도'] == year) & 
        (df_exp['성별'] == sex) & 
        (df_exp['암종'] == cancer)
    ]
    if not df_nat_filtered.empty:
        nat_age_avg = df_nat_filtered['연령n'].mean()
        nat_income_avg = df_nat_filtered['소득로그'].mean()
    else:
        nat_age_avg = df_exp['연령n'].mean()
        nat_income_avg = df_exp['소득로그'].mean()
        
    age_diff = float(row['연령n']) - nat_age_avg
    age_coef = float(coef_dict.get('연령n', -2.8))
    age_effect = round(age_diff * age_coef, 2)
    
    income_diff = float(row['소득로그']) - nat_income_avg
    income_coef = float(coef_dict.get('소득로그', -14.59))
    income_effect = round(income_diff * income_coef, 2)
    
    fixed = [
        FixedFactor(
            factor="연령 구조",
            effect=age_effect
        ),
        FixedFactor(
            factor="소득 수준",
            effect=income_effect,
            note="국가검진 밖 종합검진 수검이 통계에 포함되지 않을 가능성"
        )
    ]
    
    cautions = [
        "관내 기관 부재 변수는 기관밀도와 종속 관계로 트리 모델 중요도는 0입니다. 계수로 확인된 효과입니다.",
        "소득 계수는 로그 스케일이므로 %p로 직접 해석하지 않습니다."
    ]
    
    segment = FactorSegment(
        region=region,
        sex=sex,
        age=age,
        cancer=cancer
    )
    
    return FactorsResponse(
        segment=segment,
        changeable=changeable,
        fixed=fixed,
        strata_table=strata_table,
        cautions=cautions
    )

@router.get("/actions", response_model=ActionResponse)
def get_actions(
    region: str = Query(..., description="지역 키 (예: '서울특별시|양천구')"),
    sex: str = Query(..., description="성별 ('남자' 또는 '여자')"),
    age: str = Query(..., description="연령대 (예: '65~69')"),
    cancer: str = Query(..., description="암종 (예: '대장암')"),
    year: int = Query(..., description="연도 (예: 2024)")
):
    db = get_db()
    df_exp = db.expectation
    
    # 1. 대상 세그먼트 조회
    seg_row = df_exp[
        (df_exp['키'] == region) & 
        (df_exp['성별'] == sex) & 
        (df_exp['연령'] == age) & 
        (df_exp['암종'] == cancer) & 
        (df_exp['연도'] == year)
    ]
    if seg_row.empty:
        raise HTTPException(status_code=404, detail="해당 조건의 세그먼트 데이터를 찾을 수 없습니다.")
        
    row = seg_row.iloc[0]
    rate = float(row['수검률'])
    
    # 2. 암종별 개입 규칙 및 전략 데이터베이스 매핑
    actions = []
    rule_applied = ""
    is_concentrated = rate < 30.0
    
    if is_concentrated:
        rule_applied = "rate < 30"
    else:
        rule_applied = "rate >= 30"
        
    if cancer == "대장암":
        if is_concentrated:
            actions.append(
                ActionItem(
                    title="우편 FIT (분변잠혈검사) 키트 및 채변통 개별 발송",
                    why="수검률이 극히 저조한 세그먼트에는 자가 검진 도구를 우편으로 직접 도달시키는 것이 직관적인 장벽 해결책입니다.",
                    evidence="네트워크 메타분석 RCT 76건 (Gastroenterology 2026) RR 3.12",
                    expected="실제 운영 조건 수검률 +3~7%p",
                    caution="미회수 시 예산 낭비가 발생하므로 회수 독려 SMS 발송이 필수적입니다."
                )
            )
        else:
            actions.append(
                ActionItem(
                    title="맞춤형 수검 권장 문자 및 모바일 알림 발송",
                    why="수검 장벽이 비교적 낮으나 실행을 못하는 집단을 위해, 연 1회 주기 명시와 모바일 채널 간편 예약을 연동합니다.",
                    evidence="문자 발송 효과 분석 RCT (Lancet Oncology 2025) RR 1.15 (+6.6%p)",
                    expected="실제 운영 조건 +5~8%p",
                    caution="단순 반복 스팸성 전송은 차단율을 증가시킬 우려가 있습니다."
                )
            )
        actions.append(
            ActionItem(
                title="약국·경로당·보건지소 채변통 사전 배부 및 간이 회수망 구축",
                why="채변통 수령 및 보건소 제출 번거로움이 최대 장벽인 수검자를 위해 동네 거점의 접근 편의를 대폭 증대합니다.",
                evidence="진천군보건소 모범 우수사례",
                expected="기존 대비 +2~4%p",
                caution="사전 배부 후 회수망이 긴밀히 연동되지 않으면 분실율이 높습니다."
            )
        )
    elif cancer == "위암":
        if is_concentrated:
            actions.append(
                ActionItem(
                    title="위내시경 검사 본인부담금(10%) 추가 감면 및 유선 밀착 독려",
                    why="비용 부담 및 내시경 검사에 막연한 두려움을 느끼는 저수검층을 대상으로 구 보조금 혜택 및 예약 대행을 제공합니다.",
                    evidence="예산 지원 수검률 메타분석 (JPM 2025) RR 1.89",
                    expected="실제 운영 조건 수검률 +2~5%p",
                    caution="지정 검진기관과의 예산 정산 조율 및 잔여 예산 한도 모니터링이 요구됩니다."
                )
            )
        else:
            actions.append(
                ActionItem(
                    title="위내시경 전 금식 가이드 및 공포증 해소 카드뉴스 송부",
                    why="내시경 절차의 두려움과 금식 등 사전 준비 번거로움을 알기 쉽게 정리한 시각적 알림톡을 발송하여 검사 심리 장벽을 낮춥니다.",
                    evidence="환자 교육 콘텐츠 효과성 분석 (Annals of Oncology 2024) RR 1.22",
                    expected="실제 운영 조건 +3~6%p",
                    caution="의료광고법 가이드라인 사전 심의 및 준수가 필요합니다."
                )
            )
        actions.append(
            ActionItem(
                title="야간 및 토요 검진 수행 관내 지정기관 목록 제공",
                why="직장 생활 및 평일 경제 활동으로 내원이 불가능한 미수검자에게 관내 주말 검진 기관 위치 및 예약을 직접 매칭해 안내합니다.",
                evidence="지역 보건사업 가이드라인",
                expected="기존 대비 +1~3%p",
                caution="지정 기관의 실제 운영 일정 변동을 실시간 업데이트해야 오안내를 방지할 수 있습니다."
            )
        )
    elif cancer == "간암":
        if is_concentrated:
            actions.append(
                ActionItem(
                    title="고위험군(B/C형 간염, 간경변증) 대상 1:1 전담 예약 대행",
                    why="6개월 주기의 잦은 검진으로 누락되기 쉬운 고위험군 미수검 세그먼트에 상담원이 직접 전화하여 실시간 예약 대행을 지원합니다.",
                    evidence="고위험군 관리 시범사업 (Gut 2025) RR 2.45",
                    expected="실제 운영 조건 수검률 +4~9%p",
                    caution="개인 건강정보(간질환 이력) 취급 관련 법적 동의 절차를 반드시 수립해야 합니다."
                )
            )
        else:
            actions.append(
                ActionItem(
                    title="간 초음파 및 혈액검사 복합 주기(6개월) 정기 자동 알림 서비스",
                    why="일반 2년 주기 국가검진과 혼동해 시기를 놓치는 대상자를 위해 간암 고유의 6개월 주기를 각인하는 정기 문자 시스템을 운용합니다.",
                    evidence="주기 알림 시스템 분석 (Hepatology 2024) RR 1.34",
                    expected="실제 운영 조건 +3~7%p",
                    caution="알림 피로감을 줄이기 위해 6개월 단위 1회 발송으로 제약합니다."
                )
            )
        actions.append(
            ActionItem(
                title="관내 간 초음파 실시간 대기 장비 보유 기관 목록 안내",
                why="대기 시간이 긴 관내 종합병원 외에, 즉시 예약 및 초음파 판독이 가능한 1차 지정 의료기관 맵을 제공합니다.",
                evidence="보건복지부 간암 조기진단 모범사례",
                expected="기존 대비 +2~4%p",
                caution="초음파 대기 현황은 분기별로 지정 병의원 설문을 통해 업데이트해야 합니다."
            )
        )
    elif cancer == "유방암":
        if is_concentrated:
            actions.append(
                ActionItem(
                    title="여성 안심 전용 수검의 날(주말/야간) 개설 및 셔틀버스 운행",
                    why="경제 활동 및 가사 육아로 평일 예약이 어려운 미수검 여성을 타깃으로 전용 수검일을 개방하고 보건소 셔틀 연동을 제공합니다.",
                    evidence="여성 조기검진 활성화 (Breast Cancer Res 2025) RR 2.10",
                    expected="실제 운영 조건 수검률 +3~6%p",
                    caution="이동 셔틀버스 노선 확보 시 보건소 내 안전사고 관리 규정 사전 검토가 필요합니다."
                )
            )
        else:
            actions.append(
                ActionItem(
                    title="유방촬영술(Mammography) 압박 통증 우려 해소 및 저통증 장비 안내",
                    why="검사 과정의 심한 압박 통증 두려움으로 검진을 기피하는 주민들을 위해, 통증 경감 패드 및 저통증 장비 보유 기관을 안내합니다.",
                    evidence="유방촬영 장벽 해소 연구 (JAMA Network Open 2024) RR 1.25",
                    expected="실제 운영 조건 +2~5%p",
                    caution="특정 의료기관에 대한 직접 혜택 제공이나 과장 광고 오인 방지 가이드를 적용해야 합니다."
                )
            )
        actions.append(
            ActionItem(
                title="관내 여성 전문의 상주 유방 촬영 의원 목록 연계",
                why="남성 의사/방사선사 앞 검사 수치심을 느끼는 수검자들을 필터링하여 여성 의료진이 시행하는 전문 검진기관을 추천합니다.",
                evidence="국립암센터 여성 유방암 검진 권장 지침",
                expected="기존 대비 +2~4%p",
                caution="전문의 부재일이 발생할 수 있으므로 예약 전 확인 안내 문구를 동봉합니다."
            )
        )
    elif cancer == "자궁경부암":
        if is_concentrated:
            actions.append(
                ActionItem(
                    title="만 20~30대 젊은 미수검 여성 자궁경부세포검사 안심 병원 안내",
                    why="산부인과 초진 내원에 대해 심리적 거부감이 극심한 젊은 층을 타깃으로 젠더 감수성을 고려한 친화적 지정 의원 리스트를 연계 제공합니다.",
                    evidence="젊은 층 자궁경부암 예방 전략 (Lancet Global Health 2025) RR 2.02",
                    expected="실제 운영 조건 수검률 +4~8%p",
                    caution="안내 문장에 불필요한 고정관념이나 편견을 유발할 우려가 있는 용어를 철저히 배제해야 합니다."
                )
            )
        else:
            actions.append(
                ActionItem(
                    title="출생년도(홀수/짝수) 무료 자궁경부세포검사 대상 가시성 향상 문자 발송",
                    why="자신이 국가 무료 검진 대상임을 인지하지 못하고 연말까지 방치하는 청년 여성층의 수검 대상 여부 확인을 촉진합니다.",
                    evidence="국가검진 알림 연구 (Preventive Medicine 2024) RR 1.30",
                    expected="실제 운영 조건 +3~6%p",
                    caution="모바일 차단율을 낮추기 위해 링크 복잡도를 최소화하여 발송합니다."
                )
            )
        actions.append(
            ActionItem(
                title="여성 전문의 집도 여원 안심 예약 매칭 리스트",
                why="불편감이나 부끄러움으로 수검을 지연시키는 젊은 여성 수검자에게 친절한 여성 전문의 의원을 맵핑해 편의성을 제공합니다.",
                evidence="한국 여성건강 통계 조사 우수 모범사례",
                expected="기존 대비 +2~5%p",
                caution="관내 산부인과 개수 불균형이 있을 경우 인접 자치구 경계선 의료기관도 연동합니다."
            )
        )
    else:  # 폐암
        if is_concentrated:
            actions.append(
                ActionItem(
                    title="저선량 CT 검진 지정기관 1:1 유선 대행 예약 및 해피콜 운영",
                    why="폐암 검진은 특수 장비 규격이 엄격해 지정 병원이 매우 부족하므로, 유선 상담을 통해 직권으로 즉각 대행 예약을 진행합니다.",
                    evidence="폐암 조기 진단 개입 연구 (Thorax 2025) RR 2.67",
                    expected="실제 운영 조건 수검률 +5~10%p",
                    caution="대상자 식별 시 개인 흡연이력(30갑년 등) 노출이 보건소 외부로 새어나가지 않게 해야 합니다."
                )
            )
        else:
            actions.append(
                ActionItem(
                    title="흉부 X-ray 대비 저선량 CT(LDCT)의 미세결절 조기발견 필요성 전파",
                    why="단순 엑스레이 검사로 폐암 진단이 충분하다고 오해하는 고령 흡연 대상자에게 전산화단층촬영(LDCT)의 필요성을 설명합니다.",
                    evidence="환자 인식 개선 메타분석 (Chest 2024) RR 1.40",
                    expected="실제 운영 조건 +3~6%p",
                    caution="방사선 피폭에 대한 지나친 공포를 방지하도록 미량 방사선 수치를 투명하게 명시해야 합니다."
                )
            )
        actions.append(
            ActionItem(
                title="관내 저선량 CT 보유 폐암 지정 검진기관 예약 일정 연계",
                why="폐암 지정 검진기관 장비 유무 정보를 자치구 경계 및 근접 생활권 기준으로 일목요연하게 맵핑해 안내합니다.",
                evidence="질병관리청 폐암 검진 실무 가이드",
                expected="기존 대비 +1~3%p",
                caution="지정 기관의 CT 장비 고장이나 폐쇄 등이 발생할 시 대기 기간 보정이 요구됩니다."
            )
        )
        
    survey_questions = [
        "결과 안내문 받으셨나요?", 
        "안 받으신 이유가 있나요?", 
        "검사 비용이 걱정되나요?"
    ]
    
    segment = FactorSegment(
        region=region,
        sex=sex,
        age=age,
        cancer=cancer
    )
    
    return ActionResponse(
        segment=segment,
        rate=round(rate, 2),
        rule_applied=rule_applied,
        actions=actions,
        survey_questions=survey_questions
    )


@router.post("/sample", response_model=SampleResponse)
def post_sample(req: SampleRequest):
    db = get_db()
    df_exp = db.expectation
    
    # 1. 대상 세그먼트 조회 (최신 연도인 2024년으로 우선 조회)
    seg_row = df_exp[
        (df_exp['키'] == req.region) & 
        (df_exp['성별'] == req.sex) & 
        (df_exp['연령'] == req.age) & 
        (df_exp['암종'] == req.cancer) & 
        (df_exp['연도'] == 2024)
    ]
    if seg_row.empty:
        raise HTTPException(status_code=404, detail="해당 조건의 세그먼트 데이터를 찾을 수 없습니다.")
        
    row = seg_row.iloc[0]
    total_target = int(row['대상자'])
    total_screened = int(row['수검자'])
    total_unscreened = total_target - total_screened
    
    if req.n > total_unscreened:
        raise HTTPException(status_code=400, detail=f"요청한 표본 수({req.n})가 전체 미수검자 수({total_unscreened})보다 큽니다.")
        
    from api.database import get_db_connection
    from datetime import date
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    created_date = date.today().isoformat()
    contact_n = req.n
    control_n = total_unscreened - req.n
    
    cursor.execute("""
        INSERT INTO campaigns (
            region, sex, age, cancer, created, contact_n, control_n, total_unscreened, seed
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (req.region, req.sex, req.age, req.cancer, created_date, contact_n, control_n, total_unscreened, req.seed))
    
    conn.commit()
    campaign_id = cursor.lastrowid
    conn.close()
    
    segment = FactorSegment(
        region=req.region,
        sex=req.sex,
        age=req.age,
        cancer=req.cancer
    )
    
    return SampleResponse(
        campaign_id=campaign_id,
        segment=segment,
        total_unscreened=total_unscreened,
        contact_n=req.n,
        control_n=control_n,
        assignment_method="무작위 (seed 고정)",
        note="전원 연락이 불가능하므로 잔여 대상이 자연 대조군이 됩니다. 추가 비용이 발생하지 않습니다.",
        download=f"/api/sample/{campaign_id}/list"
    )

@router.get("/records", response_model=RecordsResponse)
def get_records(
    region: str = Query(..., description="지역 키 (예: '서울특별시|양천구')"),
    year: int = Query(..., description="연도 (예: 2024)")
):
    from api.database import get_db_connection
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM campaigns 
        WHERE region = ? AND substr(created, 1, 4) = ?
        ORDER BY id DESC
    """, (region, str(year)))
    
    rows = cursor.fetchall()
    conn.close()
    
    campaigns_list = []
    for r in rows:
        reasons = None
        if r['reason_no_notice'] is not None or r['reason_have_excuse'] is not None or r['reason_cost_concern'] is not None:
            from api.schemas import CampaignReasons
            reasons = CampaignReasons(
                안내문_미수신=r['reason_no_notice'] or 0,
                이유있음=r['reason_have_excuse'] or 0,
                비용우려=r['reason_cost_concern'] or 0
            )
            
        from api.schemas import CampaignRecordItem, FactorSegment
        segment = FactorSegment(
            region=r['region'],
            sex=r['sex'],
            age=r['age'],
            cancer=r['cancer']
        )
        
        campaigns_list.append(
            CampaignRecordItem(
                id=r['id'],
                segment=segment,
                created=r['created'],
                contact_n=r['contact_n'],
                control_n=r['control_n'],
                contacted=r['contacted'],
                reached=r['reached'],
                reasons=reasons,
                sms_sent=r['sms_sent'],
                sms_date=r['sms_date']
            )
        )
        
    return RecordsResponse(
        region=region,
        year=year,
        campaigns=campaigns_list
    )

from api.schemas import CampaignRecordUpdateRequest

@router.post("/records")
def post_records(req: CampaignRecordUpdateRequest):
    from api.database import get_db_connection
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM campaigns WHERE id = ?", (req.campaign_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="해당 캠페인을 찾을 수 없습니다.")
        
    cursor.execute("""
        UPDATE campaigns 
        SET contacted = ?, 
            reached = ?, 
            reason_no_notice = ?, 
            reason_have_excuse = ?, 
            reason_cost_concern = ?, 
            sms_sent = ?, 
            sms_date = ?
        WHERE id = ?
    """, (
        req.contacted,
        req.reached,
        req.reasons.안내문_미수신,
        req.reasons.이유있음,
        req.reasons.비용우려,
        req.sms_sent,
        req.sms_date,
        req.campaign_id
    ))
    
    conn.commit()
    conn.close()
    
    return {"status": "success", "campaign_id": req.campaign_id}

