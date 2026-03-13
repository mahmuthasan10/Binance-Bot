"""
Backtest motoru modülü.

Geçmiş OHLCV verileri üzerinde RSI tabanlı al-sat stratejisini simüle eder.
Komisyon dahil kâr/zarar, işlem sayısı ve kazanma oranı raporlar.

Kullanım:
    from strategy.backtest import run_backtest, print_report

    metrics = run_backtest(df, initial_balance=100.0)
    print_report(metrics)
"""

import pandas as pd

from core.logger import setup_logger

logger = setup_logger(__name__)

COMMISSION_RATE: float = 0.001  # %0.1 komisyon


def run_backtest(
    df: pd.DataFrame,
    initial_balance: float = 100.0,
    rsi_low: float = 30.0,
    rsi_high: float = 70.0,
) -> dict:
    """Geçmiş veriler üzerinde RSI stratejisi ile backtest çalıştırır.

    Strateji:
        - RSI_14 < rsi_low → Tüm bakiyeyle AL (komisyon düşülür)
        - RSI_14 > rsi_high → Tüm coinleri SAT (komisyon düşülür)

    Args:
        df: RSI_14 ve SMA_50 kolonları eklenmiş OHLCV DataFrame.
        initial_balance: Başlangıç bakiyesi (USDT). Varsayılan: 100.0
        rsi_low: Alım sinyali RSI eşiği. Varsayılan: 30.0
        rsi_high: Satım sinyali RSI eşiği. Varsayılan: 70.0

    Returns:
        Backtest metriklerini içeren sözlük:
            - initial_balance, final_balance, total_pnl_pct,
            - total_trades, winning_trades, win_rate_pct, trades
    """
    if df.empty:
        logger.warning("Boş DataFrame, backtest çalıştırılamadı.")
        return {}

    # Durum değişkenleri
    in_position: bool = False
    current_balance: float = initial_balance
    crypto_held: float = 0.0
    buy_price: float = 0.0
    trades: list[dict] = []

    for row in df.itertuples(index=False):
        rsi: float = row.RSI_14
        close: float = row.close

        # AL sinyali: pozisyonda değiliz ve RSI < rsi_low
        if not in_position and rsi < rsi_low:
            cost_after_commission = current_balance * (1 - COMMISSION_RATE)
            crypto_held = cost_after_commission / close
            buy_price = close
            in_position = True
            current_balance = 0.0
            logger.debug(
                f"AL  | Fiyat: {close:.2f} | Miktar: {crypto_held:.6f} | "
                f"Zaman: {row.timestamp}"
            )

        # SAT sinyali: pozisyondayız ve RSI > rsi_high
        elif in_position and rsi > rsi_high:
            revenue = crypto_held * close * (1 - COMMISSION_RATE)
            pnl_pct = ((close - buy_price) / buy_price) * 100

            trades.append({
                "buy_price": buy_price,
                "sell_price": close,
                "pnl_pct": pnl_pct,
            })

            current_balance = revenue
            crypto_held = 0.0
            buy_price = 0.0
            in_position = False
            logger.debug(
                f"SAT | Fiyat: {close:.2f} | PnL: {pnl_pct:+.2f}% | "
                f"Zaman: {row.timestamp}"
            )

    # Eğer döngü bittiğinde hâlâ pozisyondaysak, son fiyattan değerle
    if in_position:
        last_close: float = df.iloc[-1]["close"]
        current_balance = crypto_held * last_close * (1 - COMMISSION_RATE)
        logger.info(
            f"Açık pozisyon son fiyattan değerlendi: {last_close:.2f}"
        )

    # Metrikleri hesapla
    total_trades: int = len(trades)
    winning_trades: int = sum(1 for t in trades if t["pnl_pct"] > 0)
    win_rate_pct: float = (winning_trades / total_trades * 100) if total_trades > 0 else 0.0
    total_pnl_pct: float = ((current_balance - initial_balance) / initial_balance) * 100

    metrics: dict = {
        "initial_balance": initial_balance,
        "final_balance": round(current_balance, 4),
        "total_pnl_pct": round(total_pnl_pct, 2),
        "total_trades": total_trades,
        "winning_trades": winning_trades,
        "win_rate_pct": round(win_rate_pct, 2),
        "trades": trades,
    }

    logger.info(
        f"Backtest tamamlandı → {total_trades} işlem, "
        f"PnL: {total_pnl_pct:+.2f}%, Win Rate: {win_rate_pct:.1f}%"
    )

    return metrics


def print_report(metrics: dict) -> None:
    """Backtest sonuçlarını terminale okunaklı formatta yazdırır."""
    if not metrics:
        print("Backtest sonucu bulunamadı.")
        return

    print("\n" + "=" * 50)
    print("          BACKTEST RAPORU")
    print("=" * 50)
    print(f"  Başlangıç Bakiyesi : {metrics['initial_balance']:.2f} USDT")
    print(f"  Final Bakiye       : {metrics['final_balance']:.2f} USDT")
    print(f"  Net Kâr/Zarar      : {metrics['total_pnl_pct']:+.2f}%")
    print("-" * 50)
    print(f"  Toplam İşlem       : {metrics['total_trades']}")
    print(f"  Kazanan İşlem      : {metrics['winning_trades']}")
    print(f"  Kazanma Oranı      : {metrics['win_rate_pct']:.1f}%")
    print("=" * 50)

    if metrics["trades"]:
        print("\n  İşlem Detayları:")
        print(f"  {'#':<4} {'Alış':>10} {'Satış':>10} {'PnL':>10}")
        print("  " + "-" * 36)
        for i, t in enumerate(metrics["trades"], 1):
            print(
                f"  {i:<4} {t['buy_price']:>10.2f} "
                f"{t['sell_price']:>10.2f} {t['pnl_pct']:>+9.2f}%"
            )
        print()


def optimize_rsi_parameters(df: pd.DataFrame) -> dict:
    """Grid Search ile en kârlı RSI eşik kombinasyonunu bulur.

    rsi_low: 20-40 arası (5'er adım)
    rsi_high: 60-85 arası (5'er adım)

    Args:
        df: İndikatörleri eklenmiş OHLCV DataFrame.

    Returns:
        En iyi parametreler ve metriklerini içeren sözlük:
            - best_rsi_low, best_rsi_high, best_pnl_pct, best_metrics
    """
    best_pnl: float = -float("inf")
    best_rsi_low: int = 30
    best_rsi_high: int = 70
    best_metrics: dict = {}
    all_results: list[dict] = []

    for rsi_low in range(20, 41, 5):
        for rsi_high in range(60, 86, 5):
            metrics = run_backtest(df, initial_balance=100.0,
                                  rsi_low=rsi_low, rsi_high=rsi_high)

            pnl = metrics.get("total_pnl_pct", -float("inf"))
            all_results.append({
                "rsi_low": rsi_low,
                "rsi_high": rsi_high,
                "pnl_pct": pnl,
                "trades": metrics.get("total_trades", 0),
            })

            if pnl > best_pnl:
                best_pnl = pnl
                best_rsi_low = rsi_low
                best_rsi_high = rsi_high
                best_metrics = metrics

    # Sonuç tablosunu yazdır
    print("\n" + "=" * 55)
    print("        OPTİMİZASYON SONUCU (Grid Search)")
    print("=" * 55)
    print(f"  {'RSI Low':<10} {'RSI High':<10} {'PnL (%)':>10} {'İşlem':>8}")
    print("  " + "-" * 42)
    for r in sorted(all_results, key=lambda x: x["pnl_pct"], reverse=True):
        marker = " <-- EN İYİ" if (r["rsi_low"] == best_rsi_low
                                    and r["rsi_high"] == best_rsi_high) else ""
        print(
            f"  {r['rsi_low']:<10} {r['rsi_high']:<10} "
            f"{r['pnl_pct']:>+9.2f}% {r['trades']:>7}{marker}"
        )
    print("=" * 55)

    logger.info(
        f"Optimizasyon tamamlandı → En iyi: RSI_low={best_rsi_low}, "
        f"RSI_high={best_rsi_high}, PnL={best_pnl:+.2f}%"
    )

    return {
        "best_rsi_low": best_rsi_low,
        "best_rsi_high": best_rsi_high,
        "best_pnl_pct": best_pnl,
        "best_metrics": best_metrics,
    }
