# IoT Facial Recognition Traffic Light Control System

## Project Overview

This project implements an Internet of Things (IoT) facial recognition system designed to control a traffic light (LEDs) based on identified individuals. The system leverages an ESP32 microcontroller as the edge device for LED control, a Python-based backend for AI-powered facial recognition, and MQTT as the communication protocol between components.

The primary goal is to:
*   Identify familiar individuals: Activate a Green LED.
*   Identify unfamiliar individuals (strangers): Activate a Yellow LED.
*   Identify individuals on a blacklist: Activate a Red LED.

## System Architecture

The system follows a distributed architecture comprising four main components:

1.  **Camera (Edge Device):** Responsible for capturing facial images. This can be an ESP32-CAM, a standalone camera module connected to an ESP32, or a Raspberry Pi with a camera.
2.  **Backend Server (Python):** The central processing unit. It receives images from the camera, performs facial detection and recognition using AI algorithms, manages a database of known faces, and determines the access status (familiar, stranger, blacklist). It then publishes the decision via MQTT.
3.  **MQTT Broker:** Acts as a message hub, facilitating real-time communication between the backend server and the ESP32 control device. HiveMQ Cloud is used as an example in this setup.
4.  **ESP32 Control Device:** Receives MQTT messages from the broker, interprets the recognition decision, and controls three LEDs (Red, Yellow, Green) accordingly.

+----------------+      +----------------+      +--------------+      +---------------------+
| Camera Device  | ---> | Backend Server | ---> | MQTT Broker  | ---> | ESP32 Control Device| 
| (ESP32-CAM/RPi)|      | (Python AI/DB) |      | (HiveMQ)     |      | (LEDs)              |
+----------------+      +----------------+      +--------------+      +---------------------+
      |                                              ^ 
      | (Captures Images)                            | (Publishes/Subscribes)
      v                                              | 
(Real-time Image Stream / HTTP POST)

## Components and Setup

### 1. Backend Server (Python)

**Location:** `backend/` directory

The backend is responsible for facial recognition and publishing results to MQTT.

**Prerequisites:**
*   Python 3.x
*   Virtual environment (`.venv`)
*   Required Python packages (listed in `requirements.txt`)

**Setup:**

1.  **Navigate to the backend directory:**
    ```bash
    cd backend
    ```
2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv .venv
    # On Windows PowerShell:
    .\.venv\Scripts\Activate.ps1
    # On Linux/macOS:
    source ./.venv/bin/activate
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Configure MQTT Credentials:**
    Create a `.env` file in the `backend/` directory to store your MQTT broker details.
    ```
    MQTT_BROKER="your_hivemq_broker.scloud.hivemq.cloud"
    MQTT_PORT="8883"
    MQTT_TOPIC="/face_rec/status"
    MQTT_USERNAME="your_hivemq_username"
    MQTT_PASSWORD="your_hivemq_password"
    ```
    *Replace placeholder values with your actual HiveMQ Cloud credentials.*

5.  **Run the MQTT Publisher (for testing):**
    The `mqtt_publisher.py` script sends "yellow", "green", and "red" messages to the configured MQTT topic.
    ```bash
    python mqtt_publisher.py
    ```

### 2. ESP32 Control Device

**Location:** `esp32_traffic_light_control/` directory

The ESP32 connects to WiFi, subscribes to MQTT messages, and controls three LEDs (Red, Yellow, Green) based on the received commands. It also hosts a basic web server for manual LED control (HTTP endpoints).

**Hardware Requirements:**
*   ESP32 development board
*   3 LEDs (Red, Yellow, Green)
*   3 Resistors (e.g., 220 Ohm or 330 Ohm) for the LEDs
*   Breadboard and jumper wires

**Wiring:**
Connect the LEDs to the specified GPIO pins with current-limiting resistors.
*   **Red LED:** GPIO 25
*   **Yellow LED:** GPIO 26
*   **Green LED:** GPIO 27
Connect the other end of the resistors to the anode (+) of the LEDs, and the cathode (-) of the LEDs to a common GND pin on the ESP32.

**Prerequisites:**
*   Arduino IDE
*   ESP32 Board Manager installed in Arduino IDE
*   Libraries: `PubSubClient`, `WiFiClientSecure`

**Setup:**

1.  **Open `esp32_traffic_light_control.ino`:** Open the sketch in Arduino IDE.
2.  **Install Libraries:**
    *   Go to `Sketch > Include Library > Manage Libraries...`
    *   Search for and install `PubSubClient` by Nick O\'Leary.
    *   (No explicit install needed for `WiFiClientSecure` as it\'s part of the ESP32 core.)
3.  **Configure WiFi and MQTT Credentials:**
    In `esp32_traffic_light_control.ino`:
    *   Update `ssid` and `password` with your WiFi network credentials.
    *   Update `mqtt_broker`, `mqtt_port`, `mqtt_username`, and `mqtt_password` with your HiveMQ Cloud credentials.
    *   **Crucially, replace the `root_ca` placeholder:**
        ```cpp
        const char* root_ca = \
        "-----BEGIN CERTIFICATE-----\\n" \
        "YOUR_HIVE_MQ_ROOT_CA_CERTIFICATE_HERE\\n" \
        "-----END CERTIFICATE-----\\n";
        ```
        You *must* replace `"YOUR_HIVE_MQ_ROOT_CA_CERTIFICATE_HERE"` with the actual Root CA Certificate from your HiveMQ Cloud account. This is essential for secure (TLS/SSL) MQTT communication.
4.  **Select Board and Port:**
    *   Go to `Tools > Board` and select your ESP32 board (e.g., "ESP32 Dev Module").
    *   Go to `Tools > Port` and select the serial port connected to your ESP32.
5.  **Upload Sketch:**
    Click the "Upload" button (right arrow icon) in the Arduino IDE to compile and upload the sketch to your ESP32.
6.  **Monitor Serial Output:**
    Open the Serial Monitor (Tools > Serial Monitor) at 115000 baud to observe the connection status and MQTT messages.

### 3. MQTT Broker (HiveMQ Cloud)

This project uses an MQTT broker for communication. HiveMQ Cloud is recommended for ease of setup.

**Setup:**
1.  Sign up for a free account on HiveMQ Cloud.
2.  Create a new MQTT cluster.
3.  Note down the Hostname, Port (8883 for SSL), Username, and Password.
4.  Download the Root CA Certificate from your cluster details.

### 4. Camera Device

The implementation details for the camera device are outlined in the `facial_recognition_plan.md`. This component is responsible for capturing images and sending them to the backend server. Further implementation would integrate this with the backend.

## Current Status

*   **Backend MQTT Publisher:** A Python script (`backend/mqtt_publisher.py`) is implemented to publish "yellow", "green", and "red" messages to an MQTT topic. It\'s configured to read credentials from a `.env` file.
*   **ESP32 MQTT Subscriber:** The ESP32 sketch (`esp32_traffic_light_control.ino`) is configured to connect to WiFi, securely (TLS) connect to an MQTT broker, subscribe to a topic, and toggle LEDs based on received messages. It also retains its HTTP web server functionality for manual control.
*   **Facial Recognition Core:** The Python backend is prepared with necessary libraries (`face_recognition`, `scikit-learn`, `numpy`) for future integration of facial detection and recognition logic.

## Future Enhancements (from `facial_recognition_plan.md`)

*   **Camera Integration:** Implement image capture and transmission from the camera device to the backend.
*   **Facial Recognition Logic:** Develop the core facial detection, embedding extraction, and comparison logic in the Python backend.
*   **Face Database Management:** Implement a robust database (e.g., SQLite, PostgreSQL) to store face embeddings and associated user data (familiar, stranger, blacklist). A web interface for managing this database is also planned.
*   **Advanced Features:** 
    *   Storing images of unrecognized individuals for review.
    *   Sending notifications (e.g., to a mobile app) for strangers or blacklisted individuals.
    *   Displaying recognized names on a small LCD screen.
*   **Optimization:** Continuous testing and calibration of recognition thresholds and speed optimization for the entire system.

---
This README provides a high-level overview and detailed setup instructions for the current state of the project.
