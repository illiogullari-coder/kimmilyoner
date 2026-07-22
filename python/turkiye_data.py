"""Türkiye odaklı genişletilmiş konu kataloğu.

Bu modül generate_questions.py'nin kullandığı SEED_TOPICS / WIKI_CATEGORIES
listelerini şartnamedeki geniş kapsamla (İlk Türk Devletleri, İller/İlçeler,
Coğrafya, Mutfak, Kültür, Spor, İslam, Bilim, Sanayi/Turizm, Afet/Sağlık vb.)
eşleştirecek şekilde genişletir.

Yapı bilinçli olarak "bölüm" (section) bazlıdır:
  - her bölümün bir kategori etiketi (`label`) vardır — bu, üretilen sorunun
    `category` alanına yazılır ve analyzer.classify_topic ile uyumludur.
  - `seeds`: doğrudan Wikipedia makale başlıkları (curated, kaliteli).
  - `wiki_categories`: tr.wikipedia kategori adları (categorymembers taraması
    için). Var olmayan/isabetsiz bir kategori adı hataya yol açmaz —
    source_fetcher.fetch_category_members zaten boş liste döner.

Not: Kategori adlarının bir kısmı tahmine dayalıdır (tr.wikipedia kategori
ağacı zamanla değişebilir); gerçek bir çalıştırmada boş dönenler zararsızdır,
ama zamanla `python/build.py` çıktısındaki log'a bakıp isim listesini
güncellemek isteyebilirsiniz.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TopicSection:
    label: str
    seeds: list[str] = field(default_factory=list)
    wiki_categories: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# 81 il — sabit, doğrulanmış liste (alfabetik plaka kodu sırasıyla)
# ---------------------------------------------------------------------------
IL_PLAKA_KODLARI: dict[str, str] = {
    "Adana": "01", "Adıyaman": "02", "Afyonkarahisar": "03", "Ağrı": "04",
    "Amasya": "05", "Ankara": "06", "Antalya": "07", "Artvin": "08",
    "Aydın": "09", "Balıkesir": "10", "Bilecik": "11", "Bingöl": "12",
    "Bitlis": "13", "Bolu": "14", "Burdur": "15", "Bursa": "16",
    "Çanakkale": "17", "Çankırı": "18", "Çorum": "19", "Denizli": "20",
    "Diyarbakır": "21", "Edirne": "22", "Elazığ": "23", "Erzincan": "24",
    "Erzurum": "25", "Eskişehir": "26", "Gaziantep": "27", "Giresun": "28",
    "Gümüşhane": "29", "Hakkari": "30", "Hatay": "31", "Isparta": "32",
    "Mersin": "33", "İstanbul": "34", "İzmir": "35", "Kars": "36",
    "Kastamonu": "37", "Kayseri": "38", "Kırklareli": "39", "Kırşehir": "40",
    "Kocaeli": "41", "Konya": "42", "Kütahya": "43", "Malatya": "44",
    "Manisa": "45", "Kahramanmaraş": "46", "Mardin": "47", "Muğla": "48",
    "Muş": "49", "Nevşehir": "50", "Niğde": "51", "Ordu": "52",
    "Rize": "53", "Sakarya": "54", "Samsun": "55", "Siirt": "56",
    "Sinop": "57", "Sivas": "58", "Tekirdağ": "59", "Tokat": "60",
    "Trabzon": "61", "Tunceli": "62", "Şanlıurfa": "63", "Uşak": "64",
    "Van": "65", "Yozgat": "66", "Zonguldak": "67", "Aksaray": "68",
    "Bayburt": "69", "Karaman": "70", "Kırıkkale": "71", "Batman": "72",
    "Şırnak": "73", "Bartın": "74", "Ardahan": "75", "Iğdır": "76",
    "Yalova": "77", "Karabük": "78", "Kilis": "79", "Osmaniye": "80",
    "Düzce": "81",
}


def plaka_facts() -> list[dict]:
    """81 ilin plaka kodundan üretilen, Wikipedia'ya ihtiyaç duymayan
    doğrudan-güvenilir statik soru kaynağı. category='Plaka ve Kodlar'."""
    out: list[dict] = []
    for il, kod in IL_PLAKA_KODLARI.items():
        others = [k for k in IL_PLAKA_KODLARI.values() if k != kod]
        out.append({
            "subject": il,
            "kind": "plaka",
            "question": f"{il} ilinin plaka kodu kaçtır?",
            "correct": kod,
            "distractor_pool": others,
        })
    return out


# ---------------------------------------------------------------------------
# Bölümler
# ---------------------------------------------------------------------------
SECTIONS: list[TopicSection] = [
    TopicSection(
        label="İlk Türk Devletleri",
        seeds=[
            "Büyük Hun İmparatorluğu", "Asya Hun Devleti", "Göktürkler",
            "Bilge Kağan", "Kültigin", "Uygur Kağanlığı", "Karahanlılar",
            "Gazneliler", "Büyük Selçuklu Devleti", "Tuğrul Bey", "Alparslan",
            "Malazgirt Muharebesi", "Harzemşahlar", "Karahitaylar",
        ],
        wiki_categories=["Göktürkler", "Türk_devletleri", "Selçuklular"],
    ),
    TopicSection(
        label="Osmanlı Tarihi",
        seeds=[
            "Osman Gazi", "Orhan Gazi", "I. Murad", "Yıldırım Bayezid",
            "Fatih Sultan Mehmet", "Kanuni Sultan Süleyman",
            "Yavuz Sultan Selim", "II. Abdülhamid", "Vaka-i Hayriye",
            "Tanzimat Fermanı", "Islahat Fermanı", "I. Meşrutiyet",
            "II. Meşrutiyet", "Topkapı Sarayı", "Süleymaniye Camii",
            "Mimar Sinan",
        ],
        wiki_categories=[
            "Osmanlı_padişahları", "Osmanlı_sadrazamları", "Osmanlı_tarihi",
        ],
    ),
    TopicSection(
        label="Kurtuluş Savaşı ve Cumhuriyet",
        seeds=[
            "Mustafa Kemal Atatürk", "İsmet İnönü", "Kurtuluş Savaşı",
            "Türkiye Büyük Millet Meclisi", "Çanakkale Savaşı",
            "Sakarya Meydan Muharebesi", "Büyük Taarruz",
            "Amasya Genelgesi", "Erzurum Kongresi", "Sivas Kongresi",
            "Lozan Antlaşması", "Cumhuriyet Halk Partisi", "Harf İnkılabı",
        ],
        wiki_categories=[
            "Türkiye_Cumhurbaşkanları", "Türkiye_başbakanları",
            "Türkiye_Büyük_Millet_Meclisi_başkanları",
        ],
    ),
    TopicSection(
        label="Türkiye Coğrafyası",
        seeds=[
            *list(IL_PLAKA_KODLARI.keys()),
            "Ağrı Dağı", "Erciyes Dağı", "Uludağ", "Kaçkar Dağları",
            "Toros Dağları", "Fırat Nehri", "Dicle Nehri", "Kızılırmak",
            "Sakarya Nehri (Türkiye)", "Yeşilırmak", "Atatürk Barajı",
            "Keban Barajı", "Konya Ovası", "Çukurova", "Ayder Yaylası",
            "Van Gölü", "Tuz Gölü", "Marmara Denizi", "Karadeniz",
            "Ege Denizi", "Akdeniz", "Gökçeada", "Bozcaada",
        ],
        wiki_categories=[
            "Türkiye'nin_illeri", "Türkiye'nin_ilçeleri",
            "Türkiye'deki_dağlar", "Türkiye'deki_nehirler",
            "Türkiye'deki_barajlar", "Türkiye'deki_göller",
            "Türkiye'deki_adalar",
        ],
    ),
    TopicSection(
        label="Ulaşım ve Altyapı",
        seeds=[
            "İstanbul Havalimanı", "Sabiha Gökçen Uluslararası Havalimanı",
            "Mersin Limanı", "Türkiye Cumhuriyeti Devlet Demiryolları",
            "Marmaray", "Avrasya Tüneli", "15 Temmuz Şehitler Köprüsü",
            "Yavuz Sultan Selim Köprüsü", "Osmangazi Köprüsü",
        ],
        wiki_categories=[
            "Türkiye'deki_havalimanları", "Türkiye'deki_limanlar",
            "Türkiye'deki_köprüler", "Türkiye'deki_tüneller",
        ],
    ),
    TopicSection(
        label="Doğal ve Kültürel Miras",
        seeds=[
            "Kapadokya", "Pamukkale", "Nemrut Dağı", "Efes", "Troya",
            "Göbeklitepe", "Ani Harabeleri", "Xanthos", "Safranbolu",
            "Selimiye Camii", "Hierapolis", "Aspendos Tiyatrosu",
        ],
        wiki_categories=[
            "Türkiye'deki_Dünya_Mirası_alanları", "Türkiye'deki_milli_parklar",
        ],
    ),
    TopicSection(
        label="Türk Mutfağı",
        seeds=[
            "İskender Kebap", "Adana Kebap", "Mantı", "Baklava",
            "Türk kahvesi", "Ayran", "Şalgam suyu", "Rakı", "Simit",
            "Künefe", "Lahmacun", "Gözleme", "Kısır", "Çiğ köfte", "Pide",
        ],
        wiki_categories=["Türk_mutfağı"],
    ),
    TopicSection(
        label="Türk Kültürü",
        seeds=[
            "Karagöz ve Hacivat", "Nevruz", "Hıdrellez",
            "Halay", "Zeybek (dans)", "Horon", "Türk halk müziği",
            "Âşıklık geleneği", "Nasreddin Hoca", "Dede Korkut",
        ],
        wiki_categories=["Türk_kültürü", "Türk_halk_oyunları"],
    ),
    TopicSection(
        label="Türk Edebiyatı",
        seeds=[
            "Yunus Emre", "Mevlana Celaleddin Rumi", "Nazım Hikmet",
            "Orhan Pamuk", "Yaşar Kemal", "Ahmet Hamdi Tanpınar",
            "Reşat Nuri Güntekin", "Mehmet Akif Ersoy", "Sabahattin Ali",
        ],
        wiki_categories=["Türk_şairler", "Türk_yazarlar"],
    ),
    TopicSection(
        label="Sanat, Sinema ve Müzik",
        seeds=[
            "Yeşilçam", "Muhteşem Yüzyıl", "Diriliş: Ertuğrul",
            "Sezen Aksu", "Barış Manço", "Zeki Müren", "Tarkan (şarkıcı)",
            "Devlet Tiyatroları",
        ],
        wiki_categories=[
            "Türk_sinema_oyuncuları", "Türk_televizyon_dizileri",
            "Türk_müzisyenler", "Türk_besteciler",
        ],
    ),
    TopicSection(
        label="Bilim ve Teknoloji",
        seeds=[
            "TÜBİTAK", "ASELSAN", "Baykar", "Türk Havacılık ve Uzay Sanayii",
            "TOGG", "Aziz Sancar", "Cahit Arf", "Oktay Sinanoğlu",
        ],
        wiki_categories=["Türk_bilim_insanları", "Türk_mucitler"],
    ),
    TopicSection(
        label="Spor",
        seeds=[
            "Naim Süleymanoğlu", "Hakan Şükür", "Fatih Terim",
            "Galatasaray SK", "Fenerbahçe SK", "Beşiktaş JK",
            "Türkiye Milli Futbol Takımı", "Taha Akgül", "Rıza Kayaalp",
        ],
        wiki_categories=[
            "Türk_sporcular", "Türkiye'deki_spor_kulüpleri",
        ],
    ),
    TopicSection(
        label="İslam ve Dini Konular",
        seeds=[
            "Kur'an", "Hz. Muhammed", "Ayasofya Camii", "Sultan Ahmed Camii",
            "Diyanet İşleri Başkanlığı", "Ramazan Bayramı", "Kurban Bayramı",
            "Mevlid Kandili",
        ],
        wiki_categories=["Camiler", "İslam_tarihi"],
    ),
    TopicSection(
        label="Ekonomi, Tarım ve Enerji",
        seeds=[
            "Türkiye'de tarım", "Bor (element)", "Türkiye'nin enerji politikası",
            "Türkiye turizmi",
        ],
        wiki_categories=["Türkiye_ekonomisi"],
    ),
    TopicSection(
        label="Afet ve Sağlık",
        seeds=[
            "1999 Gölcük depremi", "2023 Kahramanmaraş depremleri",
            "Afet ve Acil Durum Yönetimi Başkanlığı", "Türk Kızılayı",
        ],
        wiki_categories=["Türkiye'deki_depremler"],
    ),
]


def all_seeds() -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for sec in SECTIONS:
        for s in sec.seeds:
            if s not in seen:
                seen.add(s)
                out.append(s)
    return out


def all_categories_map() -> dict[str, str]:
    """wiki kategori adı -> bölüm etiketi (classify_topic fallback'i için)."""
    out: dict[str, str] = {}
    for sec in SECTIONS:
        for c in sec.wiki_categories:
            out[c] = sec.label
    return out
