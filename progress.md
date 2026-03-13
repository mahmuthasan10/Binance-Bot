# 📈 Modüler Kripto Al-Sat Botu - Geliştirme Haritası

## Faz 0: Geliştirme Ortamı ve Mimari Temel (Tamamlandı)
- [x] Python 3.10+ kurulumu ve kontrolü.
- [x] Cursor IDE entegrasyonu.
- [x] `venv` (Sanal Ortam) oluşturulması ve aktif edilmesi.
- [x] `claude.md` ve `progress.md` dosyalarının detaylandırılarak eklenmesi.

## Faz 1: "Data Miner" - Tarihsel Veri Çekimi ve Depolama (Mevcut Aşama)
- [x] Proje klasör yapısının (core, exchange, data vb.) oluşturulması.
- [x] `requirements.txt` dosyasının oluşturulup gerekli kütüphanelerin kurulması.
- [x] `.env.example` ve `.env` dosyalarının şablonlarının oluşturulması.
- [x] `logger.py`: Sistemin yaptığı her işlemi `bot.log` dosyasına ve terminale yazdıracak modülün kodlanması.
- [x] `binance_client.py`: Binance API'ye (Testnet ayarı dahil) güvenli bağlanan ve cüzdan bakiyesini döndüren sınıfın yazılması.
- [x] `data_fetcher.py`: Belirli bir coin (Örn: BTC/USDT) için geçmiş mum (OHLCV) verilerini çeken ve bunu `pandas` DataFrame formatına çeviren modülün yazılması.
- [x] Veritabanı Modülü: Çekilen geçmiş verileri lokalde bir `SQLite` veritabanına kaydedecek yapının kurulması.

## Faz 2: "Lab" - Backtest Motoru ve İndikatörler
- [x] `strategy/indicator.py`: `pandas-ta` kullanılarak RSI (14) ve SMA (50) indikatörlerini DataFrame'e ekleyen fonksiyonun yazılması.
- [x] `strategy/backtest.py`: Geçmiş veriler üzerinde çalışan bir simülasyon motoru yazılması. (RSI < 30 → AL, RSI > 70 → SAT, %0.1 komisyon dahil).
- [x] Backtest sonuçlarının (Kâr/Zarar, Toplam İşlem, Kazanma Oranı) terminale raporlanması.
- [x] Strateji parametrelerinin Grid Search ile optimize edilerek en kârlı RSI kombinasyonunun bulunması.

## Faz 3: "Live Pulse" - Canlı Testnet Akışı
- [x] Botun, geçmiş veriler yerine Binance API'den anlık (live) veya periyodik (örneğin her 15 dakikada bir) güncel mum verisini çekecek şekilde güncellenmesi.
- [x] Yeni gelen mum verisine göre indikatörlerin anlık hesaplanması.
- [x] Sinyal (Al/Sat) oluştuğunda Testnet üzerinde ilk sanal piyasa (Market) emrinin gönderilmesi.

## Faz 4: Risk Yönetimi ve Paper Trading (Sanal Ticaret)
- [ ] Hard-coded Zarar Kes (Stop-Loss) modülünün sisteme entegre edilmesi (Örn: Pozisyon %2 eksiye düşerse anında sat).
- [ ] Kâr Al (Take-Profit) mekanizmasının eklenmesi.
- [x] Botun `main.py` üzerinden 7/24 döngüde (while loop veya scheduler ile) çalışacak hale getirilmesi.
- [ ] Sistemin kendi bilgisayarımızda 1 hafta boyunca Testnet parasıyla kendi kendine çalışmaya bırakılması.

## Faz 5: "Confluence" (Çoklu Onay) Zeka Katmanı
- [ ] **5.1 - İleri Teknik Analiz:** `indicator.py` güncellenerek EMA_200, MACD ve ATR indikatörlerinin sisteme eklenmesi. `data_fetcher.py` limitinin EMA_200'ü besleyecek şekilde (min 250 mum) artırılması.
- [ ] **5.2 - Derinlik (Order Book) Analizi:** `binance_client.py` içine anlık Tahta (Order Book) verisini çekip Alıcı/Satıcı baskısını (Imbalance) hesaplayan metodun eklenmesi.
- [ ] **5.3 - Duygu (Sentiment) Analizi:** Ücretsiz bir API'den (Örn: Alternative.me) Korku ve Açgözlülük (Fear & Greed) endeksinin çekilmesi.
- [ ] **5.4 - Hibrit Karar Motoru (Refactoring):** `main.py` içindeki Live Loop'un sadece RSI'a göre değil; Trend (EMA), Momentum (MACD), Derinlik ve Duygu onaylarının Hepsinden "Geçer" notu aldığında işlem yapacak şekilde baştan yazılması.

## Faz 6: Bulut ve Kesintisiz Çalışma (Deployment)
- [ ] Kodların GitHub'a (.env hariç) push edilmesi.
- [ ] Ücretsiz bir Linux VPS'e (Google Cloud/Koyeb) sistemin taşınması ve 7/24 canlıya alınması.