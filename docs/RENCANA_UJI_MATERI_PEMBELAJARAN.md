# Rencana Pengujian 2 — Materi Pembelajaran BINUSMAYA

**ID dokumen:** TP-MATERI-02  
**Status:** Rencana pengujian; bukan laporan hasil eksekusi  
**Versi:** 1.0  
**Pemilik/penguji:** Diisi oleh tim proyek  
**Tanggal pelaksanaan:** Diisi saat pengujian

Struktur dokumen ini mengikuti tahapan *Test Plan* dari School of Information Systems BINUS: Overview, Bounds, Quality Risks, Proposed Schedule for Milestone, Transitions, Test Configurations & Environments, Test System Development, Test Execution, Risks and Contingencies, Change History, Referenced Documents, dan FAQ.[1]

## 1. Overview (Gambaran Umum)

Tujuan pengujian adalah memastikan Selenium dapat membuka halaman sesi mata kuliah **dari salah satu kartu jadwal yang terlihat**, menemukan baris **Video Conference**, menekan area utama materi yang **tepat berada di bawahnya**, menunggu 10 detik setelah klik, lalu menyimpan screenshot halaman yang dibuka. Dashboard lokal FastAPI menampilkan progres dan hasil. Ini adalah pemeriksaan alur UI dan bukti akses materi, **bukan** pemeriksaan bahwa seluruh isi slide benar atau setiap slide telah dimuat sempurna.

Pengujian ini berkaitan dengan rencana jadwal (TP-JADWAL-01) karena kelas dibuka melalui halaman Schedule, bukan melalui tautan materi langsung. Kartu yang cocok dengan preferensi mata kuliah/seksi/sesi dipilih lebih dulu; bila tidak ditemukan, implementasi memilih kartu terisi pertama. Apabila sesi terpilih tidak memiliki baris Video Conference dan materi sesudahnya, pemeriksaan materi gagal.

## 2. Bounds (Batasan)

### 2.1 Scope (Ruang Lingkup)

| IS — diuji | IS NOT — tidak diuji |
|---|---|
| Navigasi dari kartu kelas pada Schedule ke halaman sesi mata kuliah pada host BINUS yang dikenali. | Login otomatis/SSO/MFA atau pemilihan semua mata kuliah dan semua sesi. |
| Penemuan baris Video Conference dan area buka materi pada baris **berikutnya**. | Menekan Video Conference, Attendance, Download, Report, Assessment, atau Submit. |
| Klik area utama materi, perpindahan ke tab baru jika muncul, jeda 10 detik, dan penyimpanan `materials.png`. | Validasi isi setiap slide, durasi pemuatan sebenarnya, nilai akademik, dan pengunduhan file. |
| Status **passed** hanya jika klik tidak gagal dan screenshot aman berhasil disimpan. | Jaminan bahwa membuka artikel tidak tercatat sebagai aktivitas pada server BINUSMAYA. |

### 2.2 Definitions (Definisi)

- **Baris acuan:** elemen daftar sesi yang menampilkan label tepat `Video Conference`.
- **Materi pertama di bawahnya:** item daftar tepat setelah baris acuan, bukan tombol Download atau Report di sisi item.
- **Area buka materi:** elemen interaktif utama pada item tersebut (`div[id^='id_offline_'].pointer` dalam markup yang diamati).
- **Halaman artikel:** rute HTTPS LMS yang dikenal, misalnya `/lms/view-article/…`; ID artikel bersifat berubah-ubah dan tidak dicatat dalam rencana ini.
- **Bukti aman:** screenshot halaman yang dikenali oleh runner dan tidak menampilkan input sandi pada dokumen utama; pemeriksaan ini tidak menganalisis setiap piksel atau seluruh iframe.

### 2.3 Setting (Lokasi/Tempat)

Penguji menjalankan dashboard di `http://127.0.0.1:8000/`. Selenium menggunakan profil Chrome khusus, memasuki LMS melalui BINUSMAYA, membuka Schedule, menekan kartu kelas, lalu membuka satu artikel dari daftar aktivitas sesi. Status dan bukti disimpan lokal.

```text
Penguji → Dashboard FastAPI lokal → Selenium/Chrome khusus
                                     → BINUSMAYA → LMS → Schedule
                                     → Kartu kelas → Sesi mata kuliah
                                     → Video Conference → Item berikutnya
                                     → Tab/halaman artikel → screenshot
                    data/runs/<run-id>/result.json dan materials.png
```

## 3. Quality Risks (Risiko Kualitas)

Analisis ini kualitatif, **bukan** FMEA dengan skor formal.

| Risiko | Dampak pada kesimpulan | Pengendalian/mitigasi |
|---|---|---|
| Baris materi berpindah atau label Video Conference berubah. | Skrip gagal menemukan target atau memilih item yang salah. | Batasi pencarian pada `#thingstodocontainer .activity-item-lms`, cocokkan label Video Conference, dan pilih hanya item sesudahnya. |
| Kartu terpilih berbeda dari mata kuliah yang diharapkan. | Sesi tidak punya materi target; gagal walaupun materi ada pada kelas lain. | Catat preferensi dan perilaku fallback; tinjau kartu yang terbuka jika gagal. |
| Klik tanpa screenshot atau screenshot halaman salah. | Lulus palsu. | Status lulus mensyaratkan tangkapan layar berhasil; hanya rute LMS yang dikenali diizinkan untuk halaman artikel. |
| Slide dimuat lambat atau iframe meminta login eksternal. | Screenshot belum menunjukkan slide walau file berhasil disimpan. | Tunggu 10 detik setelah berpindah tab, tinjau screenshot secara manual, klasifikasikan bila konten belum siap. |
| Bukti mengandung informasi pribadi. | Risiko privasi saat hasil dibagikan. | Simpan lokal, batasi akses folder `data/`, dan samarkan bukti sebelum dibagikan. |

## 4. Proposed Schedule for Milestone (Rencana Tahapan)

Target ini relatif terhadap siklus pengujian; tanggal resmi ditetapkan pemilik proyek.

| Tahap | Keluaran | Penanggung jawab | Target |
|---|---|---|---|
| Persiapan | Akun, profil Chrome, sesi kelas dengan Video Conference dan materi setelahnya tersedia. | Penguji | Sebelum eksekusi |
| Eksekusi | TC-MP-01 berjalan; progres, status, dan screenshot disimpan. | Penguji | Saat siklus uji |
| Penelaahan | Screenshot diperiksa untuk memastikan halaman artikel yang sesuai benar-benar terlihat. | Penguji/reviewer | Setelah eksekusi |
| Tindak lanjut | Kegagalan diklasifikasi dan diuji ulang jika locator, sesi, atau jaringan berubah. | Pengembang dashboard/penguji | Setelah penelaahan |

## 5. Transitions (Kriteria Peralihan)

### 5.1 Entry Criteria

Server dashboard aktif; Chrome, Selenium, dan jaringan tersedia; profil Chrome khusus telah login; akun berwenang melihat kelas dan membuka materi; ada kartu kelas terisi yang dapat diklik. Untuk pengujian positif, kelas terpilih harus memiliki Video Conference yang diikuti item materi yang dapat dibuka. Tidak ada run lain pada profil yang sama.

### 5.2 Continuation Criteria

Halaman sesi menampilkan judul mata kuliah pada host LMS yang dikenali; daftar aktivitas terisi; area buka pada item tepat setelah Video Conference terlihat. Setelah klik, jika muncul tab baru, Selenium harus berpindah ke tab itu **sebelum** menunggu 10 detik. Jika login kedaluwarsa atau target tidak ada, jangan menganggapnya keberhasilan.

### 5.3 Exit Criteria

Langkah Materi **passed** hanya bila klik area materi tidak gagal, jeda 10 detik telah selesai, dan `materials.png` berhasil disimpan dari halaman yang diizinkan. Bila tidak, status **failed** dengan pesan penyebab yang tersedia. Penguji harus memeriksa screenshot secara manual: implementasi saat ini **tidak** menilai secara otomatis apakah teks/isi setiap slide tampil benar. Status run keseluruhan **passed** mensyaratkan langkah Schedule **dan** Materi sama-sama passed.

## 6. Test Configurations & Environments (Konfigurasi dan Lingkungan)

| Komponen | Konfigurasi yang dipakai |
|---|---|
| Komputer | Windows dengan Git Bash; spesifikasi perangkat keras minimum belum ditentukan. |
| Server | Python virtual environment, FastAPI/Uvicorn pada `127.0.0.1:8000`; dependensi pada `requirements.txt`. |
| Browser | Chrome + Selenium WebDriver/ChromeDriver; profil khusus di `data/chrome-profile`. |
| Sistem target | BINUSMAYA dan `lms.binus.ac.id` melalui HTTPS, dengan akun milik penguji yang berwenang. |
| Preferensi target | `MAYA_COURSE_TITLE`, `MAYA_SECTION`, `MAYA_SESSION`; bila kartu preferensi tidak tampil, runner memakai kartu terisi pertama. |
| Bukti | `data/runs/<run-id>/materials.png` dan `result.json`; hanya tersedia lokal. |

## 7. Test System Development (Pengembangan Sistem Uji)

- `maya_dashboard/runner.py` (`open_materials_from_schedule`): memilih kartu terisi, mengkliknya, menunggu judul kelas, dan memeriksa host resmi.
- `maya_dashboard/runner.py` (`first_material_after_video_conference`): menemukan baris acuan dan area buka pada baris sesudahnya tanpa menekan Download/Report.
- `maya_dashboard/runner.py` (`run_maya`, `_capture`): mengklik, beralih ke tab baru jika ada, menunggu 10 detik, menerima halaman sesi/artikel resmi yang dikenal, dan menyimpan screenshot bila aman.
- `maya_dashboard/service.py`, `maya_dashboard/app.py`, dan `static/app.js`: status run, riwayat, progres, serta tautan bukti lokal.
- `tests/test_navigation.py` dan `tests/test_runner.py`: pengujian logika dengan browser tiruan, **bukan** bukti bahwa situs langsung akan selalu berhasil.

## 8. Test Execution (Pelaksanaan Pengujian)

### 8.1 Key Participants (Peserta Utama)

| Peran | Tanggung jawab |
|---|---|
| Penguji/pemilik akun (nama diisi saat pelaksanaan) | Menyiapkan sesi sah, menjalankan tes, dan menilai screenshot. |
| Pengembang dashboard (nama diisi saat pelaksanaan) | Memperbaiki locator/navigasi serta menjalankan pengujian regresi lokal. |
| Reviewer hasil (jika ditetapkan) | Memastikan bukti sesuai target tanpa menyebarkan data pribadi. |
| Pengelola BINUSMAYA (eksternal; kontak tidak ditetapkan) | Dihubungi melalui kanal resmi hanya jika masalah sistem target telah dipisahkan dari masalah skrip. |

### 8.2 Test Case dan Bug Tracking

| ID | Prosedur | Hasil yang diharapkan |
|---|---|---|
| TC-MP-01 | Dari dashboard pilih Start tests; setelah Schedule terbuka, klik kartu kelas; cari Video Conference; klik area utama item berikutnya; pindah tab bila perlu; tunggu 10 detik. | `materials.png` tersimpan dan langkah Materi **passed**; reviewer dapat melihat halaman artikel/slides yang sesuai. |
| TC-MP-02 | Gunakan sesi yang tidak memiliki Video Conference atau item buka sesudahnya. | Langkah Materi **failed**, tanpa klik Download/Report atau materi lain. |
| TC-MP-03 | Simulasikan halaman target di luar rute resmi yang diizinkan atau screenshot gagal dibuat. | Langkah Materi **failed**; tidak mengklaim bukti yang tidak tersedia. |

Hasil setiap eksekusi tersimpan menurut `run-id` dalam `data/runs/<run-id>/result.json`. Rekam temuan pada issue tracker yang dipilih tim (belum ditentukan), sertakan ID kasus/run, kondisi prasyarat, langkah reproduksi, hasil aktual/harapan, klasifikasi, serta bukti yang telah disamarkan. Riwayat dashboard bukan pengganti issue tracker.

### 8.3 Bug Isolation and Classification

- **Requirements Failure:** halaman materi yang seharusnya dapat diakses tidak bisa dibuka pada sesi dan akun yang valid.
- **Nonrequirement Failure:** masalah presentasi visual di luar kriteria klik dan screenshot yang memengaruhi kegunaan.
- **Waiver Requested:** permintaan pengecualian yang harus disetujui pemilik proyek; tidak mengubah hasil secara otomatis.
- **External Failure:** sesi kedaluwarsa, jaringan terputus, layanan LMS/penampil slide eksternal terganggu.
- **Test Failure:** selector baris tidak sesuai DOM, tab yang salah diambil, atau aturan keamanan screenshot menolak halaman artikel yang sebenarnya sah.

Periksa progres terakhir, hasil `result.json`, dan bukti sebelum menyimpulkan kegagalan situs; status failed dapat berasal dari alat uji.

### 8.4 Test Release Management

Setiap perubahan alur/selector/syarat bukti di runner dicatat pada versi kode yang diuji. Jalankan unit test setelah revisi, lalu run langsung pada akun yang berwenang. Jangan menganggap bukti dari versi lama mewakili implementasi baru.

### 8.5 Test Cycles

Siklus minimal: jalankan pengujian lokal (`.venv/Scripts/python.exe -m unittest discover -s tests -v`), jalankan satu run dashboard, cek TC-MP-01 dan screenshot, klasifikasikan bila gagal, lalu uji ulang setelah perbaikan. Aplikasi menolak run paralel pada profil Chrome yang sama.

## 9. Risks and Contingencies (Risiko Pelaksanaan dan Kontingensi)

Jika kelas pilihan tidak memiliki Video Conference dan materi sesudahnya, pilih data/sesi lain secara sah untuk siklus berikutnya dan catat perubahan target; jangan mengubah konten BINUSMAYA. Jika penampil materi mengarah ke halaman luar atau meminta login ulang, jangan melonggarkan aturan screenshot tanpa penilaian privasi; lakukan pemeriksaan manual yang aman. Jika 10 detik belum cukup untuk memuat slide, catat keterbatasan bukti dan pertimbangkan kriteria siap-muat yang terukur pada revisi berikutnya. Screenshot tidak boleh dibagikan tanpa menutupi identitas pribadi.

## 10. Change History (Riwayat Perubahan)

| Versi | Perubahan | Tanggal |
|---|---|---|
| 1.0 | Dokumen awal untuk klik materi tepat setelah Video Conference dan bukti setelah 10 detik. | Diisi saat disahkan |

## 11. Referenced Documents (Dokumen Rujukan)

- Artikel *Test Plan* dari School of Information Systems BINUS sebagai acuan struktur dokumen.[1]
- `docs/RENCANA_UJI_JADWAL_KELAS.md`, `README.md`, `maya_dashboard/runner.py`, `maya_dashboard/service.py`, `maya_dashboard/app.py`, dan pengujian pada folder `tests/`.

## 12. FAQ

**Apakah passed membuktikan semua slide benar?** Tidak. Passed membuktikan alur klik dan tersimpannya screenshot; isi slide tetap perlu diperiksa oleh penguji.

**Tombol mana yang ditekan?** Area utama item pertama tepat sesudah Video Conference, bukan kontrol Download atau Report.

**Mengapa bisa gagal padahal slide terbuka?** Jika screenshot tidak aman/tidak tersimpan, kriteria bukti gagal. Tinjau URL halaman secara aman, pesan langkah, dan bukti run; jangan membagikan URL bertoken.

**Mengapa materi yang dibuka bukan kelas preferensi?** Runner menggunakan kartu terisi pertama bila kartu preferensi tidak terlihat pada jadwal yang tampil.

## Sources

[1] https://sis.binus.ac.id/2018/07/29/test-plan-2 — Test Plan - School of Information Systems BINUS
