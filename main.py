"""
Ana giriş noktası - Geliştirme aşamasında test amaçlı kullanılır.
"""

from core.logger import setup_logger
from core.database import init_db, save_market_data, load_market_data
from exchange.binance_client import BinanceClient
from data.data_fetcher import get_historical_data

logger = setup_logger("main")

SYMBOL = "BTCUSDT"


def main() -> None:
    # 1) Veritabanini hazirla
    init_db()

    # 2) Binance'e baglan
    client = BinanceClient()
    client.test_connection()

    # 3) OHLCV verilerini cek
    df = get_historical_data(
        client=client.client,
        symbol=SYMBOL,
        interval="1d",
        lookback="1 month ago UTC",
    )

    if df.empty:
        logger.warning("Veri cekilemedi, islem durduruluyor.")
        return

    print(f"\n=== API'den Cekilen Veri ({len(df)} mum) ===")
    print(df.head().to_string(index=False))

    # 4) Veritabanina kaydet
    new_rows = save_market_data(df, SYMBOL)
    print(f"\nYeni eklenen satir: {new_rows}")

    # 5) Veritabanindan geri oku (dogrulama)
    df_loaded = load_market_data(SYMBOL)
    print(f"\n=== Veritabanindan Okunan Veri ({len(df_loaded)} mum) ===")
    print(f"Veri tipleri:\n{df_loaded.dtypes}\n")
    print(df_loaded.head().to_string(index=False))

    # 6) Duplicate testi: ayni veriyi tekrar kaydet
    print("\n=== Duplicate Testi (ayni veri tekrar kaydediliyor) ===")
    dup_rows = save_market_data(df, SYMBOL)
    print(f"Tekrar eklenen satir: {dup_rows} (0 olmali)")


if __name__ == "__main__":
    main()
