"""Write 91-gorsel-envanteri.json + titles.json for Masallar ve Efsaneler."""

from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
CATEGORY = "Masallar ve Efsaneler"
DIFF = {
    1: "Çok Kolay",
    2: "Kolay",
    3: "Kolay-Orta",
    4: "Orta",
    5: "Orta-Zor",
    6: "Zor",
    7: "Uzman",
}
# Placeholder grid; import progression_plan replaces with Doğa-matched sizes.
GRID = {
    1: (80, 60, 14),
    2: (120, 90, 20),
    3: (160, 120, 25),
    4: (200, 150, 28),
    5: (280, 210, 35),
    6: (400, 300, 40),
    7: (800, 600, 52),
}

# order, slug, title_tr — 13 per tier; first 3 of each tier map to approved previews.
ENTRIES: list[tuple[int, str, str]] = [
    # Tier 1
    (1, "tac", "Kral Tacı"),
    (2, "sihirli-lamba", "Sihirli Lamba"),
    (3, "cam-ayakkabi", "Cam Ayakkabı"),
    (4, "buyulu-yuzuk", "Büyülü Yüzük"),
    (5, "altin-anahtar", "Altın Anahtar"),
    (6, "sihir-asasi", "Sihir Asası"),
    (7, "buyulu-ayna", "Büyülü Ayna"),
    (8, "zehirli-elma", "Zehirli Elma"),
    (9, "buyulu-kitap", "Büyülü Kitap"),
    (10, "kristal-top", "Kristal Top"),
    (11, "buyulu-kese", "Büyülü Kese"),
    (12, "peri-toz", "Peri Tozu"),
    (13, "altin-yumurta", "Altın Yumurta"),
    # Tier 2
    (14, "peri", "Peri"),
    (15, "kurbaga-prens", "Kurbağa Prens"),
    (16, "kurt", "Masal Kurdu"),
    (17, "beyaz-tavsan", "Beyaz Tavşan"),
    (18, "baykus", "Bilge Baykuş"),
    (19, "tekboynuz", "Tekboynuz"),
    (20, "cin", "Cin"),
    (21, "cuce", "Orman Cücesi"),
    (22, "kugu", "Kuğu"),
    (23, "tilki", "Masal Tilkisi"),
    (24, "anka-yavru", "Anka Yavrusu"),
    (25, "ejderha-yavru", "Ejderha Yavrusu"),
    (26, "gulyabani", "Gulyabani"),
    # Tier 3
    (27, "orman-kulubesi", "Orman Kulübesi"),
    (28, "kule", "Peri Kulesi"),
    (29, "denizkizi", "Denizkızı"),
    (30, "buyulu-kopru", "Büyülü Köprü"),
    (31, "degirmen", "Masal Değirmeni"),
    (32, "gizli-bahce", "Gizli Bahçe"),
    (33, "magara", "Gizemli Mağara"),
    (34, "buyulu-gol", "Büyülü Göl"),
    (35, "tas-kapi", "Taş Kapı"),
    (36, "orman-yolu", "Orman Yolu"),
    (37, "peri-halka", "Peri Halkası"),
    (38, "dilekkuyusu", "Dilek Kuyusu"),
    (39, "cam-kosk", "Cam Köşk"),
    # Tier 4
    (40, "ejderha", "Ejderha"),
    (41, "cadi", "Cadı"),
    (42, "savasci", "Kahraman Savaşçı"),
    (43, "prenses", "Prenses"),
    (44, "prens", "Prens"),
    (45, "buyucu", "Büyücü"),
    (46, "cizmeli-kedi", "Çizmeli Kedi"),
    (47, "pamuk-prenses", "Pamuk Prenses"),
    (48, "kirmizi-baslik", "Kırmızı Başlıklı Kız"),
    (49, "cin-cikis", "Lambadan Cin"),
    (50, "anka", "Anka Kuşu"),
    (51, "grifon", "Grifon"),
    (52, "deniz-canavari", "Deniz Canavarı"),
    # Tier 5
    (53, "buyulu-orman", "Büyülü Orman"),
    (54, "ucan-hali", "Uçan Halı"),
    (55, "peri-sarayi", "Peri Sarayı"),
    (56, "buyulu-kale", "Büyülü Kale"),
    (57, "gol-kalesi", "Göl Kalesi"),
    (58, "orman-tapinak", "Orman Tapınağı"),
    (59, "yuzer-ada", "Yüzen Ada"),
    (60, "yeralti-saray", "Yeraltı Sarayı"),
    (61, "buz-sarayi", "Buz Sarayı"),
    (62, "ates-dagi", "Ateş Dağı"),
    (63, "sisli-vadi", "Sisli Vadi"),
    (64, "kopru-kent", "Köprü Kent"),
    (65, "yildiz-kule", "Yıldız Kulesi"),
    # Tier 6
    (66, "keloglan", "Keloğlan"),
    (67, "nasreddin", "Nasreddin Hoca"),
    (68, "alibaba", "Ali Baba Mağarası"),
    (69, "dede-korkut", "Dede Korkut"),
    (70, "tepegoz", "Tepegöz"),
    (71, "asik-garip", "Âşık Garip"),
    (72, "kirk-haramiler", "Kırk Haramiler"),
    (73, "simbad", "Simbad'ın Gemisi"),
    (74, "alaaddin-saray", "Alaaddin Sarayı"),
    (75, "gul-bultul", "Gül ile Bülbül"),
    (76, "karagoz", "Karagöz"),
    (77, "yedi-basli", "Yedi Başlı Ejder"),
    (78, "dev-kule", "Dev Kulesi"),
    # Tier 7
    (79, "ejderha-savasi", "Ejderha Savaşı"),
    (80, "efsane-krallik", "Efsane Krallık"),
    (81, "binbir-gece", "Binbir Gece"),
    (82, "troya-ati", "Troya Atı"),
    (83, "anka-yuvasi", "Anka Yuvası"),
    (84, "buyulu-savas", "Büyülü Savaş"),
    (85, "efsane-liman", "Efsane Liman"),
    (86, "peri-diyari", "Peri Diyarı"),
    (87, "karanlik-kale", "Karanlık Kale"),
    (88, "altin-sehir", "Altın Şehir"),
    (89, "efsane-dag", "Efsane Dağ"),
    (90, "buyulu-ada", "Büyülü Ada"),
    (91, "son-efsane", "Son Efsane"),
]


def main() -> None:
    items = []
    titles: dict[str, str] = {}
    for order, slug, title in ENTRIES:
        tier = (order - 1) // 13 + 1
        w, h, colors = GRID[tier]
        pid = f"sample-masallar-{order:03d}"
        items.append(
            {
                "id": pid,
                "title": title,
                "category": CATEGORY,
                "file": f"{order:03d}-{slug}.png",
                "tier": tier,
                "difficulty": DIFF[tier],
                "order": order,
                "width": w,
                "height": h,
                "colors": colors,
                "slug": slug,
            }
        )
        titles[pid] = title
    assert len(items) == 91
    (OUT / "91-gorsel-envanteri.json").write_text(
        json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (OUT / "titles.json").write_text(
        json.dumps(titles, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Wrote {len(items)} inventory entries")


if __name__ == "__main__":
    main()
