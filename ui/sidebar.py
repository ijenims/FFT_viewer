# coding: utf-8
"""
ui.sidebar — サイドバー UI コンポーネント

FFT 分析に必要な設定（対象列、サンプリング周波数、データ抽出方法）を
Streamlit のサイドバーウィジェットとして描画し、設定値を返す。

描画とビジネスロジックを分離するため、点数計算・バリデーションは
services.extraction に委譲している。
"""

from typing import List, Optional, Tuple

import pandas as pd
import streamlit as st

from core.models import ExtractionSettings
from services.extraction import calculate_data_points, validate_data_range


def render_fft_settings(
    usecols: List[int],
    df: pd.DataFrame,
    rate: Optional[int] = None,
) -> Tuple[int, ExtractionSettings]:
    """FFT 分析用のサイドバー設定ウィジェットを描画する。

    描画する項目:
        - FFT 分析対象列の選択
        - サンプリング周波数（CSV: ユーザー入力 / WAV: 読み取り専用表示）
        - データ抽出方法（全範囲 / データ個数 / 秒数）
        - 抽出点数の表示と超過警告

    Args:
        usecols: 選択可能な列番号のリスト。
        df: 読み込み済みの DataFrame（点数の把握に使用）。
        rate: サンプリング周波数 [Hz]。
              None の場合は入力フィールドを表示（CSV 用）。
              値がある場合は読み取り専用で表示（WAV 用）。

    Returns:
        (fft_column, extraction_settings) のタプル。
        fft_column: FFT 分析対象の列番号。
        extraction_settings: データ抽出設定。
    """
    with st.sidebar:
        # --- FFT 対象列 ---
        col = st.selectbox(
            "FFT分析する列",
            options=usecols,
            format_func=lambda x: f"列 {x}",
        )

        # --- サンプリング周波数 ---
        # CSV: ユーザーが自由に入力  /  WAV: ファイルから取得済みなので表示のみ
        if rate is None:
            rate = st.number_input(
                "サンプリング周波数 (Hz)", value=1000, min_value=1,
            )
        else:
            st.markdown(
                f"<div style='color:gray;'>サンプリング周波数 (Hz)</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<div style='font-size:1.2em;'>{rate} Hz</div>",
                unsafe_allow_html=True,
            )

        st.markdown("---")
        st.markdown("### データ抽出設定")

        # --- 抽出方法の選択 ---
        selection_type = st.radio(
            "抽出方法",
            options=["全範囲", "データ個数", "秒数"],
            horizontal=True,
        )

        # --- 抽出方法に応じた入力フィールド ---
        data_points = None
        if selection_type == "データ個数":
            # 2^10 (1024) 〜 2^20 (1,048,576) から選択
            n_power = st.selectbox(
                "データ個数 (2^n個)",
                options=list(range(10, 21)),
                format_func=lambda x: f"2^{x} = {2**x}点",
            )
            data_points = calculate_data_points(selection_type, n_power=n_power)
        elif selection_type == "秒数":
            seconds = st.number_input(
                "秒数", value=1.0, min_value=0.1, step=0.1,
            )
            data_points = calculate_data_points(
                selection_type, seconds=seconds, sampling_rate=rate,
            )

        # --- 点数の表示 & 超過警告 ---
        if data_points is not None:
            total_points = len(df[col])
            st.info(f"選択データ点数: {data_points}点")
            if not validate_data_range(total_points, data_points):
                st.warning(
                    f"警告: 選択点数がデータ総数({total_points}点)を超えています"
                )

        settings = ExtractionSettings(
            selection_type=selection_type,
            data_points=data_points,
            sampling_rate=rate,
        )
        return col, settings
