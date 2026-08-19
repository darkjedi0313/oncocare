import os
import json
import pandas as pd

class DataLoader:
    def __init__(self):
        self.expectation = None
        self.similar_regions = None
        self.similar_rates = None
        self.national_avg = None
        self.coefficients = None
        self.strata = None
        self.region_profiles = None
        self.trend = None
        self.load_data()

    def load_data(self):
        print("Loading analytical artifacts into memory...")
        current_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.abspath(os.path.join(current_dir, "..", "data", "processed"))

        expectation_path = os.path.join(base_dir, "expectation.parquet")
        similar_regions_path = os.path.join(base_dir, "similar_regions.json")
        similar_rates_path = os.path.join(base_dir, "similar_rates.parquet")
        national_avg_path = os.path.join(base_dir, "national_avg.parquet")
        coefficients_path = os.path.join(base_dir, "coefficients.json")
        strata_path = os.path.join(base_dir, "strata.parquet")
        region_profiles_path = os.path.join(base_dir, "region_profiles.parquet")
        trend_path = os.path.join(base_dir, "trend.parquet")

        # 필수 파일 존재 체크
        for p in [expectation_path, similar_regions_path, similar_rates_path, national_avg_path, coefficients_path, strata_path]:
            if not os.path.exists(p):
                raise FileNotFoundError(f"필수 산출물 파일이 없습니다: {p}. 먼저 'python analysis/build_artifacts.py'를 실행하십시오.")

        self.expectation = pd.read_parquet(expectation_path)
        with open(similar_regions_path, "r", encoding="utf-8") as f:
            self.similar_regions = json.load(f)
        self.similar_rates = pd.read_parquet(similar_rates_path)
        self.national_avg = pd.read_parquet(national_avg_path)
        with open(coefficients_path, "r", encoding="utf-8") as f:
            self.coefficients = json.load(f)
        self.strata = pd.read_parquet(strata_path)

        # 선택적 산출물 — 없으면 빈 DataFrame으로 초기화
        if os.path.exists(region_profiles_path):
            self.region_profiles = pd.read_parquet(region_profiles_path)
        else:
            self.region_profiles = pd.DataFrame()
            print(f"Warning: {region_profiles_path} 없음. build_artifacts.py 재실행 권장.")

        if os.path.exists(trend_path):
            self.trend = pd.read_parquet(trend_path)
        else:
            self.trend = pd.DataFrame()

        print("All OncoCare analytical artifacts loaded into memory successfully.")

# 싱글톤 객체 초기화
db = DataLoader()

def get_db() -> DataLoader:
    return db
