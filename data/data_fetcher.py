"""
Geçmiş mum (OHLCV) verisi çekme modülü.

Binance API'den tarihsel kline verilerini çeker, temizler ve
pandas DataFrame olarak döndürür.

Kullanım:
    from data.data_fetcher import get_historical_data
    df = get_historical_data("BTCUSDT", "1d", "1 month ago UTC")
"""

import pandas as pd
from binance.client import Client
from binance.exceptions import BinanceAPIException

from core.logger import setup_logger

logger = setup_logger(__name__)

# Binance kline verisinin ham kolon sırası
RAW_COLUMNS: list[str] = [
    "timestamp", "open", "high", "low", "close", "volume",
    "close_time", "quote_asset_volume", "number_of_trades",
    "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume", "ignore",
]

# Nihai DataFrame'de tutulacak kolonlar
KEEP_COLUMNS: list[str] = ["timestamp", "open", "high", "low", "close", "volume"]

# float'a çevrilecek fiyat/hacim kolonları
NUMERIC_COLUMNS: list[str] = ["open", "high", "low", "close", "volume"]


def get_historical_data(
    client: Client,
    symbol: str = "BTCUSDT",
    interval: str = "1d",
    lookback: str = "1 month ago UTC",
) -> pd.DataFrame:
    """Binance'den geçmiş OHLCV mum verilerini çeker ve temizler.

    Args:
        client: python-binance Client nesnesi.
        symbol: İşlem çifti (Örn: 'BTCUSDT').
        interval: Mum aralığı (Örn: '15m', '1h', '1d').
        lookback: Geriye dönük süre (Örn: '1 month ago UTC').

    Returns:
        Temizlenmiş DataFrame (timestamp, open, high, low, close, volume).
        Hata durumunda boş DataFrame döner.
    """
    try:
        logger.info(f"{symbol} için {interval} mumları çekiliyor ({lookback})...")

        raw_klines: list = client.get_historical_klines(symbol, interval, lookback)

        if not raw_klines:
            logger.warning(f"{symbol} için veri bulunamadı.")
            return pd.DataFrame(columns=KEEP_COLUMNS)

        # --- Ham listeyi DataFrame'e çevir ---
        df = pd.DataFrame(raw_klines, columns=RAW_COLUMNS)

        # --- Tip Dönüşümleri ---
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

        for col in NUMERIC_COLUMNS:
            df[col] = df[col].astype(float)

        # --- Sadece ihtiyacımız olan kolonları tut ---
        df = df[KEEP_COLUMNS]

        logger.info(f"{symbol}: {len(df)} adet mum verisi başarıyla çekildi.")
        return df

    except BinanceAPIException as e:
        logger.error(f"Binance API hatası ({symbol}): {e}")
        return pd.DataFrame(columns=KEEP_COLUMNS)
    except Exception as e:
        logger.error(f"Beklenmeyen hata ({symbol}): {e}")
        return pd.DataFrame(columns=KEEP_COLUMNS)


def get_live_data(
    client: Client,
    symbol: str = "BTCUSDT",
    interval: str = "1h",
    limit: int = 100,
) -> pd.DataFrame:
    """Binance'den son N mumu (anlık/canlı) çeker ve temizler.

    get_historical_data'dan farkı: lookback yerine sabit limit kullanır,
    böylece canlı döngüde her çağrıda sadece son mumları alır.

    Args:
        client: python-binance Client nesnesi.
        symbol: İşlem çifti (Örn: 'BTCUSDT').
        interval: Mum aralığı (Örn: '15m', '1h', '1d').
        limit: Çekilecek mum sayısı (varsayılan 100).

    Returns:
        Temizlenmiş DataFrame (timestamp, open, high, low, close, volume).
        Hata durumunda boş DataFrame döner.
    """
    try:
        logger.info(f"{symbol} için son {limit} adet {interval} mum çekiliyor...")

        raw_klines: list = client.get_klines(
            symbol=symbol, interval=interval, limit=limit
        )

        if not raw_klines:
            logger.warning(f"{symbol} için canlı veri bulunamadı.")
            return pd.DataFrame(columns=KEEP_COLUMNS)

        df = pd.DataFrame(raw_klines, columns=RAW_COLUMNS)

        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

        for col in NUMERIC_COLUMNS:
            df[col] = df[col].astype(float)

        df = df[KEEP_COLUMNS]

        logger.info(f"{symbol}: {len(df)} adet canlı mum verisi alındı.")
        return df

    except BinanceAPIException as e:
        logger.error(f"Binance API hatası (canlı veri - {symbol}): {e}")
        return pd.DataFrame(columns=KEEP_COLUMNS)
    except Exception as e:
        logger.error(f"Beklenmeyen hata (canlı veri - {symbol}): {e}")
        return pd.DataFrame(columns=KEEP_COLUMNS)
