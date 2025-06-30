from mimetypes import init
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from pymongo import MongoClient
from datastore import mongo_crud
import os


UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv'}

app = Flask(__name__)
app.secret_key = 'tkr-super-secret'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Koneksi MongoDB
client = MongoClient("mongodb://admin:admin123@localhost:27017/tkr?authSource=admin")
db = client["tkr"]
materi_collection = db["materi"]

user_collection = db["users"]
mongo_crud.create_one(user_collection, {"username": "admin", "password": "admin"})


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

        print(username, password)

        user = user_collection.find_one({'username': username})
        if user and check_password_hash(user['password'], password):
            session['username'] = username
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Login gagal')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
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
        judul = request.form.get('judul')
        deskripsi = request.form.get('deskripsi')

        submateri_list = []
        index = 0
        while True:
            prefix = f"submateri[{index}]"
            if f"{prefix}[judul]" not in request.form:
                break

            judul_sub = request.form.get(f"{prefix}[judul]")
            tipe = request.form.get(f"{prefix}[tipe]")

            sub_obj = {"judul": judul_sub, "tipe": tipe}

            if tipe == "text":
                sub_obj["konten"] = request.form.get(f"{prefix}[konten]")
            elif tipe == "video":
                video_file = request.files.get(f"{prefix}[video]")
                if video_file:
                    filename = secure_filename(video_file.filename)
                    video_path = os.path.join('static/uploads', filename)
                    video_file.save(video_path)
                    sub_obj["konten"] = filename
            elif tipe == "multi":
                subs = []
                subindex = 0
                while True:
                    subjudul_key = f"{prefix}[subs][{subindex}][judul]"
                    subkonten_key = f"{prefix}[subs][{subindex}][konten]"
                    if subjudul_key not in request.form:
                        break
                    subs.append({
                        "judul": request.form.get(subjudul_key),
                        "konten": request.form.get(subkonten_key)
                    })
                    subindex += 1
                sub_obj["konten"] = subs

            submateri_list.append(sub_obj)
            index += 1

        # Simpan ke database
        materi_collection.insert_one({
            "id": materi_collection.count_documents({}) + 1,
            "judul": judul,
            "deskripsi": deskripsi,
            "sub_materi": submateri_list
        })

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
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        judul = request.form['judul']
        deskripsi = request.form['deskripsi']
        icon_url = request.form['icon_url']

        # Ambil ID terakhir, lalu tambah 1
        last = materi_collection.find_one(sort=[("id", -1)])
        new_id = (last['id'] + 1) if last else 1

        materi_collection.insert_one({
            "id": new_id,
            "judul": judul,
            "deskripsi": deskripsi,
            "icon_url": icon_url
        })

        return redirect(url_for('dashboard'))

    return render_template("tambah_materi.html")



