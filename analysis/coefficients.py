import os
import json
import pandas as pd
from sklearn.linear_model import LinearRegression

def run_coefficients():
    print("\n========== [coefficients.py] 선형 회귀 계수 추출 ==========")
    
    segments_path = "data/processed/segments.parquet"
    if not os.path.exists(segments_path):
        print(f"Error: {segments_path} 파일이 없습니다. 파이프라인을 먼저 실행하세요.")
        return False
        
    df = pd.read_parquet(segments_path)
    
    # 2023년 학습용 데이터
    train_df = df[df['연도'] == 2023].copy()
    
    FEATURES = [
        '소득로그', '인구로그', '기관밀도', '관내0', '기관전체밀도',
        '군', '구', '연령n', '여자',
        '암_위암', '암_대장암', '암_간암', '암_유방암', '암_자궁경부암', '암_폐암'
    ]
    TARGET = '수검률'
    
    X = train_df[FEATURES]
    y = train_df[TARGET]
    
    model = LinearRegression()
    model.fit(X, y)
    
    # 계수 추출
    coef_dict = {}
    for feature, coef in zip(FEATURES, model.coef_):
        coef_dict[feature] = float(coef)
        
    intercept = float(model.intercept_)
    
    # 계수에서 동적으로 해석 메모를 생성 — 하드코딩 금지 (절대 규칙 3)
    kwan0_coef = coef_dict.get('관내0', 0)
    sodk_coef = coef_dict.get('소득로그', 0)
    
    # 소득로그 계수: 로그 단위 → %p 체감 영향 (ln(소득 중위 대비 1분위) ≈ 0.35 차이 가정)
    income_approx_effect = sodk_coef * 0.35

    coefficients_data = {
        "coef": coef_dict,
        "intercept": intercept,
        "notes": [
            f"관내 검진기관이 없는 경우(관내0=1) 수검률이 약 {kwan0_coef:.2f}%p 낮아집니다. (재산출 계수 {kwan0_coef:.4f})",
            f"소득 변수는 로그 스케일이며, 부유한 지역이 검진을 덜 받는 경향은 국가검진 외 종합검진 수검이 공단 통계에 잡히지 않기 때문일 수 있습니다. (소득로그 계수 {sodk_coef:.4f})"
        ]
    }
    
    output_path = "data/processed/coefficients.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(coefficients_data, f, ensure_ascii=False, indent=2)
        
    print(f"산출물 저장 완료: {output_path}")
    print("추출된 주요 계수:")
    print(f"  - 관내0 (검진기관 부재 효과): {coef_dict.get('관내0', 0):.4f}%p")
    print(f"  - 소득로그: {coef_dict.get('소득로그', 0):.4f}")
    
    return True

if __name__ == '__main__':
    run_coefficients()
