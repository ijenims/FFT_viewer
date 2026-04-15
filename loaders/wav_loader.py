# coding: utf-8
"""
loaders.wav_loader — WAV ファイルの読み込み

soundfile ライブラリを使用して WAV ファイルを読み込み、
サンプリング周波数を自動取得する。
モノラル・ステレオの両方に対応。
"""

import io

import pandas as pd
import soundfile as sf
import streamlit as st

from core.models import LoadedData
from loaders.base import FileLoader


class WavLoader(FileLoader):
    """WAV ファイルの読み込みを担当するローダー。

    soundfile でデコードし、DataFrame + サンプリング周波数として返す。
    ステレオの場合は各チャンネルが別列になる。
    """

    def load(self, uploaded_file) -> LoadedData:
        """WAV ファイルを読み込み、LoadedData を返す。

        Args:
            uploaded_file: Streamlit の file_uploader が返すオブジェクト。

        Returns:
            LoadedData: 音声データの DataFrame とサンプリング周波数。
                        モノラルなら列 0 のみ、ステレオなら列 0, 1, ... 。
        """
        data, samplerate = sf.read(io.BytesIO(uploaded_file.read()))

        # モノラル（1次元）→ 1列の DataFrame に変換
        if data.ndim == 1:
            df = pd.DataFrame({0: data})
        else:
            # ステレオ以上 → 各チャンネルが列になる
            df = pd.DataFrame(data)

        return LoadedData(
            df=df,
            sample_rate=samplerate,
            file_name=uploaded_file.name,
            file_type="WAV",
        )

    def preview(self, uploaded_file) -> None:
        """WAV ファイルのプレビュー（現状は何も表示しない）。

        WAV は CSV と異なりヘッダ行の確認が不要なため、
        プレビューは show_info() で代替する。

        Args:
            uploaded_file: 未使用（インターフェース互換のため）。
        """
        pass

    def show_info(self, loaded: LoadedData) -> None:
        """読み込み済み WAV データの基本情報を Streamlit 上に表示する。

        Args:
            loaded: load() で取得した LoadedData。
        """
        st.success("WAVファイルの読み込みに成功しました")
        st.write(f"サンプリング周波数: {loaded.sample_rate} Hz")
        st.write(f"データ点数: {len(loaded.df)}")
