import paho.mqtt.client as mqtt
import time
import os
from dotenv import load_dotenv

load_dotenv() # Load environment variables from .env file

# MQTT Broker details - REPLACE WITH YOUR HIVE_MQ CLOUD DETAILS
MQTT_BROKER = os.getenv("MQTT_BROKER", "broker.hivemq.com")  # Example: "your_hivemq_broker.scloud.hivemq.cloud"
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))               # Example: 8883 for SSL
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "/home/door/status")
MQTT_USERNAME = os.getenv("MQTT_USERNAME", "")              # Your HiveMQ username
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")              # Your HiveMQ password

# Function to connect to MQTT broker
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"Connected to MQTT Broker: {MQTT_BROKER}")
    else:
        print(f"Failed to connect, return code {rc}\n")

# Function to publish a message
def publish_message(client, message):
    result = client.publish(MQTT_TOPIC, message)
    status = result[0]
    if status == 0:
        print(f"Sent `{message}` to topic `{MQTT_TOPIC}`")
    else:
        print(f"Failed to send message to topic {MQTT_TOPIC}")

def main():
    client = mqtt.Client()
    client.on_connect = on_connect

    # Set username and password if provided
    if MQTT_USERNAME and MQTT_PASSWORD:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    
    # If using SSL (e.g., port 8883), you might need to configure TLS
    # client.tls_set(tls_version=mqtt.ssl.PROTOCOL_TLS)

    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()

    print("Publishing 'yellow' message in 5 seconds...")
    time.sleep(5)
    publish_message(client, "yellow")
    
    print("Publishing 'green' message in 5 seconds...")
    time.sleep(5)
    publish_message(client, "green")

    print("Publishing 'red' message in 5 seconds...")
    time.sleep(5)
    publish_message(client, "red")

    client.loop_stop()
    client.disconnect()
    print("Publisher finished.")

if __name__ == "__main__":
    main()
