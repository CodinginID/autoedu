# clear screeen
clear

#!/bin/bash

# Aktifkan virtual environment jika menggunakan venv (opsional)
# Uncomment baris ini jika pakai virtualenv
# source venv/bin/activate

# Set environment variable Flask
export FLASK_APP=main.py
export FLASK_ENV=development
export FLASK_DEBUG=1

# Jalankan Flask dengan hot reload
flask run --host=0.0.0.0 --port=8008 --reload
