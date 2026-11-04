"""Timeline bersama video 'Sejarah Piramida'."""
W, H, FPS, DUR = 1080, 1920, 30, 50.0
SCENES = [  # (mulai, selesai, tahun, judul)
    (0, 4, "", ""),
    (4, 10, "± 2670 SM", "Piramida Berundak Djoser"),
    (10, 16, "± 2600 SM", "Eksperimen Snefru"),
    (16, 24, "± 2560 SM", "Piramida Agung Khufu"),
    (24, 30, "± 2500 SM", "Tiga Piramida Giza"),
    (30, 35, "1303 M", "Selimut Batu Putih"),
    (35, 41, "± 300 SM", "Piramida Nubia"),
    (41, 50, "Kini", "Saksi Zaman"),
]
NODES = ["2670 SM", "2600", "2560", "2500", "1303 M", "300 SM", "Kini"]
CAPS = [
    (4.6, 9.8, "Imhotep merancang Piramida Djoser di Saqqara — bangunan batu raksasa pertama.", ""),
    (10.5, 13.1, "Raja Snefru bereksperimen: Piramida Bengkok mengubah sudutnya di tengah jalan.", ""),
    (13.4, 15.8, "Piramida Merah akhirnya menjadi piramida bersisi mulus yang pertama.", ""),
    (16.5, 20.0, "Piramida Agung Khufu: ± 2,3 juta balok batu disusun selama sekitar 20 tahun.", ""),
    (20.2, 23.6, "Dikerjakan puluhan ribu pekerja terampil yang dibayar — bukan budak.", ""),
    (24.5, 29.5, "Khafre dan Menkaure menyusul, membentuk tiga piramida utama Giza.", ""),
    (30.4, 32.6, "Dulu ia berselimut batu kapur Tura putih yang berkilau.", ""),
    (32.9, 34.9, "Gempa 1303 M meruntuhkan banyak batu pelapisnya.", ""),
    (35.6, 40.4, "Di Nubia (Sudan), Kerajaan Kush membangun piramida kecil nan curam — jumlahnya lebih banyak dari di Mesir.", ""),
    (43.6, 46.5, "Piramida Giza: satu-satunya keajaiban dunia kuno yang masih berdiri.", ""),
]
INFO = [  # (mulai, selesai, teks) di bawah judul adegan
    (4.8, 9.8, "6 tingkat  •  tinggi ± 62 m"),
    (10.5, 13.2, "Piramida Bengkok: sudut 54° → 43°"),
    (13.4, 15.8, "Piramida Merah: sudut 43°, tinggi 105 m"),
    (24.5, 29.5, "Khufu 146 m  •  Khafre 144 m  •  Menkaure 65 m"),
    (30.4, 34.9, "Tinggi asli 146,6 m  →  kini ± 138,5 m"),
    (35.8, 40.4, "Lebih dari 200 piramida di Sudan"),
]
