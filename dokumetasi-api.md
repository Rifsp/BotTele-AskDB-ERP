v2.0.0 Production
Dokumentasi API
Selamat datang di Konektika Pro. Infrastruktur API Gateway berkinerja tinggi yang sepenuhnya kompatibel dengan standar OpenAI. Integrasikan model konektika-pro ke aplikasi Anda dalam hitungan detik.

Kemampuan Model: Model konektika-pro mendukung jendela konteks hingga 201k token dengan penalaran yang dioptimalkan untuk logika pemrograman.

Autentikasi
Sertakan kunci Anda dalam header HTTP Authorization sebagai Bearer token.

HTTP Header
Authorization:
Bearer <YOUR_API_KEY>
Base URL & Model Tersedia
Endpoint
https://konektikacloud.web.id/v1
Model Tersedia
konektika-pro
Wajib Dibaca

Panduan Integrasi konektika-pro
Menerima Status 400 Bad Request?
Jika Anda menerima status 400 Bad Request saat menggunakan aplikasi pihak ketiga (Zed, Cursor, OpenClaw, dsb.), pastikan request JSON Anda bersih dari parameter custom yang tidak didukung.

Parameter yang Harus Dinonaktifkan
Model konektika-pro tidak menerima parameter sampling custom. Silakan nonaktifkan atau hapus parameter berikut pada settings aplikasi Anda:

temperature
top_k
top_p
seed
Contoh Request JSON yang Benar
request_body.json
Copy
{
"model": "konektika-pro",
"messages": [
{
"role": "user",
"content": "Jelaskan konsep async/await di Python."
}
],
"stream": true
}
Cukup kirimkan model, messages, dan opsional stream. Tanpa parameter tambahan lainnya, request Anda dijamin berjalan lancar.

Penting untuk OpenClaw, OpenCode, Roo Code, Kilo Code, Cursor, dan agent sejenis

Pengaturan Context Window
Context window adalah batas seberapa banyak teks yang bisa dibawa aplikasi ke model dalam satu percakapan. Isinya bisa berupa instruksi, riwayat chat, isi file, log terminal, hasil pencarian, dan data lain yang dikirim oleh agent.

Gejala umum
Muncul pesan seperti ctx=4000, context overflow, atau prompt too large, padahal model Konektika mendukung konteks besar.

Penyebab yang sering terjadi
Aplikasi agent memakai angka bawaan kecil, misalnya 4000 atau 4096, karena belum mengenali metadata model custom secara benar.

Solusi cepat
Atur manual contextWindow dan maxTokens pada konfigurasi aplikasi yang Anda pakai.

Rekomendasi nilai aman
Untuk pemakaian harian, gunakan nilai aman terlebih dahulu. Jangan langsung memakai angka maksimum jika aplikasi Anda sering membawa banyak file atau membuka banyak request.

Aman untuk mulai
contextWindow: 64000
maxTokens: 8000
Lebih besar
contextWindow: 128000
maxTokens: 12000
Maksimum publik
contextWindow: 201000
maxTokens: 16000
openclaw.json
Contoh konfigurasi manual untuk OpenClaw

Copy
{
"providers": {
"konektika": {
"baseUrl": "https://konektikacloud.web.id/v1",
"apiKey": "YOUR_API_KEY",
"models": [
{
"id": "konektika-pro",
"name": "Konektika Pro",
"contextWindow": 64000,
"maxTokens": 8000
}
]
}
}
}
Cara cek di OpenClaw
Buka konfigurasi OpenClaw, biasanya di ~/.openclaw/openclaw.json.
Cari provider Konektika atau custom provider yang Anda buat.
Pastikan model konektika-pro punya nilai contextWindow.
Mulai dari 64000. Jika stabil, baru naikkan bertahap.
Gunakan perintah seperti /status, /context, atau /context detail jika tersedia di versi Anda.
Cara cek di OpenCode, Roo Code, Kilo Code, dan sejenisnya
Buka pengaturan model atau custom provider.
Pastikan Base URL memakai https://konektikacloud.web.id/v1.
Pastikan nama model adalah konektika-pro.
Cari kolom seperti contextWindow, context length, max input tokens, atau max tokens.
Jika ada, isi nilai aman: 64000 untuk context dan 8000 untuk output.
Catatan penting
Jika aplikasi Anda tetap menampilkan ctx=4000 setelah konfigurasi diubah, kemungkinan aplikasi belum membaca konfigurasi baru. Tutup aplikasi sepenuhnya, buka ulang, lalu cek kembali halaman status atau context. Jika masih sama, hapus konfigurasi provider lama dan buat ulang custom provider Konektika dari awal.

Khusus agent AI dan coding tools

Gunakan Internet Stabil
OpenClaw, OpenCode, Roo Code, Kilo Code, Cursor, dan agent sejenis sering membuka request secara berurutan atau paralel. Beberapa request bisa berjalan lama karena membawa isi file, log, dan riwayat percakapan. Karena itu, koneksi internet yang stabil sangat penting.

Disarankan
Gunakan internet kabel, fiber, Wi-Fi rumah/kantor yang stabil, atau jaringan yang tidak sering pindah sinyal.

Hati-hati
Jaringan seluler bisa berubah kualitasnya saat sinyal naik turun. Ini bisa membuat streaming terasa putus.

Jangan berlebihan
Jangan menaikkan jumlah proses paralel terlalu tinggi. Mulai dari 1 sampai 3 request paralel dulu.

Jika jawaban terasa sering putus
Coba ulang memakai Wi-Fi atau internet kabel.
Kurangi jumlah request paralel di aplikasi agent.
Kurangi jumlah file yang dimasukkan ke context.
Gunakan stream: true agar jawaban mengalir bertahap.
Jika masih bermasalah, kirimkan waktu kejadian, IP publik, nama model, dan screenshot error ke tim Konektika.
Bahasa sederhananya
Konektika seperti jalan tol menuju model AI. Jika aplikasi Anda mengirim banyak mobil sekaligus lewat jaringan seluler yang sinyalnya naik turun, perjalanan bisa terasa tersendat. Untuk kerja berat seperti agent AI dan coding tools, gunakan koneksi yang lebih stabil agar percakapan panjang tidak mudah terputus.

Integrasi Python
example.py
Copy
from openai import OpenAI

client = OpenAI(
api_key="YOUR_API_KEY",
base_url="https://konektikacloud.web.id/v1"
)

response = client.chat.completions.create(
model="konektika-pro",
messages=[{"role": "user", "content": "Halo!"}],
stream=True
)

for chunk in response:
print(chunk.choices[0].delta.content or "", end="")
Integrasi JavaScript / Node.js
index.js
Copy
import OpenAI from 'openai';

const openai = new OpenAI({
apiKey: 'YOUR_API_KEY',
baseURL: 'https://konektikacloud.web.id/v1'
});

async function main() {
const completion = await openai.chat.completions.create({
model: 'konektika-pro',
messages: [{ role: 'user', content: 'Halo!' }],
});

console.log(completion.choices[0].message);
}

main();
OpenClaw Integration
Peringatan Keamanan & Rekomendasi Versi
Beberapa pelanggan melaporkan kegagalan sistem saat mengonfigurasi OpenClaw melalui file JSON manual pada pembaruan terbaru (terutama versi 2026.3.2 ke atas). Berdasarkan laporan komunitas, versi-versi ini mengandung tingkat regression bug yang tinggi yang secara sepihak mengubah izin akses alat (tool permissions) menjadi nonaktif secara default.

Oleh karena itu, demi memastikan semua fitur (eksekusi terminal, modifikasi file, dan sandbox) berjalan mulus tanpa masalah, kami sangat menyarankan Anda untuk melakukan instalasi menggunakan OpenClaw versi 2026.3.13 (Stable).

Alih-alih memodifikasi file openclaw.json secara manual, ikuti langkah-langkah default berikut agar Konektika terhubung dengan aman:

Jalankan dan buka aplikasi OpenClaw Anda.
Gunakan antarmuka pengaturan bawaan dengan mengakses Wizard OpenClaw.
Pada bagian pemilihan AI Provider, pilih opsi Custom Provider (atau OpenAI-Compatible).
Masukkan Base URL secara presisi: https://konektikacloud.web.id/v1
Masukkan API Key Anda yang aktif pada isian kredensial token.
Ketikkan nama model: konektika-pro
Simpan konfigurasi tersebut. OpenClaw kini sepenuhnya siap menggunakan reasoning dari Konektika!
Jika OpenClaw tetap menampilkan ctx=4000
Buka bagian Pengaturan Context Window di halaman ini. Tambahkan nilai contextWindow dan maxTokens secara manual pada konfigurasi OpenClaw.

Gunakan nilai aman terlebih dahulu: contextWindow: 64000 dan maxTokens: 8000. Setelah stabil, Anda boleh menaikkan bertahap sesuai kebutuhan.

Chat Completions
Endpoint utama untuk mengirim pesan dan menerima respons dari model AI.

POST
/v1/chat/completions
curl -X POST https://konektikacloud.web.id/v1/chat/completions \
 -H "Content-Type: application/json" \
 -H "Authorization: Bearer YOUR_API_KEY" \
 -d '{
"model": "konektika-pro",
"messages": [
{"role": "user", "content": "Halo Konek!"}
],
"stream": true
}'
List Models
Endpoint untuk melihat daftar model yang tersedia di Konektika.

GET
/v1/models
curl https://konektikacloud.web.id/v1/models \
 -H "Authorization: Bearer YOUR_API_KEY"
