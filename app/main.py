from mimetypes import init
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from pymongo import MongoClient
from datastore import mongo_crud
from dotenv import load_dotenv
import os

load_dotenv()


UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv'}

app = Flask(__name__)
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

# In-memory database dummy
materi_list = []

@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    materi_list = list(materi_collection.find({}, {"_id": 0}))  # Ambil semua materi
    return render_template('dashboard.html', materi_list=materi_list)

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
    return redirect(url_for('login'))

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

# @app.route('/materi/tambah', methods=['GET', 'POST'])
# def tambah_materi():
#     if 'username' not in session:
#         return redirect(url_for('login'))

#     if request.method == 'POST':
#         judul = request.form['judul']
#         deskripsi = request.form['deskripsi']
#         icon_url = request.form['icon_url']

#         # Ambil ID terakhir, lalu tambah 1
#         last = materi_collection.find_one(sort=[("id", -1)])
#         new_id = (last['id'] + 1) if last else 1

#         materi_collection.insert_one({
#             "id": new_id,
#             "judul": judul,
#             "deskripsi": deskripsi,
#             "icon_url": icon_url
#         })

#         return redirect(url_for('dashboard'))

#     return render_template("tambah_materi.html")


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


if __name__ == "__main__" :
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)