# coding: utf-8
"""
core.models — アプリケーション全体で共有するデータモデル定義

各層（loader / service / ui）間のデータ受け渡しに使う dataclass を集約する。
将来の機能追加（ピークサーチ、低周波カット等）に備え、
extra / metadata フィールドで拡張可能な設計としている。
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd


@dataclass
class LoadedData:
    """ファイルから読み込んだデータの統一表現。

    CSV / WAV など形式を問わず、ローダーが返す共通の型。
    UI 層やサービス層はこの型だけに依存する（依存性逆転）。

    Attributes:
        df: 読み込んだ数値データ。列番号は整数インデックス。
        sample_rate: サンプリング周波数 [Hz]。
                     WAV の場合はファイルから自動取得、CSV の場合は None（ユーザー入力）。
        file_name: アップロードされたファイル名。
        file_type: ファイル形式を示す文字列。"CSV" または "WAV"。
    """

    df: pd.DataFrame
    sample_rate: Optional[int]
    file_name: str
    file_type: str  # "CSV" | "WAV"


@dataclass
class ExtractionSettings:
    """FFT 分析に使うデータ抽出の設定値。

    サイドバー UI で選択された抽出方法・点数・サンプリング周波数を保持する。

    Attributes:
        selection_type: 抽出方法。"全範囲" / "データ個数" / "秒数" のいずれか。
        data_points: 抽出するデータ点数。"全範囲" の場合は None。
        sampling_rate: サンプリング周波数 [Hz]。FFT 計算と秒数→点数変換に使用。
        extra: 将来の拡張用辞書。
               想定キー: start_offset（開始地点）, low_freq_cutoff（低周波カット）など。
    """

    selection_type: str  # "全範囲" | "データ個数" | "秒数"
    data_points: Optional[int]
    sampling_rate: int
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FFTResult:
    """FFT 分析の実行結果。

    FFTAnalyzer が返す結果オブジェクト。UI 層でのグラフ描画に使用する。

    Attributes:
        frequencies: 正の周波数成分の配列 [Hz]。DC 成分（0 Hz）は除外済み。
        amplitudes: 各周波数に対応する振幅スペクトル（絶対値）。
        column: 分析対象の列番号。グラフタイトル等に使用。
        data_points_used: 実際に FFT に投入したデータ点数。
        metadata: 将来の拡張用辞書。
                  想定キー: peaks（ピークサーチ結果）, annotations（グラフ注釈）など。
    """

    frequencies: np.ndarray
    amplitudes: np.ndarray
    column: int
    data_points_used: int
    metadata: Dict[str, Any] = field(default_factory=dict)
