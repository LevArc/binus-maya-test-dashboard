# Rencana Pengujian 1 — Jadwal Kelas BINUSMAYA

**ID dokumen:** TP-JADWAL-01  
**Status:** Rencana pengujian; bukan laporan hasil eksekusi  
**Versi:** 1.0  
**Pemilik/penguji:** Diisi oleh tim proyek  
**Tanggal pelaksanaan:** Diisi saat pengujian

Struktur dokumen ini mengikuti tahapan *Test Plan* dari School of Information Systems BINUS: Overview, Bounds, Quality Risks, Proposed Schedule for Milestone, Transitions, Test Configurations & Environments, Test System Development, Test Execution, Risks and Contingencies, Change History, Referenced Documents, dan FAQ.[1]

## 1. Overview (Gambaran Umum)

Tujuan pengujian adalah memastikan pengguna dengan sesi BINUSMAYA yang sudah aktif dapat membuka **My Schedule** melalui peluncur LMS dan menu Schedule, serta melihat kalender dan minimal satu kartu kelas yang telah selesai dimuat. Pengujian dilakukan dengan Selenium yang dikendalikan oleh dashboard lokal FastAPI. Pengujian ini memeriksa antarmuka dan alur navigasi (*end-to-end UI check*), bukan unit test milik server BINUSMAYA. Unit test lokal menggunakan WebDriver tiruan untuk memverifikasi logika dashboard; hasilnya tidak membuktikan situs langsung berhasil.

Objek uji: peluncur LMS, menu Schedule, judul **My Schedule**, kalender, dan kartu kelas. Output yang diharapkan: status langkah **passed/failed**, jumlah kartu, durasi, cuplikan label aman, dan tangkapan layar lokal bila halaman memenuhi aturan pengambilan bukti.

## 2. Bounds (Batasan)

### 2.1 Scope (Ruang Lingkup)

| IS — diuji | IS NOT — tidak diuji |
|---|---|
| Akses dari halaman utama BINUSMAYA menuju LMS dan menu Schedule. | Proses login otomatis, SSO, atau MFA. |
| Keberadaan judul My Schedule, kalender, dan kartu kelas berisi judul/kelas yang nyata. | Kebenaran akademik setiap tanggal, dosen, ruangan, atau perubahan jadwal di basis data. |
| Penolakan kartu *placeholder* yang belum berisi nama kelas. | Mengubah jadwal, mengirim ke Outlook, atau membuka tautan kelas lain. |
| Status, jumlah kartu, durasi, dan bukti lokal dari satu siklus uji. | Pengujian beban, keamanan menyeluruh, dan semua bulan/akun. |

### 2.2 Definitions (Definisi)

- **Kartu kelas terisi:** elemen jadwal dengan teks `.schedule-title` dan `.schedule-desc` yang tidak kosong.
- **Placeholder:** kerangka antarmuka saat data masih dimuat; tidak dihitung sebagai kartu kelas berhasil.
- **Sesi tersimpan:** keadaan login pada profil Chrome Selenium terpisah di `data/chrome-profile`, bukan profil Chrome pribadi.
- **Bukti:** `schedule.png` dan metadata langkah dalam `result.json` pada satu folder run. Tangkapan layar bersifat sensitif.

### 2.3 Setting (Lokasi/Tempat)

Pengujian dipicu pada dashboard `http://127.0.0.1:8000/` di komputer penguji. Selenium membuka Chrome dengan profil khusus, menavigasi situs BINUSMAYA/LMS melalui internet, kemudian menyimpan hasil hanya pada komputer tersebut.

```text
Penguji → Dashboard lokal (FastAPI) → Selenium/Chrome khusus
                                      → BINUSMAYA → LMS → My Schedule
                     data/runs/<run-id>/result.json dan schedule.png
```

## 3. Quality Risks (Risiko Kualitas)

Penilaian berikut bersifat kualitatif, **bukan** skor FMEA formal.

| Risiko | Dampak pada kesimpulan | Pengendalian/mitigasi |
|---|---|---|
| Kartu placeholder dihitung sebagai kelas. | Lulus palsu. | Tunggu teks kartu terisi; verifikasi judul, kalender, `.schedule-title`, dan `.schedule-desc`. |
| Perubahan DOM atau menu LMS. | Gagal walau situs berfungsi. | Periksa tahap terakhir, bukti, dan perbarui locator sebelum menjalankan ulang. |
| Profil Selenium keluar dari sesi login. | Pengujian tidak dapat dimulai. | Laporkan kegagalan sesi; login dilakukan pemilik akun secara manual pada profil khusus. |
| Tangkapan layar memuat data pribadi. | Kebocoran jika folder dibagikan. | Simpan pada disk lokal; jangan publikasikan `data/` atau hasil tanpa penyamaran. |

## 4. Proposed Schedule for Milestone (Rencana Tahapan)

Jadwal berikut relatif terhadap satu siklus, bukan tanggal yang diklaim sudah disetujui.

| Tahap | Keluaran | Penanggung jawab | Target |
|---|---|---|---|
| Persiapan | Lingkungan lokal, profil login, koneksi, dan data jadwal tersedia. | Penguji | Sebelum eksekusi |
| Eksekusi | Jalankan TC-JD-01 dan periksa bukti/status. | Penguji | Saat siklus uji |
| Evaluasi | Tinjau kegagalan, klasifikasikan penyebab, uji ulang bila perlu. | Penguji/pengembang dashboard | Setelah eksekusi |
| Serah hasil | Simpan run ID, ringkasan, dan keputusan penerimaan. | Pemilik proyek | Setelah evaluasi |

## 5. Transitions (Kriteria Peralihan)

### 5.1 Entry Criteria

Dashboard dan Chrome terpasang; server lokal hidup; internet tersedia; profil Selenium khusus sudah login; akun berwenang melihat jadwal; tidak ada run lain yang sedang berjalan. Jika bulan yang ditampilkan memang tidak memiliki kelas, kasus ini **tidak** memenuhi prasyarat positif TC-JD-01 dan harus dicatat terpisah, bukan diluluskan secara paksa.

### 5.2 Continuation Criteria

Peluncur LMS dan menu Schedule dapat diakses; halaman menampilkan konten terisi sebelum pemeriksaan. Bila sesi habis, DOM berubah, atau kelas tidak ada, hentikan penilaian positif dan catat kegagalan/ketidakmampuan melanjutkan.

### 5.3 Exit Criteria

Satu run selesai, langkah Schedule berstatus **passed** jika judul My Schedule, kalender, dan sedikitnya satu kartu terisi ditemukan; selain itu **failed**. Catat run ID dan jumlah kartu. Tangkapan layar diambil setelah jeda sekitar dua detik bila halaman dikenali; kegagalan menyimpan screenshot Schedule sendiri belum menjadi syarat kegagalan langkah pada implementasi saat ini, sehingga bukti yang kosong harus dicatat sebagai keterbatasan.

## 6. Test Configurations & Environments (Konfigurasi dan Lingkungan)

| Komponen | Konfigurasi yang dipakai |
|---|---|
| Komputer | Windows dengan Git Bash; spesifikasi CPU/RAM tidak ditetapkan oleh proyek. |
| Server lokal | Python virtual environment, FastAPI/Uvicorn pada `127.0.0.1:8000`; dependensi pada `requirements.txt`. |
| Browser | Chrome + Selenium WebDriver/ChromeDriver; profil tersimpan di `data/chrome-profile`. |
| Sistem target | Situs BINUSMAYA dan host LMS resmi melalui HTTPS; bukan lingkungan staging yang telah diverifikasi. |
| Data dan jaringan | Akun pengguna yang diizinkan, sesi yang masih aktif, jadwal kelas yang terisi, dan akses internet. |
| Keamanan | Jangan menyimpan sandi dalam kode atau mempublikasikan port dan folder bukti. |

## 7. Test System Development (Pengembangan Sistem Uji)

- `maya_dashboard/runner.py`: membuka profil Chrome, menavigasi peluncur LMS dan menu Schedule, menunggu konten, lalu merekam progres.
- `maya_dashboard/checks.py` (`inspect_schedule`): memeriksa judul, kalender, dan menghitung kartu berisi teks.
- `maya_dashboard/service.py` dan `maya_dashboard/app.py`: mengatur satu run pada satu waktu, menyimpan hasil, dan menyediakan status serta bukti pada dashboard lokal.
- `tests/test_checks.py`, `tests/test_navigation.py`, `tests/test_runner.py`, `tests/test_app.py`: pengujian lokal dengan WebDriver tiruan/API; bukan pengganti pengujian langsung terhadap BINUSMAYA.

## 8. Test Execution (Pelaksanaan Pengujian)

### 8.1 Key Participants (Peserta Utama)

| Peran | Tanggung jawab |
|---|---|
| Penguji/pemilik akun (nama diisi saat pelaksanaan) | Menjalankan server, menjaga sesi login, memicu pengujian, dan memeriksa hasil. |
| Pengembang dashboard (nama diisi saat pelaksanaan) | Memelihara locator, logika Selenium, serta unit test. |
| Pengelola BINUSMAYA (eksternal; kontak tidak ditetapkan) | Hanya dihubungi melalui jalur resmi jika ada dugaan masalah sistem target; tidak dianggap anggota tim penguji. |

### 8.2 Test Case dan Bug Tracking

| ID | Prosedur | Hasil yang diharapkan |
|---|---|---|
| TC-JD-01 | Klik **Start tests**; otomatis buka BINUSMAYA → LMS → Schedule; tunggu halaman. | My Schedule dan kalender terlihat; minimal satu kartu terisi dihitung; langkah Schedule **passed**, jumlah kartu tercatat. |
| TC-JD-02 | Jalankan ketika judul/kalender/kartu terisi tidak tersedia atau DOM berubah. | Langkah Schedule **failed**; tidak menyatakan placeholder sebagai kelas yang valid. |

Setiap eksekusi memiliki `run-id` dan `data/runs/<run-id>/result.json`; screenshot, bila tersedia, bernama `schedule.png`. Catat temuan bug secara terpisah (misalnya issue tracker tim yang dipilih nanti) dengan run ID, waktu, perilaku yang diharapkan/aktual, langkah reproduksi, klasifikasi, dan bukti yang sudah disamarkan. Dashboard menyimpan riwayat tetapi **bukan** sistem pelacakan bug lengkap.

### 8.3 Bug Isolation and Classification

- **Requirements Failure:** My Schedule yang seharusnya tersedia tidak menampilkan data wajib setelah lingkungan/prasyarat valid.
- **Nonrequirement Failure:** masalah visual atau usability di luar kriteria kasus uji ini.
- **Waiver Requested:** pengecualian yang diminta pengembang; perlu persetujuan pemilik proyek, tidak otomatis mengubah hasil.
- **External Failure:** jaringan, SSO, profil login, atau layanan BINUSMAYA tidak tersedia.
- **Test Failure:** locator/skrip Selenium salah, placeholder terbaca sebagai konten, atau bukti tangkapan layar tidak representatif.

Klasifikasi membutuhkan pemeriksaan bukti dan reproduksi; status **failed** sendiri tidak membuktikan bug pada BINUSMAYA.

### 8.4 Test Release Management

Setiap perubahan locator/runner dicatat bersama versi kode atau commit yang dipakai pada siklus berikutnya. Jalankan suite unit lokal sebelum pengujian langsung; jangan membandingkan dua run tanpa mengetahui versi kode, akun, dan keadaan jadwalnya.

### 8.5 Test Cycles

Siklus minimal: jalankan suite lokal (`.venv/Scripts/python.exe -m unittest discover -s tests -v`), lakukan satu run dashboard pada akun yang diizinkan, tinjau hasil TC-JD-01, lalu ulangi setelah perbaikan bila ada kegagalan. Jangan menjalankan dua run bersamaan pada profil Chrome yang sama.

## 9. Risks and Contingencies (Risiko Pelaksanaan dan Kontingensi)

Jika tidak ada kelas pada bulan yang terlihat, laporkan **tidak memenuhi data prasyarat** dan jadwalkan ulang dengan jadwal yang relevan; jangan mengubah data akademik. Jika login kedaluwarsa, pemilik akun memperbarui sesi secara manual pada profil Selenium. Jika situs mengubah antarmuka, hentikan klaim keberhasilan sampai locator ditinjau. Jika screenshot memuat identitas, jangan bagikan sebelum disamarkan.

## 10. Change History (Riwayat Perubahan)

| Versi | Perubahan | Tanggal |
|---|---|---|
| 1.0 | Dokumen awal untuk pengujian jadwal sesuai perilaku dashboard saat disusun. | Diisi saat disahkan |

## 11. Referenced Documents (Dokumen Rujukan)

- Artikel *Test Plan* dari School of Information Systems BINUS sebagai acuan struktur dokumen.[1]
- `README.md`, `maya_dashboard/runner.py`, `maya_dashboard/checks.py`, `maya_dashboard/service.py`, dan pengujian pada folder `tests/` dalam repositori dashboard.

## 12. FAQ

**Apakah status lulus berarti semua jadwal saya benar?** Tidak. Uji ini hanya memastikan halaman, kalender, dan minimal satu kartu kelas terisi terlihat.

**Mengapa saya sudah login di Chrome biasa, tetapi tes gagal?** Selenium memakai profil Chrome khusus yang tidak berbagi sesi dengan profil biasa.

**Apakah screenshot wajib agar langkah jadwal lulus?** Pada implementasi saat ini tidak; jika screenshot kosong, catat keterbatasan bukti dan evaluasi run.

**Di mana data pengujian tersimpan?** Di `data/runs/<run-id>/`; folder tersebut dapat berisi informasi pribadi dan dihapus manual sesuai kebijakan retensi tim.

## Sources

[1] https://sis.binus.ac.id/2018/07/29/test-plan-2 — Test Plan - School of Information Systems BINUS
