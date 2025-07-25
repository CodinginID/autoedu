from mimetypes import init
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from pymongo import MongoClient
from datastore import mongo_crud
from bson.objectid import ObjectId
from dotenv import load_dotenv
from datetime import datetime
from werkzeug.utils import secure_filename
import os

load_dotenv()


UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv'}

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = 'tkr-super-secret'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Koneksi MongoDB

dsn = f"{os.getenv('MONGO_PUBLIC_URL')}?authSource=admin"
if dsn == None:
    raise Exception("MONGO_PUBLIC_URL not found in .env file")

client = MongoClient(dsn)
db = client["tkr"]
materi_collection = db["materi"]
user_collection = db["users"]
nilai_collection = db["nilai"]
esai_collection = db["esai"]

# In-memory database dummy
materi_list = []

@app.route('/')
def index():
    return render_template('landing_page.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = user_collection.find_one({'username': username})
        if user and check_password_hash(user['password'], password):
            session['username'] = username
            flash('Berhasil login!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Username atau password salah', 'error')
            return render_template('login.html')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('Berhasil logout!', 'success')
    return redirect(url_for('index'))

@app.route('/materi/<int:materi_id>')
def materi_detail(materi_id):
    materi = materi_collection.find_one({"id": materi_id}, {"_id": 0})
    if not materi:
        return "Materi tidak ditemukan", 404

    for sub in materi.get("sub_materi", []):
        if isinstance(sub.get("konten"), dict) and sub["konten"].get("type") == "video":
            filename = sub["konten"].get("filename")
            if filename:
                sub["konten"]["filename"] = filename
    return render_template("materi_detail.html", materi=materi)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        existing_user = user_collection.find_one({'username': username})
        if existing_user:
            return render_template('register.html', error="Username sudah terdaftar")

        hashed_pw = generate_password_hash(password)
        user_collection.insert_one({'username': username, 'password': hashed_pw})
        flash("Registrasi berhasil! Silakan login.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')

# @app.route('/dashboard', methods=['GET', 'POST'])
# def dashboard():
#     if 'username' not in session:
#         return redirect(url_for('login'))

#     if request.method == 'POST':
#         judul = request.form['judul']
#         deskripsi = request.form['deskripsi']
#         # icon_url = request.form['icon_url']

#         # Upload video apersepsi
#         video_file = request.files.get('video_apersepsi')
#         video_path = None
#         if video_file and allowed_file(video_file.filename):
#             filename = secure_filename(video_file.filename)
#             video_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#             video_file.save(video_path)

        

#         sub_materi = [
#             {"judul": "Apersepsi", "konten": video_path.replace('static/', '') if video_path else ""},
#             {"judul": "KI/KD", "konten": request.form.get('sub_ki_kd', '')},
#             {"judul": "Materi", "konten": request.form.get('sub_materi', '')},
#             {"judul": "Simulasi", "konten": request.form.get('sub_simulasi', '')},
#             {"judul": "Pengayaan", "konten": request.form.get('sub_pengayaan', '')},
#         ]

#         # Ambil ID terakhir, lalu tambah 1
#         last = materi_collection.find_one(sort=[("id", -1)])
#         new_id = (last['id'] + 1) if last else 1

#         materi_collection.insert_one({
#             "id": new_id,
#             "judul": judul,
#             "deskripsi": deskripsi,
#             "sub_materi": sub_materi
#         })

#         return redirect(url_for('dashboard'))

#     # Get all materi
#     materi_list = list(materi_collection.find({}, {"_id": 0}))

#     # Cek apakah ?tambah=true di query string
#     tambah = request.args.get('tambah') == 'true'

#     return render_template("dashboard.html",
#                            username=session['username'],
#                            materi_list=materi_list,
#                            tambah=tambah)

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        tambah_materi()
        # judul = request.form.get('judul')
        # deskripsi = request.form.get('deskripsi')

        # submateri_list = []
        # index = 0
        # while True:
        #     prefix = f"submateri[{index}]"
        #     if f"{prefix}[judul]" not in request.form:
        #         break

        #     judul_sub = request.form.get(f"{prefix}[judul]")
        #     tipe = request.form.get(f"{prefix}[tipe]")

        #     sub_obj = {"judul": judul_sub, "tipe": tipe}

        #     if tipe == "text":
        #         sub_obj["konten"] = request.form.get(f"{prefix}[konten]")
        #     elif tipe == "video":
        #         video_file = request.files.get(f"{prefix}[video]")
        #         if video_file:
        #             filename = secure_filename(video_file.filename)
        #             video_path = os.path.join('static/uploads', filename)
        #             video_file.save(video_path)
        #             sub_obj["konten"] = filename
        #     elif tipe == "multi":
        #         subs = []
        #         subindex = 0
        #         while True:
        #             subjudul_key = f"{prefix}[subs][{subindex}][judul]"
        #             subkonten_key = f"{prefix}[subs][{subindex}][konten]"
        #             if subjudul_key not in request.form:
        #                 break
        #             subs.append({
        #                 "judul": request.form.get(subjudul_key),
        #                 "konten": request.form.get(subkonten_key)
        #             })
        #             subindex += 1
        #         sub_obj["konten"] = subs

        #     submateri_list.append(sub_obj)
        #     index += 1

        # # Simpan ke database
        # materi_collection.insert_one({
        #     "id": materi_collection.count_documents({}) + 1,
        #     "judul": judul,
        #     "deskripsi": deskripsi,
        #     "sub_materi": submateri_list
        # })


        return redirect(url_for('dashboard'))

    # GET method
    materi_list = list(materi_collection.find({}, {"_id": 0}))

    # Cek apakah ?tambah=true di query string
    tambah = request.args.get('tambah') == 'true'
    return render_template("dashboard.html",
                           username=session['username'],
                           materi_list=materi_list,
                           tambah=tambah)


@app.route('/materi/tambah', methods=['GET', 'POST'])
def tambah_materi():
    if request.method == 'POST':
        # Ambil data utama
        judul = request.form.get('judul')
        deskripsi = request.form.get('deskripsi')

        submateri_list = []
        i = 0
        while True:
            judul_sub = request.form.get(f"submateri[{i}][judul]")
            if not judul_sub:
                break

            tipe_sub = request.form.get(f"submateri[{i}][tipe]")
            sub_data = {"judul": judul_sub, "tipe": tipe_sub}

            if tipe_sub == "text":
                sub_data["konten"] = request.form.get(f"submateri[{i}][konten]")

            elif tipe_sub == "video":
                video = request.files.get(f"submateri[{i}][video]")
                if video and video.filename:
                    filename = secure_filename(video.filename)
                    video.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    sub_data["konten"] = filename
                else:
                    sub_data["konten"] = None

            elif tipe_sub == "multi":
                sub_data["konten"] = []
                j = 0
                while True:
                    subjudul = request.form.get(f"submateri[{i}][subs][{j}][judul]")
                    if not subjudul:
                        break

                    tipe = request.form.get(f"submateri[{i}][subs][{j}][tipe]")
                    subsub = {"judul": subjudul, "tipe": tipe}

                    if tipe == "text":
                        subsub["konten"] = request.form.get(f"submateri[{i}][subs][{j}][konten]")

                    elif tipe in ("video", "image"):
                        file = request.files.get(f"submateri[{i}][subs][{j}][konten]")
                        if file and file.filename:
                            filename = secure_filename(file.filename)
                            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                            subsub["konten"] = filename
                        else:
                            subsub["konten"] = None
                    elif tipe_sub == "image":
                        image = request.files.get(f"submateri[{i}][gambar]")
                        if image and image.filename:
                            filename = secure_filename(image.filename)
                            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                            sub_data["konten"] = filename
                        else:
                            sub_data["konten"] = None


                    sub_data["konten"].append(subsub)
                    j += 1

            submateri_list.append(sub_data)
            i += 1

        # Simpan ke MongoDB
        materi_collection.insert_one({
            "id": materi_collection.count_documents({}) + 1,
            "judul": judul,
            "deskripsi": deskripsi,
            "sub_materi": submateri_list
        })

        return redirect(url_for('dashboard'))

# parsing form data
def parse_form_data(request):
    data = {
        "judul": request.form.get("judul"),
        "deskripsi": request.form.get("deskripsi"),
        "sub_materi": []
    }

    submateri = {}

    for key in request.form:
        if key.startswith("submateri["):
            # Misal: submateri[0][judul]
            parts = key.split('[')
            i = int(parts[1][:-1])  # ambil index i
            field = parts[2][:-1]   # ambil field misal 'judul' atau 'tipe'

            sub = submateri.setdefault(i, {})
            sub[field] = request.form.get(key)

    for key in request.files:
        if key.startswith("submateri["):
            parts = key.split('[')
            i = int(parts[1][:-1])
            field = parts[2][:-1]

            file = request.files[key]
            if file.filename:
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)

                sub = submateri.setdefault(i, {})
                sub['konten'] = filename
            elif f"submateri[{i}][existing]" in request.form:
                # keep existing file
                sub = submateri.setdefault(i, {})
                sub['konten'] = request.form.get(f"submateri[{i}][existing]")

    # Handle sub-sub materi (multi)
    for i, sub in submateri.items():
        if sub.get('tipe') == 'multi':
            sub['konten'] = []
            j = 0
            while True:
                prefix = f"submateri[{i}][subs][{j}]"
                if f"{prefix}[judul]" not in request.form:
                    break

                subsub = {
                    "judul": request.form.get(f"{prefix}[judul]"),
                    "tipe": request.form.get(f"{prefix}[tipe]"),
                }

                if subsub["tipe"] == "text":
                    subsub["konten"] = request.form.get(f"{prefix}[konten]")
                else:
                    file = request.files.get(f"{prefix}[konten]")
                    if file and file.filename:
                        filename = secure_filename(file.filename)
                        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        file.save(filepath)
                        subsub["konten"] = filename
                    elif f"{prefix}[existing]" in request.form:
                        subsub["konten"] = request.form.get(f"{prefix}[existing]")

                sub['konten'].append(subsub)
                j += 1

    data["sub_materi"] = [submateri[i] for i in sorted(submateri.keys())]
    return data

@app.route('/edit_materi/<int:materi_id>', methods=['GET', 'POST'])
def edit_materi(materi_id):
    try:
        materi = db.materi.find_one({'id': materi_id})
    except:
        flash("materi tidak ditemukan")

    if request.method == 'POST':
        data = parse_form_data(request)

        db.materi.update_one({'id': materi_id}, {'$set': data})
        flash('Materi berhasil diperbarui!', 'success')
        return redirect(url_for('dashboard'))

    return render_template("edit_materi.html", form_action=url_for('edit_materi', materi_id=materi_id), materi=materi)



def save_file(file):
    ext = os.path.splitext(file.filename)[1]
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    return filename


@app.route('/tentang-saya')
def tentang_saya():
    if 'username' not in session:
        return redirect(url_for('login'))

    user = session['username']  # Pastikan ini sudah tersimpan saat login
    return render_template('tentang_saya.html', user=user)


# latihan soal

soal_pg = [
    {
        "soal": "Fungsi utama sistem starter pada kendaraan adalah...",
        "opsi": {
            "A": "Mengatur pengisian baterai",
            "B": "Memutar poros engkol untuk menghidupkan mesin",
            "C": "Menyediakan bahan bakar ke ruang bakar",
            "D": "Menghidupkan sistem pengapian",
        },
        "jawaban": "B"
    },
    {
        "soal": "Komponen utama dalam sistem starter yang berfungsi mengubah energi listrik menjadi energi mekanik adalah...",
        "opsi": {
            "A": "Alternator",
            "B": "Motor starter",
            "C": "Ignition coil",
            "D": "Flywheel",
        },
        "jawaban": "B"
    },
    {
        "soal": "Berikut ini yang termasuk komponen sistem starter adalah, kecuali...",
        "opsi": {
            "A": "Solenoid",
            "B": "Motor starter",
            "C": "Aki",
            "D": "Karburator",
        },
        "jawaban": "D"
    },
    {
        "soal": "Komponen yang menghubungkan putaran motor starter ke flywheel adalah...",
        "opsi": {
            "A": "Bendix (pinion gear)",
            "B": "Komutator",
            "C": "Rotor",
            "D": "Saklar starter",
        },
        "jawaban": "A"
    },
    {
        "soal": "Baterai (aki) dalam sistem starter berfungsi sebagai...",
        "opsi": {
            "A": "Pembangkit arus AC",
            "B": "Sumber energi panas",
            "C": "Penyedia arus listrik DC",
            "D": "Pengontrol waktu pengapian",
        },
        "jawaban": "C"
    },
    {
        "soal": "Mengapa solenoid penting dalam sistem starter?",
        "opsi": {
            "A": "Mengatur arah arus pada sistem kelistrikan",
            "B": "Mendorong pinion gear dan menyalurkan arus listrik ke motor starter",
            "C": "Mengisi ulang baterai saat mesin hidup",
            "D": "Menghentikan kerja sistem starter saat mesin mati",
        },
        "jawaban": "B"
    },
    {
        "soal": "Apabila saat distarter hanya terdengar bunyi ‘klik’, kemungkinan besar kerusakan terdapat pada...",
        "opsi": {
            "A": "Flywheel",
            "B": "Relay lampu",
            "C": "Solenoid starter",
            "D": "Karburator",
        },
        "jawaban": "C"
    },
    {
        "soal": "Pada sistem starter tipe konvensional, arus listrik mengalir pertama kali ke...",
        "opsi": {
            "A": "Komutator",
            "B": "Ignition coil",
            "C": "Saklar starter",
            "D": "Busi",
        },
        "jawaban": "C"
    },
    {
        "soal": "Jika pinion gear tidak kembali setelah mesin hidup, maka...",
        "opsi": {
            "A": "Mesin menjadi lebih cepat hidup",
            "B": "Motor starter bisa rusak terbakar",
            "C": "Busi menjadi mati",
            "D": "Arus listrik menjadi stabil",
        },
        "jawaban": "B"
    },
    {
        "soal": "Berikut ini adalah cara merawat sistem starter, kecuali...",
        "opsi": {
            "A": "Memastikan kabel tidak longgar",
            "B": "Membersihkan kutub aki",
            "C": "Menambah air radiator",
            "D": "Memeriksa kondisi solenoid",
        },
        "jawaban": "C"
    }
]


@app.route("/quiz/pilihan-ganda", methods=["GET", "POST"])
def quiz_pg():
    if "user_info" not in session:
        return redirect(url_for("data_diri"))

    if request.method == "POST":
        skor = 0
        for idx, soal in enumerate(soal_pg):
            jawaban_user = request.form.get(f"soal_{idx}")
            if jawaban_user == soal["jawaban"]:
                skor += 1

         # simpan skor di session sementara
        session["last_score"] = {
            "skor": skor,
            "total": len(soal_pg),
            "tipe_soal": "Pilihan Ganda"
        }
        return render_template("quiz_pg_result.html", skor=skor, total=len(soal_pg))

    return render_template("quiz_pg.html", soal_list=soal_pg)

@app.route("/nilai", methods=["GET", "POST"])
def daftar_nilai():
    user_info = session.get("user_info")
    if not user_info:
        return redirect(url_for("data_diri"))

    if request.method == "POST":
        try:
            skor = int(request.form.get("skor"))
            total = int(request.form.get("total"))
            persentase = (skor / total) * 100
            tipe = request.form.get("tipe", "PG")  # default ke PG jika tidak dikirim

            nilai_collection.insert_one({
                "username": user_info["username"],
                "class": user_info["kelas"],
                "major": user_info["jurusan"],
                "tipe_soal": tipe,
                "skor": skor,
                "total": total,
                "persentase": persentase,
                "tanggal": datetime.now()
            })
            print("✅ Nilai berhasil disimpan ke database.")
        except Exception as e:
            print("❌ Gagal menyimpan nilai:", e)

        return redirect(url_for("daftar_nilai"))

    # hasil = list(nilai_collection.find({"username": user_info["username"]}).sort("tanggal", -1)) # using parameter filter username
    page = int(request.args.get("page", 1))
    per_page = 10
    skip = (page - 1) * per_page

    total = nilai_collection.count_documents({})
    hasil = list(nilai_collection.find({}).sort("tanggal", -1).skip(skip).limit(per_page))
    total_pages = (total + per_page - 1) // per_page

    # Untuk range pagination dinamis
    range_size = 5  # tampilkan 5 page max
    start_page = max(1, page - range_size // 2)
    end_page = min(start_page + range_size - 1, total_pages)
    start_page = max(1, end_page - range_size + 1)  # biar jumlah tetap 5

    pages = range(start_page, end_page + 1)
    return render_template("daftar_nilai.html", hasil=hasil, page=page, total_pages=total_pages, pages=pages)



@app.route("/quiz/esai", methods=["GET", "POST"])
def latihan_esai():
    soal_esai = [
        "Jelaskan fungsi utama sistem starter pada kendaraan bermotor!",
        "Sebutkan dan jelaskan fungsi minimal 3 komponen utama dalam sistem starter!",
        "Apa yang terjadi jika solenoid starter rusak? Jelaskan gejala yang muncul dan pengaruhnya terhadap sistem starter!",
        "Bagaimana prosedur pemeriksaan sederhana untuk mengetahui apakah sistem starter masih berfungsi dengan baik?",
        "Gambarkan alur kerja sistem starter saat kunci kontak diputar ke posisi START, dan jelaskan prosesnya secara berurutan!"
    ]
    
    if request.method == "POST":
        jawaban_user = []
        for i in range(len(soal_esai)):
            jawaban_user.append(request.form.get(f"jawaban_{i}"))

        # Di sini bisa simpan ke MongoDB jika perlu
        esai_collection.insert_one({
            "username": session.get("username"),
            "jawaban": jawaban_user,
            "tanggal": datetime.now()
        })

        flash("Jawaban berhasil dikirim. Terima kasih!", "success")
        return redirect(url_for("dashboard"))

    return render_template("latihan_esai.html", soal_list=soal_esai)

@app.route("/quiz/data-diri", methods=["GET", "POST"])
def data_diri():
    if request.method == "POST":
        session["user_info"] = {
            "username": request.form["username"],
            "kelas": request.form["kelas"],
            "jurusan": request.form["jurusan"]
        }
        return redirect(url_for("quiz_menu"))
    return render_template("data_diri.html")


@app.route("/quiz/menu")
def quiz_menu():
    if "user_info" not in session:
        return redirect(url_for("data_diri"))
    return render_template("quiz_menu.html")



if __name__ == "__main__" :
    port = int(os.getenv('APP_PORT', 8080))
    app.run(debug=False, host='0.0.0.0', port=port)