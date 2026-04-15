# coding: utf-8
"""
loaders.base — ファイルローダーの抽象基底クラス

全てのファイルローダー（CSV, WAV, 将来の Excel 等）が
実装すべきインターフェースを定義する。

新しいファイル形式に対応する場合は、このクラスを継承して
load() と preview() を実装するだけでよい（開放閉鎖原則）。
"""

from abc import ABC, abstractmethod

from core.models import LoadedData


class FileLoader(ABC):
    """ファイル読み込みの共通インターフェース（抽象基底クラス）。

    サブクラスは load() と preview() を必ず実装する。
    app.py やサービス層はこの基底型に依存し、
    具象ローダーには直接依存しない（依存性逆転原則）。
    """

    @abstractmethod
    def load(self, uploaded_file) -> LoadedData:
        """アップロードされたファイルを読み込み、LoadedData を返す。

        Args:
            uploaded_file: Streamlit の st.file_uploader が返すファイルオブジェクト。

        Returns:
            LoadedData: 読み込んだデータとメタ情報を格納したオブジェクト。
        """
        ...

    @abstractmethod
    def preview(self, uploaded_file) -> None:
        """Streamlit 上でファイル内容のプレビューを表示する。

        Args:
            uploaded_file: Streamlit の st.file_uploader が返すファイルオブジェクト。
        """
        ...
