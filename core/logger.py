"""
Merkezi loglama modülü.

Tüm modüller bu dosyadan logger alır:
    from core.logger import setup_logger
    logger = setup_logger(__name__)
"""

import logging
import os
from logging.handlers import RotatingFileHandler

# Proje kök dizini (Binance-Bot/)
BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_FILE: str = os.path.join(BASE_DIR, "bot.log")

# Ortak log formatı: [Tarih-Saat] - [Seviye] - [Mesaj]
LOG_FORMAT: str = "[%(asctime)s] - [%(levelname)s] - %(message)s"
DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"


def setup_logger(name: str, level: int = logging.DEBUG) -> logging.Logger:
    """Verilen isimle yapılandırılmış bir logger döndürür.

    Args:
        name: Logger adı (genellikle __name__).
        level: Minimum log seviyesi.

    Returns:
        Hem konsola hem bot.log dosyasına yazan Logger nesnesi.
    """
    logger = logging.getLogger(name)

    # Aynı logger'a tekrar handler eklemeyi önle
    if logger.handlers:
        return logger

    logger.setLevel(level)

    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    # --- Konsol Handler ---
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # --- Dosya Handler (RotatingFileHandler) ---
    # Max 5 MB, en fazla 3 yedek dosya (bot.log.1, bot.log.2, bot.log.3)
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger
