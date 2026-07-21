"""Main question generation orchestrator.

Runs the full pipeline: fetch encyclopedic Turkish content, analyze,
generate distractors, estimate difficulty, deduplicate, export.
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

from analyzer import classify_topic, extract_facts
from deduplicate import filter_unique, question_hash
from difficulty import estimate_difficulty
from distractor import generate_distractors
from exporter import export, load_existing, merge
from source_fetcher import clean_text, fetch_article, fetch_raw_titles

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "questions.json"
SEED_TOPICS = [
    "Anıtkabir", "İstiklal Marşı", "TBMM", "Meclis", "Lozan Antlaşması",
"Sultanahmet Camii", "Ayasofya", "Topkapı Sarayı", "Dolmabahçe Sarayı", "Galata Kulesi",
"Kız Kulesi", "İnciraltı", "Bodrum", "Alanya", "Antalya",
"İzmir", "Bursa", "Trabzon", "Rize", "Trabzon Kalesi",
"Karadeniz Bölgesi", "İç Anadolu", "Ege Bölgesi", "Akdeniz Bölgesi", "Marmara Bölgesi",
"Doğu Anadolu", "Güneydoğu Anadolu", "Kaçkar Dağları", "Toroslar", "Erciyes Dağı",
"Uludağ", "Palandöken", "Sakarya Nehri", "Çoruh Nehri", "Seyhan Nehri",
"Ceyhan Nehri", "Eğirdir Gölü", "Beyşehir Gölü", "Burdur Gölü", "Abant Gölü",
"Uzungöl", "Ayder Yaylası", "Şahmeran Efsanesi", "Nasreddin Hoca", "Keloğlan",
"Dede Korkut", "Köroğlu", "Mehmet Akif Ersoy", "Nazım Hikmet", "Sabahattin Ali",
"Atilla İlhan", "Cemal Süreya", "Edip Cansever", "Neşet Ertaş", "Aşık Veysel",
"Zeki Müren", "Müzeyyen Senar", "Sezen Aksu", "Tarkan", "Cem Yılmaz",
"Şener Şen", "Kemal Sunal", "Türkan Şoray", "Cüneyt Arkın", "Nuri Bilge Ceylan",
"Fatih Terim", "Şenol Güneş", "Mustafa Denizli", "Arda Turan", "Hakan Şükür",
"Hamza Hamzaoğlu", "Naim Süleymanoğlu", "Halis Müftüoğlu", "Yasemin Adar", "Rıza Kayaalp",
"Taha Akgül", "İbrahim Çelikkol", "Hande Erçel", "Kıvanç Tatlıtuğ", "Kenan İmirzalıoğlu",
"Bergüzar Korel", "Halit Ergenç", "Ezogelin Çorbası", "İskender Kebap", "Adana Kebap",
"Urfa Kebap", "Lahmacun", "Pide", "Mantı", "Menemen",
"Kuru Fasulye", "Pilav", "Simit", "Ayran", "Şalgam Suyu",
"Rakı", "Türk Çayı", "Pişmaniye", "Künefe", "Güllaç",
"Çırağan Sarayı", "Yıldız Sarayı", "Beylerbeyi Sarayı", "Anadolu Hisarı", "Rumeli Hisarı",
"Yedikule Zindanları", "Süleymaniye Camii", "Selimiye Camii", "Divriği Ulu Camii", "Hattat",
"Ebru Sanatı", "Tezhip", "Minyatür", "Hat Sanatı", "Çini",
"Oltutaşı", "Lüle taşı", "Kütahya Çinisi", "Hereke Halısı", "Uşak Halısı",
"Zeybek", "Horon", "Halay", "Bar", "Kasap Havası",
"Karşılama", "Sema Gösterisi", "Mevlana", "Hacı Bektaş-ı Veli", "Yunus Emre",
"Ahilik", "Osman Gazi", "Orhan Gazi", "Fatih Sultan Mehmet", "Kanuni Sultan Süleyman",
"Yavuz Sultan Selim", "II. Mahmud", "III. Selim", "Abdülhamid II", "Milli Mücadele",
"Amasya Genelgesi", "Erzurum Kongresi", "Sivas Kongresi", "Misak-ı Millî", "Samsun'a Çıkış",
"Sakarya Meydan Savaşı", "Büyük Taarruz", "İzmir'in Kurtuluşu", "Cumhuriyetin İlanı", "Harf İnkılabı",
"Kılık Kıyafet İnkılabı", "Soyadı Kanunu", "Kadın Hakları", "Türk Dil Kurumu", "Türk Tarih Kurumu",
"MTA", "TPAO", "TÜBİTAK", "ASELSAN", "TAI",
"Baykar", "TOGG", "Kızılay", "Yeşilay", "ÇEKÜL",
"TEMA Vakfı", "Anadolu Ajansı", "TRT", "İstanbul Üniversitesi", "Ankara Üniversitesi",
"Galatasaray Lisesi", "İstanbul Erkek Lisesi", "Kabataş Erkek Lisesi", "Boğaziçi Üniversitesi", "Orta Doğu Teknik Üniversitesi",
"İTÜ", "Yıldız Teknik Üniversitesi", "Hacettepe Üniversitesi", "Ege Üniversitesi", "Dokuz Eylül Üniversitesi"
]
CATEGORY_POOL = [
    "Adana", "Aladağ", "Ceyhan", "Çukurova", "Feke", "İmamoğlu", "Karaisalı", "Karataş", "Kozan", "Pozantı", "Saimbeyli", "Sarıçam", "Seyhan", "Tufanbeyli", "Yumurtalık", "Yüreğir",
"Adıyaman", "Besni", "Çelikhan", "Gerger", "Gölbaşı", "Kahta", "Merkez", "Samsat", "Sincik", "Tut",
"Afyonkarahisar", "Başmakçı", "Bayat", "Bolvadin", "Çay", "Çobanlar", "Dazkırı", "Dinar", "Emirdağ", "Evciler", "Hocalar", "İhsaniye", "İscehisar", "Kızılören", "Merkez", "Sandıklı", "Sinanpaşa", "Sultandağı", "Şuhut",
"Ağrı", "Diyadin", "Doğubayazıt", "Eleşkirt", "Hamur", "Merkez", "Patnos", "Taşlıçay", "Tutak",
"Aksaray", "Ağaçören", "Eskil", "Gülağaç", "Güzelyurt", "Merkez", "Ortaköy", "Sarıyahşi", "Sultanhanı",
"Amasya", "Göynücek", "Gümüşhacıköy", "Hamamözü", "Merkez", "Merzifon", "Suluova", "Taşova",
"Ankara", "Akyurt", "Altındağ", "Ayaş", "Bala", "Beypazarı", "Çamlıdere", "Çankaya", "Çubuk", "Elmadağ", "Etimesgut", "Evren", "Gölbaşı", "Güdül", "Haymana", "Kahramankazan", "Kalecik", "Keçiören", "Kızılcahamam", "Mamak", "Nallıhan", "Polatlı", "Pursaklar", "Sincan", "Şereflikoçhisar", "Yenimahalle",
"Antalya", "Akseki", "Aksu", "Alanya", "Demre", "Döşemealtı", "Elmalı", "Finike", "Gazipaşa", "Gündoğmuş", "İbradı", "Kaş", "Kemer", "Kepez", "Konyaaltı", "Korkuteli", "Kumluca", "Manavgat", "Muratpaşa", "Serik",
"Ardahan", "Çıldır", "Damal", "Göle", "Hanak", "Merkez", "Posof",
"Artvin", "Ardanuç", "Arhavi", "Borçka", "Hopa", "Kemalpaşa", "Murgul", "Şavşat", "Yusufeli",
"Aydın", "Bozdoğan", "Buharkent", "Çine", "Didim", "Efeler", "Germencik", "İncirliova", "Karacasu", "Karpuzlu", "Koçarlı", "Köşk", "Kuşadası", "Kuyucak", "Nazilli", "Söke", "Sultanhisar", "Yenipazar",
"Balıkesir", "Altıeylül", "Ayvalık", "Balya", "Bandırma", "Bigadiç", "Burhaniye", "Dursunbey", "Edremit", "Erdek", "Gömeç", "Gönen", "Havran", "İvrindi", "Karesi", "Kepsut", "Marmara", "Savaştepe", "Sındırgı", "Susurluk",
"Bartın", "Amasra", "Kurucaşile", "Merkez", "Ulus",
"Batman", "Beşiri", "Gercüş", "Hasankeyf", "Kozluk", "Merkez", "Sason",
"Bayburt", "Aydıntepe", "Demirözü", "Merkez",
"Bilecik", "Bozüyük", "Gölpazarı", "İnhisar", "Merkez", "Osmaneli", "Pazaryeri", "Söğüt", "Yenipazar",
"Bingöl", "Adaklı", "Genç", "Karlıova", "Kiğı", "Merkez", "Solhan", "Yayladere", "Yedisu",
"Bitlis", "Adilcevaz", "Ahlat", "Güroymak", "Hizan", "Merkez", "Mutki", "Tatvan",
"Bolu", "Dörtdivan", "Gerede", "Göynük", "Kıbrıscık", "Mengen", "Mudurnu", "Seben", "Merkez", "Yeniçağa",
"Burdur", "Ağlasun", "Altınyayla", "Bucak", "Çavdır", "Çeltikçi", "Gölhisar", "Karamanlı", "Kemer", "Merkez", "Tefenni", "Yeşilova",
"Bursa", "Büyükorhan", "Gemlik", "Gürsu", "Harmancık", "İnegöl", "İznik", "Karacabey", "Keles", "Kestel", "Mudanya", "Mustafakemalpaşa", "Nilüfer", "Orhaneli", "Orhangazi", "Osmangazi", "Yenişehir", "Yıldırım",
"Çanakkale", "Ayvacık", "Bayramiç", "Biga", "Bozcaada", "Çan", "Eceabat", "Ezine", "Gelibolu", "Gökçeada", "Lapseki", "Merkez", "Yenice",
"Çankırı", "Atkaracalar", "Bayramören", "Çerkeş", "Eldivan", "Ilgaz", "Kızılırmak", "Korgun", "Kurşunlu", "Merkez", "Orta", "Şabanözü", "Yapraklı",
"Çorum", "Alaca", "Bayat", "Boğazkale", "Dodurga", "İskilip", "Kargı", "Laçin", "Mecitözü", "Merkez", "Oğuzlar", "Ortaköy", "Osmancık", "Sungurlu", "Uğurludağ",
"Denizli", "Acıpayam", "Babadağ", "Baklan", "Bekilli", "ağaçıran", "Beyağaç", "Bozkurt", "Buldan", "Çal", "Çameli", "Çardak", "Çivril", "Güney", "Honaz", "Kale", "Merkezefendi", "Pamukkale", "Sarayköy", "Serinhisar", "Tavas",
"Diyarbakır", "Bağlar", "Bismil", "Çermik", "Çınar", "Çüngüş", "Dicle", "Eğil", "Ergani", "Hani", "Hazro", "Kayapınar", "Kocaköy", "Kulp", "Lice", "Silvan", "Sur", "Yenişehir",
"Düzce", "Akçakoca", "Cumayeri", "Çilimli", "Gümüşova", "Kaynaşlı", "Merkez", "Yığılca",
"Edirne", "Enez", "Havsa", "İpsala", "Keşan", "Lüleburgaz", "Meriç", "Merkez", "Süloğlu", "Uzunköprü",
"Elazığ", "Ağın", "Alacakaya", "Arıcak", "Baskil", "Karakoçan", "Keban", "Kovancılar", "Maden", "Merkez", "Palu", "Sivrice",
"Erzincan", "Çayırlı", " İliç", "Kemah", "Kemaliye", "Merkez", "Otlukbeli", "Refahiye", "Tercan", "Üzümlü",
"Erzurum", "Aşkale", "Aziziye", "Çat", "Hınıs", "Horasan", "İspir", "Karaçoban", "Karayazı", "Köprüköy", "Narman", "Oltu", "Olur", "Palandöken", "Pasinler", "Pazaryolu", "Şenkaya", "Tekman", "Tortum", "Uzundere", "Yakutiye",
"Eskişehir", "Alpu", "Beylikova", "Çifteler", "Günyüzü", "Han", "İnönü", "Mahmudiye", "Mihalgazi", "Mihalıççık", "Odunpazarı", "Sarıgöz", "Seyitgazi", "Sivrihisar", "Tepebaşı",
"Gaziantep", "Araban", "İslahiye", "Karkamış", "Nizip", "Nurdağı", "Oğuzeli", "Şahinbey", "Şehitkamil", "Yavuzeli",
"Giresun", "Alucra", "Bulancak", "Çamoluk", "Çanakçı", "Dereli", "Doğankent", "Espiye", "Eynesil", "Görele", "Güce", "Keşap", "Merkez", "Piraziz", "Şebinkarahisar", "Tirebolu", "Yağlıdere",
"Gümüşhane", "Kelkit", "Köse", "Kürtün", "Merkez", "Şiran", "Torul",
"Hakkari", "Çukurca", "Merkez", "Şemdinli", "Yüksekova",
"Hatay", "Altınözü", "Antakya", "Arsuz", "Belen", "Defne", "Dörtyol", "Erzin", "Hassa", "İskenderun", "Kırıkhan", "Kumlu", "Reyhanlı", "Samandağ", "Yayladağı",
"Iğdır", "Aralık", "Karakoyunlu", "Merkez", "Tuzluca",
"Isparta", "Aksu", "Atabey", "Eğirdir", "Gelendost", "Gönen", "Keçiborlu", "Merkez", "Senirkent", "Sütçüler", "Şarkikaraağaç", "Uluborlu", "Yalvaç", "Yenişarbademli",
"İstanbul", "Adalar", "Arnavutköy", "Ataşehir", "Avcılar", "Bağcılar", "Bahçelievler", "Bakırköy", "Başakşehir", "Bayrampaşa", "Beşiktaş", "Beykoz", "Beylikdüzü", "Beyoğlu", "Büyükçekmece", "Çatalca", "Çekmeköy", "Esenler", "Esenyurt", "Eyüpsultan", "Fatih", "Gaziosmanpaşa", "Güngören", "Kadıköy", "Kağıthane", "Kartal", "Küçükçekmece", "Maltepe", "Pendik", "Sancaktepe", "Sarıyer", "Silivri", "Sultanbeyli", "Sultangazi", "Şile", "Şişli", "Tuzla", "Ümraniye", "Üsküdar", "Zeytinburnu",
"İzmir", "Aliağa", "Balçova", "Bayındır", "Bayraklı", "Bergama", "Beydağ", "Bornova", "Buca", "Çeşme", "Çiğli", "Dikili", "Foça", "Gaziemir", "Güzelbahçe", "Karabağlar", "Karaburun", "Karşıyaka", "Kemalpaşa", "Kınık", "Kiraz", "Konak", "Menderes", "Menemen", "Narlıdere", "Ödemiş", "Seferihisar", "Selçuk", "Tire", "Torbalı", "Urla",
"Kahramanmaraş", "Afşin", "Andırın", "Çağlayancerit", "Dulkadiroğlu", "Ekinözü", "Elbistan", "Göksun", "Nurhak", "Onikişubat", "Pazarcık", "Türkoğlu",
"Karabük", "Eflani", "Eskipazar", "Merkez", "Ovacık", "Safranbolu", "Yenice",
"Karaman", "Ayrancı", "Başyayla", "Ermenek", "Kazımkarabekir", "Merkez", "Sarıveliler",
"Kars", "Akyaka", "Arpaçay", "Digor", "Kağızman", "Merkez", "Sarıkamış", "Selim", "Susuz",
"Kastamonu", "Abana", "Ağlı", "Araç", "Azdavay", "Bozkurt", "Cide", "Çatalzeytin", "Daday", "Devrekani", "Doğanyurt", "Hanönü", "İhsangazi", "İnebolu", "Küre", "Merkez", "Pınarbaşı", "Seydiler", "Şenpazar", "Taşköprü", "Tosya",
"Kayseri", "Akkışla", "Bünyan", "Develi", "Fecirli", "Hacılar", "İncesu", "Kocasinan", "Melikgazi", "Pınarbaşı", "Sarıoğlan", "Sarız", "Talas", "Tomarza", "Yahyalı", "Yeşilhisar",
"Kırıkkale", "Bahşılı", "Balışeyh", "Çelebi", "Delice", "Karakeçili", "Keskin", "Merkez", "Sulakyurt", "Yahşihan",
"Kırklareli", "Babaeski", "Demirköy", "Kofçaz", "Lüleburgaz", "Merkez", "Pehlivanköy", "Pınarhisar", "Vize",
"Kırşehir", "Akpınar", "Akçakent", "Boztepe", "Çiçekdağı", "Kaman", "Merkez", "Mucur",
"Kilis", "Elbeyli", "Merkez", "Musabeyli", "Polateli",
"Kocaeli", "Başiskele", "Çayırova", "Darıca", "Derince", "Dilovası", "Gebze", "Gölcük", "İzmit", "Kandıra", "Karamürsel", "Kartepe", "Körfez",
"Konya", "Ahırlı", "Akören", "Akşehir", "Altınekin", "Beyşehir", "Bozkır", "Cihanbeyli", "Çeltik", "Çumra", "Derbent", "Derebucak", "Doğanhisar", "Emirgazi", "Ereğli", "Güneysınır", "Hadim", "Halkapınar", "Hüyük", "Ilgın", "Kadınhanı", "Karapınar", "Karatay", "Kulu", "Meram", "Sarayönü", "Selçuklu", "Seydişehir", "Taşkent", "Tuzlukçu", "Yalıhüyük", "Yunak",
"Kütahya", "Altıntaş", "Aslanapa", "Çavdarhisar", "Domaniç", "Dumlupınar", "Emet", "Gediz", "Hisarcık", "Merkez", "Pazarlar", "Simav", "Şaphane", "Tavşanlı",
"Malatya", "Akçadağ", "Arapgir", "Arguvan", "Battalgazi", "Darende", "Doğanşehir", "Doğanyol", "Hekimhan", "Kale", "Kuluncak", "Pütürge", "Yazıhan", "Yeşilyurt",
"Manisa", "Ahmetli", "Akhisar", "Alaşehir", "Demirci", "Gölmarmara", "Gördes", "Kırkağaç", "Köprübaşı", "Kula", "Salihli", "Sarıgöl", "Saruhanlı", "Selendi", "Soma", "Şehzadeler", "Turgutlu", "Yunusemre",
"Mardin", "Artuklu", "Dargeçit", "Derik", "Kızıltepe", "Mazıdağı", "Midyat", "Nusaybin", "Ömerli", "Savur", "Yeşirli",
"Mersin", "Akdeniz", "Anamur", "Aydıncık", "Bozyazı", "Çamlıyayla", "Erdemli", "Gülnar", "Mezitli", "Silifke", "Tarsus", "Toroslar", "Yenişehir",
"Muğla", "Bodrum", "Dalaman", "Datça", "Fethiye", "Kavaklıdere", "Köyceğiz", "Marmaris", "Menteşe", "Milas", "Ortaca", "Seydikemer", "Ula", "Yatağan",
"Muş", "Bulanık", "Hasköy", "Korkut", "Malazgirt", "Merkez", "Varto",
"Nevşehir", "Acıgöl", "Avanos", "Derinkuyu", "Gülşehir", "Hacıbektaş", "Kozaklı", "Merkez", "Ürgüp",
"Niğde", "Altunhisar", "Bor", "Çamardı", "Çiftlik", "Merkez", "Ulukışla",
"Ordu", "Akkuş", "Altınordu", "Aybastı", "Çamaş", "Çatalpınar", "Çaybaşı", "Fatsa", "Gölköy", "Gülyalı", "Gürgentepe", "İkizce", "Kabadüz", "Kabataş", "Korgan", "Kumru", "Mesudiye", "Perşembe", "Ulubey", "Ünye",
"Osmaniye", "Bahçe", "Düziçi", "Hasanbeyli", "Kadirli", "Merkez", "Sumbas", "Toprakkale",
"Rize", "Ardeşen", "Çamlıhemşin", "Çayeli", "Derepazarı", "Fındıklı", "Güneysu", "Hemşin", "İkizdere", "İyidere", "Kalkandere", "Merkez", "Pazar",
"Sakarya", "Akyazı", "Arifiye", "Erenler", "Ferizli", "Geyve", "Hendek", "Karapürçek", "Karasu", "Kaynarca", "Kocaali", "Pamukova", "Sapanca", "Serdivan", "Söğütlü", "Taraklı",
"Samsun", "Alaçam", "Asarcık", "Atakum", "Ayvacık", "Bafra", "Canik", "Çarşamba", "Havza", "İlkadım", "Kavak", "Ladik", "Ondokuzmayıs", "Salıpazarı", "Tekkeköy", "Terme", "Vezirköprü", "Yakakent",
"Siirt", "Baykan", "Eruh", "Kurtalan", "Merkez", "Pervari", "Şirvan", "Tillo",
"Sinop", "Ayancık", "Boyabat", "Dikmen", "Durağan", "Erfelek", "Gerze", "Merkez", "Saraydüzü", "Türkeli",
"Sivas", "Akıncılar", "Altınyayla", "Divriği", "Doğanşar", "Gemerek", "Gürün", "Hafik", "İmranlı", "Kangal", "Koyulhisar", "Merkez", "Suşehri", "Şarkışla", "Ulaş", "Yıldızeli", "Zara",
"Şanlıurfa", "Akçakale", "Birecik", "Bozova", "Ceylanpınar", "Eyyübiye", "Halfeti", "Haliliye", "Harran", "Hilvan", "Karaköprü", "Siverek", "Suruç", "Viranşehir",
"Şırnak", "Beytüşşebap", "Cizre", "Güçlükonak", "İdil", "Merkez", "Silopi", "Uludere",
"Tekirdağ", "Çerkezköy", "Çorlu", "Ergene", "Hayrabolu", "Kapaklı", "Malkara", "Marmaraereğlisi", "Muratlı", "Saray", "Süleymanpaşa", "Şarköy",
"Tokat", "Almus", "Artova", "Başçiftlik", "Erbaa", "Merkez", "Niksar", "Pazar", "Reşadiye", "Sulusaray", "Turhal", "Yeşilyurt", "Zile",
"Trabzon", "Akçaabat", "Araklı", "Arsin", "Beşikdüzü", "Çarşıbaşı", "Çaykara", "Dernekpazarı", "Düzköy", "Hayrat", "Köprübaşı", "Maçka", "Of", "Ortahisar", "Sürmene", "Şalpazarı", "Tonya", "Vakfıkebir", "Yomra",
"Tunceli", "Çemişgezek", "Hozat", "Mazgirt", "Merkez", "Nazımiye", "Ovacık", "Pertek", "Pülümür",
"UŞAK", "Banaz", "Eşme", "Karahallı", "Merkez", "Sivaslı", "Ulubey",
"Van", "Bahçesaray", "Başkale", "Çaldıran", "Çatak", "Edremit", "Erciş", "Gevaş", "Gürpınar", "İpekyolu", "Muradiye", "Özalp", "Saray", "Tuşba",
"Yalova", "Altınova", "Armutlu", "Çınarcık", "Çiftlikköy", "Merkez", "Termal",
"Yozgat", "Akdağmadeni", "Aydıncık", "Boğazlıyan", "Çandır", "Çayıralan", "Çekerek", "Kadışehri", "Merkez", "Saraykent", "Sarıkaya", "Sorgun", "Şefaatli", "Yenifakılı", "Yerköy",
"Zonguldak", "Alaplı", "Çaycuma", "Devrek", "Gökçebey", "Karadeniz Ereğli",
]

def build_question(fact, category: str, difficulty: str) -> dict | None:
    if not fact.value or len(fact.value) < 2:
        return None
    question_text = f"{fact.subject} ile ilgili: {fact.predicate}?"
    correct = fact.value
    distractors = generate_distractors(correct, CATEGORY_POOL, 3)
    if len(set(distractors)) < 3:
        return None
    return {
        "id": f"gen-{random.randint(100000, 999999)}",
        "hash": question_hash(question_text, correct),
        "category": category,
        "difficulty": difficulty,
        "question": question_text,
        "correctAnswer": correct,
        "distractors": distractors,
    }


def main() -> int:
    seed = random.randint(1, 100000)
    titles = fetch_raw_titles(seed) + SEED_TOPICS
    generated: list[dict] = []
    for title in titles[:30]:
        raw = fetch_article(title)
        text = clean_text(raw)
        if not text:
            continue
        category = classify_topic(text)
        facts = extract_facts(text, subject=title)
        for fact in facts:
            difficulty = estimate_difficulty(fact)
            q = build_question(fact, category, difficulty)
            if q:
                generated.append(q)
    unique = filter_unique(generated)
    existing = load_existing(OUTPUT)
    merged = merge(existing, unique)
    export(OUTPUT, merged)
    print(f"Generated {len(unique)} new questions. Total: {len(merged)}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
