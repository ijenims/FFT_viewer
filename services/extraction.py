# coding: utf-8
"""
services.extraction — データ抽出ロジック

FFT 分析に投入するデータの点数計算・バリデーション・抽出を行う。
UI 層（sidebar）から呼び出され、抽出方法に応じた点数を返す。

将来、開始地点の指定（start_offset）を追加する場合は
extract_series() を拡張する。
"""

from typing import Optional

import pandas as pd

from core.models import ExtractionSettings


def calculate_data_points(
    selection_type: str,
    n_power: Optional[int] = None,
    seconds: Optional[float] = None,
    sampling_rate: Optional[int] = None,
) -> Optional[int]:
    """抽出方法に応じたデータ点数を計算する。

    Args:
        selection_type: "全範囲" / "データ個数" / "秒数" のいずれか。
        n_power: "データ個数" 選択時の指数 n（2^n 点）。10〜20 を想定。
        seconds: "秒数" 選択時の秒数。
        sampling_rate: サンプリング周波数 [Hz]。"秒数" 選択時に必須。

    Returns:
        抽出するデータ点数。"全範囲" の場合は None。
    """
    if selection_type == "全範囲":
        return None
    elif selection_type == "データ個数":
        return 2 ** n_power
    else:  # "秒数"
        return int(seconds * sampling_rate)


def validate_data_range(total_points: int, selected_points: int) -> bool:
    """選択されたデータ点数が元データの範囲内かチェックする。

    超過していてもエラーにはせず、呼び出し側で警告表示に使う。

    Args:
        total_points: 元データの総点数。
        selected_points: ユーザーが選択した点数。

    Returns:
        True なら範囲内、False なら超過。
    """
    if selected_points is None:
        return True
    return selected_points <= total_points


def extract_series(
    series: pd.Series,
    settings: ExtractionSettings,
) -> pd.Series:
    """ExtractionSettings に基づいてデータ系列を抽出する。

    "全範囲" の場合はそのまま返し、それ以外は先頭から
    指定点数分を切り出す。元データより多い点数が指定された場合は
    元データ全体を返す（iloc のスライスが自動的に処理する）。

    将来、開始地点（start_offset）を追加する場合は
    settings.extra["start_offset"] を参照してスライス範囲を変更する。

    Args:
        series: 抽出元の 1 列分のデータ。
        settings: 抽出設定。data_points が None なら全範囲。

    Returns:
        抽出後の Series。
    """
    if settings.data_points is None:
        return series
    return series.iloc[: settings.data_points]
