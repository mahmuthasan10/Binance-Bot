"""
Faz 3 - Canlı Veri + İndikatör + Sinyal Testi.

Binance'den son 100 saatlik mumu çeker, RSI/SMA hesaplar,
kapanmış son muma göre sinyal olup olmadığını raporlar.
"""

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


def main() -> None:
    # 1) Binance bağlantısını kur
    client = BinanceClient()

    if not client.test_connection():
        logger.error("Binance bağlantısı kurulamadı, çıkılıyor.")
        return

    # 2) Son 100 saatlik mumu çek
    df = get_live_data(
        client=client.client,
        symbol=SYMBOL,
        interval=INTERVAL,
        limit=100,
    )

    if df.empty:
        logger.warning("Canlı veri çekilemedi, işlem durduruluyor.")
        return

    print(f"\n=== Çekilen Canlı Veri: {len(df)} mum ({SYMBOL} / {INTERVAL}) ===")

    # 3) İndikatörleri hesapla
    df = add_indicators(df)

    if df.empty:
        logger.warning("İndikatör sonrası veri kalmadı (yetersiz mum sayısı).")
        return

    # 4) Kapanmış son mumu baz al (iloc[-2]: son kapanmış, iloc[-1]: henüz açık)
    last_closed = df.iloc[-2]

    close_price = last_closed["close"]
    sma_50 = last_closed["SMA_50"]
    rsi_14 = last_closed["RSI_14"]
    timestamp = last_closed["timestamp"]

    print(f"\n{'='*55}")
    print(f"  Son Kapanmış Mum : {timestamp}")
    print(f"  Kapanış Fiyatı   : {close_price:,.2f} USDT")
    print(f"  SMA_50           : {sma_50:,.2f} USDT")
    print(f"  RSI_14           : {rsi_14:.2f}")
    print(f"{'='*55}")

    # 5) Sinyal kontrolü (optimize edilmiş eşikler)
    print(f"\n  Strateji Eşikleri: RSI < {RSI_LOW} → AL | RSI > {RSI_HIGH} → SAT")
    print(f"  {'-'*50}")

    if rsi_14 < RSI_LOW:
        signal = "AL (BUY)"
        print(f"  >>> SİNYAL: {signal}")
        print(f"      RSI ({rsi_14:.2f}) < {RSI_LOW} → Aşırı satım bölgesi!")
    elif rsi_14 > RSI_HIGH:
        signal = "SAT (SELL)"
        print(f"  >>> SİNYAL: {signal}")
        print(f"      RSI ({rsi_14:.2f}) > {RSI_HIGH} → Aşırı alım bölgesi!")
    else:
        signal = "BEKLE (HOLD)"
        print(f"  >>> SİNYAL: {signal}")
        print(f"      RSI ({rsi_14:.2f}) nötr bölgede, emir yok.")

    print(f"{'='*55}\n")
    logger.info(f"Sinyal sonucu: {signal} | RSI={rsi_14:.2f}, Close={close_price:.2f}")


if __name__ == "__main__":
    main()
