# coding: utf-8
"""
FFT 分析アプリケーション — エントリポイント

Streamlit で動作する FFT 分析ツール。
CSV または WAV ファイルをアップロードし、時系列データの表示と
FFT（高速フーリエ変換）分析結果のグラフ表示を行う。

起動方法::

    streamlit run app.py

アーキテクチャ:
    - core/       … データモデル、エンコーディング検出、FFT 計算
    - loaders/    … ファイル読み込み（CSV / WAV）
    - services/   … データ抽出ロジック
    - ui/         … サイドバー設定、Plotly グラフ描画
"""

import streamlit as st

from core.fft import FFTAnalyzer
from loaders.csv_loader import CsvLoader
from loaders.wav_loader import WavLoader
from services.extraction import extract_series
from ui.plots import show_fft_result, show_time_series
from ui.sidebar import render_fft_settings


def main() -> None:
    """アプリケーションのメインエントリポイント。

    処理フロー:
        1. サイドバーでファイル形式を選択し、ファイルをアップロード
        2. ローダーでデータを読み込み（CSV: プレビュー→設定→読込 / WAV: 即時読込）
        3. 時系列データをグラフ表示
        4. サイドバーで FFT 設定（対象列、抽出方法）を入力
        5. 「FFT分析実行」ボタンで FFT を実行し、結果をグラフ表示
    """
    st.title("FFT分析アプリケーション")

    # --- ファイル形式の選択とアップロード ---
    with st.sidebar:
        st.header("設定")
        file_type = st.selectbox("ファイル形式を選択", ["CSV", "WAV"])
        if file_type == "CSV":
            uploaded = st.file_uploader("CSVファイルを選択してください", type=["csv"])
        else:
            uploaded = st.file_uploader("WAVファイルを選択してください", type=["wav"])

    if not uploaded:
        return

    # ファイルが変わったらセッション状態をリセット（前回の分析結果を破棄）
    if (
        "last_uploaded_file" not in st.session_state
        or st.session_state.last_uploaded_file != uploaded
    ):
        st.session_state.clear()
        st.session_state.last_uploaded_file = uploaded

    try:
        # --- データ読み込み ---
        if file_type == "CSV":
            loader = CsvLoader()
            loaded = loader.configure_and_load(uploaded)
            usecols = loader.usecols

            # CSV はボタンを押して初めて時系列表示に進む
            with st.sidebar:
                if st.button("時系列データを表示", key="show_raw_data"):
                    st.session_state.show_raw = True
                    st.session_state.loaded = loaded
                    st.session_state.usecols = usecols
        else:
            wav_loader = WavLoader()
            loaded = wav_loader.load(uploaded)
            wav_loader.show_info(loaded)
            usecols = list(loaded.df.columns)

            # WAV は読み込み直後に時系列表示へ進む
            st.session_state.show_raw = True
            st.session_state.loaded = loaded
            st.session_state.usecols = usecols

        # --- 時系列表示 & FFT 設定 ---
        if not st.session_state.get("show_raw", False):
            return

        loaded = st.session_state.loaded
        usecols = st.session_state.usecols

        # サイドバーで FFT 分析の設定を入力
        fft_column, extraction_settings = render_fft_settings(
            usecols, loaded.df, rate=loaded.sample_rate,
        )

        # 時系列グラフの描画（抽出範囲の可視化を含む）
        st.subheader("選択列の時系列データ")
        show_time_series(loaded.df, usecols, extraction_settings)

        # --- FFT 実行 ---
        with st.sidebar:
            if st.button("FFT分析実行"):
                # 対象列のデータを抽出設定に従って切り出す
                series = loaded.df[fft_column]
                series = extract_series(series, extraction_settings)

                # FFT を実行
                analyzer = FFTAnalyzer(series.values, extraction_settings.sampling_rate)
                result = analyzer.execute(column=fft_column)

                st.session_state.fft_result = result
                st.session_state.fft_done = True
                st.info(f"FFT実行データ点数: {result.data_points_used}点")

        # --- FFT 結果の表示 ---
        if st.session_state.get("fft_done", False):
            show_fft_result(st.session_state.fft_result)

    except Exception as e:
        st.error(f"データの読み込み中にエラーが発生しました: {e}")
        st.stop()


if __name__ == "__main__":
    main()
