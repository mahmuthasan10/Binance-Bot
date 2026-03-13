"""
Ana giriş noktası - Geliştirme aşamasında test amaçlı kullanılır.
"""

from core.logger import setup_logger
from core.database import init_db, load_market_data
from exchange.binance_client import BinanceClient
from data.data_fetcher import get_historical_data
from strategy.indicator import add_indicators
from strategy.backtest import run_backtest, print_report, optimize_rsi_parameters

logger = setup_logger("main")

SYMBOL = "BTCUSDT"


def main() -> None:
    # 1) Veritabanını hazırla
    init_db()

    # 2) Saatlik OHLCV verisini API'den çek
    client = BinanceClient()
    df = get_historical_data(
        client=client.client,
        symbol=SYMBOL,
        interval="1h",
        lookback="1 month ago UTC",
    )

    if df.empty:
        logger.warning("Veri çekilemedi, işlem durduruluyor.")
        return

    print(f"\n=== API'den Çekilen Ham Veri ({len(df)} mum) ===")

    # 3) Teknik indikatörleri ekle
    df = add_indicators(df)

    if df.empty:
        logger.warning("İndikatör sonrası veri kalmadı (yetersiz mum sayısı).")
        return

    # 4) RSI parametrelerini optimize et
    best = optimize_rsi_parameters(df)

    # 5) En iyi parametrelerle detaylı backtest raporu
    print(f"\n>>> En iyi parametrelerle backtest: "
          f"RSI_low={best['best_rsi_low']}, RSI_high={best['best_rsi_high']}")
    best_metrics = run_backtest(
        df, initial_balance=100.0,
        rsi_low=best["best_rsi_low"],
        rsi_high=best["best_rsi_high"],
    )
    print_report(best_metrics)


if __name__ == "__main__":
    main()
