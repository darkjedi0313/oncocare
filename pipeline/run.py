import os
import sys
import argparse
import zipfile
import pandas as pd
import numpy as np
import openpyxl

sys.stdout.reconfigure(encoding='utf-8')

# 시도 표준화 맵
SIDO_MAP = {"강원도": "강원특별자치도", "전라북도": "전북특별자치도"}

def norm_sido(s: str) -> str:
    s = str(s).strip()  # 후행 공백 제거 (결함 2)
    return SIDO_MAP.get(s, s)  # 개편 명칭 통일 (결함 1)

# 소득 데이터 시도 분할용
SIDO_LIST = [
    '서울특별시', '부산광역시', '대구광역시', '인천광역시', '광주광역시', '대전광역시', '울산광역시', 
    '세종특별자치시', '경기도', '강원특별자치도', '충청북도', '충청남도', 
    '전북특별자치도', '전라남도', '경상북도', '경상남도', '제주특별자치도',
    '강원도', '전라북도'  # 표준화 전 명칭도 매칭에 포함
]

def split_income_sido_sgg(s: str) -> tuple:
    s = str(s).strip()
    for sido in SIDO_LIST:
        if s.startswith(sido):
            sgg = s[len(sido):].strip()
            return norm_sido(sido), sgg
    return "미분류", s

def stage_s1():
    print("\n========== Stage S1: 원천 데이터 수집 및 로드 ==========")
    raw_dir = "data/raw"
    interim_dir = "data/interim"
    os.makedirs(interim_dir, exist_ok=True)

    # 1. 암검진 현황 데이터 로드
    screening_path = os.path.join(raw_dir, "국민건강보험공단_시군구별_성별_암검진_대상_및_수검인원_현황_20241231.xlsx")
    if not os.path.exists(screening_path):
        print(f"Error: {screening_path} 파일이 없습니다.")
        sys.exit(1)
    
    print("암검진 현황 로딩 중...")
    wb = openpyxl.load_workbook(screening_path, read_only=True)
    sheets = [s for s in wb.sheetnames if s != "2021"]  # 2021년 제외 (결함 3)
    print(f"로드할 연도 시트: {sheets}")

    screening_dfs = []
    for sheet in sheets:
        df = pd.read_excel(screening_path, sheet_name=sheet)
        # 연도 컬럼 파싱 (ex: '2020년' -> 2020)
        if '건강검진사업년도' in df.columns:
            df['연도'] = df['건강검진사업년도'].astype(str).str.replace('년', '').astype(int)
        else:
            df['연도'] = int(sheet)
        screening_dfs.append(df)
    
    screening_df = pd.concat(screening_dfs, ignore_index=True)
    print(f"암검진 현황 통합 완료: {screening_df.shape[0]}행 로드됨.")
    
    # 2. 검진기관 현황 데이터 로드
    inst_path = os.path.join(raw_dir, "국민건강보험공단_시군구별_검진기관_현황_20241231.xlsx")
    if not os.path.exists(inst_path):
        print(f"Error: {inst_path} 파일이 없습니다.")
        sys.exit(1)
        
    print("검진기관 현황 로딩 중 (2020년 기준)...")
    inst_df = pd.read_excel(inst_path, sheet_name="2020", skiprows=1)
    print(f"검진기관 로드됨: {inst_df.shape[0]}행.")
    
    # 3. 평균소득 데이터 로드
    income_path = os.path.join(raw_dir, "국민연금공단_자격_시구신고_평균소득월액_20241231.csv")
    if not os.path.exists(income_path):
        print(f"Error: {income_path} 파일이 없습니다.")
        sys.exit(1)
        
    print("평균소득 데이터 로딩 중...")
    income_df = pd.read_csv(income_path, encoding='cp949')
    print(f"평균소득 로드됨: {income_df.shape[0]}행.")
    
    # 4. 적용인구 데이터 로드
    pop_path = os.path.join(raw_dir, "국민건강보험공단_월별_시군구별_성별_연령별_직역별_건강보험_적용인구_20241231.csv")
    if not os.path.exists(pop_path):
        print(f"Error: {pop_path} 파일이 없습니다.")
        sys.exit(1)
        
    print("적용인구 데이터 로딩 중...")
    pop_df = pd.read_csv(pop_path, encoding='cp949')
    print(f"적용인구 로드됨: {pop_df.shape[0]}행.")
    
    # 5. 국가건강검진 현황자료 (일반검진 및 대장암 판정 결과)
    zip_path = os.path.join(raw_dir, "국민건강보험공단_시군구별_국가건강검진_현황자료(일반검진_암검진)_20231231.zip")
    if not os.path.exists(zip_path):
        print(f"Error: {zip_path} 파일이 없습니다.")
        sys.exit(1)
        
    print("국가건강검진 현황자료 zip 파싱 중...")
    with zipfile.ZipFile(zip_path) as z:
        names = z.namelist()
        general_file = [n for n in names if '1' in n and n.endswith('.xlsx')][0]
        colon_file = [n for n in names if '3' in n and n.endswith('.xlsx')][0]
        
        print(f"  - 일반검진 파일 추출: {general_file}")
        with z.open(general_file) as f:
            general_df = pd.read_excel(f, sheet_name="2023")
            
        print(f"  - 대장암 판정 파일 추출: {colon_file}")
        with z.open(colon_file) as f:
            colon_df = pd.read_excel(f, sheet_name="2023")
            
    # parquet 포맷 중간 저장 (문자열 캐스팅으로 pyarrow 호환성 보장)
    screening_df.astype(str).to_parquet(os.path.join(interim_dir, "s1_screening.parquet"), index=False)
    inst_df.astype(str).to_parquet(os.path.join(interim_dir, "s1_inst.parquet"), index=False)
    income_df.astype(str).to_parquet(os.path.join(interim_dir, "s1_income.parquet"), index=False)
    pop_df.astype(str).to_parquet(os.path.join(interim_dir, "s1_pop.parquet"), index=False)
    general_df.astype(str).to_parquet(os.path.join(interim_dir, "s1_general.parquet"), index=False)
    colon_df.astype(str).to_parquet(os.path.join(interim_dir, "s1_colon.parquet"), index=False)
    
    print("Stage S1 완료 및 parquet 백업 완료.")

def stage_s2():
    print("\n========== Stage S2: 데이터 정제 및 키 생성 ==========")
    interim_dir = "data/interim"
    
    # 1. 암검진 데이터 정제
    df = pd.read_parquet(os.path.join(interim_dir, "s1_screening.parquet"))
    df['연도'] = pd.to_numeric(df['연도'], errors='coerce').fillna(0).astype(int)
    df['시도'] = df['시도'].apply(norm_sido)
    df['시군구'] = df['시군구'].astype(str).str.strip()
    df['키'] = df['시도'] + '|' + df['시군구']
    
    # 행정구역 계층 불일치 해결 키 (부천시, 세종시 처리)
    df['키_시'] = df['키'].str.replace(r'부천시 (소사|오정|원미)구', '부천시', regex=True)
    df['키_시'] = df['키_시'].replace({'세종특별자치시|세종시': '세종특별자치시|'})
    
    # 검증 게이트
    unique_sidos = df['시도'].unique()
    num_sidos = len(unique_sidos)
    blank_sidos = df['시도'].str.endswith(' ').sum()
    
    print(f"검증 게이트 - 시도 수: {num_sidos}개 (기준: 17개)")
    print(f"검증 게이트 - 시도명 후행 공백 수: {blank_sidos}건 (기준: 0건)")
    if num_sidos != 17 or blank_sidos != 0:
        print("Warning: S2 검증 기준을 만족하지 못했습니다.")
        print(f"발견된 시도 목록: {unique_sidos}")
        
    df.to_parquet(os.path.join(interim_dir, "s2_screening.parquet"), index=False)

    # 2. 검진기관 데이터 정제
    inst = pd.read_parquet(os.path.join(interim_dir, "s1_inst.parquet"))
    inst = inst.replace('nan', np.nan).replace('None', np.nan)
    
    # 첫번째 행을 실제 컬럼명으로 변경
    orig_cols = inst.iloc[0].tolist()
    new_cols = [str(x).strip() for x in orig_cols]
    inst.columns = new_cols
    inst = inst.iloc[1:].copy()  # 첫행 드랍
    
    inst = inst.rename(columns={'시도명': '시도', '시군구명': '시군구'})
    inst['시도'] = inst['시도'].ffill().apply(norm_sido)
    inst['시군구'] = inst['시군구'].astype(str).str.strip()
    inst = inst[~inst['시군구'].isin(['총계', '소계'])]
    
    inst['키'] = inst['시도'] + '|' + inst['시군구']
    
    inst_cols = {
        '위암': '기관_위암', '대장암': '기관_대장암', '간암': '기관_간암',
        '유방암': '기관_유방암', '자궁경부암': '기관_자궁경부암', '폐암': '기관_폐암',
        '암 전체': '기관_전체'
    }
    
    col_mapping = {}
    for col in inst.columns:
        val = str(col).strip()
        if val in inst_cols:
            col_mapping[col] = inst_cols[val]
            
    inst = inst.rename(columns=col_mapping)
    keep_cols = ['키', '기관_위암', '기관_대장암', '기관_간암', '기관_유방암', '기관_자궁경부암', '기관_폐암', '기관_전체']
    inst = inst[keep_cols].copy()
    
    for c in keep_cols[1:]:
        inst[c] = pd.to_numeric(inst[c], errors='coerce').fillna(0).astype(int)
        
    inst.to_parquet(os.path.join(interim_dir, "s2_inst.parquet"), index=False)

    # 3. 평균소득 데이터 정제
    income = pd.read_parquet(os.path.join(interim_dir, "s1_income.parquet"))
    income['연도'] = income['기준년월'].astype(str).str.split('-').str[0].astype(int)
    
    split_res = income['시군구'].apply(split_income_sido_sgg)
    income['시도'] = [r[0] for r in split_res]
    income['시군구_명'] = [r[1] for r in split_res]
    income['키'] = income['시도'] + '|' + income['시군구_명']
    
    income['평균소득월액'] = pd.to_numeric(income['평균소득월액'], errors='coerce').fillna(0).astype(int)
    
    income = income[['연도', '키', '평균소득월액']].copy()
    income.to_parquet(os.path.join(interim_dir, "s2_income.parquet"), index=False)

    # 4. 적용인구 데이터 정제 (2024년 12월 기준 시군구별 적용인구수 합산)
    pop = pd.read_parquet(os.path.join(interim_dir, "s1_pop.parquet"))
    pop = pop[pop['기준년월'] == '2024-12'].copy()
    pop['시도'] = pop['시도'].apply(norm_sido)
    pop['시군구'] = pop['시군구'].astype(str).str.strip()
    pop['키'] = pop['시도'] + '|' + pop['시군구']
    
    pop['건강보험적용인구수'] = pd.to_numeric(pop['건강보험적용인구수'], errors='coerce').fillna(0).astype(int)
    
    pop_agg = pop.groupby('키')['건강보험적용인구수'].sum().reset_index()
    
    # [군위군 예외 처리] 대구광역시 군위군 인구값을 경상북도 군위군 키로 복제
    if '대구광역시|군위군' in pop_agg['키'].values:
        val = pop_agg[pop_agg['키'] == '대구광역시|군위군']['건강보험적용인구수'].values[0]
        if '경상북도|군위군' not in pop_agg['키'].values:
            pop_agg = pd.concat([
                pop_agg, 
                pd.DataFrame([{'키': '경상북도|군위군', '건강보험적용인구수': val}])
            ], ignore_index=True)
            
    pop_agg.to_parquet(os.path.join(interim_dir, "s2_pop.parquet"), index=False)
    print("Stage S2 완료.")

def stage_s3():
    print("\n========== Stage S3: 데이터 결합 ==========")
    interim_dir = "data/interim"
    
    df = pd.read_parquet(os.path.join(interim_dir, "s2_screening.parquet"))
    inst = pd.read_parquet(os.path.join(interim_dir, "s2_inst.parquet"))
    income = pd.read_parquet(os.path.join(interim_dir, "s2_income.parquet"))
    pop = pd.read_parquet(os.path.join(interim_dir, "s2_pop.parquet"))
    
    orig_len = len(df)
    
    # 1. 검진기관 결합 (left join via 키_시)
    df = df.merge(inst, left_on='키_시', right_on='키', how='left', suffixes=('', '_inst'))
    if '키_inst' in df.columns:
        df = df.drop(columns=['키_inst'])
    
    # 2. 평균소득 결합
    inc_a = income.rename(columns={'평균소득월액': '소득_정확'})
    inc_b = income.rename(columns={'평균소득월액': '소득_시단위'})
    
    df = df.merge(inc_a, on=['연도', '키'], how='left')
    df['키2'] = df['키_시']
    
    inc_b = inc_b.rename(columns={'키': '키2'})
    df = df.merge(inc_b, on=['연도', '키2'], how='left')
    df['소득'] = df['소득_정확'].fillna(df['소득_시단위'])
    
    # 3. 적용인구 결합
    pop_a = pop.rename(columns={'건강보험적용인구수': '적용인구'})
    df = df.merge(pop_a, on='키', how='left')
    
    df = df.drop(columns=['소득_정확', '소득_시단위'])
    
    # 매칭률 계산
    inst_match_rate = (df['기관_위암'].notna()).sum() / len(df) * 100
    income_match_rate = (df['소득'].notna()).sum() / len(df) * 100
    pop_match_rate = (df['적용인구'].notna()).sum() / len(df) * 100
    
    print(f"결합 완료 후 행수: {len(df)} (원본 행수: {orig_len})")
    print(f"검증 게이트 - 검진기관 매칭률: {inst_match_rate:.2f}% (기준: ≥ 99%)")
    print(f"검증 게이트 - 소득 매칭률: {income_match_rate:.2f}% (기준: ≥ 85%)")
    print(f"검증 게이트 - 적용인구 매칭률: {pop_match_rate:.2f}% (기준: ≥ 99%)")
    
    if inst_match_rate < 99.0 or income_match_rate < 85.0 or pop_match_rate < 99.0:
        print("Warning: S3 결합 매칭률 기준 미달!")
        
    df.to_parquet(os.path.join(interim_dir, "s3_combined.parquet"), index=False)
    print("Stage S3 완료 및 s3_combined.parquet 저장 성공.")

def stage_s4():
    print("\n========== Stage S4: wide -> long 전개 ==========")
    interim_dir = "data/interim"
    s3_path = os.path.join(interim_dir, "s3_combined.parquet")
    
    if not os.path.exists(s3_path):
        print(f"Error: {s3_path} 파일이 없습니다. S3 단계를 먼저 실행하세요.")
        sys.exit(1)
        
    df = pd.read_parquet(s3_path)
    
    # 성별, 연령대 컬럼 rename
    df = df.rename(columns={'성별코드': '성별', '연령대(5세단위)': '연령'})
    
    BASE_COLS = ['연도', '시도', '시군구', '성별', '연령', '키', '키_시', '소득', '적용인구', '기관_전체']
    CANCERS = ['위암', '대장암', '간암', '유방암', '자궁경부암', '폐암']
    
    frames = []
    for c in CANCERS:
        t = df[BASE_COLS + [f'기관_{c}', f'{c}_대상자수', f'{c}_수검자수']].copy()
        t.columns = BASE_COLS + ['기관수', '대상자', '수검자']
        t['암종'] = c
        frames.append(t)
        
    L = pd.concat(frames, ignore_index=True)
    
    L['대상자'] = pd.to_numeric(L['대상자'], errors='coerce')
    L['수검자'] = pd.to_numeric(L['수검자'], errors='coerce')
    L['기관수'] = pd.to_numeric(L['기관수'], errors='coerce').fillna(0).astype(int)
    L['기관_전체'] = pd.to_numeric(L['기관_전체'], errors='coerce').fillna(0).astype(int)
    L['소득'] = pd.to_numeric(L['소득'], errors='coerce')
    L['적용인구'] = pd.to_numeric(L['적용인구'], errors='coerce')
    
    # 정의상 없는 조합 제거
    L = L[L['대상자'].notna() & (L['대상자'] > 0)].copy()
    
    # 수검률 계산
    L['수검률'] = L['수검자'] / L['대상자'] * 100
    
    row_count = len(L)
    out_of_bounds = ((L['수검률'] < 0) | (L['수검률'] > 100)).sum()
    
    print(f"검증 게이트 - 전개 완료 후 행수: {row_count}행 (기준: 89,299행 ± 100)")
    print(f"검증 게이트 - 수검률 범위 초과 건수 (0~100 이외): {out_of_bounds}건 (기준: 0건)")
    
    L.to_parquet(os.path.join(interim_dir, "s4_long.parquet"), index=False)
    print("Stage S4 완료.")

def stage_s5():
    print("\n========== Stage S5: 파생 피처 및 시차변수 생성 ==========")
    interim_dir = "data/interim"
    processed_dir = "data/processed"
    os.makedirs(processed_dir, exist_ok=True)
    
    s4_path = os.path.join(interim_dir, "s4_long.parquet")
    if not os.path.exists(s4_path):
        print(f"Error: {s4_path} 파일이 없습니다. S4 단계를 먼저 실행하세요.")
        sys.exit(1)
        
    L = pd.read_parquet(s4_path)
    
    # 1. 15종 피처 생성
    L['소득로그'] = np.log(L['소득'].clip(lower=1))
    
    region_pop_sum = L.groupby(['연도', '키'])['대상자'].transform('sum')
    L['인구로그'] = np.log(region_pop_sum.clip(lower=1))
    
    L['기관밀도'] = L['기관수'] / (region_pop_sum / 10000)
    L['기관밀도'] = L['기관밀도'].fillna(0)
    
    L['관내0'] = (L['기관수'] == 0).astype(int)
    
    L['기관전체밀도'] = L['기관_전체'] / (region_pop_sum / 10000)
    L['기관전체밀도'] = L['기관전체밀도'].fillna(0)
    
    L['군'] = L['시군구'].astype(str).str.strip().str.endswith('군').astype(int)
    L['구'] = L['시군구'].astype(str).str.strip().str.endswith('구').astype(int)
    
    AGE_LIST = ['20~24', '25~29', '30~34', '35~39', '40~44', '45~49', '50~54', 
                '55~59', '60~64', '65~69', '70~74', '75~79', '80~84', '85이상']
    AGE_MAP = {age: i for i, age in enumerate(AGE_LIST)}
    L['연령n'] = L['연령'].map(AGE_MAP).fillna(0).astype(int)
    L['여자'] = (L['성별'] == '여자').astype(int)
    
    CANCERS = ['위암', '대장암', '간암', '유방암', '자궁경부암', '폐암']
    for c in CANCERS:
        L[f'암_{c}'] = (L['암종'] == c).astype(int)
        
    # 2. 시차 변수 생성
    lookup = L.set_index(['키', '성별', '연령', '암종', '연도'])['수검률'].to_dict()
    
    prev_rates = []
    for r in L.itertuples():
        prev_year = r.연도 - 1
        # 군위군 편입 예외 처리 (2023년 대구 군위군 -> 2022년 경북 군위군)
        prev_key = '경상북도|군위군' if (r.연도 == 2023 and r.키 == '대구광역시|군위군') else r.키
        prev_rates.append(lookup.get((prev_key, r.성별, r.연령, r.암종, prev_year), np.nan))
    L['전년수검률'] = prev_rates
    
    # 2023, 2024년 세그먼트 중 결측 피처 제거 (기획서 37,672행 복원)
    L_filtered = L[L['연도'].isin([2023, 2024])].copy()
    
    # 주요 피처 및 수검률, 시차수검률 전체에 대해 결측 제거
    L_filtered = L_filtered.dropna(subset=['소득', '적용인구', '수검률', '전년수검률']).copy()
    
    row_count = len(L_filtered)
    target_features = ['소득로그', '인구로그', '기관밀도', '관내0', '기관전체밀도', '군', '구', '연령n', '여자', '전년수검률'] + [f'암_{c}' for c in CANCERS]
    na_count = L_filtered[target_features].isna().sum().sum()
    
    print(f"검증 게이트 - 필터링 후 행수: {row_count}행 (기준: 37,672행)")
    print(f"검증 게이트 - 15종 피처 및 시차변수 결측 수: {na_count}건 (기준: 0건)")
    
    L_filtered.to_parquet(os.path.join(processed_dir, "segments.parquet"), index=False)
    print("Stage S5 완료 및 segments.parquet 저장 완료.")

def stage_s6():
    print("\n========== Stage S6: 시간 분할 검증 ==========")
    processed_dir = "data/processed"
    segments_path = os.path.join(processed_dir, "segments.parquet")
    
    if not os.path.exists(segments_path):
        print(f"Error: {segments_path} 파일이 없습니다. S5 단계를 먼저 실행하세요.")
        sys.exit(1)
        
    df = pd.read_parquet(segments_path)
    
    tr = df[df['연도'] == 2023].copy()
    te = df[df['연도'] == 2024].copy()
    
    tr_len = len(tr)
    te_len = len(te)
    
    tr_mean = tr['수검률'].mean()
    te_mean = te['수검률'].mean()
    diff = abs(tr_mean - te_mean)
    
    print(f"검증 게이트 - 학습 데이터 행수: {tr_len}행 (기준: 18,859행)")
    print(f"검증 게이트 - 검증 데이터 행수: {te_len}행 (기준: 18,813행)")
    print(f"검증 게이트 - 학습/검증 수검률 평균 편차: {diff:.4f}%p (기준: ≤ 1.0%p)")
    
    print("Stage S6 완료.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="OncoCare Data Preprocessing Pipeline")
    parser.add_argument('--stage', type=str, required=True, choices=['s1', 's2', 's3', 's4', 's5', 's6', 'all'],
                        help="실행할 파이프라인 단계 (s1, s2, s3, s4, s5, s6, all)")
    args = parser.parse_args()
    
    if args.stage == 's1':
        stage_s1()
    elif args.stage == 's2':
        stage_s2()
    elif args.stage == 's3':
        stage_s3()
    elif args.stage == 's4':
        stage_s4()
    elif args.stage == 's5':
        stage_s5()
    elif args.stage == 's6':
        stage_s6()
    elif args.stage == 'all':
        stage_s1()
        stage_s2()
        stage_s3()
        stage_s4()
        stage_s5()
        stage_s6()
