"""
Faz 4 - Canlı Döngü (Live Engine).

7/24 çalışan sonsuz döngü ile Binance Testnet üzerinde
RSI sinyallerine göre otomatik AL/SAT emri gönderir.
"""

import time

from core.logger import setup_logger
from exchange.binance_client import BinanceClient
from data.data_fetcher import get_live_data
from strategy.indicator import add_indicators

logger = setup_logger("main")

SYMBOL = "BTCUSDT"
INTERVAL = "1h"

# Faz 2'de optimize edilmiş RSI eşikleri
RSI_LOW = 25
RSI_HIGH = 80

# Döngü bekleme süresi (saniye)
SLEEP_SECONDS = 60


def run_live_bot() -> None:
    """7/24 çalışan canlı trading döngüsü.

    Her döngüde son 100 saatlik mumu çeker, RSI hesaplar ve
    optimize edilmiş eşiklere göre MARKET BUY/SELL emri gönderir.
    """
    # ── Binance bağlantısı ──
    client = BinanceClient()

    if not client.test_connection():
        logger.error("Binance bağlantısı kurulamadı, çıkılıyor.")
        return

    # ── Durum değişkenleri ──
    in_position: bool = False
    trade_amount_usdt: float = 15.0
    held_quantity: float = 0.0

    logger.info(
        f"Live Engine başlatıldı | {SYMBOL} | RSI_LOW={RSI_LOW}, RSI_HIGH={RSI_HIGH} | "
        f"İşlem tutarı: {trade_amount_usdt} USDT"
    )

    # ── Ana döngü ──
    while True:
        try:
            # 1) Son 100 saatlik mumu çek
            df = get_live_data(
                client=client.client,
                symbol=SYMBOL,
                interval=INTERVAL,
                limit=100,
            )

            if df.empty:
                logger.warning("Canlı veri çekilemedi, bir sonraki döngüye geçiliyor.")
                time.sleep(SLEEP_SECONDS)
                continue

            # 2) İndikatörleri hesapla
            df = add_indicators(df)

            if df.empty:
                logger.warning("İndikatör sonrası veri kalmadı, bir sonraki döngüye geçiliyor.")
                time.sleep(SLEEP_SECONDS)
                continue

            # 3) Kapanmış son mumu seç (iloc[-2]: son kapanmış, iloc[-1]: henüz açık)
            last_closed = df.iloc[-2]
            close_price: float = float(last_closed["close"])
            rsi_14: float = float(last_closed["RSI_14"])

            # 4) Kalp Atışı
            logger.info(
                f"[Kalp Atışı] {SYMBOL}: {close_price:,.2f} USDT | "
                f"RSI: {rsi_14:.2f} | Pozisyon: {in_position}"
            )

            # 5) AL SİNYALİ
            if not in_position and rsi_14 < RSI_LOW:
                logger.info(
                    f">>> AL SİNYALİ! RSI={rsi_14:.2f} < {RSI_LOW} | "
                    f"{trade_amount_usdt} USDT ile MARKET BUY gönderiliyor..."
                )
                raw_quantity = trade_amount_usdt / close_price
                order = client.create_market_order(
                    symbol=SYMBOL,
                    side="BUY",
                    quantity=raw_quantity,
                )

                if order is not None:
                    # Doldurulan gerçek miktarı yanıttan al
                    executed_qty = float(order.get("executedQty", raw_quantity))
                    held_quantity = executed_qty
                    in_position = True
                    logger.info(
                        f"ALIŞ BAŞARILI! Miktar: {held_quantity} | "
                        f"Emir ID: {order.get('orderId')}"
                    )
                else:
                    logger.error("ALIŞ emri başarısız oldu, pozisyon açılmadı.")

            # 6) SAT SİNYALİ
            elif in_position and rsi_14 > RSI_HIGH:
                logger.info(
                    f">>> SAT SİNYALİ! RSI={rsi_14:.2f} > {RSI_HIGH} | "
                    f"{held_quantity} adet MARKET SELL gönderiliyor..."
                )
                order = client.create_market_order(
                    symbol=SYMBOL,
                    side="SELL",
                    quantity=held_quantity,
                )

                if order is not None:
                    in_position = False
                    held_quantity = 0.0
                    logger.info(
                        f"SATIŞ BAŞARILI! Emir ID: {order.get('orderId')}"
                    )
                else:
                    logger.error("SATIŞ emri başarısız oldu, pozisyon hâlâ açık.")

        except Exception as e:
            logger.error(f"Döngü hatası: {e}")
            time.sleep(SLEEP_SECONDS)
            continue

        time.sleep(SLEEP_SECONDS)


if __name__ == "__main__":
    run_live_bot()
