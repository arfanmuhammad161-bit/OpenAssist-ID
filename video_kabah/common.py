"""Timeline bersama video 'Sejarah Ka'bah'."""
W, H, FPS, DUR = 1080, 1920, 30, 50.0
# (mulai, selesai, tahun, judul)
SCENES = [
    (0, 4, "", ""),
    (4, 10, "± 2000 SM", "Fondasi Baitullah"),
    (10, 15, "570 M", "Tahun Gajah"),
    (15, 22, "605 M", "Dibangun Ulang Quraisy"),
    (22, 27, "630 M", "Fathu Makkah"),
    (27, 33, "683 – 693 M", "Dibangun Ulang"),
    (33, 37, "930 M", "Hajar Aswad"),
    (37, 43, "1630 M", "Banjir Besar"),
    (43, 50, "Kini", "Kiblat Umat Islam"),
]
NODES = ["± 2000 SM", "570", "605", "630", "683", "930", "1630", "Kini"]
CAPS = [  # (mulai, selesai, teks, rujukan)
    (4.6, 9.8, "Nabi Ibrahim dan Ismail 'alaihimassalam meninggikan fondasi Baitullah.", "QS Al-Baqarah: 127"),
    (10.5, 14.8, "Pasukan Abrahah hendak menghancurkan Ka'bah, namun gagal.", "QS Al-Fil"),
    (15.5, 18.8, "Setelah banjir merusaknya, Quraisy membangun ulang Ka'bah hingga setinggi ±9 m.", ""),
    (19.0, 21.9, "Muhammad muda, Al-Amin, menengahi sengketa Hajar Aswad dengan sehelai kain.", ""),
    (22.6, 26.8, "Berhala dibersihkan. Ka'bah kembali menjadi pusat tauhid.", ""),
    (27.5, 30.0, "Ibnu Az-Zubair membangunnya ulang setelah terbakar, dan meninggikannya.", ""),
    (30.3, 32.9, "Al-Hajjaj kemudian mengembalikan denahnya seperti masa Quraisy.", ""),
    (33.5, 36.8, "Kaum Qaramithah merampas Hajar Aswad; ia kembali pada tahun 952 M.", ""),
    (37.5, 40.4, "Banjir besar merusak dinding Ka'bah. Sultan Murad IV membangunnya kembali.", ""),
    (40.6, 42.9, "Bentuk itulah yang kita kenal hingga kini.", ""),
    (43.5, 46.4, "Tingginya ±13 m, berselimut kiswah hitam bersulam emas.", ""),
]
