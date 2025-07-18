import os
from dotenv import load_dotenv
from minio import Minio
import uuid
from werkzeug.utils import secure_filename

# Load dari .env
load_dotenv()

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "uploads")
MINIO_PUBLIC_URL = os.getenv("MINIO_PUBLIC_URL", f"http://{MINIO_ENDPOINT}")

# Inisialisasi client MinIO
minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=MINIO_SECURE
)

# Pastikan bucket ada
if not minio_client.bucket_exists(MINIO_BUCKET):
    minio_client.make_bucket(MINIO_BUCKET)


def upload_file_to_minio(file):
    filename = secure_filename(file.filename)
    ext = filename.split('.')[-1]
    unique_name = f"{uuid.uuid4()}.{ext}"
    object_name = f"uploads/{unique_name}"  # Folder dalam bucket

    minio_client.put_object(
        MINIO_BUCKET,
        object_name,
        file.stream,
        length=-1,
        part_size=10*1024*1024,
        content_type=file.mimetype
    )

    return f"{MINIO_PUBLIC_URL}/{MINIO_BUCKET}/{object_name}"
