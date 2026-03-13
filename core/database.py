"""
SQLite veritabanı yönetim modülü.

Çekilen OHLCV verilerini yerel veritabanında saklar ve geri okur.
Aynı mum verisinin tekrar kaydedilmesini UNIQUE INDEX ile engeller.

Kullanım:
    from core.database import init_db, save_market_data, load_market_data

    init_db()
    save_market_data(df, "BTCUSDT")
    df = load_market_data("BTCUSDT")
"""

import os
import sqlite3

import pandas as pd

from core.logger import setup_logger

logger = setup_logger(__name__)

# Veritabanı dosya yolu (Binance-Bot/bot_data.db)
BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH: str = os.path.join(BASE_DIR, "bot_data.db")


def _get_connection() -> sqlite3.Connection:
    """Veritabanı bağlantısı döndürür."""
    return sqlite3.connect(DB_PATH)


def init_db() -> None:
    """market_data tablosunu ve UNIQUE INDEX'i oluşturur."""
    try:
        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS market_data (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol      TEXT    NOT NULL,
                    timestamp   TEXT    NOT NULL,
                    open        REAL    NOT NULL,
                    high        REAL    NOT NULL,
                    low         REAL    NOT NULL,
                    close       REAL    NOT NULL,
                    volume      REAL    NOT NULL
                )
            """)
            cursor.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_symbol_timestamp
                ON market_data (symbol, timestamp)
            """)
            conn.commit()
        logger.info("Veritabanı hazır (market_data tablosu mevcut).")
    except sqlite3.Error as e:
        logger.error(f"Veritabanı oluşturma hatası: {e}")
        raise


def save_market_data(df: pd.DataFrame, symbol: str) -> int:
    """DataFrame'deki OHLCV verilerini veritabanına kaydeder.

    Duplicate kayıtlar UNIQUE INDEX sayesinde otomatik atlanır.

    Args:
        df: timestamp, open, high, low, close, volume kolonlu DataFrame.
        symbol: İşlem çifti (Örn: 'BTCUSDT').

    Returns:
        Yeni eklenen satır sayısı.
    """
    if df.empty:
        logger.warning(f"Boş DataFrame geldi, kayıt yapılmadı ({symbol}).")
        return 0

    try:
        with _get_connection() as conn:
            # Mevcut kayıt sayısını al (karşılaştırma için)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM market_data WHERE symbol = ?", (symbol,)
            )
            before_count: int = cursor.fetchone()[0]

            # Geçici tablo oluştur, DataFrame'i oraya yaz
            temp_df = df.copy()
            temp_df["symbol"] = symbol
            temp_df["timestamp"] = temp_df["timestamp"].astype(str)
            temp_df.to_sql("_temp_market_data", conn, if_exists="replace", index=False)

            # Geçici tablodan ana tabloya INSERT OR IGNORE
            cursor.execute("""
                INSERT OR IGNORE INTO market_data
                    (symbol, timestamp, open, high, low, close, volume)
                SELECT symbol, timestamp, open, high, low, close, volume
                FROM _temp_market_data
            """)
            conn.commit()

            # Geçici tabloyu temizle
            cursor.execute("DROP TABLE IF EXISTS _temp_market_data")
            conn.commit()

            # Yeni eklenen satır sayısını hesapla
            cursor.execute(
                "SELECT COUNT(*) FROM market_data WHERE symbol = ?", (symbol,)
            )
            after_count: int = cursor.fetchone()[0]
            new_rows: int = after_count - before_count

            logger.info(
                f"{symbol}: {new_rows} yeni satır eklendi "
                f"(toplam: {after_count}, atlanılan: {len(df) - new_rows})."
            )
            return new_rows

    except sqlite3.Error as e:
        logger.error(f"Veri kaydetme hatası ({symbol}): {e}")
        return 0


def load_market_data(symbol: str) -> pd.DataFrame:
    """Veritabanından belirtilen sembolün OHLCV verilerini okur.

    Args:
        symbol: İşlem çifti (Örn: 'BTCUSDT').

    Returns:
        Temiz DataFrame (timestamp datetime64, fiyatlar float64).
        Veri yoksa boş DataFrame döner.
    """
    try:
        with _get_connection() as conn:
            df = pd.read_sql_query(
                "SELECT timestamp, open, high, low, close, volume "
                "FROM market_data WHERE symbol = ? ORDER BY timestamp",
                conn,
                params=(symbol,),
            )

        if df.empty:
            logger.warning(f"{symbol} için veritabanında kayıt bulunamadı.")
            return df

        # Tip dönüşümleri
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = df[col].astype(float)

        logger.info(f"{symbol}: Veritabanından {len(df)} satır okundu.")
        return df

    except sqlite3.Error as e:
        logger.error(f"Veri okuma hatası ({symbol}): {e}")
        return pd.DataFrame()
