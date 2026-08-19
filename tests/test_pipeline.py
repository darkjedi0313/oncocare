import os
import pandas as pd
import pytest

# interim 디렉토리 및 파일 경로 정의
INTERIM_DIR = "data/interim"
COMBINED_PATH = os.path.join(INTERIM_DIR, "s3_combined.parquet")

def test_interim_files_exist():
    """중간 파이프라인 결합물 파일이 존재하는지 확인"""
    assert os.path.exists(COMBINED_PATH), f"{COMBINED_PATH} 파일이 존재하지 않습니다."

def test_combined_row_count():
    """결합 완료 후 행수가 정확히 24048행(2021 제외 4개 연도 통합본)인지 확인"""
    df = pd.read_parquet(COMBINED_PATH)
    assert len(df) == 24048, f"결합 결과 행수가 {len(df)}로 24048행이 아닙니다."

def test_unique_sidos():
    """시도명이 정제된 후 정확히 17개 지자체 유형을 가지는지 검증 (결함 1 정합)"""
    df = pd.read_parquet(COMBINED_PATH)
    sidos = df['시도'].unique()
    assert len(sidos) == 17, f"정제된 시도 종류가 {len(sidos)}개로 17개가 아닙니다."
    
def test_no_trailing_spaces_in_sido():
    """시도명에 후행 공백이 없는지 확인 (결함 2 정합)"""
    df = pd.read_parquet(COMBINED_PATH)
    blank_sidos = df['시도'].str.endswith(' ').sum()
    assert blank_sidos == 0, f"시도명에 후행 공백이 {blank_sidos}건 발견되었습니다."

def test_match_rates():
    """S3 결합 매칭률(검진기관 >= 99%, 소득 >= 85%, 적용인구 >= 99%) 검증"""
    df = pd.read_parquet(COMBINED_PATH)
    
    inst_match_rate = (df['기관_위암'].notna()).sum() / len(df) * 100
    income_match_rate = (df['소득'].notna()).sum() / len(df) * 100
    pop_match_rate = (df['적용인구'].notna()).sum() / len(df) * 100
    
    assert inst_match_rate >= 99.0, f"검진기관 매칭률 {inst_match_rate:.2f}%가 99% 미만입니다."
    assert income_match_rate >= 85.0, f"소득 매칭률 {income_match_rate:.2f}%가 85% 미만입니다."
    assert pop_match_rate >= 99.0, f"적용인구 매칭률 {pop_match_rate:.2f}%가 99% 미만입니다."

def test_s4_long_shape():
    """S4 wide->long 전개 완료 후 형태 및 이탈값 검증"""
    s4_path = os.path.join(INTERIM_DIR, "s4_long.parquet")
    assert os.path.exists(s4_path), f"{s4_path} 파일이 없습니다."
    
    df = pd.read_parquet(s4_path)
    assert abs(len(df) - 89299) <= 100, f"S4 전개 행수 {len(df)}가 기준 89299행 ±100 범위를 벗어납니다."
    
    out_of_bounds = ((df['수검률'] < 0) | (df['수검률'] > 100)).sum()
    assert out_of_bounds == 0, f"수검률이 0~100 범위를 초과하는 행이 {out_of_bounds}건 존재합니다."

def test_s5_features():
    """S5 15종 파생 피처 및 시차변수 결측 및 최종 행수 검증"""
    processed_path = "data/processed/segments.parquet"
    assert os.path.exists(processed_path), f"{processed_path} 파일이 없습니다."
    
    df = pd.read_parquet(processed_path)
    assert abs(len(df) - 37672) <= 100, f"S5 최종 행수 {len(df)}가 기준 37672행 ±100 범위를 벗어납니다."
    
    CANCERS = ['위암', '대장암', '간암', '유방암', '자궁경부암', '폐암']
    target_features = ['소득로그', '인구로그', '기관밀도', '관내0', '기관전체밀도', '군', '구', '연령n', '여자', '전년수검률'] + [f'암_{c}' for c in CANCERS]
    na_count = df[target_features].isna().sum().sum()
    assert na_count == 0, f"파생 피처 및 시차변수 중 결측치 {na_count}건이 발견되었습니다."

def test_s6_split():
    """S6 시간 분할 검증 정합성 테스트"""
    processed_path = "data/processed/segments.parquet"
    df = pd.read_parquet(processed_path)
    
    tr = df[df['연도'] == 2023]
    te = df[df['연도'] == 2024]
    
    assert abs(len(tr) - 18859) <= 100, f"학습 데이터 행수 {len(tr)}가 기준 18859행 ±100 범위를 벗어납니다."
    assert abs(len(te) - 18813) <= 100, f"검증 데이터 행수 {len(te)}가 기준 18813행 ±100 범위를 벗어납니다."
    
    diff = abs(tr['수검률'].mean() - te['수검률'].mean())
    assert diff <= 1.0, f"학습/검증 수검률 평균 편차 {diff:.4f}%p가 1.0%p를 초과합니다."

