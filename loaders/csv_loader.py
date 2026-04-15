# coding: utf-8
"""
loaders.csv_loader — CSV ファイルの読み込みとプレビュー

日本語エンコーディングの自動検出、冒頭プレビュー表示、
ユーザーによるデータ開始行・使用列の選択を経て DataFrame を構築する。

典型的な使用フロー::

    loader = CsvLoader()
    loaded = loader.configure_and_load(uploaded_file)
    # loaded.df にユーザーが選択した列のデータが入る
"""

import io
from typing import List, Optional

import pandas as pd
import streamlit as st

from core.encoding import EncodingChecker
from core.models import LoadedData
from loaders.base import FileLoader


class CsvLoader(FileLoader):
    """CSV ファイルの読み込み・プレビュー・ユーザー設定を担当するローダー。

    FileLoader インターフェースを実装しつつ、CSV 固有の操作
    （エンコーディング検出、スキップ行指定、列選択）を提供する。

    Attributes:
        _encoding: 検出されたエンコーディング名。
        _text_content: デコード済みの CSV テキスト全体。
        _skiprows: ユーザーが指定したデータ開始行（0-indexed）。
        _usecols: ユーザーが選択した列番号のリスト。
    """

    def __init__(self):
        self._encoding: str = ""
        self._text_content: str = ""
        self._skiprows: int = 0
        self._usecols: List[int] = []

    # ----------------------------------------------------------------
    # FileLoader インターフェース実装
    # ----------------------------------------------------------------

    def load(self, uploaded_file) -> LoadedData:
        """CSV ファイルを読み込み、エンコーディングを自動検出する。

        Args:
            uploaded_file: Streamlit の file_uploader が返すオブジェクト。

        Returns:
            LoadedData: 全行・全列を含む生データ。
        """
        raw = uploaded_file.read()
        self._encoding = EncodingChecker(raw).encoding
        self._text_content = raw.decode(self._encoding)
        return self._build_loaded_data(uploaded_file.name)

    def preview(self, uploaded_file) -> None:
        """CSV ファイルの冒頭 20 行をテーブル表示する。

        load() の後に呼び出すこと（_text_content が必要）。

        Args:
            uploaded_file: 未使用（インターフェース互換のため）。
        """
        self._show_head_preview()

    # ----------------------------------------------------------------
    # CSV 固有の公開メソッド
    # ----------------------------------------------------------------

    def configure_and_load(self, uploaded_file) -> LoadedData:
        """プレビュー → ユーザー設定 → 最終読み込みを一括で行う。

        処理フロー:
            1. ファイル読み込み & エンコーディング検出
            2. 冒頭 20 行のプレビュー表示
            3. サイドバーでデータ開始行を入力
            4. スキップ後のプレビュー（5 行）を表示
            5. サイドバーで使用列を選択
            6. 選択列のみで DataFrame を構築して返す

        Args:
            uploaded_file: Streamlit の file_uploader が返すオブジェクト。

        Returns:
            LoadedData: ユーザー設定を反映した最終データ。
        """
        loaded = self.load(uploaded_file)
        self.preview(uploaded_file)

        # ユーザーにデータ開始行を指定してもらう
        self._skiprows = self._ask_skiprows()
        df_after_skip = self._read_with_skip(nrows=5)
        st.subheader(f"データ開始行({self._skiprows}行目)以降のプレビュー")
        st.dataframe(df_after_skip)

        # ユーザーに使用列を選択してもらう
        self._usecols = self._ask_usecols(df_after_skip)
        df = self._read_with_skip(usecols=self._usecols)

        return LoadedData(
            df=df,
            sample_rate=None,  # CSV ではサンプリング周波数はユーザー入力
            file_name=uploaded_file.name,
            file_type="CSV",
        )

    @property
    def usecols(self) -> List[int]:
        """ユーザーが選択した列番号のリスト。"""
        return self._usecols

    # ----------------------------------------------------------------
    # 内部メソッド
    # ----------------------------------------------------------------

    def _build_loaded_data(self, name: str) -> LoadedData:
        """テキスト全体から DataFrame を構築する（スキップ行・列選択なし）。"""
        buf = io.StringIO(self._text_content)
        df = pd.read_csv(
            buf, header=None, on_bad_lines="skip",
            sep=",", skipinitialspace=True,
        )
        return LoadedData(df=df, sample_rate=None, file_name=name, file_type="CSV")

    def _show_head_preview(self) -> None:
        """CSV テキストの冒頭 20 行を整形してテーブル表示する。

        列数が不揃いな行は空文字で埋めて正規化する。
        """
        lines = self._text_content.splitlines()[:20]
        split_rows = [line.split(",") for line in lines]
        max_cols = max(len(r) for r in split_rows)
        normalized = [r + [""] * (max_cols - len(r)) for r in split_rows]
        df = pd.DataFrame(normalized)
        df.index.name = "行番号"
        df.columns = [f"列 {i}" for i in range(max_cols)]
        st.subheader("CSVファイルの冒頭20行")
        st.dataframe(df)

    def _ask_skiprows(self) -> int:
        """サイドバーでデータ開始行の入力を受け付ける。"""
        with st.sidebar:
            return st.number_input("データ開始行", value=0, min_value=0)

    def _ask_usecols(self, df_preview: pd.DataFrame) -> List[int]:
        """サイドバーで使用列の選択を受け付ける。

        何も選択されていない場合は警告を出してアプリを停止する。

        Args:
            df_preview: スキップ行適用後のプレビュー DataFrame（列数の把握に使用）。

        Returns:
            選択された列番号のリスト。
        """
        with st.sidebar:
            available = list(range(df_preview.shape[1]))
            selected = st.multiselect(
                "表示する列を選択",
                options=available,
                default=[0],
                format_func=lambda x: f"列 {x}",
            )
            if not selected:
                st.warning("少なくとも1つの列を選択してください")
                st.stop()
            return selected

    def _read_with_skip(
        self,
        nrows: Optional[int] = None,
        usecols: Optional[List[int]] = None,
    ) -> pd.DataFrame:
        """スキップ行を適用して CSV を読み込む。

        Args:
            nrows: 読み込む行数。None の場合は全行。
            usecols: 読み込む列番号のリスト。None の場合は全列。

        Returns:
            読み込んだ DataFrame。
        """
        buf = io.StringIO(self._text_content)
        kwargs = dict(
            skiprows=self._skiprows,
            encoding=self._encoding,
            header=None,
            on_bad_lines="skip",
            sep=",",
            skipinitialspace=True,
        )
        if nrows is not None:
            kwargs["nrows"] = nrows
        if usecols is not None:
            kwargs["usecols"] = usecols
        return pd.read_csv(buf, **kwargs)
