import os
import json
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors

def run_similar():
    print("\n========== [similar.py] kNN 유사 지역 매칭 ==========")
    
    segments_path = "data/processed/segments.parquet"
    if not os.path.exists(segments_path):
        print(f"Error: {segments_path} 파일이 없습니다. 파이프라인을 먼저 실행하세요.")
        return False
        
    df = pd.read_parquet(segments_path)
    
    # 1. 시군구 단위 고유 프로필 생성 (최근 연도 데이터 기준)
    # 소득로그, 인구로그, 군, 구, 기관전체밀도는 지역 수준 변수임
    sgg_cols = ['시도', '시군구', '소득로그', '인구로그', '군', '구', '기관전체밀도']
    df_sgg = df.drop_duplicates(subset=['시도', '시군구'], keep='last')[sgg_cols].copy()
    df_sgg['키'] = df_sgg['시도'] + '|' + df_sgg['시군구']
    
    # 인덱스를 '키'로 설정하여 이웃 매칭 시 키 조회가 쉽도록 함
    df_sgg = df_sgg.set_index('키')
    print(f"시군구 수: {df_sgg.shape[0]}개")
    
    # 2. 피처 표준화
    features = ['소득로그', '인구로그', '군', '구', '기관전체밀도']
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(df_sgg[features])
    
    # 3. NearestNeighbors를 이용한 유사 20곳 매칭
    # 자신을 포함하여 21개를 찾은 뒤, 첫번째(자신)를 제외
    knn = NearestNeighbors(n_neighbors=21, metric='euclidean')
    knn.fit(scaled_features)
    
    distances, indices = knn.kneighbors(scaled_features)
    
    similar_regions = {}
    sgg_keys = df_sgg.index.tolist()
    
    for i, key in enumerate(sgg_keys):
        # 자신(index i)을 제외한 20개 이웃
        neighbor_indices = indices[i][1:]
        neighbors = [sgg_keys[idx] for idx in neighbor_indices]
        similar_regions[key] = neighbors
        
    # JSON 저장
    output_json = "data/processed/similar_regions.json"
    os.makedirs(os.path.dirname(output_json), exist_ok=True)
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(similar_regions, f, ensure_ascii=False, indent=2)
    print(f"산출물 저장 완료: {output_json}")
    
    # 도농 일치율 검증
    # 도농 구분은 '군' 및 '구' 피처가 일치하는지 여부로 판정
    match_count = 0
    total_neighbors = 0
    for key, neighbors in similar_regions.items():
        base_is_gun = df_sgg.loc[key, '군']
        base_is_gu = df_sgg.loc[key, '구']
        for n in neighbors:
            n_is_gun = df_sgg.loc[n, '군']
            n_is_gu = df_sgg.loc[n, '구']
            if base_is_gun == n_is_gun and base_is_gu == n_is_gu:
                match_count += 1
            total_neighbors += 1
            
    rural_urban_match_rate = match_count / total_neighbors * 100
    print(f"검증 게이트 - 도농 일치율: {rural_urban_match_rate:.2f}% (기준: ≥ 95%)")
    
    # 4. 세그먼트 단위 유사 지역 실제 수검률 가중평균 및 범위/SE 산출 (similar_rates.parquet)
    # 효율적인 판다스 병합을 위해 (키, 유사키) 쌍의 DataFrame 생성
    pairs = []
    for k, vs in similar_regions.items():
        for v in vs:
            pairs.append((k, v))
    mapping = pd.DataFrame(pairs, columns=['키', '유사키'])
    
    # segments 데이터에 mapping 머지
    df_mapped = df.merge(mapping, on='키')
    
    # 유사키에 해당하는 segments 데이터 조인
    df_ref = df[['연도', '성별', '연령', '암종', '키', '대상자', '수검자', '수검률']].rename(
        columns={
            '키': '유사키', 
            '대상자': '유사_대상자', 
            '수검자': '유사_수검자', 
            '수검률': '유사_수검률'
        }
    )
    
    df_joined = df_mapped.merge(df_ref, on=['연도', '성별', '연령', '암종', '유사키'])
    
    # 그룹 연산을 통해 가중평균, 최소, 최대, 표준오차 산출
    # 표본수가 다를 수 있으므로 표준오차 계산 시 실제 매칭 수(N)를 카운트하여 계산
    # 20개 지역의 수검률 표준편차 / sqrt(N)
    group_cols = ['연도', '시도', '시군구', '성별', '연령', '암종', '키']
    agg_res = df_joined.groupby(group_cols).agg(
        유사_대상자_sum=('유사_대상자', 'sum'),
        유사_수검자_sum=('유사_수검자', 'sum'),
        유사_최소=('유사_수검률', 'min'),
        유사_최대=('유사_수검률', 'max'),
        유사_std=('유사_수검률', 'std'),
        유사_count=('유사_수검률', 'count')
    ).reset_index()
    
    agg_res['유사_평균'] = agg_res['유사_수검자_sum'] / agg_res['유사_대상자_sum'] * 100
    agg_res['유사_SE'] = agg_res['유사_std'] / np.sqrt(agg_res['유사_count'])
    
    # 결측치 처리 (std가 NaN인 경우 등)
    agg_res['유사_SE'] = agg_res['유사_SE'].fillna(0)
    
    # 최종 결과 컬럼 필터링 및 저장
    keep_cols = ['연도', '시도', '시군구', '성별', '연령', '암종', '유사_평균', '유사_최소', '유사_최대', '유사_SE']
    similar_rates = agg_res[keep_cols].copy()
    
    output_parquet = "data/processed/similar_rates.parquet"
    similar_rates.to_parquet(output_parquet, index=False)
    print(f"산출물 저장 완료: {output_parquet} ({similar_rates.shape[0]}행)")
    
    mean_se = similar_rates['유사_SE'].mean()
    print(f"검증 게이트 - 유사 20곳 평균 표준오차 (SE): {mean_se:.4f}%p (기준: ≤ 2.0%p)")
    
    if rural_urban_match_rate < 95.0:
        print("Warning: 도농 일치율이 기준치(95%)에 미달하였습니다.")
    if mean_se > 2.0:
        print("Warning: 평균 표준오차가 기준치(2.0%p)를 초과하였습니다.")
        
    return True

if __name__ == '__main__':
    run_similar()
