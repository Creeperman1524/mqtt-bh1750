# https://bitbucket.org/MattHawkinsUK/rpispy-misc/raw/master/python/bh1750.py
import configparser
import json
import math
import sys
import time

import paho.mqtt.client as mqtt
import smbus

DEVICE = 0x23  # Default device I2C address
ONE_TIME_HIGH_RES_MODE_2 = 0x21  # Start measurement at 1lx resolution
bus = smbus.SMBus(1)  # Rev 2 Pi uses 1


class MQTTControl:

    def __init__(self, config_path) -> None:
        self._config = configparser.ConfigParser()
        if len(self._config.read(config_path)) == 0:
            raise RuntimeError(
                "Failed to find configuration file at {0}, is the application properly installed?".format(
                    config_path
                )
            )

        self._mqtt_broker = self._config.get("mqtt", "broker")
        self._mqtt_user = self._config.get("mqtt", "user")
        self._mqtt_password = self._config.get("mqtt", "password")
        self._mqtt_connected = False
        self._mqtt_clientid = self._config.get("mqtt", "clientid")

        self._mqtt_lux_topic = self._config.get("mqtt", "lux_topic")
        self._mqtt_brightness_command_topic = self._config.get(
            "mqtt", "brightness_command_topic"
        )
        self._mqtt_device = json.loads(self._config.get("mqtt", "device"))

        self._mqtt_discovery_prefix = self._config.get("mqtt", "discovery_prefix")

        self._prev_brightness = -1
        self._prev_lux = -1

    def on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            print("Connected!")
            self._mqtt_connected = True

            # Listen for when Home Assistant goes online
            client.subscribe(f"{self._mqtt_discovery_prefix}/status")
            self.send_discovery(client)
        else:
            self._mqtt_connected = False
            print("Could not connect. Return code: " + str(reason_code))

    def on_disconnect(self, client, userdata, flags, reason_code, properties):
        print("Disconnected. Reason: " + str(reason_code))
        self._mqtt_connected = False

    def send_status(self, client):
        # Only send an update when the value actually changes
        lux = self.readLight()
        if lux == self._prev_lux:
            return

        self._prev_lux = lux

        payload_lux = str(lux)
        print(f"Publishing lux: {payload_lux}")
        client.publish(self._mqtt_lux_topic, payload_lux, 0, True)

        # Updates the clock's brightness
        brightness = math.floor(self.calculateBrightness(float(payload_lux)) / 31 * 100)

        if brightness == self._prev_brightness:
            return

        self._prev_brightness = brightness

        print(f"Updating brightness {brightness}")
        client.publish(self._mqtt_brightness_command_topic, str(brightness), 0, False)

    def convertToNumber(self, data):
        return (data[1] + (256 * data[0])) / 1.2

    def readLight(self, addr=DEVICE):
        # Read data from I2C interface
        data = bus.read_i2c_block_data(addr, ONE_TIME_HIGH_RES_MODE_2)
        return self.convertToNumber(data)

    def calculateBrightness(self, lux):
        return (min(250, 60 * math.log10(lux + 1))) / 250 * 30 + 1

    def on_message(self, client, userdata, msg):
        payload = str(msg.payload.decode("utf-8"))
        topic = msg.topic

        if topic == f"{self._mqtt_discovery_prefix}/status":
            # Send discovery message when homeassistant is online
            if str(payload) == "online":
                self.send_discovery(client)

    def send_discovery(self, client):
        """Sends a discovery message whenever home assistant is detected online for the entity"""
        luxDiscovery = (
            f"{self._mqtt_discovery_prefix}/sensor/{self._mqtt_clientid}-lux/config"
        )

        luxConfig = {
            "name": self._mqtt_clientid + "-lux",
            "unique_id": self._mqtt_clientid + "-lux",
            "state_topic": self._mqtt_lux_topic,
            "unit_of_measurement": "lx",
            "device_class": "illuminance",
            "device": self._mqtt_device,
        }

        print("Sending lux discovery message...")
        client.publish(luxDiscovery, json.dumps(luxConfig), 0, False)
        self.send_status(client)

    def run(self):
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, self._mqtt_clientid)
        client.on_connect = self.on_connect
        client.on_disconnect = self.on_disconnect
        client.on_message = self.on_message
        client.username_pw_set(self._mqtt_user, self._mqtt_password)

        print("Connecting to broker " + self._mqtt_broker)
        client.loop_start()
        try:
            client.connect(self._mqtt_broker, 1883, 60)
        except:
            print("ABORT: Connection failed!")
            exit(1)

        while not self._mqtt_connected:
            time.sleep(1)
        while self._mqtt_connected:
            try:
                self.send_status(client)
            except Exception as e:
                print("exception")
                print(str(e))

            time.sleep(1)

        client.loop_stop()  # Stop loop
        client.disconnect()  # disconnect


if __name__ == "__main__":
    print("Starting rpi BH1750 sensor control via mqtt")

    config_path = "./settings.conf"
    # Override config path if provided as parameter.
    if len(sys.argv) == 2:
        config_path = sys.argv[1]

    controller = MQTTControl(config_path)
    controller.run()
