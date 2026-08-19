import os
import pandas as pd
from expectation import run_expectation
from similar import run_similar
from coefficients import run_coefficients
from strata import run_strata

def run_national_avg():
    print("\n========== [build_artifacts.py] 전국 세그먼트 평균 산출 ==========")
    segments_path = "data/processed/segments.parquet"
    if not os.path.exists(segments_path):
        print(f"Error: {segments_path} 파일이 없습니다.")
        return False
        
    df = pd.read_parquet(segments_path)
    
    # 전국 세그먼트 가중평균 (연도, 성별, 연령, 암종별)
    # 전국 수검률 = 전국 수검자 합 / 전국 대상자 합 * 100
    group_cols = ['연도', '성별', '연령', '암종']
    national_avg = df.groupby(group_cols).agg(
        대상자_sum=('대상자', 'sum'),
        수검자_sum=('수검자', 'sum')
    ).reset_index()
    
    national_avg['전국_평균'] = national_avg['수검자_sum'] / national_avg['대상자_sum'] * 100
    
    # 필요한 컬럼만 추출
    national_avg = national_avg[group_cols + ['전국_평균']].copy()
    
    output_path = "data/processed/national_avg.parquet"
    national_avg.to_parquet(output_path, index=False)
    print(f"산출물 저장 완료: {output_path} ({national_avg.shape[0]}행)")
    return True

def main():
    print("==================================================")
    print("      OncoCare 분석 산출물 생성 (Day 2-3) 시작")
    print("==================================================")
    
    # 1. 기대치 모델 실행
    success_exp = run_expectation()
    if not success_exp:
        print("Error: 기대치 모델 생성 실패")
        return
        
    # 2. kNN 유사 매칭 실행
    success_sim = run_similar()
    if not success_sim:
        print("Error: kNN 유사 매칭 실패")
        return
        
    # 3. 선형 회귀 계수 실행
    success_coef = run_coefficients()
    if not success_coef:
        print("Error: 선형 회귀 계수 추출 실패")
        return
        
    # 4. 전국 세그먼트 평균 실행
    success_nat = run_national_avg()
    if not success_nat:
        print("Error: 전국 세그먼트 평균 산출 실패")
        return
        
    # 5. 층화 분석 교차표 실행
    success_strata = run_strata()
    if not success_strata:
        print("Error: 층화 분석 교차표 산출 실패")
        return
        
    print("\n==================================================")
    print("      OncoCare 분석 산출물 6종 생성 완료!")
    print("==================================================")

if __name__ == '__main__':
    main()
