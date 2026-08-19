import os
import pandas as pd
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import r2_score, mean_absolute_error

def run_expectation():
    print("\n========== [expectation.py] 기대치 회귀 모델 학습 및 평가 ==========")
    
    segments_path = "data/processed/segments.parquet"
    if not os.path.exists(segments_path):
        print(f"Error: {segments_path} 파일이 없습니다. 파이프라인을 먼저 실행하세요.")
        return False
        
    df = pd.read_parquet(segments_path)
    print(f"데이터 로드 완료: {df.shape[0]}행")
    
    # 피처 및 타겟 설정 (A안 15개 피처 사용, 전년수검률 제외)
    FEATURES = [
        '소득로그', '인구로그', '기관밀도', '관내0', '기관전체밀도',
        '군', '구', '연령n', '여자',
        '암_위암', '암_대장암', '암_간암', '암_유방암', '암_자궁경부암', '암_폐암'
    ]
    TARGET = '수검률'
    
    # 시간 분할 (2023 학습, 2024 검증)
    train_df = df[df['연도'] == 2023].copy()
    test_df = df[df['연도'] == 2024].copy()
    
    X_train = train_df[FEATURES]
    y_train = train_df[TARGET]
    X_test = test_df[FEATURES]
    y_test = test_df[TARGET]
    
    print(f"학습 데이터: {X_train.shape[0]}행, 검증 데이터: {X_test.shape[0]}행")
    
    # HistGradientBoostingRegressor 모델 정의 및 학습
    model = HistGradientBoostingRegressor(
        max_iter=300,
        learning_rate=0.08,
        random_state=42
    )
    model.fit(X_train, y_train)
    
    # 예측 및 평가
    y_pred = model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    
    print(f"검증 성능 결과:")
    print(f"  - R² Score: {r2:.4f} (기준: ≥ 0.85)")
    print(f"  - MAE: {mae:.4f}%p (기준: ≤ 4.5%p)")
    
    if r2 < 0.85:
        print("Warning: R² Score가 기준치(0.85)에 미달하였습니다.")
    if mae > 4.5:
        print("Warning: MAE가 기준치(4.5%p)를 초과하였습니다.")
        
    # 전체 데이터에 기대치, 잔차, 회복여지 추가
    # 2023, 2024 전체 데이터셋에 대해 기대치를 계산하여 저장
    df['기대치'] = model.predict(df[FEATURES])
    df['잔차'] = df['수검률'] - df['기대치']
    df['회복여지'] = (df['기대치'] - df['수검률']) * df['대상자'] / 100
    
    # 저장 경로 생성 및 파일 저장
    output_path = "data/processed/expectation.parquet"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_parquet(output_path, index=False)
    print(f"산출물 저장 완료: {output_path} ({df.shape[0]}행)")
    return True

if __name__ == '__main__':
    run_expectation()
