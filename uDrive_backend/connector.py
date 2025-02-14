from socket import create_connection

from flask import Flask, request, jsonify, send_file, send_from_directory
import mysql.connector
import random
import os
import uuid
from moviepy.editor import VideoFileClip



app = Flask(__name__)

# MySQL bağlantısı için gerekli bilgiler
db_config = {
    'user': 'username',
    'password': 'password',
    'host': 'host',
    'database': 'dbname'
}

def get_users():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM uDrives.users")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

@app.route('/users', methods=['GET'])
def users():
    user_list = get_users()
    return jsonify(user_list)
@app.route('/', methods=['GET'])
def index():
    return "Flask uygulaması çalışıyor!"

@app.route('/register', methods=['POST'])
def register():
    # Kullanıcı bilgilerini al
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    # Rastgele bir userID oluştur
    user_id = random.randint(1, 100)

    # MySQL veritabanına bağlan
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    try:
        # Kullanıcıyı veritabanına ekle
        sql = "INSERT INTO users (userID, userName, userPassword) VALUES (%s, %s, %s)"
        val = (user_id, username, password)
        cursor.execute(sql, val)

        # Değişiklikleri kaydet
        conn.commit()

        return jsonify({"message": "Kullanıcı başarıyla kaydedildi!"}), 201
    except mysql.connector.Error as err:
        print("Hata: {}".format(err))
        return jsonify({"message": "Kullanıcı kaydedilemedi!"}), 500
    finally:
        # Bağlantıyı kapat
        cursor.close()
        conn.close()


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE userName=%s AND userPassword=%s", (username, password))
    user = cursor.fetchone()

    if user:
        user_id = user['userID']
        cursor.execute("SELECT tarih FROM user WHERE id=%s", (user_id,))
        tarih = cursor.fetchall()
        return jsonify({"userID": user_id, "tarih": tarih}), 200
    else:
        return jsonify({"message": "Kullanıcı adı veya şifre yanlış!"}), 401

    cursor.close()
    conn.close()


@app.route('/user_data/<int:user_id>', methods=['GET'])
def get_user_data(user_id):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    try:
        # Kullanıcının hız verisini al
        cursor.execute("SELECT hiz FROM user WHERE id=%s", (user_id,))
        hiz_data = cursor.fetchone()

        # Kullanıcının trafik ışığı verisini al
        cursor.execute("SELECT trafikIsigi FROM user WHERE id=%s", (user_id,))
        trafik_isigi_data = cursor.fetchone()

        # Kullanıcının nesne tespit verisini al
        cursor.execute("SELECT nesneTespit FROM user WHERE id=%s", (user_id,))
        nesne_tespit_data = cursor.fetchone()

        # Kullanıcının şerit takip verisini al
        cursor.execute("SELECT seritTakip FROM user WHERE id=%s", (user_id,))
        serit_takip_data = cursor.fetchone()

        # Kullanıcının analiz verisini al
        cursor.execute("SELECT analysis FROM user WHERE id=%s", (user_id,))
        analysis_data = cursor.fetchone()

        return jsonify({
            "userID": user_id,
            "hiz": hiz_data['hiz'],
            "trafikIsigi": trafik_isigi_data['trafikIsigi'],
            "nesneTespit": nesne_tespit_data['nesneTespit'],
            "seritTakip": serit_takip_data['seritTakip'],
            "analysis": analysis_data['analysis']
        }), 200
    except mysql.connector.Error as err:
        print("Hata: {}".format(err))
        return jsonify({"message": "Veri çekilemedi!"}), 500
    finally:
        cursor.close()
        conn.close()

"""
@app.route('/video/<int:video_id>', methods=['GET'])
def get_video(video_id):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("SELECT videoBlob FROM videos WHERE id=%s", (video_id,))
    video_blob = cursor.fetchone()[0]
    cursor.close()
    conn.close()

    # Geçici bir dosyaya yaz
    temp_file_path = f"temp_video_{video_id}.mp4"
    with open(temp_file_path, 'wb') as f:
        f.write(video_blob)

    # Dosya URL'sini döndür
    return send_file(temp_file_path, as_attachment=True)
    """
@app.route('/analysis_video/<string:nesneTespit>', methods=['GET'])
def get_analysis_video(column_name):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT {} FROM user".format(column_name))
        video_blob = cursor.fetchone()[0]

        return send_file(video_blob, mimetype='video/mp4')
    except mysql.connector.Error as err:
        print("Hata: {}".format(err))
        return jsonify({"message": "Video verisi alınamadı!"}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/analysis_video', methods=['POST'])
def get_video():
    data = request.json
    column_name = data.get('column_name')
    record_id = data.get('id')

    if not column_name or not record_id:
        return jsonify({'error': 'Column name and record ID are required'}), 400

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    query = f"SELECT {column_name} FROM user WHERE id = %s"
    cursor.execute(query, (record_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()

    if result and result[0]:
        video_path = result[0]
        if not os.path.exists(video_path):
            return jsonify({'error': 'Video file not found'}), 404

        video_url = f"http://127.0.0.1:5000/video?path={video_path}"
        return jsonify({'video_url': video_url})
    else:
        return jsonify({'error': 'Video not found'}), 404

@app.route('/video', methods=['GET'])
def serve_video():
    video_path = request.args.get('path')
    if video_path and os.path.exists(video_path):
        return send_file(video_path)
    else:
        return jsonify({'error': 'File not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)
