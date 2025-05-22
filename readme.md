# AWS IoT Greengrass BLE Sensor Gateway

## Introduction

Bluetooth Low Energy (BLE) sensor nodes are increasingly utilized across a wide range of applications, including health and wellness, industrial, and environmental monitoring. These devices typically operate with short-range communication, making them ideal for localized data collection in diverse environments. The **AWS IoT Greengrass BLE Sensor Gateway** enables seamless communication between BLE sensor nodes and AWS cloud services through a Linux-based MPU platform. This solution allows users to securely collect data from a variety of BLE-enabled sensor nodes and transmit it to AWS IoT Core for further processing, analytics, and integration with other AWS services.

![Architecture](./assets/aws_greengrass_ble_gateway_architecture.png)

In this solution, the **[STEVAL-PROTEUS1](https://www.st.com/en/evaluation-tools/steval-proteus1.html)** series microcontroller acts as the BLE node, transmitting sensor data. The application sets up the **[STM32MPU](https://www.st.com/en/microcontrollers-microprocessors/stm32-arm-cortex-mpus.html)** as the **AWS IoT Greengrass BLE Sensor Gateway**, allowing it to securely transmits data from the STEVAL-PROTEUS1 devices to AWS IoT Core for processing, analytics, and integration with other AWS services. Additionally, the solution supports remote deployment to the STM32MPU devices operating **[Greengrass Lite](https://docs.aws.amazon.com/greengrass/v2/developerguide/greengrass-nucleus-lite-component.html)** in the field, providing flexibility for managing remote and distributed sensor networks.

### What is AWS IoT Greengrass?

AWS IoT Greengrass is a service that extends AWS to edge devices, allowing them to act locally on the data they generate. It enables local execution of AWS Lambda functions, message brokering, data caching, and synchronization with AWS cloud services, even when the devices are offline. Greengrass helps you manage remote devices at scale, securely deploy applications, and keep devices up-to-date with remote software updates. 

#### What is AWS IoT Greengrass Lite?

The Greengrass nucleus lite is a device runtime for constrained edge devices optimized for minimal memory footprint (uses less than 5MB RAM). It has been introduced with AWS IoT Greengrass version 2.14.0 release and is backward compatible with AWS IoT Greengrass generic components, Greengrass V2 API, and SDK.

### AWS IoT Greengrass Remote Deployment

The **BLE Gateway** is packaged as an **[AWS IoT Greengrass V2 component](https://docs.aws.amazon.com/greengrass/v2/developerguide/greengrass-components.html)**, enabling seamless **[remote deployment](https://docs.aws.amazon.com/greengrass/v2/developerguide/create-deployments.html)** onto **STM32MPU** devices with the provided `deploy.sh` script. 
This setup allows you to:

1. **Manage Devices at Scale**: Easily deploy and manage your sensor networks in remote locations without requiring direct interaction with each device.
2. **Real-time Monitoring**: Continuously collect data from sensors in the field and monitor it in real time in **AWS IoT Core**.
3. **Remote Firmware Updates**: Push updates to devices remotely, ensuring they remain up-to-date with minimal intervention.
4. **Edge Computing**: Run **AWS Lambda** functions on the edge to process data locally, reducing latency and bandwidth usage by sending only relevant data to the cloud.

#### Deployment Process:

![Deployment](./assets/aws_greengrass_ble_gateway_deployment.png)

1. **Developer Prepares the Component**:
   - The **Developer PC** clones this **BLE Gateway Component**.

2. **Upload the Component to Greengrass**:
   - The developer uploads the component artifacts to **Amazon S3**.

3. **Greengrass Deploys to the Gateway Device**:
   - The developer interacts with **AWS Greengrass** to deploy the **BLE Gateway Component** to the **STM32MPU Gateway Device**.

4. **Communication with BLE Sensor Nodes**:
   - The **Gateway Device** begins scanning for nearby **BLE Sensor Nodes** (e.g., health thermometers or other BLE devices).
   - The gateway securely collects BLE sensor data.

5. **Data Transmission to AWS IoT Core**:
   - The **Gateway Device** formats sensor data into MQTT messages, and sends it to AWS IoT Core over the internet.
   - **AWS IoT Core** can be used for further processing, analysis, and integration with other AWS services.

This deployment process ensures you can manage remote sensor networks at scale, monitor data in real-time, and update devices remotely with minimal physical intervention, making it ideal for both on-premise and edge use cases.

---

## Use-Cases

This project serves as a proof of concept, collecting data from BLE devices using the Health Thermometer Service UUID. However, it can be easily adapted for a wide range of BLE sensor node applications. Some potential use cases include:

- **Remote Health Monitoring**: Gather temperature data from personal or home-based health thermometers, leveraging AWS services to analyze trends, detect anomalies, and offer remote health insights.
![Health](assets/remote_health_monitoring.png)
- **Smart Home Integration**: Seamlessly connect BLE thermometers with smart home systems to trigger automatic actions, such as adjusting heating or cooling based on temperature readings.
![Home](assets/smart_home_integration.png)
- **Medical Device Integration**: Enable BLE-enabled medical devices to send data to AWS IoT Core, facilitating centralized data management, real-time analytics, and improved patient care.
![Medical](assets/medical_device_integration.png)
- **Industrial Equipment Monitoring**: Integrate BLE-enabled sensors with industrial machinery to monitor operating conditions in real-time. Data can be sent to AWS IoT Core for predictive maintenance, alerting operators to abnormalities, thereby reducing downtime and maintenance costs.
![Industrial](assets/industrial_equipment_monitoring.png)

---

## **Technical Overview**

This gateway is a Python-based application packaged as an **[AWS IoT Greengrass V2 component](https://docs.aws.amazon.com/greengrass/v2/developerguide/greengrass-components.html)** for **STM32MPU devices**. It enables **STM32MPU devices** to communicate with nearby **BLE sensor nodes**. The component is **[deployed remotely](https://docs.aws.amazon.com/greengrass/v2/developerguide/create-deployments.html) from the developer's PC** to an STM32MPU board, allowing it to function independently in the field, providing seamless data collection and communication with AWS IoT Core.

Key features of the component include:

- **BLE Device Scanning**: The component uses the **[Bleak](https://bleak.readthedocs.io/en/latest/)** library to scan for nearby BLE devices that advertise the [STMicroelectronics Manufacturer ID](https://www.bluetooth.com/specifications/assigned-numbers/)
  
- **Data Collection**: The system subscribes to BLE notifications for **temperature**, **accelerometer events**, **switch status**, and **battery status** from nearby PROTEUS devices. It processes and formats the received data into structured **JSON MQTT messages**. For more details, refer to the [Data Collection](#data-collection) section.  

- **Secure MQTT Communication**: The component uses the **[Paho-MQTT](https://pypi.org/project/paho-mqtt/)** library along with **TLS encryption** to securely send data to AWS IoT Core via the MQTT protocol.

- **AWS IoT Integration**: Data collected from BLE devices is published to **AWS IoT Core** in real time, where it can be further processed, analyzed, and integrated with other AWS services for monitoring, analytics, and decision-making.

By packaging this functionality as an AWS Greengrass component, developers can deploy and manage the gateway remotely, without needing direct access to each device in the field, ensuring scalability and ease of maintenance.

### Data Collection  

#### Overview  
This system collects and processes sensor data from a Bluetooth Low Energy (BLE) device using predefined **service** and **characteristic UUIDs**. Incoming notifications are parsed based on the characteristic type, and the extracted data is published via MQTT.  

#### **Service and Characteristic UUIDs**  
- **Service UUID**: `00000000-0001-11e1-9ab4-0002a5d5c51b` (PROTEUS)  
- **Characteristics**:  
  - **Battery**: `00020000-0001-11e1-ac36-0002a5d5c51b`  
  - **Temperature**: `00040000-0001-11e1-ac36-0002a5d5c51b`  
  - **Accelerometer Event**: `00000400-0001-11e1-ac36-0002a5d5c51b`  
  - **Switch**: `20000000-0001-11e1-ac36-0002a5d5c51b`  

#### **Notification Handling**  
Incoming BLE notifications are processed based on the characteristic UUID, and data is extracted accordingly:  

##### **1. Temperature Data**  
- **Ignored**: First temperature reading  
- **Fields**:  
  - `timestamp` (UInt16)  
  - `temperature` (°C, scaled by 10)  
- **MQTT Topic**: `{device_name}/temp/{device_address}`  

##### **2. Battery Data**  
- **Fields**:  
  - `timestamp` (UInt16)  
  - `battery` percentage (scaled by 10)  
  - `voltage` (V, scaled by 1000)  
  - `current` (mA, scaled by 10)  
  - `status` (mapped from a predefined set of values)  
- **Status Mapping**:  
  - `0`: Low battery  
  - `1`: Discharging  
  - `2`: Plugged, not charging  
  - `3`: Charging  
  - `4`: Unknown  
- **MQTT Topic**: `{device_name}/battery/{device_address}`  

##### **3. Accelerometer Event Data**  
- **Fields**:  
  - `timestamp` (UInt16)  
  - `event` (mapped from predefined values)  
  - `steps` (UInt16)  
- **Event Mapping**:  
  - `0x00`: No event  
  - `0x01`: Orientation top right  
  - `0x02`: Orientation bottom right  
  - `0x03`: Orientation bottom left  
  - `0x04`: Orientation top left  
  - `0x05`: Orientation up  
  - `0x06`: Orientation bottom  
  - `0x08`: Tilt  
  - `0x10`: Free fall  
  - `0x20`: Single tap  
  - `0x40`: Double tap  
  - `0x80`: Wake up  
- **MQTT Topic**: `{device_name}/acc_event/{device_address}`  

##### **4. Switch Data**  
- **Fields**:  
  - `timestamp` (UInt16)  
  - `switch` state (`0`: OFF, `1`: ON)  
- **MQTT Topic**: `{device_name}/switch/{device_address}`  

### Summary

- The Greengrass BLE Gateway component is deployed onto a STM32MPU device. 
- The STM32MPU then periodically scans for BLE sensor nodes advertising specific UUIDs.
- The STM32MPU loops through available BLE devices collecting sensor data.
- The data is structured as a JSON message and sent securely to AWS IoT Core via MQTT.
- The integration with AWS IoT Core allows for real-time processing and analytics.

---

## **Project Structure**

```plaintext
GG_BLE_Gateway/
├── BleGatewayComponent/
│   ├── artifacts/
│   │   └── com.example.BleGateway/
│   │       └── 1.0.0/
│   │           ├── BleGateway.py                  # Main BLE gateway script
│   │           └── install.sh                     # Dependency installation script
│   └── recipes/
│       └── com.example.BleGateway-TEMPLATE.yaml   # Greengrass component recipe template
├── config.json                                    # Deployment configuration file
└── deploy.sh                                      # Deployment script
```

### **Key Files**
- **`BleGatewayComponent/`**: Contains the Greengrass component's recipe and its artifacts.

- **`install.sh`**: Installs complete version of Python3, Pip3, [Bleak](https://bleak.readthedocs.io/en/latest/), and [Paho-Mqtt](https://pypi.org/project/paho-mqtt/) if not present 
- **`deploy.sh`**: Automates AWS Greengrass Deployment of BLE Gateway Component. Depends on [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html) (refer to Required Software section). 
- **`config.json`**: Configuration script for deploy.sh. 
---

## **Required Software and Hardware**

### 1. **STEVAL-PROTEUS1:**
   <div style="text-align:center;">
     <img src="assets/PROTEUS.png" alt="STEVAL-PROTEUS1" width="300" />
   </div>

   - **Compatible Firmware:**  
      - The **STEVAL-PROTEUS** comes preloaded with compatible firmware. Both **version 1.0.0** and **version 1.1.1** are supported. You can use the preloaded firmware or rebuild and flash your own image. 
      - For detailed build instructions, refer to the official documentation: [STSW-PROTEUS](https://www.st.com/en/embedded-software/stsw-proteus.html).  

### 2. **STM32MPU Boards (Greengrass-Compatible):**
   - A **Greengrass-compatible** STM32MPU board is required for deployment.
   - Supported STM32MPU boards include:

   <div style="text-align:center;">
     <img src="assets/MP1DK.jpeg" alt="STM32MP135F-DK" width="300" />
   </div>

   - **[STM32MP135F-DK](https://www.st.com/en/evaluation-tools/stm32mp135f-dk.html)**  

   <div style="text-align:center;">
     <img src="assets/MP2DK.jpeg" alt="STM32MP257F-DK" width="300" />
   </div>

   - **[STM32MP257F-DK](https://www.st.com/en/evaluation-tools/stm32mp257f-dk.html)**  

### 3. **AWS CLI (Command Line Interface):**
To interact with AWS services from the terminal, you need to have the AWS CLI installed and configured.

   - **Installation:**  
   Follow the official [AWS CLI installation guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) for your operating system.

   - **Configuration:**  
   After installing the AWS CLI, you must configure it with your AWS credentials (access key and secret key):
      1. Run the [aws configure](https://docs.aws.amazon.com/cli/latest/reference/configure/) command:
         ```bash
         aws configure
         ```
      2. You will be prompted to enter:
         - **AWS Access Key ID** (see [AWS docs](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html))
         - **AWS Secret Access Key** (see [AWS docs](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html))
         - **Default region name** (e.g., `us-west-2`)
         - **Default output format** (e.g., `json`)

---

## **Setup Instructions**

### **1. Clone This Repository**

   ```bash
   git clone https://github.com/AlnurElberier/GreenGrass_Lite_BLE_Gateway_Proteus
   ```

### **2. Power on STEVAL-PROTEUS**
  
   - Power on your STEVAL-PROTEUS board
   - Ensure you are using a [comptible firmware version](#1-steval-proteus1)
   - For additional support please review [Getting started with the STEVAL-PROTEUS1](https://www.st.com/resource/en/user_manual/um3000-getting-started-with-the-stevalproteus1-evaluation-kit-for-condition-monitoring-based-on-the-24-ghz-stm32wb5mmg-module-stmicroelectronics.pdf)


### **3. Register Your STM32MPU Board as an AWS IoT Greengrass Lite Device**

   Follow this lightweight approach to set up AWS IoT Greengrass on STM32MPU devices :
   - **[STM32MP1_AWS-IoT-Greengrass-nucleus-lite](https://github.com/stm32-hotspot/STM32MP1_AWS-IoT-Greengrass-nucleus-lite)**
   



### **4. Deploy the Component**
   The BLE Gateway Component is packaged as a Greengrass V2 Component and deployment is automated with **`deploy.sh`**. 

   1. **Configure `config.json`**
      The `config.json` file contains essential parameters for deploying the **BleGateway** component using AWS Greengrass. Follow the instructions below to correctly populate the fields.  


      ##### **Parameter Descriptions**
      | **Key**              | **Description** |
      |----------------------|---------------|
      | `TARGET_NAME`       | The name of the AWS IoT Thing or Group that will receive the Greengrass deployment. Example: `"MyGreengrassDevice"` or `"MyGreengrassGroup"`. |
      | `BASE_BUCKET_NAME`   | The base name for the AWS S3 bucket where artifacts will be stored. Your AWS account ID will be appended to this name automatically. |
      | `REGION`            | The AWS region where your resources (S3 bucket, Greengrass component, IoT Thing) are located. Example: `"us-west-2"`. |
      | `VERSION`          | The version number of the component. This should match the version of your deployment. Example: `"1.0.0"`. |
      | `COMPONENT_NAME`    | The name of the AWS Greengrass component being deployed. Example: `"com.example.BleGateway"`. |

      ##### **Example `config.json` File**
      ```json
      {
         "TARGET_NAME": "MyGreengrassDevice",
         "BASE_BUCKET_NAME": "ble-gateway",
         "REGION": "us-west-2",
         "VERSION": "1.0.0",
         "COMPONENT_NAME": "com.example.BleGateway"
      }
      ```


      >##### **Notes:**
      >- Ensure that **`BASE_BUCKET_NAME`** is unique across AWS (your account ID helps with this).  
      >- The **`TARGET_NAME`** should match an existing AWS IoT Thing **OR** Group Name.
      >- **Creating New Versions or Modifying Artifacts:**  
      >     - If you create a new version or modify artifacts (e.g., `BleGateway.py`, `install.sh`), place them in a directory corresponding to the new version.  
      >     - The script expects artifacts to be in:  
      >        ```./BleGatewayComponent/artifacts/com.example.BleGateway/<VERSION>/```
      >     - This ensures the deployment script can find and upload the correct files.

   2. **Run `Deploy.sh`**

      ##### **Prerequisites**  
      - **AWS CLI** [installed](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html) and [configured](https://docs.aws.amazon.com/cli/latest/reference/configure/).  
      - A properly filled `config.json`

      ##### **Running the Script**  
      ```sh
      cd GG_BLE_GATEWAY
      chmod +x deploy.sh  # Ensure it's executable (only needed once)
      ./deploy.sh
      ```
      This will:  
      - Load settings from `config.json`.  
      - Upload artifacts (`BleGateway.py`, `install.sh`) to S3.  
      - Update the component recipe.  
      - Create and deploy the component in AWS Greengrass.  

### **5. Viewing MQTT Messages in AWS IoT Core**  

   To monitor and debug MQTT messages from your AWS Greengrass BLE Gateway, use the AWS IoT MQTT test client:  

   1. **Open AWS IoT Core**  
      - Sign in to the [AWS IoT Console](https://console.aws.amazon.com/iot).  
      
   2. **Access the MQTT Test Client**  
      - In the left navigation pane, select **Test** under **Message Routing**.  
      
   3. **Subscribe to Topics**  
      - Enter the topic filter (e.g., `HTSTM/temp/`) and choose **Subscribe to topic**.  
      
   4. **Publish and View Messages**  
      - Monitor incoming messages or send test messages to your IoT Core topics.  

   For detailed instructions, refer to the [AWS documentation](https://docs.aws.amazon.com/iot/latest/developerguide/view-mqtt-messages.html).  

---

## **Contributing**
Contributions are welcome! If you'd like to improve the repository or add new features, feel free to open a pull request or submit an issue.
