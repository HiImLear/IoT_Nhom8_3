from flask import Flask, request, jsonify
import face_recognition
import numpy as np
import paho.mqtt.client as mqtt
import json
import os
import io
import ssl # Import ssl module

from dotenv import load_dotenv

app = Flask(__name__)

# Tải biến môi trường từ file .env
load_dotenv()

# --- Cấu hình MQTT ---
# Lấy thông tin từ biến môi trường
MQTT_BROKER_HOST = os.getenv("MQTT_BROKER_HOST")
MQTT_BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT", 1883)) # Mặc định 1883 nếu không có
MQTT_BROKER_USERNAME = os.getenv("MQTT_BROKER_USERNAME")
MQTT_BROKER_PASSWORD = os.getenv("MQTT_BROKER_PASSWORD")
MQTT_TOPIC_STATUS = os.getenv("MQTT_TOPIC_STATUS", "/home/door/status") # Mặc định nếu không có

mqtt_client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
    else:
        print(f"Failed to connect, return code {rc}. Please check MQTT broker host, port, username, password and network connection.\n")

def on_publish(client, userdata, mid):
    print(f"Message {mid} published successfully.")

mqtt_client.on_connect = on_connect
mqtt_client.on_publish = on_publish # Add on_publish callback
mqtt_client.username_pw_set(MQTT_BROKER_USERNAME, MQTT_BROKER_PASSWORD)
# Cấu hình TLS/SSL cho kết nối an toàn đến HiveMQ Cloud (sử dụng cổng 8883)
mqtt_client.tls_set(tls_version=ssl.PROTOCOL_TLSv1_2) # Sử dụng TLSv1.2 hoặc cao hơn
mqtt_client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)
mqtt_client.loop_start() # Chạy loop trong background để duy trì kết nối và xử lý tin nhắn

# --- Cấu hình lưu trữ embeddings khuôn mặt ---
# Sử dụng JSONL để lưu trữ data
KNOWN_FACES_FILE = "known_faces.jsonl"
known_faces_data = [] # List chứa các dictionary của từng người
known_face_encodings = [] # List chứa các numpy array của embeddings
known_face_names = [] # List chứa tên của từng người
known_face_types = [] # List chứa loại của từng người (familiar, blacklist)

def load_known_faces():
    """Tải dữ liệu khuôn mặt đã biết từ file JSONL."""
    global known_faces_data, known_face_encodings, known_face_names, known_face_types
    if os.path.exists(KNOWN_FACES_FILE):
        with open(KNOWN_FACES_FILE, 'r') as f:
            for line in f:
                data = json.loads(line)
                known_faces_data.append(data)
                known_face_encodings.append(np.array(data["encoding"]))
                known_face_names.append(data["name"])
                known_face_types.append(data.get("type", "familiar")) # Lấy type hoặc mặc định là "familiar"
        print(f"Loaded {len(known_faces_data)} known faces.")
    else:
        print("No known faces file found. Starting with empty database.")

def save_known_face(name, encoding, face_type="familiar"):
    """Lưu một khuôn mặt mới vào file JSONL."""
    data = {"name": name, "encoding": encoding.tolist(), "type": face_type} # Convert numpy array to list for JSON
    with open(KNOWN_FACES_FILE, 'a') as f:
        f.write(json.dumps(data) + '\n')
    known_faces_data.append(data)
    known_face_encodings.append(encoding)
    known_face_names.append(name)
    known_face_types.append(face_type)
    print(f"Saved new face: {name} as {face_type}")

# Tải khuôn mặt đã biết khi server khởi động
load_known_faces()


@app.route("/")
def home():
    return "Backend Server for Facial Recognition is running!"

@app.route("/recognize", methods=["POST"])
def recognize_face():
    """
    Endpoint nhận ảnh từ thiết bị camera, thực hiện nhận diện và gửi kết quả qua MQTT.
    Ảnh được gửi dưới dạng binary data trong request body.
    """
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file part in the request"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "error", "message": "No selected file"}), 400

    if file:
        try:
            # Đọc ảnh từ stream
            img_bytes = file.read()
            # Chuyển đổi bytes thành numpy array (ảnh)
            # Dùng face_recognition.load_image_file() trực tiếp từ BytesIO
            # hoặc dùng OpenCV để decode nếu cần xử lý phức tạp hơn
            image = face_recognition.load_image_file(io.BytesIO(img_bytes))

            # Phát hiện vị trí khuôn mặt trong ảnh
            face_locations = face_recognition.face_locations(image)

            if not face_locations:
                print("No faces found in the image.")
                mqtt_client.publish(MQTT_TOPIC_STATUS, "yellow")  # Người lạ
                return jsonify({"status": "success", "result": "stranger", "message": "No faces found"}), 200

            # Lấy embeddings cho tất cả các khuôn mặt tìm thấy
            face_encodings = face_recognition.face_encodings(image, face_locations)

            results = []
            for face_encoding in face_encodings:
                # So sánh với các khuôn mặt đã biết
                if len(known_face_encodings) > 0:
                    # Lấy ngưỡng từ biến môi trường hoặc dùng mặc định 0.6
                    FACE_RECOGNITION_THRESHOLD = float(os.getenv("FACE_RECOGNITION_THRESHOLD", 0.6))

                    matches = face_recognition.compare_faces(
                        known_face_encodings,
                        face_encoding,
                        tolerance=FACE_RECOGNITION_THRESHOLD
                    )

                    name = "Unknown"
                    face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)

                    # Lấy khuôn mặt gần nhất
                    best_match_index = np.argmin(face_distances)
                    if matches[best_match_index]:
                        name = known_face_names[best_match_index]

                    results.append({"name": name, "distance": face_distances[best_match_index]})

                else:
                    results.append({"name": "Unknown", "distance": None})

            # Logic đưa ra quyết định (cập nhật để sử dụng type)
            final_status = "yellow" # Mặc định là người lạ

            if results:
                # Tìm người gần nhất đã biết
                # Lọc ra những người không phải "Unknown" và có khoảng cách nhỏ nhất
                known_matches = [
                    (known_face_types[best_match_index], known_face_names[best_match_index], face_distances[best_match_index])
                    for i, res in enumerate(results)
                    if res["name"] != "Unknown"
                ]

                # Nếu có người quen/blacklist được nhận diện
                if known_matches:
                    # Sắp xếp theo khoảng cách để lấy người gần nhất
                    known_matches.sort(key=lambda x: x[2])
                    best_known_type = known_matches[0][0] # Lấy type của người gần nhất

                    if best_known_type == "blacklist":
                        final_status = "red" # Người trong danh sách đen
                    elif best_known_type == "familiar":
                        final_status = "green" # Người quen
                else:
                    final_status = "yellow" # Người lạ
            
            mqtt_client.publish(MQTT_TOPIC_STATUS, final_status)

            return jsonify({"status": "success", "result": final_status, "faces": results}), 200

        except Exception as e:
            print(f"Error processing image: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
    
    return jsonify({"status": "error", "message": "Unexpected error"}), 500


@app.route("/register", methods=["POST"])
def register_face():
    """
    Endpoint để đăng ký một khuôn mặt mới.
    Yêu cầu 'name' và 'file' (ảnh) trong form data.
    """
    if 'name' not in request.form:
        return jsonify({"status": "error", "message": "Missing \'name\' in form data"}), 400
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file part in the request"}), 400

    name = request.form['name']
    face_type = request.form.get('type', 'familiar') # Lấy type hoặc mặc định là familiar

    # Kiểm tra xem tên đã tồn tại chưa
    # Cần kiểm tra kỹ hơn: nếu tên tồn tại nhưng là cùng type thì sao?
    # Hiện tại, chỉ kiểm tra tên duy nhất.
    if name in known_face_names:
        return jsonify({"status": "error", "message": f"Face with name '{name}' already exists."}), 409
    file = request.files['file']

    if file.filename == '':
        return jsonify({"status": "error", "message": "No selected file"}), 400

    if file:
        try:
            image = face_recognition.load_image_file(io.BytesIO(file.read()))
            face_locations = face_recognition.face_locations(image)

            if not face_locations:
                return jsonify({"status": "error", "message": "No face found in the provided image"}), 400
            
            # Chỉ lấy embedding của khuôn mặt đầu tiên được tìm thấy
            face_encoding = face_recognition.face_encodings(image, face_locations)[0]
            
            save_known_face(name, face_encoding, face_type=face_type)
            
            return jsonify({"status": "success", "message": f"Face '{name}' registered successfully."}), 201

        except Exception as e:
            print(f"Error registering face: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
    
    return jsonify({"status": "error", "message": "Unexpected error"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)