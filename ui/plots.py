# coding: utf-8
"""
ui.plots — Plotly ベースのグラフ描画

時系列データと FFT 分析結果のグラフを Plotly で描画する。
matplotlib は使用せず、全て Plotly + Streamlit の plotly_chart で表示する。

将来、グラフ内への情報コメント（ファイル名、日時等）の追加や
ピークサーチ結果のオーバーレイ表示を行う場合は、
各関数に引数を追加する形で拡張する。
"""

from typing import List

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core.models import ExtractionSettings, FFTResult


def show_time_series(
    df: pd.DataFrame,
    usecols: List[int],
    settings: ExtractionSettings,
) -> None:
    """時系列データを Plotly で描画する。

    選択された全列を重ねてプロットし、データ抽出範囲が指定されている場合は
    半透明の赤色領域と破線で可視化する。

    Args:
        df: 表示対象の DataFrame。
        usecols: 表示する列番号のリスト。
        settings: データ抽出設定。抽出範囲の可視化に使用。
    """
    fig = go.Figure()

    # 各列のデータをトレースとして追加
    for col in usecols:
        fig.add_trace(go.Scatter(
            y=df[col],
            mode="lines",
            name=f"Column {col}",
            opacity=0.7,
        ))

    # --- 抽出範囲の可視化 ---
    if settings.selection_type != "全範囲" and settings.data_points is not None:
        pts = settings.data_points

        # 抽出範囲を半透明の赤色矩形で表示
        fig.add_vrect(
            x0=0, x1=pts,
            fillcolor="red", opacity=0.08,
            line_width=0,
        )
        # 開始・終了位置に破線を表示
        fig.add_vline(x=0, line_dash="dash", line_color="red", opacity=0.5)
        fig.add_vline(x=pts, line_dash="dash", line_color="red", opacity=0.5)

        # 抽出範囲の情報をアノテーションとして表示
        if settings.selection_type == "データ個数":
            label = f"Selected: {pts}pts"
        else:  # "秒数"
            secs = pts / settings.sampling_rate
            label = f"Selected: {secs:.1f}sec ({pts}pts)"
        fig.add_annotation(
            x=pts / 2, y=1, yref="paper",
            text=label, showarrow=False,
            font=dict(color="red"),
            bgcolor="rgba(255,255,255,0.7)",
        )

    fig.update_layout(
        xaxis_title="Sample",
        yaxis_title="Acceleration",
        height=400,
        legend=dict(font=dict(size=14)),
    )
    st.plotly_chart(fig, width="stretch")


def show_fft_result(result: FFTResult) -> None:
    """FFT 分析結果の周波数スペクトルを Plotly で描画する。

    Plotly のインタラクティブ機能（ズーム・パン）で
    周波数表示範囲はグラフ上で直接操作できる。

    ユーザーが操作できる項目:
        - 縦軸スケール（線形 / 対数）

    Args:
        result: FFTAnalyzer が返した FFTResult オブジェクト。
    """
    st.subheader(f"列 {result.column} のFFT分析結果")

    # --- 縦軸スケール選択 ---
    yscale = st.radio(
        "**縦軸の目盛**",
        options=["linear", "log"],
        format_func=lambda x: "線形目盛" if x == "linear" else "対数目盛",
        horizontal=True,
        index=0,
    )

    # --- FFT スペクトルの描画 ---
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=result.frequencies,
        y=result.amplitudes,
        mode="lines",
        name="FFT Result",
        opacity=0.7,
    ))
    fig.update_layout(
        xaxis_title="Frequency (Hz)",
        yaxis_title="Acceleration",
        title=f"Column {result.column} FFT Result",
        yaxis_type=yscale,
        height=500,
        xaxis=dict(tickfont=dict(size=14)),
        legend=dict(font=dict(size=12)),
    )
    st.plotly_chart(fig, width="stretch")
