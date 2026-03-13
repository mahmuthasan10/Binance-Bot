"""
Teknik indikatör hesaplama modülü.

OHLCV DataFrame'ine teknik analiz indikatörlerini ekler.
Backtest ve canlı strateji motorları bu modülü kullanır.

Kullanım:
    from strategy.indicator import add_indicators

    df = add_indicators(df)
"""

import pandas as pd
import pandas_ta as ta

from core.logger import setup_logger

logger = setup_logger(__name__)


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """DataFrame'e teknik indikatörleri ekler ve NaN satırları temizler.

    Eklenen indikatörler:
        - RSI_14: 14 periyotluk Göreceli Güç Endeksi
        - SMA_50: 50 periyotluk Basit Hareketli Ortalama
        - EMA_200: 200 periyotluk Üstel Hareketli Ortalama (Trend filtresi)
        - MACD_12_26_9: MACD çizgisi
        - MACDh_12_26_9: MACD Histogramı (Momentum gücü)
        - MACDs_12_26_9: MACD Sinyal çizgisi
        - ATR_14: 14 periyotluk Average True Range (Volatilite ölçümü)

    Args:
        df: timestamp, open, high, low, close, volume kolonlu OHLCV DataFrame.

    Returns:
        İndikatör kolonları eklenmiş ve NaN satırları temizlenmiş DataFrame.
    """
    if df.empty:
        logger.warning("Boş DataFrame geldi, indikatör hesaplanamadı.")
        return df

    # RSI (14 periyot)
    df["RSI_14"] = ta.rsi(df["close"], length=14)

    # SMA (50 periyot)
    df["SMA_50"] = ta.sma(df["close"], length=50)

    # EMA (200 periyot) - Uzun vadeli trend filtresi
    df["EMA_200"] = ta.ema(df["close"], length=200)

    # MACD (12, 26, 9) - Momentum göstergesi
    macd_df = ta.macd(df["close"], fast=12, slow=26, signal=9)
    df["MACD_12_26_9"] = macd_df["MACD_12_26_9"]
    df["MACDh_12_26_9"] = macd_df["MACDh_12_26_9"]
    df["MACDs_12_26_9"] = macd_df["MACDs_12_26_9"]

    # ATR (14 periyot) - Volatilite ölçümü
    df["ATR_14"] = ta.atr(df["high"], df["low"], df["close"], length=14)

    # NaN satırları temizle (EMA_200 ilk ~199 satırda NaN üretir)
    before_count: int = len(df)
    df.dropna(inplace=True)
    df.reset_index(drop=True, inplace=True)
    dropped: int = before_count - len(df)

    logger.info(
        f"İndikatörler eklendi → RSI_14, SMA_50, EMA_200, MACD, ATR_14 | "
        f"{dropped} NaN satır temizlendi, kalan: {len(df)} satır."
    )

    return df
