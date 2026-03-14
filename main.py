"""
Faz 5 - Confluence (Çoklu Onay) Hibrit Karar Motoru.

7/24 çalışan sonsuz döngü ile Binance Testnet üzerinde
Trend, Momentum, Derinlik ve Duygu onaylarının hepsinden
"Geçer" notu aldığında işleme giren akıllı trading botu.
"""

import time
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import time

from core.logger import setup_logger
from exchange.binance_client import BinanceClient
from data.data_fetcher import get_live_data, get_fear_and_greed_index
from strategy.indicator import add_indicators

logger = setup_logger("main")

SYMBOL = "BTCUSDT"
INTERVAL = "1h"

# Döngü bekleme süresi (saniye)
SLEEP_SECONDS = 60



# --- TRUVA ATI: BULUT SAĞLAYICIYI KANDIRAN SAHTE SUNUCU ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Bot is running!")
    
    # Log kirliliğini önlemek için HTTP loglarını kapatıyoruz
    def log_message(self, format, *args):
        pass

def start_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()



def run_live_bot() -> None:
    """7/24 çalışan Confluence tabanlı canlı trading döngüsü.

    Her döngüde 5 farklı veri kaynağından onay alarak
    (Trend, Momentum, RSI, Derinlik, Duygu) AL/SAT kararı verir.
    Dinamik ATR tabanlı stop-loss ve çoklu take-profit kuralları uygular.
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
    buy_price: float = 0.0

    logger.info(
        f"Confluence Engine başlatıldı | {SYMBOL} | "
        f"İşlem tutarı: {trade_amount_usdt} USDT"
    )

# Sahte sunucuyu arka plan (daemon) iş parçacığı olarak başlat
    threading.Thread(target=start_dummy_server, daemon=True).start()
    logger.info("Truva Atı (Health Check Sunucusu) başlatıldı.")
    
    # ── Ana döngü ──
    while True:
        try:
            # 1) Son 250 saatlik mumu çek (EMA_200 için gerekli)
            df = get_live_data(
                client=client.client,
                symbol=SYMBOL,
                interval=INTERVAL,
                limit=250,
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

            # 3) Kapanmış son mumu temiz değişkenlere al
            last_closed = df.iloc[-2]
            current_price: float = float(last_closed["close"])
            rsi: float = float(last_closed["RSI_14"])
            ema_200: float = float(last_closed["EMA_200"])
            macd_hist: float = float(last_closed["MACDh_12_26_9"])
            atr: float = float(last_closed["ATR_14"])

            # 4) Dış veri kaynaklarını çek
            tahta_alici_yuzdesi: float = client.get_order_book_imbalance(SYMBOL)

            fng: dict = get_fear_and_greed_index()
            duygu_puani: int = fng["value"]
            duygu_sinif: str = fng["classification"]

            # 5) Kalp Atışı
            trend_label: str = "YUKARI" if current_price > ema_200 else "ASAGI"
            macd_label: str = "POZİTİF" if macd_hist > 0 else "NEGATİF"
            book_label: str = "ALICI" if tahta_alici_yuzdesi > 50 else "SATICI"

            logger.info(
                f"[Kalp Atışı] {SYMBOL}: {current_price:,.2f} USDT | "
                f"RSI: {rsi:.2f} | EMA_200: {ema_200:,.2f} (Trend: {trend_label}) | "
                f"MACD Hist: {macd_hist:.4f} ({macd_label}) | "
                f"Tahta: %{tahta_alici_yuzdesi:.1f} ({book_label}) | "
                f"Duygu: {duygu_puani} ({duygu_sinif}) | "
                f"ATR: {atr:.2f} | Pozisyon: {in_position}"
            )

            # ══════════════════════════════════════════════
            # 6) CONFLUENCE AL (BUY) KARARI - 5 ONAY GEREKLİ
            # ══════════════════════════════════════════════
            if not in_position:
                trend_ok: bool = current_price > ema_200
                momentum_ok: bool = macd_hist > 0
                rsi_ok: bool = rsi < 50
                tahta_ok: bool = tahta_alici_yuzdesi > 52.0
                duygu_ok: bool = duygu_puani < 55

                checks = {
                    "Trend (Fiyat>EMA200)": trend_ok,
                    "Momentum (MACD>0)": momentum_ok,
                    "RSI (<50)": rsi_ok,
                    "Tahta (Alıcı>%52)": tahta_ok,
                    "Duygu (<55)": duygu_ok,
                }
                passed = [name for name, ok in checks.items() if ok]
                failed = [name for name, ok in checks.items() if not ok]

                if all(checks.values()):
                    logger.info(
                        f">>> CONFLUENCE AL SİNYALİ! 5/5 onay geçti: "
                        f"{', '.join(passed)} | "
                        f"{trade_amount_usdt} USDT ile MARKET BUY gönderiliyor..."
                    )
                    raw_quantity = trade_amount_usdt / current_price
                    order = client.create_market_order(
                        symbol=SYMBOL,
                        side="BUY",
                        quantity=raw_quantity,
                    )

                    if order is not None:
                        executed_qty = float(order.get("executedQty", raw_quantity))
                        held_quantity = executed_qty
                        in_position = True
                        buy_price = current_price
                        logger.info(
                            f"ALIŞ BAŞARILI! Miktar: {held_quantity} | "
                            f"Alış Fiyatı: {buy_price:,.2f} | "
                            f"Stop-Loss seviyesi: {buy_price - (1.5 * atr):,.2f} "
                            f"(1.5 ATR = {1.5 * atr:,.2f}) | "
                            f"Emir ID: {order.get('orderId')}"
                        )
                    else:
                        logger.error("ALIŞ emri başarısız oldu, pozisyon açılmadı.")
                else:
                    logger.info(
                        f"AL sinyali YOK → Geçen: {len(passed)}/5 "
                        f"({', '.join(passed) if passed else '-'}) | "
                        f"Kalan: {', '.join(failed)}"
                    )

            # ══════════════════════════════════════════════
            # 7) CONFLUENCE SAT (SELL) KARARI - HERHANGİ BİRİ YETERLİ
            # ══════════════════════════════════════════════
            elif in_position:
                stop_loss_level: float = buy_price - (1.5 * atr)
                hit_stop_loss: bool = current_price < stop_loss_level
                hit_rsi_tp: bool = rsi > 75
                hit_momentum_tp: bool = macd_hist < 0 and duygu_puani > 75

                sell_reason: str = ""

                if hit_stop_loss:
                    sell_reason = (
                        f"STOP-LOSS! Fiyat ({current_price:,.2f}) < "
                        f"Stop ({stop_loss_level:,.2f}) | "
                        f"Alış: {buy_price:,.2f}, 1.5×ATR: {1.5 * atr:,.2f}"
                    )
                elif hit_rsi_tp:
                    sell_reason = (
                        f"TAKE-PROFIT (RSI)! RSI={rsi:.2f} > 75 → Aşırı alım"
                    )
                elif hit_momentum_tp:
                    sell_reason = (
                        f"TAKE-PROFIT (Momentum+Duygu)! "
                        f"MACD Hist={macd_hist:.4f} < 0 VE "
                        f"Duygu={duygu_puani} > 75 → Açgözlülük"
                    )

                if sell_reason:
                    logger.info(
                        f">>> SAT SİNYALİ! {sell_reason} | "
                        f"{held_quantity} adet MARKET SELL gönderiliyor..."
                    )
                    order = client.create_market_order(
                        symbol=SYMBOL,
                        side="SELL",
                        quantity=held_quantity,
                    )

                    if order is not None:
                        pnl = (current_price - buy_price) * held_quantity
                        pnl_pct = ((current_price - buy_price) / buy_price) * 100
                        logger.info(
                            f"SATIŞ BAŞARILI! Emir ID: {order.get('orderId')} | "
                            f"Alış: {buy_price:,.2f} → Satış: {current_price:,.2f} | "
                            f"PnL: {pnl:,.4f} USDT ({pnl_pct:+.2f}%)"
                        )
                        in_position = False
                        held_quantity = 0.0
                        buy_price = 0.0
                    else:
                        logger.error("SATIŞ emri başarısız oldu, pozisyon hâlâ açık.")
                else:
                    logger.info(
                        f"SAT sinyali YOK → Stop-Loss: {stop_loss_level:,.2f} | "
                        f"RSI: {rsi:.2f}/75 | MACD+Duygu: "
                        f"{'EVET' if macd_hist < 0 else 'HAYIR'}+"
                        f"{'EVET' if duygu_puani > 75 else 'HAYIR'}"
                    )

        except Exception as e:
            logger.error(f"Döngü hatası: {e}")
            time.sleep(SLEEP_SECONDS)
            continue

        time.sleep(SLEEP_SECONDS)


if __name__ == "__main__":
    run_live_bot()
