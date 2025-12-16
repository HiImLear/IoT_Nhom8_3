#include <WiFi.h>
#include <WebServer.h>
#include <PubSubClient.h>
#include <WiFiClientSecure.h> // Include for secure MQTT

// MQTT Broker details
const char* mqtt_broker = "1ac6b495ac8a42589a2f13a21e09541b.s1.eu.hivemq.cloud"; // Example: "your_hivemq_broker.scloud.hivemq.cloud"
const int mqtt_port = 8883;                     // Example: 8883 for SSL
const char* mqtt_topic = "/face_rec/status";
const char* mqtt_username = "hdang";                 // Your HiveMQ username (optional)
const char* mqtt_password = "HaiDang18";                 // Your HiveMQ password (optional)

// Thay đổi tên WiFi và mật khẩu của bạn tại đây
const char* ssid = "Vinh Da"; // Ví dụ: "MyHomeWiFi"
const char* password = "QNXM12@@"; // Ví dụ: "mywifipassword"

// Định nghĩa các chân GPIO cho đèn giao thông
const int RED_LED_PIN = 25;   // Chân GPIO cho đèn Đỏ
const int YELLOW_LED_PIN = 26; // Chân GPIO cho đèn Vàng
const int GREEN_LED_PIN = 27; // Chân GPIO cho đèn Xanh

// HiveMQ Cloud Root CA (Replace with your actual HiveMQ Root CA Certificate)
const char* root_ca = \
"-----BEGIN CERTIFICATE-----\n" \
"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\n" \
"-----END CERTIFICATE-----\n";

// Khởi tạo đối tượng WiFiClientSecure cho PubSubClient
WiFiClientSecure espClient;
PubSubClient client(espClient);

// Tạo đối tượng WebServer trên cổng 80 (cổng HTTP mặc định)
WebServer server(80);

// Hàm thiết lập ban đầu (chạy một lần khi khởi động)
void setup() {
  Serial.begin(115200); // Khởi tạo Serial Monitor để debug
  delay(10);

  // Khởi tạo các chân LED là OUTPUT
  pinMode(RED_LED_PIN, OUTPUT);
  pinMode(YELLOW_LED_PIN, OUTPUT);
  pinMode(GREEN_LED_PIN, OUTPUT);

  // Đảm bảo tất cả đèn đều tắt khi khởi động
  digitalWrite(RED_LED_PIN, LOW);
  digitalWrite(YELLOW_LED_PIN, LOW);
  digitalWrite(GREEN_LED_PIN, LOW);

  // Kết nối WiFi
  Serial.print("Connecting to ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP()); // In địa chỉ IP của ESP32

  // Cấu hình chứng chỉ SSL/TLS cho kết nối MQTT
  espClient.setCACert(root_ca);
  // For testing, you might want to disable insecure client temporarily (not recommended for production)
  // espClient.setInsecure(); 

  // Cấu hình MQTT client
  client.setServer(mqtt_broker, mqtt_port);
  client.setCallback(callback);

  // Định nghĩa các hàm xử lý cho các yêu cầu HTTP
  server.on("/", handleRoot); // Khi truy cập trang chủ
  server.on("/red_on", handleRedOn);
  server.on("/red_off", handleRedOff);
  server.on("/yellow_on", handleYellowOn);
  server.on("/yellow_off", handleYellowOff);
  server.on("/green_on", handleGreenOn);
  server.on("/green_off", handleGreenOff);
  server.onNotFound(handleNotFound); // Khi truy cập một địa chỉ không tồn tại

  server.begin(); // Khởi động WebServer
  Serial.println("HTTP server started");
}

// Hàm vòng lặp chính (chạy liên tục)
void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop(); // Xử lý các tin nhắn MQTT đến và duy trì kết nối
  server.handleClient(); // Xử lý các yêu cầu từ client (trình duyệt)
}

// Hàm xử lý khi truy cập trang chủ "/"
void handleRoot() {
  // Tạo trang HTML đơn giản với các nút điều khiển
  String html = "<html><body>";
  html += "<h1>ESP32 Traffic Light Control</h1>";
  html += "<p>Red LED: ";
  html += "<a href='/red_on'><button>ON</button></a> ";
  html += "<a href='/red_off'><button>OFF</button></a></p>";
  html += "<p>Yellow LED: ";
  html += "<a href='/yellow_on'><button>ON</button></a> ";
  html += "<a href='/yellow_off'><button>OFF</button></a></p>";
  html += "<p>Green LED: ";
  html += "<a href='/green_on'><button>ON</button></a> ";
  html += "<a href='/green_off'><button>OFF</button></a></button></p>";
  html += "</body></html>";
  server.send(200, "text/html", html); // Gửi trang HTML về trình duyệt
}

// Các hàm xử lý bật/tắt đèn
void handleRedOn() {
  digitalWrite(RED_LED_PIN, HIGH);
  digitalWrite(YELLOW_LED_PIN, LOW); // Đảm bảo các đèn khác tắt khi 1 đèn bật
  digitalWrite(GREEN_LED_PIN, LOW);
  server.sendHeader("Location", "/", true); // Chuyển hướng về trang chủ
  server.send(302, "text/plain", "");
}

void handleRedOff() {
  digitalWrite(RED_LED_PIN, LOW);
  server.sendHeader("Location", "/", true);
  server.send(302, "text/plain", "");
}

void handleYellowOn() {
  digitalWrite(RED_LED_PIN, LOW);
  digitalWrite(YELLOW_LED_PIN, HIGH);
  digitalWrite(GREEN_LED_PIN, LOW);
  server.sendHeader("Location", "/", true);
  server.send(302, "text/plain", "");
}

void handleYellowOff() {
  digitalWrite(YELLOW_LED_PIN, LOW);
  server.sendHeader("Location", "/", true);
  server.send(302, "text/plain", "");
}

void handleGreenOn() {
  digitalWrite(RED_LED_PIN, LOW);
  digitalWrite(YELLOW_LED_PIN, LOW);
  digitalWrite(GREEN_LED_PIN, HIGH);
  server.sendHeader("Location", "/", true);
  server.send(302, "text/plain", "");
}

void handleGreenOff() {
  digitalWrite(GREEN_LED_PIN, LOW);
  server.sendHeader("Location", "/", true);
  server.send(302, "text/plain", "");
}

// Hàm xử lý khi không tìm thấy trang
void handleNotFound() {
  server.send(404, "text/plain", "404: Not found");
}

// Hàm callback khi nhận được tin nhắn MQTT
void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Message arrived on topic: ");
  Serial.print(topic);
  Serial.print(". Message: ");
  String messageTemp;
  
  for (int i = 0; i < length; i++) {
    Serial.print((char)payload[i]);
    messageTemp += (char)payload[i];
  }
  Serial.println();

  // Chuyển tất cả đèn về trạng thái OFF trước khi bật đèn mới
  digitalWrite(RED_LED_PIN, LOW);
  digitalWrite(YELLOW_LED_PIN, LOW);
  digitalWrite(GREEN_LED_PIN, LOW);

  // Điều khiển đèn LED dựa trên nội dung tin nhắn
  if (messageTemp == "red") {
    digitalWrite(RED_LED_PIN, HIGH);
    Serial.println("Red LED ON");
  } else if (messageTemp == "yellow") {
    digitalWrite(YELLOW_LED_PIN, HIGH);
    Serial.println("Yellow LED ON");
  } else if (messageTemp == "green") {
    digitalWrite(GREEN_LED_PIN, HIGH);
    Serial.println("Green LED ON");
  }
}

// Hàm cố gắng kết nối lại với MQTT Broker
void reconnect() {
  // Loop cho đến khi chúng ta kết nối lại
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    // Tạo client ID ngẫu nhiên
    String clientId = "ESP32Client-";
    clientId += String(random(0xffff), HEX);
    // Cố gắng kết nối
    if (client.connect(clientId.c_str(), mqtt_username, mqtt_password)) {
      Serial.println("connected");
      // Sau khi kết nối, đăng ký topic
      client.subscribe(mqtt_topic);
      Serial.print("Subscribed to topic: ");
      Serial.println(mqtt_topic);
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      // Đợi 5 giây trước khi thử lại
      delay(5000);
    }
  }
}
