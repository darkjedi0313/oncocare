import os
import pandas as pd


def run_trend():
    print("\n========== [trend.py] 연도별 수검률 추이 산출 ==========")
    segments_path = "data/processed/segments.parquet"
    if not os.path.exists(segments_path):
        print(f"Error: {segments_path} 파일이 없습니다. 파이프라인을 먼저 실행하세요.")
        return False

    df = pd.read_parquet(segments_path)

    # 1. 시군구×암종×연도 단위 가중평균 수검률
    group_cols = ["연도", "시도", "시군구", "암종"]
    trend = (
        df.groupby(group_cols)
        .agg(대상자=("대상자", "sum"), 수검자=("수검자", "sum"))
        .reset_index()
    )
    trend["수검률"] = trend["수검자"] / trend["대상자"] * 100

    output_path = "data/processed/trend.parquet"
    trend.to_parquet(output_path, index=False)

    years = sorted(trend["연도"].unique().tolist())
    n_regions = trend[["시도", "시군구"]].drop_duplicates().shape[0]
    print(f"산출물 저장 완료: {output_path} ({trend.shape[0]}행)")
    print(f"포함 연도: {years} / 시군구: {n_regions}개")

    # 2. 검증 게이트 — 수검률 범위 이탈 없음
    out_of_range = trend[(trend["수검률"] < 0) | (trend["수검률"] > 100)]
    if not out_of_range.empty:
        print(f"Warning: 수검률 범위 이탈 {len(out_of_range)}행 발견")
    else:
        print("검증 게이트 — 수검률 0~100 범위 이탈: 0행 ✓")

    return True


if __name__ == "__main__":
    run_trend()
