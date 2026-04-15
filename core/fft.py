# coding: utf-8
"""
core.fft — FFT（高速フーリエ変換）分析処理

時系列の数値データを受け取り、周波数スペクトルを計算する。
numpy.fft を使用し、正の周波数成分のみを返す。

前処理として以下を適用する:
    - 平均値除去: DC オフセット（センサバイアス等）を除去
    - Hann 窓: 有限長データのスペクトル漏れ（リーケージ）を低減

将来的にゼロパディングや他の窓関数への切替などの
拡張を行う場合は、このモジュール内で対応する。
"""

from typing import Tuple

import numpy as np

from core.models import FFTResult


class FFTAnalyzer:
    """時系列データに対して FFT を実行し、周波数スペクトルを得る。

    使用例::

        analyzer = FFTAnalyzer(data_array, sampling_freq=1000)
        result = analyzer.execute(column=2)
        # result.frequencies — 周波数 [Hz]
        # result.amplitudes  — 振幅スペクトル

    Attributes:
        _data: 分析対象の 1 次元数値配列。
        _sampling_freq: サンプリング周波数 [Hz]。
    """

    def __init__(self, data: np.ndarray, sampling_freq: int):
        """
        Args:
            data: 1 次元の時系列データ。内部で float に変換される。
            sampling_freq: サンプリング周波数 [Hz]。1 以上の整数。
        """
        self._data = np.asarray(data, dtype=float)
        self._sampling_freq = sampling_freq

    def execute(self, column: int = 0) -> FFTResult:
        """FFT を実行し、結果を FFTResult として返す。

        Args:
            column: 分析対象の列番号（結果の識別用。計算自体には影響しない）。

        Returns:
            FFTResult: 正の周波数成分と対応する振幅を格納した結果オブジェクト。
        """
        freqs, amps = self._compute()
        return FFTResult(
            frequencies=freqs,
            amplitudes=amps,
            column=column,
            data_points_used=len(self._data),
        )

    def _compute(self) -> Tuple[np.ndarray, np.ndarray]:
        """FFT の実計算を行う内部メソッド。

        前処理として平均値除去と Hann 窓を適用してから FFT を実行する。

        処理手順:
            1. 平均値除去（DC オフセットの除去）
               — データの平均値を引くことで、0 Hz 付近の巨大なピークを抑制する。
                 センサのバイアスや計測系のオフセットに起因する成分を取り除く。
            2. Hann 窓の適用
               — 有限長データの両端不連続によるスペクトル漏れ（リーケージ）を低減する。
                 Hann 窓は汎用性が高く、周波数分解能と漏れ抑制のバランスが良い。
            3. numpy.fft.fft で複素スペクトルを取得
            4. numpy.fft.fftfreq で対応する周波数軸を生成
            5. 正の周波数成分のみを抽出（DC 成分 0 Hz は除外）
            6. 振幅は複素数の絶対値

        Returns:
            (frequencies, amplitudes) のタプル。
            frequencies: 正の周波数 [Hz] の配列（0 Hz を除く）。
            amplitudes: 対応する振幅スペクトルの配列。
        """
        # 平均値除去 — DC オフセットを取り除く
        detrended = self._data - np.mean(self._data)

        # Hann 窓適用 — スペクトル漏れを低減
        window = np.hanning(len(detrended))
        windowed = detrended * window

        dt = 1.0 / self._sampling_freq
        fft_vals = np.fft.fft(windowed)
        freqs = np.fft.fftfreq(len(windowed), d=dt)

        # 前半（正の周波数側）のみ取り出す
        half = len(freqs) // 2
        pos_freqs = freqs[:half]
        pos_amps = np.abs(fft_vals)[:half]

        # DC 成分（0 Hz）を除外
        mask = pos_freqs > 0
        return pos_freqs[mask], pos_amps[mask]
