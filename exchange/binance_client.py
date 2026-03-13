"""
Binance API bağlantı modülü.

.env dosyasındaki anahtarlarla Binance'e (veya Testnet'e) güvenli bağlantı sağlar.

Kullanım:
    from exchange.binance_client import BinanceClient
    client = BinanceClient()
    balances = client.get_account_balance()
"""

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
