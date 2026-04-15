# coding: utf-8
"""
core.encoding — ファイルエンコーディングの自動検出

日本語 CSV ファイルで頻出するエンコーディング（Shift_JIS, CP932, UTF-8 等）を
順番に試行し、最初にデコードに成功したものを採用する。

使用例::

    checker = EncodingChecker(raw_bytes)
    text = raw_bytes.decode(checker.encoding)
"""

from typing import List, Optional


class EncodingChecker:
    """バイト列のエンコーディングを試行検出するユーティリティ。

    コンストラクタで検出を実行し、結果を ``encoding`` 属性に格納する。
    全候補で失敗した場合は ``ValueError`` を送出する。

    Attributes:
        file_contents: 検出対象のバイト列。
        encodings: 試行するエンコーディング名のリスト（優先順）。
        encoding: 検出されたエンコーディング名。
    """

    DEFAULT_ENCODINGS: List[str] = [
        "shift_jis",
        "utf-8-sig",
        "cp932",
        "cp775",
        "utf-8",
    ]

    def __init__(
        self,
        file_contents: bytes,
        encodings: Optional[List[str]] = None,
    ):
        self.file_contents = file_contents
        self.encodings = encodings or self.DEFAULT_ENCODINGS
        self.encoding = self._detect()

    def _detect(self) -> str:
        """エンコーディングを順番に試し、最初に成功したものを返す。

        Returns:
            デコードに成功したエンコーディング名。

        Raises:
            ValueError: 全てのエンコーディングでデコードに失敗した場合。
        """
        for enc in self.encodings:
            try:
                self.file_contents.decode(enc)
                return enc
            except Exception:
                continue
        raise ValueError("全てのエンコーディングで読み込みに失敗しました。")
