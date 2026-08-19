import os
import pandas as pd
import numpy as np

def run_strata():
    print("\n========== [strata.py] 층화 분석(Strata) 교차표 산출 ==========")
    segments_path = "data/processed/segments.parquet"
    if not os.path.exists(segments_path):
        print(f"Error: {segments_path} 파일이 없습니다. 파이프라인을 먼저 실행하세요.")
        return False
        
    df = pd.read_parquet(segments_path)
    print(f"데이터 로드 완료: {df.shape[0]}행")
    
    # 1. 도농 분류 ('군', '시', '구')
    def get_urban_type(row):
        if row['군'] == 1:
            return '군'
        elif row['구'] == 1:
            return '구'
        else:
            return '시'
            
    df['도농'] = df.apply(get_urban_type, axis=1)
    
    # 2. 소득 3분위 분류 (각 연도별로 고유 시군구 단위의 소득 기준 3분위수 생성)
    df['소득분위'] = ''
    for year in df['연도'].unique():
        year_mask = df['연도'] == year
        df_year = df[year_mask]
        
        # 키(시군구) 기준 유니크 소득로그 값 추출
        unique_income = df_year.groupby('키')['소득로그'].first().reset_index()
        
        try:
            unique_income['분위'] = pd.qcut(unique_income['소득로그'], q=3, labels=['하', '중', '상'])
        except Exception as e:
            print(f"qcut 실패 ({e}), rank 기반 분위 분할 적용")
            unique_income['분위'] = pd.qcut(unique_income['소득로그'].rank(method='first'), q=3, labels=['하', '중', '상'])
            
        income_map = unique_income.set_index('키')['분위'].to_dict()
        df.loc[year_mask, '소득분위'] = df_year['키'].map(income_map).astype(str)
        
    df['stratum'] = df['도농'] + '·소득' + df['소득분위']
    
    # 3. 층화 교차표 작성 (암종 x 연도 x stratum x 관내0)
    records = []
    grouped = df.groupby(['연도', '암종', 'stratum'])
    
    for (year, cancer, stratum), group in grouped:
        absent_group = group[group['관내0'] == 1]
        present_group = group[group['관내0'] == 0]
        
        absent_target = absent_group['대상자'].sum()
        absent_screened = absent_group['수검자'].sum()
        absent_rate = (absent_screened / absent_target * 100) if absent_target > 0 else None
        
        present_target = present_group['대상자'].sum()
        present_screened = present_group['수검자'].sum()
        present_rate = (present_screened / present_target * 100) if present_target > 0 else None
        
        total_target = group['대상자'].sum()
        
        # 층당 대상자 1,000명 미만 층은 제외
        if total_target < 1000:
            continue
            
        if absent_rate is not None and present_rate is not None:
            diff = present_rate - absent_rate
            records.append({
                '연도': int(year),
                '암종': cancer,
                'stratum': stratum,
                'absent': round(float(absent_rate), 2),
                'present': round(float(present_rate), 2),
                'diff': round(float(diff), 2),
                'absent_target': int(absent_target),
                'present_target': int(present_target)
            })
            
    strata_df = pd.DataFrame(records)
    
    output_path = "data/processed/strata.parquet"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    strata_df.to_parquet(output_path, index=False)
    print(f"층화 교차표 저장 완료: {output_path} ({strata_df.shape[0]}행)")
    return True

if __name__ == '__main__':
    run_strata()
