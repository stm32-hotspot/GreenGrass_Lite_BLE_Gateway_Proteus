import asyncio
import subprocess
from bleak import BleakScanner, BleakClient
import paho.mqtt.client as paho
import json
import functools


# Runtime in Seconds
RUNTIME = 6000

# Interval at which a BLE Scan is run for devices with correct UUID
SCAN_INTERVAL = 60

# ST Manufacturer ID https://www.bluetooth.com/specifications/assigned-numbers/
STMICROELECTRONICS_MANUFACTURER_KEY = 0x30

SERVICE_UUID = "00000000-0001-11e1-9ab4-0002a5d5c51b"   # PROTEUS
CHARACTERISTIC_UUIDS = {
    "BATTERY": "00020000-0001-11e1-ac36-0002a5d5c51b",
    "TEMPERATURE": "00040000-0001-11e1-ac36-0002a5d5c51b",
    "ACCELEROMETER_EVENT": "00000400-0001-11e1-ac36-0002a5d5c51b",
    "SWITCH": "20000000-0001-11e1-ac36-0002a5d5c51b"
}

# Path to the certificates
DEVICE_CERT = "/home/root/certs/certificate.pem"
DEVICE_KEY = "/home/root/certs/private.key"
ROOT_CA = "/home/root/certs/AmazonRootCA1.pem"

# AWS IoT Endpoint
ENDPOINT = "a1qwhobjtvew8t-ats.iot.us-west-2.amazonaws.com"

class MqttPublisher:
    def __init__(self, device_cert, device_key, root_ca, mqtt_endpoint):
        self.client = paho.Client(callback_api_version=paho.CallbackAPIVersion.VERSION2)
        self.device_cert = device_cert
        self.device_key = device_key
        self.root_ca = root_ca
        self.mqtt_endpoint = mqtt_endpoint
        self.client.loop_start

    def on_connect(self, client, userdata, flags, reason_code, properties):
        """Callback function when connected to the broker"""
        print(f"Connected with result code {reason_code}")

    def on_publish(self, client, userdata, mid, reason_codes, properties):
        """Callback function when a message is successfully published"""
        print(f"Message Published with ID {mid}")

    def setup_mqtt_client(self):
            self.client.on_connect = self.on_connect
            self.client.on_publish = self.on_publish
            self.client.tls_set(ca_certs=self.root_ca, certfile=self.device_cert, keyfile=self.device_key)
            self.client.connect(self.mqtt_endpoint, 8883, 60)

    async def publish_message(self, topic, message):
        """Asynchronous MQTT message publishing."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.client.publish, topic, message, 1)

    def start(self):
        """Start the MQTT loop."""
        self.client.loop_start()

class SensorGateway:
    """
    A gateway to handle Bluetooth communication, collect temperature data, and publish to MQTT.
    """
    def __init__(self, manufacturer_id, service_uuid, characteristic_uuids, mqtt_publisher):
        self.manufacturer_id = manufacturer_id
        self.service_uuid = service_uuid
        self.characteristic_uuids = characteristic_uuids
        self.devices = []
        self.mqtt_publisher = mqtt_publisher
        self.setup_bluetooth()

    def setup_bluetooth(self):
        """
        Initializes the SensorGateway.

        Args:
            manufacturer_id (int): The BLE manufacturer ID to filter devices.
            service_uuid (str): The UUID of the service to search for.
            characteristic_uuids (list): List of characteristic UUIDs to subscribe to.
        """
        try:
            subprocess.run(["hciconfig", "hci0", "up"], check=True)
            print("Bluetooth interface hci0 brought up successfully.")
            result = subprocess.run(["hciconfig", "-a"], check=True, text=True, capture_output=True)
            print("Bluetooth interface configuration:")
            print(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"Error setting up Bluetooth: {e}")
            exit(1)

    async def find_devices(self):
        """
        Scans for BLE devices advertising the specified manufacturer ID.
        Stores devices matching the manufacturer ID.
        """

        print(f"Scanning for nearby BLE devices...")

        discovered_devices_and_advertisement_data = await BleakScanner.discover(return_adv=True)
        self.devices = []  # Reset the device list before scanning

        for device, adv_data in discovered_devices_and_advertisement_data.values():
            device_name = device.name or "Unknown"
            device_address = device.address
            rssi = device.rssi  # Signal strength (in dBm)
            service_uuids = adv_data.service_uuids  # List of advertised service UUIDs
            manufacturer_data = adv_data.manufacturer_data  # Manufacturer-specific data
            raw_data = adv_data  # Raw advertisement data

            manufacturer_key = next(iter(manufacturer_data), None) if manufacturer_data else None

            # Print detailed device information for all devices
            print(f"Found device: {device_name} ({device_address})")
            print(f"   - RSSI: {rssi} dBm")
            print(f"   - Advertised Services: {service_uuids if service_uuids else 'None'}")
            if manufacturer_data:
                print(f"   - Manufacturer Data: {manufacturer_data}")
            if raw_data:
                print(f"   - Raw Advertisement Data: {raw_data}")

            if manufacturer_key == self.manufacturer_id:
                self.devices.append((device_name, device_address))
                print(f"Added {device_name} ({device_address}) to the device list.")


        if not self.devices:
            print(f"No devices Manufacturer ID '{self.manufacturer_id}' found.")
        else:
            print(f"Devices advertising Manufacturer ID '{self.manufacturer_id}': {self.devices}")


    def notification_handler(self, data, device_info, char_uuid, first_temp_ignored):
        """
        Handles incoming BLE notifications and processes sensor data.

        Args:
            data (bytes): The received notification data.
            device_info (tuple): Tuple containing (device_name, device_address).
            char_uuid (str): The UUID of the characteristic that sent the notification.
        """
        device_name, device_address = device_info
        byte_data = ' '.join(f'0x{byte:02X}' for byte in data)  # Convert to hexadecimal byte representation
        print(f"Received data from {char_uuid} on {device_name} ({device_address}): {byte_data}")

        message, topic = None, None

        try:
            # Process temperature data
            if char_uuid == self.characteristic_uuids.get("TEMPERATURE"):
                if first_temp_ignored[0]:  # Ignore first temperature value

                    timestamp = int.from_bytes(data[0:2], byteorder='little')
                    temperature = int.from_bytes(data[2:4], byteorder='little') / 10.0
                    message = {"device": device_name, "address": device_address, "temperature": temperature, "timestamp": timestamp}
                    topic = f"{device_name}/temp/{device_address}"

                first_temp_ignored[0] = True
                

            # Process battery data
            elif char_uuid == self.characteristic_uuids.get("BATTERY"):
                timestamp = int.from_bytes(data[0:2], byteorder='little')
                battery_percentage = int.from_bytes(data[2:4], byteorder='little') / 10.0
                voltage = int.from_bytes(data[4:6], byteorder='little') / 1000.0
                current = int.from_bytes(data[6:8], byteorder='little') / 10.0
                state = int.from_bytes(data[8:], byteorder='little') / 1.0

                 # Map status byte to human-readable string
                status_map = {
                    0: "Low battery",
                    1: "Discharging",
                    2: "Plugged, not charging",
                    3: "Charging",
                    4: "Unknown"
                }
                status = status_map.get(state, "Unknown")  # Default to "Unknown" if status byte is not in the map
                
                message = {"device": device_name, "address": device_address, "battery": battery_percentage, "voltage": voltage, "current": current, "status": status, "timestamp": timestamp}
                topic = f"{device_name}/battery/{device_address}"

            elif char_uuid == self.characteristic_uuids.get("ACCELEROMETER_EVENT"):
                timestamp = int.from_bytes(data[0:2], byteorder='little')
                event_int = int.from_bytes(data[2:3], byteorder='little')
                steps = int.from_bytes(data[3:5], byteorder='little')

                event_map = {
                    0: "No event",
                    1: "Orientation top right",
                    2: "Orientation bottom right",
                    3: "Orientation bottom left",
                    4: "Orientation top left",
                    5: "Orientation up",
                    6: "Orientation bottom",
                    8: "Tilt",
                    16: "Free fall",
                    32: "Single tap",
                    64: "Double tap",
                    128: "Wake up"
                }

                event = event_map.get(event_int, "Unknown")
                message = {"device": device_name, "address": device_address, "event": event, "steps": steps}
                topic = f"{device_name}/acc_event/{device_address}"

            elif char_uuid == self.characteristic_uuids.get("SWITCH"):
                timestamp = int.from_bytes(data[0:2], byteorder='little')
                switch_int = int.from_bytes(data[2:3], byteorder='little')

                switch_map = {
                    0: "OFF",
                    1: "ON"
                }

                switch = switch_map.get(switch_int, "Unknown")
                message = {"device": device_name, "address": device_address, "switch": switch}
                topic = f"{device_name}/switch/{device_address}"

            if message and topic:
                print(f"Publishing to {topic}: {message}")
                asyncio.create_task(self.mqtt_publisher.publish_message(topic, json.dumps(message)))


        except Exception as e:
            print(f"Error processing notification from {char_uuid}: {e}")


    async def read_data_from_device(self, device_name, device_address):
        """Connects to a BLE device, subscribes to notifications, listens for a short time, then moves on."""
        try:
            async with BleakClient(device_address) as client:
                if not client.is_connected:
                    print(f"Failed to connect to {device_name} ({device_address})")
                    return

                print(f"Connected to {device_name} ({device_address})")

                first_temp_ignored = [False]  # Track if the first temperature value has been ignored

                async def on_notification(sender, data):
                    self.notification_handler(data, (device_name, device_address), sender.uuid, first_temp_ignored)

                # Subscribe to characteristics
                for char_uuid in self.characteristic_uuids.values():
                    try:
                        await client.start_notify(char_uuid, functools.partial(on_notification))
                    except Exception as e:
                        print(f"Failed to subscribe to {char_uuid} on {device_name}: {e}")

                await asyncio.sleep(10)  # Listen for 5 seconds

                # Unsubscribe from characteristics
                for char_uuid in self.characteristic_uuids:
                    try:
                        await client.stop_notify(char_uuid)
                    except Exception as e:
                        print(f"Error unsubscribing from {char_uuid}: {e}")

        except Exception as e:
            print(f"Error with {device_name} ({device_address}): {e}")

    async def read_data_from_all_devices(self):
        """Connects to each discovered BLE device and subscribes to notifications."""
        if not self.devices:
            print("No devices found. Please run `find_devices()` first.")
            return

        for device_name, device_address in self.devices:
            try:
                print(f"Connecting to {device_name} ({device_address})...")
                await self.read_data_from_device(device_name, device_address)
            except Exception as e:
                print(f"Failed to collect data from {device_name} ({device_address}): {e}")
            finally:
                print(f"Finished processing {device_name} ({device_address}).")


async def main():
    mqtt_publisher = MqttPublisher(DEVICE_CERT, DEVICE_KEY, ROOT_CA, ENDPOINT)
    mqtt_publisher.setup_mqtt_client()

    # # Create the SensorGateway instance
    bt_sensor = SensorGateway(STMICROELECTRONICS_MANUFACTURER_KEY, SERVICE_UUID, CHARACTERISTIC_UUIDS, mqtt_publisher)

    # Start MQTT loop in the background
    mqtt_publisher.start()

    # Periodically scan and read data from devices
    start_time = asyncio.get_event_loop().time()
    while asyncio.get_event_loop().time() - start_time < RUNTIME:
        # Scan for devices and populate the device list
        await bt_sensor.find_devices()

        if not bt_sensor.devices:
            print("No devices found. Retrying after a delay...")
            await asyncio.sleep(5)  # Delay before rescanning
            continue  

        # Continuously read temperature data from each discovered device for the duration of scan_interval
        end_time = asyncio.get_event_loop().time() + SCAN_INTERVAL
        while asyncio.get_event_loop().time() < end_time:
            await bt_sensor.read_data_from_all_devices()

        # Wait before the next scan (just to ensure the logic is followed; the inner loop takes care of timing)
        await asyncio.sleep(0)

    print("Finished collecting data from BLE devices.")


if __name__ == "__main__":
    asyncio.run(main())