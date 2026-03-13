# 📈 Modüler Kripto Al-Sat Botu - Geliştirme Haritası

## Faz 0: Geliştirme Ortamı ve Mimari Temel (Tamamlandı)
- [x] Python 3.10+ kurulumu ve kontrolü.
- [x] Cursor IDE entegrasyonu.
- [x] `venv` (Sanal Ortam) oluşturulması ve aktif edilmesi.
- [x] `claude.md` ve `progress.md` dosyalarının detaylandırılarak eklenmesi.

## Faz 1: "Data Miner" - Tarihsel Veri Çekimi ve Depolama (Mevcut Aşama)
- [ ] Proje klasör yapısının (core, exchange, data vb.) oluşturulması.
- [ ] `requirements.txt` dosyasının oluşturulup gerekli kütüphanelerin kurulması.
- [ ] `.env.example` ve `.env` dosyalarının şablonlarının oluşturulması.
- [ ] `logger.py`: Sistemin yaptığı her işlemi `bot.log` dosyasına ve terminale yazdıracak modülün kodlanması.
- [ ] `binance_client.py`: Binance API'ye (Testnet ayarı dahil) güvenli bağlanan ve cüzdan bakiyesini döndüren sınıfın yazılması.
- [ ] `data_fetcher.py`: Belirli bir coin (Örn: BTC/USDT) için geçmiş mum (OHLCV) verilerini çeken ve bunu `pandas` DataFrame formatına çeviren modülün yazılması.
- [ ] Veritabanı Modülü: Çekilen geçmiş verileri lokalde bir `SQLite` veritabanına kaydedecek yapının kurulması.

## Faz 2: "Lab" - Backtest Motoru ve İndikatörler
- [ ] `strategy.py`: `pandas-ta` kullanılarak RSI (14) ve SMA (50) indikatörlerini DataFrame'e ekleyen fonksiyonun yazılması.
- [ ] `backtest.py`: Geçmiş veriler üzerinde çalışan bir simülasyon motoru yazılması. (Örn: RSI 30'un altındaysa al, 70'in üstündeyse sat).
- [ ] Backtest sonuçlarının (Kâr/Zarar, Toplam İşlem, Kazanma Oranı, Max Drawdown) terminale raporlanması.
- [ ] Strateji parametrelerinin optimize edilerek kârlı bir sonucun bulunması.

## Faz 3: "Live Pulse" - Canlı Testnet Akışı
- [ ] Botun, geçmiş veriler yerine Binance API'den anlık (live) veya periyodik (örneğin her 15 dakikada bir) güncel mum verisini çekecek şekilde güncellenmesi.
- [ ] Yeni gelen mum verisine göre indikatörlerin anlık hesaplanması.
- [ ] Sinyal (Al/Sat) oluştuğunda Testnet üzerinde ilk sanal piyasa (Market) emrinin gönderilmesi.

## Faz 4: Risk Yönetimi ve Paper Trading (Sanal Ticaret)
- [ ] Hard-coded Zarar Kes (Stop-Loss) modülünün sisteme entegre edilmesi (Örn: Pozisyon %2 eksiye düşerse anında sat).
- [ ] Kâr Al (Take-Profit) mekanizmasının eklenmesi.
- [ ] Botun `main.py` üzerinden 7/24 döngüde (while loop veya scheduler ile) çalışacak hale getirilmesi.
- [ ] Sistemin kendi bilgisayarımızda 1 hafta boyunca Testnet parasıyla kendi kendine çalışmaya bırakılması.

## Faz 5: Bulut ve Gerçek Para (Gelecek Planı)
- [ ] Ortamın canlı (Real) API anahtarlarıyla güncellenmesi.
- [ ] Kodların GitHub'a (.env hariç) push edilmesi.
- [ ] Ücretsiz/Uygun maliyetli bir Linux VPS'e (Google Cloud/Koyeb) sistemin taşınması ve `systemd` ile arka planda kesintisiz çalıştırılması.