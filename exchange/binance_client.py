"""
Binance API bağlantı modülü.

.env dosyasındaki anahtarlarla Binance'e (veya Testnet'e) güvenli bağlantı sağlar.

Kullanım:
    from exchange.binance_client import BinanceClient
    client = BinanceClient()
    balances = client.get_account_balance()
"""

import math
import os
from typing import Optional

from binance.client import Client
from binance.exceptions import BinanceAPIException
from dotenv import load_dotenv

from core.logger import setup_logger

logger = setup_logger(__name__)

# Binance Testnet base URL'leri
TESTNET_API_URL = "https://testnet.binance.vision/api"


class BinanceClient:
    """Binance API istemcisi. Testnet desteği dahil."""

    def __init__(self) -> None:
        load_dotenv()

        api_key: Optional[str] = os.getenv("BINANCE_API_KEY")
        api_secret: Optional[str] = os.getenv("BINANCE_API_SECRET")
        use_testnet: bool = os.getenv("USE_TESTNET", "True").strip().lower() == "true"

        if not api_key or not api_secret:
            logger.error("BINANCE_API_KEY veya BINANCE_API_SECRET .env dosyasında bulunamadı!")
            raise ValueError(".env dosyasında API anahtarları eksik.")

        try:
            if use_testnet:
                self.client = Client(
                    api_key.strip(),
                    api_secret.strip(),
                    testnet=True,
                )
                logger.info("Binance TESTNET bağlantısı kuruldu.")
            else:
                self.client = Client(api_key.strip(), api_secret.strip())
                logger.info("Binance GERÇEK (Production) bağlantısı kuruldu.")
        except BinanceAPIException as e:
            logger.error(f"Binance API bağlantı hatası: {e}")
            raise

    def test_connection(self) -> bool:
        """API bağlantısını test eder (ping)."""
        try:
            self.client.ping()
            server_time = self.client.get_server_time()
            logger.info(f"Binance API bağlantısı başarılı. Sunucu zamanı: {server_time}")
            return True
        except BinanceAPIException as e:
            logger.error(f"Bağlantı testi başarısız: {e}")
            return False

    def get_account_balance(self, only_positive: bool = True) -> list[dict]:
        """Hesap bakiyelerini döndürür.

        Args:
            only_positive: True ise sadece bakiyesi > 0 olan varlıkları döndürür.

        Returns:
            [{"asset": "BTC", "free": "0.001", "locked": "0.0"}, ...] formatında liste.
        """
        try:
            account_info = self.client.get_account()
            balances = account_info.get("balances", [])

            if only_positive:
                balances = [
                    b for b in balances
                    if float(b["free"]) > 0 or float(b["locked"]) > 0
                ]

            logger.info(f"{len(balances)} adet varlık bakiyesi alındı.")
            return balances
        except BinanceAPIException as e:
            logger.error(f"Bakiye bilgisi alınamadı: {e}")
            return []

    def get_symbol_precision(self, symbol: str) -> int:
        """Bir sembolün LOT_SIZE stepSize bilgisinden emir hassasiyetini (ondalık basamak) döndürür.

        Örnek: stepSize='0.00100000' → precision=3

        Args:
            symbol: İşlem çifti (ör. 'BTCUSDT').

        Returns:
            Miktarın yuvarlanması gereken ondalık basamak sayısı.

        Raises:
            ValueError: Sembol bilgisi veya LOT_SIZE filtresi bulunamazsa.
        """
        try:
            info = self.client.get_symbol_info(symbol)
            if info is None:
                raise ValueError(f"{symbol} sembol bilgisi Binance'den alınamadı.")

            for f in info["filters"]:
                if f["filterType"] == "LOT_SIZE":
                    step_size = f["stepSize"]
                    # stepSize'ı ondalık basamak sayısına çevir
                    # Örn: '0.00100000' → 3, '0.01000000' → 2
                    precision = int(round(-math.log10(float(step_size)), 0))
                    logger.info(f"{symbol} LOT_SIZE stepSize={step_size}, precision={precision}")
                    return precision

            raise ValueError(f"{symbol} için LOT_SIZE filtresi bulunamadı.")
        except BinanceAPIException as e:
            logger.error(f"{symbol} sembol bilgisi alınamadı: {e}")
            raise

    def get_order_book_imbalance(self, symbol: str, limit: int = 100) -> float:
        """Emir defterindeki alıcı/satıcı baskısını yüzde olarak hesaplar.

        Tahtadaki bids (alış) ve asks (satış) hacimlerini toplayarak
        alıcı baskısı oranını döndürür.

        Args:
            symbol: İşlem çifti (ör. 'BTCUSDT').
            limit: Çekilecek emir derinliği (varsayılan 100).

        Returns:
            Alıcı baskısı yüzdesi (0-100). Örn: 55.4 → alıcılar baskın.
            Hata durumunda 50.0 (nötr) döner.
        """
        try:
            order_book: dict = self.client.get_order_book(symbol=symbol, limit=limit)

            bids: list = order_book.get("bids", [])
            asks: list = order_book.get("asks", [])

            # Her satır [Fiyat, Miktar] şeklinde string olarak gelir
            total_bids_volume: float = sum(float(bid[1]) for bid in bids)
            total_asks_volume: float = sum(float(ask[1]) for ask in asks)

            total_volume: float = total_bids_volume + total_asks_volume

            if total_volume == 0:
                logger.warning(f"{symbol} emir defteri boş, nötr (50.0) döndürülüyor.")
                return 50.0

            imbalance: float = (total_bids_volume / total_volume) * 100

            logger.info(
                f"{symbol} Emir Defteri → Alış hacmi: {total_bids_volume:.4f}, "
                f"Satış hacmi: {total_asks_volume:.4f}, Alıcı baskısı: %{imbalance:.1f}"
            )
            return imbalance

        except BinanceAPIException as e:
            logger.error(f"Order Book API hatası ({symbol}): {e}")
            return 50.0
        except Exception as e:
            logger.error(f"Order Book beklenmeyen hata ({symbol}): {e}")
            return 50.0

    def create_market_order(
        self, symbol: str, side: str, quantity: float
    ) -> Optional[dict]:
        """Piyasa emri (MARKET order) gönderir.

        Miktar, sembolün LOT_SIZE hassasiyetine göre aşağıya yuvarlanır (floor).
        Bakiye yetersizliği veya API hatası durumunda None döndürür.

        Args:
            symbol: İşlem çifti (ör. 'BTCUSDT').
            side: 'BUY' veya 'SELL'.
            quantity: Ham miktar (yuvarlanmadan önce).

        Returns:
            Başarılıysa Binance API'nin emir yanıtı (dict), başarısızsa None.
        """
        try:
            precision = self.get_symbol_precision(symbol)

            # Aşağıya doğru yuvarla (floor)
            factor = 10 ** precision
            rounded_qty = math.floor(quantity * factor) / factor

            if rounded_qty <= 0:
                logger.error(
                    f"Yuvarlanmış miktar 0 veya negatif: {quantity} → {rounded_qty} "
                    f"(precision={precision}). Emir gönderilmedi."
                )
                return None

            logger.info(
                f"MARKET {side} emri gönderiliyor: {symbol} | "
                f"Ham miktar: {quantity}, Yuvarlanmış: {rounded_qty}"
            )

            order = self.client.create_order(
                symbol=symbol,
                side=side,
                type="MARKET",
                quantity=rounded_qty,
            )

            logger.info(f"Emir başarıyla gönderildi! Yanıt: {order}")
            return order

        except BinanceAPIException as e:
            logger.error(f"MARKET {side} emri başarısız ({symbol}): {e}")
            return None
        except ValueError as e:
            logger.error(f"Precision hesaplama hatası: {e}")
            return None
        except Exception as e:
            logger.error(f"Beklenmeyen hata (create_market_order): {e}")
            return None
