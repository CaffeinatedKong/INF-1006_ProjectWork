# Healthcare System: README

## Overview

You can view the project on [GitHub](https://github.com/CaffeinatedKong/INF-1006_ProjectWork).


This project implements a **healthcare monitoring system** where various devices are controlled remotely using **AWS SNS**, **MQTT**, and **Blockchain** technology for **authentication** and **security**. The system consists of multiple components running on different devices:

- **Main Pi (poll.py)**: The central Raspberry Pi that communicates with other raspberry pi devices through MQTT and listens for AWS SNS messages via SQS.
- **Medication Pi (medicationClient.py)**: A Raspberry Pi that controls the medication dispenser, including dispensing medication and notifying the system when medication is picked up.
- **Aircon Pi (airconClient.py)**: A Raspberry Pi that controls the aircon in a room, including a touch sensor that notifies the care taker if it is pressed.
- **Flask Webserver** (app.py): A cloud-hosted Flask application that serves a user interface and interacts with the blockchain smart contract for user authentication.

## Components

### 1. **Main Pi (poll.py)**
   - **Purpose**: Acts as the central hub that listens for messages from AWS SQS and handles MQTT communication between the **Flask Web Server** and devices.
   - **Responsibilities**:
     - Listens to **SQS** queues for commands to control devices like the **Aircon** or **Medication Dispenser**.
     - Sends commands over **MQTT** to the respective **Pi** (either **Aircon Pi** or **Medication Pi**).
     - Receives status updates from devices over **MQTT** and publishes these updates to **AWS SNS**.

   - **Key Dependencies**:
     - `boto3` (AWS SDK for Python)
     - `paho.mqtt.client` (MQTT communication)
     - `threading` (to handle multiple processes simultaneously)
   
### 2. **Medication Pi (medicationClient.py)**
   - **Purpose**: Handles the **medication dispenser** and communicates with the **Main Pi** via **MQTT**.
   - **Responsibilities**:
     - Listens for **dispense** commands via MQTT.
     - Activates the medication dispensing process.
     - Notifies when medication is dispensed and checks if the medication is picked up using an ultrasonic sensor.
     - Sends a message via MQTT indicating whether the medication was picked up or not.

   - **Key Dependencies**:
     - `RPi.GPIO` (for interacting with GPIO pins)
     - `paho.mqtt.client` (MQTT communication)


### 3. **Aircon Pi (airconClient.py)**
   - **Purpose**: Handles the **aircon** and communicates with the **Main Pi** via **MQTT**.
   - **Responsibilities**:
     - Listens for **on/off** commands via MQTT.
     - Activates or deactivates system based on received command
     - Sends a message via MQTT indicating whether the aircon was turned on or off
     - Touch sensor to communicate with care taker phone

   - **Key Dependencies**:
     - `RPi.GPIO` (for interacting with GPIO pins)
     - `paho.mqtt.client` (MQTT communication)

### 4. **Flask Webserver + Smart Contract on Blockchain(app.py)**
   - **Purpose**: Provides a **web interface** for the user (caregiver) to interact with the system.
   - **Responsibilities**:
     - Verifies the **user's authorization** using a **smart contract** on the **Ethereum blockchain**.
     - Communicates with the **Main Pi** via **AWS SNS** and **SQS** to perform tasks like turning on/off the **air conditioning** or dispensing medication.
     - Sends the **user's action** (such as turning on the aircon or dispensing medication) to **SQS** for further processing by **Main Pi**.
   
   - **Key Dependencies**:
     - `Flask` (for serving the web interface)
     - `Web3.py` (to interact with the Ethereum blockchain and the smart contract)
     - `boto3` (AWS SDK for Python)

   - **Purpose**: Handles user authentication through blockchain-based smart contracts, ensuring that only authorized users can interact with the system.
   - **Responsibilities**:
     - Stores a list of **authorized users** (addresses).
     - Verifies the user's **Ethereum address** to allow access to system controls.

   - **Key Dependencies**:
     - Ethereum blockchain (Sepolia testnet)
     - Web3.js (used in the Flask app to interact with the blockchain)




## Setup Instructions

### 1. **Flask Webserver Setup**

To set up and run the **Flask Webserver** on your cloud-hosted Ubuntu machine:

1. **Access the Web Server**:
   Use the `inf-1006-key.pem` file to access your **web server** hosted on the cloud via SSH:
   ```bash
   ssh -i inf-1006-key.pem ubuntu@3.149.253.192
   ```

2. **Activate the Virtual Environment**:
   After logging into the server, navigate to your project directory (`flask_webserver`) and activate the virtual environment:
   ```bash
   source env/bin/activate
   ```

3. **Install Required Dependencies**:
   Install the necessary dependencies in your virtual environment (if not already installed):
   ```bash
   pip install flask web3 boto3
   ```

4. **Deploy the Smart Contract on Remix**:
   - Go to the **Remix IDE** (https://remix.ethereum.org/).
   - Create a new Solidity file (`flask_app.sol`) and paste your smart contract code.
   - Compile the smart contract using Remix's compiler.
   - Deploy the smart contract on the **Sepolia testnet**:
     - Use **MetaMask** for deploying the contract by selecting **Sepolia** as the network.
     - Once deployed, make a note of the **contract address**
   
5. **Install MetaMask**:
   - Install the **MetaMask** browser extension: https://metamask.io/.
   - Set up your MetaMask wallet if you haven't already.
   - Make sure your wallet is connected to the **Sepolia testnet** in MetaMask.

6. **Add Your MetaMask Wallet Address as an Authorized User**:
   - In Remix IDE, interact with the deployed smart contract and use the `addAuthorizedUser()` function.
   - Provide your **MetaMask wallet address** (the one connected to the Sepolia testnet) to the contract to add it as an authorized user.

7. **Run the Flask Application**:
   After setting up everything, start the **Flask app**:
   ```bash
   python app.py
   ```

8. **Accessing the Flask App**:
   Once the Flask app is running, you can access it by navigating to the appropriate **IP address** and **port** in a web browser.

---

### Notes:
- The **smart contract** deployed on **Remix IDE** ensures that only authorized users (based on their **MetaMask wallet address**) can access the functions on the **Flask web server**.
- **MetaMask** will allow you to interact with the smart contract, ensuring that the user is verified before performing any actions like controlling the air conditioner or dispensing medication.

---
### 2. **Main Pi Setup**
   - Ensure that **MQTT** and **SQS** are properly configured.
   - Install the required dependencies:
     ```bash
     pip install paho-mqtt boto3
     ```
   - Run `poll.py`:
     ```bash
     python poll.py
     ```

### 3. **Medication Pi Setup**
   - Install the required dependencies:
     ```bash
     pip install paho-mqtt RPi.GPIO
     ```
   - Run `medicationClient.py`:
     ```bash
     python medicationClient.py
     ```


### 4. **Aircon Pi Setup**
   - Install the required dependencies:
     ```bash
     pip install paho-mqtt RPi.GPIO
     ```
   - Run `airconClient.py`:
     ```bash
     python airconClient.py
     ```

## Running the System
1. The **Flask Webserver** serves the interface where caretakers can press buttons to control devices.
2. Once a button is pressed, the Flask app signs the action message and sends it to the backend for verification through the **smart contract** on the blockchain.
3. If the user is authorized, the Flask app publishes a message to **AWS SNS**, which is processed by the **Main Pi**.
4. The **Main Pi** communicates with the **Aircon Pi** or **Medication Pi** using **MQTT** to perform the action (e.g., turn on the aircon or dispense medication).
5. The **Medication Pi** also communicates back to **Main Pi** via MQTT to notify about the status (e.g., medication picked up).