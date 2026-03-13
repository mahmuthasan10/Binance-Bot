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

    # NaN satırları temizle (SMA_50 ilk 49 satırda NaN üretir)
    before_count: int = len(df)
    df.dropna(inplace=True)
    df.reset_index(drop=True, inplace=True)
    dropped: int = before_count - len(df)

    logger.info(
        f"İndikatörler eklendi → RSI_14, SMA_50 | "
        f"{dropped} NaN satır temizlendi, kalan: {len(df)} satır."
    )

    return df
