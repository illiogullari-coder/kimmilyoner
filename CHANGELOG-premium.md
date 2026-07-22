# Premium Güncelleme — Değişiklik Notları

Bu geçiş, mevcut **React + TypeScript + Vite** mimarisi korunarak yapılmıştır
(spesifikasyondaki "Vanilla JS" talebi, "mevcut mimariyi koru" talebiyle
çelişiyordu; siz React/TS'i korumayı seçtiniz).

## Bu turda tamamlananlar

- **Kullanıcı sistemi**: Avatar kaldırıldı → ilk açılışta yalnızca Erkek/Kadın
  sembolü. Kullanıcı adı yalnızca ilk oluşturmada girilir, sonra sadece
  Ayarlar'dan değiştirilebilir.
- **Sonsuz para ağacı**: `src/lib/moneyTree.ts` artık BigInt tabanlı,
  500 TL'den başlayıp sınırsız ikiye katlanıyor (overflow yok). Görsel bileşen
  sadece aktif seviyenin etrafındaki pencereyi render ediyor, sticky + smooth
  auto-scroll ile.
- **IndexedDB katmanı**: `src/lib/idb.ts` — LocalStorage'ın yanında yazma
  yapan, hataya toleranslı bir ayna.
- **BigInt-güvenli JSON storage** + **eski profillerin otomatik migrasyonu**
  (avatar/number şemasından gender/BigInt şemasına, veri kaybı olmadan).
- **Soru sistemi**: görülmemiş sorulara öncelik + art arda aynı kategori
  gelmeme mantığı.
- **Yeni joker**: +30 Saniye. Tüm jokerler her 20 doğru cevapta otomatik
  yenileniyor.
- **İstatistik dashboard**: "Kullanılan Jokerler" kartları eklendi.
- **Ana sayfa**: "Game Developer: Hamdi Uludağ" kredisi eklendi.
- **Python veri motoru**: `python/deduplicate.py`'ye Levenshtein tabanlı
  yakın-kopya (near-duplicate) filtresi eklendi; SHA-256 tam eşleşmenin
  yakalayamadığı parafraz/yazım farklı kopyaları da eliyor.
- **Doğrulama**: `src/lib/` altındaki tüm mantık dosyaları (BigInt aritmetiği,
  storage, achievements, questionPool, idb, moneyTree) izole bir TypeScript
  derleyicisiyle hatasız derlendi. Python dosyalarının tümü sözdizimi olarak
  doğrulandı ve yeni dedup fonksiyonu birim testle kontrol edildi.

## Derinlemesine analiz turu — bulunan ve düzeltilen sorunlar

- **KRİTİK HATA (düzeltildi)**: `infobox.py`'nin ürettiği yeni fact tipleri
  (`population`, `area`, `elevation`, `length`, `phone`, `plaka`)
  `distractor.py`'de tanınmıyordu ve GENERIC_POOL'a (kişi/şehir isimleri)
  düşüyordu — yani "Ankara'nın nüfusu kaçtır? A) 5.782.285 B) Sabahattin
  Ali C) Şenol Güneş" gibi anlamsız sorular üretilebiliyordu. Artık her
  sayısal kind için doğru cevabın etrafında biçim-uyumlu (binlik ayraçlı)
  sayısal çeldiriciler üretiliyor; `plaka`/`phone` için kendi kod havuzu
  kullanılıyor. `quality_score()`'a da savunma amaçlı ikinci bir katman
  eklendi: sayısal bir soruda rakam içermeyen bir çeldirici sızarsa puan
  ağır şekilde düşürülüyor (tek başına eleme sebebi).
- **Kategori-üyesi rotasyonu etkisizdi (düzeltildi)**: `fetch_category_members`
  zaten `cmlimit=count` ile sınırlı geldiği için sonradan uygulanan cursor
  kaydırması hiçbir şey değiştirmiyordu — her çalıştırma aynı ilk üyeleri
  işliyordu. Artık API'den daha büyük bir ham havuz (40) çekilip cursor
  bunun üzerinde gerçek anlamda ilerliyor.
- **Türkiye-odaklılık sızıntısı (düzeltildi)**: Rastgele madde ve
  "ilişkili maddeler" taraması küratörlü olmadığından konu dışı (Türkiye
  ile ilgisiz) makaleler soru havuzuna sızabiliyordu. `analyzer.is_turkey_related()`
  eklendi ve yalnızca bu iki güvensiz kaynağa uygulanıyor (küratörlü
  seed/kategori listeleri zaten güvenilir, ekstra kontrole gerek yok).

## Bilinçli olarak kapsam dışı bırakılanlar (bu modülde)

- **Liste sayfaları, tarih/yıl sayfaları, tablolar, yönlendirmeler**:
  Şartname bunları ayrı kaynak tipleri olarak istiyor; mevcut motor bunları
  ayrı ayrı ayrıştırmıyor (yalnızca seed/kategori/alt-kategori/ilişkili
  madde/infobox var). Bunları eklemek anlamlı bir ek modüldür (özellikle
  tablo ayrıştırma — wikitable sözdizimi karmaşık ve hatalı veri riski
  yüksek); istenirse ayrı bir adımda ele alınabilir.
- **Telefon kodu / posta kodu tam veri setleri**: Plaka kodlarının aksine
  bu ikisi için 81 ilin tamamını hatasız ezbere doğrulayamadığımdan
  (yanlış "gerçek" bilgi vermek bir bilgi yarışmasında ciddi bir risk)
  bilinçli olarak eklemedim. `infobox.py` yine de bir makalenin infobox'ında
  varsa gerçek `telefonkodu` alanını okuyabiliyor — sadece ayrı, statik
  bir doğrulanmış tablo (plaka gibi) sunmuyorum. İsterseniz resmi bir
  kaynaktan (örn. BTK) doğrulanmış tam liste ile birlikte ekleyebilirim.

## Bu turda tamamlananlar — Python Soru Üretim Motoru genişletmesi

- **`python/turkiye_data.py`** (yeni): 15 bölüme ayrılmış, şartnamedeki tam
  kapsamı (İlk Türk Devletleri, Osmanlı, Kurtuluş Savaşı/Cumhuriyet, 81 il,
  coğrafya, ulaşım, UNESCO/miras, mutfak, kültür, edebiyat, sinema/müzik,
  bilim, spor, İslam, ekonomi/tarım/enerji, afet/sağlık) kapsayan seed
  makale + Wikipedia kategori kataloğu. Ayrıca 81 ilin **doğrulanmış plaka
  kodu tablosu** — Wikipedia'ya bağımlı olmayan, doğrudan güvenilir statik
  bir soru kaynağı olarak eklendi.
- **`python/infobox.py`** (yeni): Wikipedia REST özetinin veremediği
  yapılandırılmış "bilgi kutusu" (infobox) alanlarını (nüfus, yüzölçümü,
  rakım, kuruluş yılı, plaka, vali/başkan) ham wikitext'ten ayrıştırıp
  soru fact'ine çevirir. Türkçe ünlü uyumuna göre doğru iyelik eki üretir
  ("Ankara'nın", "İzmir'in", "Muş'un").
- **`source_fetcher.py`**: `fetch_subcategories` (kategori altı taraması),
  `fetch_wikitext` (infobox için ham içerik), `fetch_related_links`
  (ilişkili maddeler) eklendi.
- **`analyzer.py`**: `classify_topic` eşlemesi genişletilmiş kataloğun tüm
  kategorilerini kapsayacak şekilde büyütüldü; yeni **`quality_score()`**
  fonksiyonu (0-100) otomatik doğrulama sisteminin parçası olarak eklendi
  — belirsiz cevaplar, tekrarlı/placeholder çeldiriciler, sayısal
  tutarsızlıklar otomatik olarak düşük puan alıp elenir (eşik: 55).
- **`deduplicate.py`**: `filter_against_existing()` eklendi — yeni sorular
  artık yalnızca aynı turun içindekilerle değil, **mevcut havuzdaki aynı
  kategorideki** sorularla da Levenshtein benzerliğine göre karşılaştırılıyor
  (kategoriye göre gruplama sayesinde tüm havuzla O(n²) karşılaştırma
  yapılmıyor).
- **`generate_questions.py`**: Kalıcı bir tarama durumu (`.crawl_state.json`)
  ile her çalıştırma kataloğun farklı bir diliminden geçiyor (aynı 40 başlık
  sürekli tekrar taranmıyor). Her turda **az soru biriken kategoriler
  önceliklendiriliyor** (dengeli dağılım). Üretilen her soruya `source`
  (Wikipedia URL'si veya `static:...`) ve dahili `qualityScore` alanı
  ekleniyor (yalnızca `questions.json`'da; `Question` tipi ve
  `questions.ts` değişmedi, geriye dönük tam uyumlu).
- **`.github/workflows/generate-questions.yml`** (yeni): Günlük cron
  (01:00 UTC) ile `python python/build.py` çalıştırıp `questions.json` /
  `questions.ts` / `.crawl_state.json` değişikliklerini otomatik commit'ler.
  Daha önce depoda hiç workflow dosyası yoktu.
- **Doğrulama**: Tüm yeni/değişen `.py` dosyaları derlendi (`py_compile`);
  infobox ayrıştırıcı ve Türkçe iyelik eki üretimi birim testle doğrulandı;
  tüm pipeline ağ erişimi kapalıyken uçtan uca çalıştırıldı — hatasız
  tamamlandı, statik plaka sorularından 79 yeni soru üretti, `questions.ts`
  geçerli TypeScript sözdizimiyle yazıldı.

## Bilinçli olarak ertelenenler (bir sonraki faz)

- **`.tsx` bileşenlerinin tam bağımlılıklarla derlenmesi**: Bu ortamda ağ
  erişimi kapalı olduğu için `npm install` çalışmadı; JSX dosyaları React tip
  tanımlarıyla derlenip test edilemedi. Kendi makinenizde
  `npm install && npm run typecheck && npm run build` çalıştırmanızı
  öneririm.
- **Python Wikipedia tarama motorunun canlı çalıştırılması**: Script'ler
  mevcuttu ve genişletildi, ama bu sandbox'ta internet erişimi olmadığı için
  gerçek bir Wikipedia taraması yapıp sonucu doğrulayamadım. Kendi
  makinenizde `python python/build.py` ile çalıştırıp `questions.json` /
  `src/data/questions.ts` dosyalarının güncellendiğini görebilirsiniz.
- **Para ağacının gerçek "üstte yatay sticky bar" haline getirilmesi**: Şu an
  sol panelde sticky + auto-scroll olarak duruyor (fonksiyonel olarak
  spesifikasyonu karşılıyor); tamamen üst yatay bara dönüştürmek daha büyük
  bir layout değişikliği, istenirse ayrı bir adımda yapılabilir.
- **Günlük/Haftalık/Aylık/Tüm Zamanlar istatistik periyotları**: Bunun için
  zaman damgalı bir oyun geçmişi logu gerekiyor (şu an sadece toplam sayaçlar
  tutuluyor); ayrı bir veri modeli gerektirdiğinden ertelendi.
- **Tam WCAG AA denetimi**: Temel klavye/ARIA davranışları korunuyor ama
  uçtan uca bir erişilebilirlik denetimi yapılmadı.
