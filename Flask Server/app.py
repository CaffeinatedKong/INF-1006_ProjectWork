from flask import Flask, request, jsonify, render_template
from web3 import Web3
from eth_account.messages import encode_defunct
import boto3
import threading

app = Flask(__name__)

# Connect to Infura 
web3 = Web3(Web3.HTTPProvider("https://sepolia.infura.io/v3/"))

# Check connection to Sepolia testnet
if not web3.is_connected():
    print("Failed to connect to the Sepolia network.")
else:
    print("Connected to Sepolia testnet.")

# Smart contract details
contract_address = ""
contract_abi = [
	{
		"inputs": [],
		"stateMutability": "nonpayable",
		"type": "constructor"
	},
	{
		"anonymous": False,
		"inputs": [
			{
				"indexed": False,
				"internalType": "address",
				"name": "user",
				"type": "address"
			}
		],
		"name": "ButtonPressed",
		"type": "event"
	},
	{
		"inputs": [
			{
				"internalType": "address",
				"name": "user",
				"type": "address"
			}
		],
		"name": "addAuthorizedUser",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "address",
				"name": "",
				"type": "address"
			}
		],
		"name": "authorizedUsers",
		"outputs": [
			{
				"internalType": "bool",
				"name": "",
				"type": "bool"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "address",
				"name": "user",
				"type": "address"
			}
		],
		"name": "isUserAuthorized",
		"outputs": [
			{
				"internalType": "bool",
				"name": "",
				"type": "bool"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [],
		"name": "owner",
		"outputs": [
			{
				"internalType": "address",
				"name": "",
				"type": "address"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [],
		"name": "pressButton",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "address",
				"name": "user",
				"type": "address"
			}
		],
		"name": "removeAuthorizedUser",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	}
]

contract = web3.eth.contract(address=contract_address, abi=contract_abi)

#AWS Credentials
aws_access_key = ''
aws_secret_key = ''
iot_client = boto3.client('sns', region_name='us-east-2',aws_access_key_id=aws_access_key,
                          aws_secret_access_key=aws_secret_key)
SNS_TOPIC_ARN_AIRPORT = ""
SNS_TOPIC_ARN_MEDICATION = ""
# The AWS IoT topic Raspberry Pi is subscribed to
TOPIC = 'home/aircon/control'

# Route to serve the index.html page
@app.route('/')
def home():
    return render_template('index.html')  

# Route to perform an action (such as controlling aircon or medication)
@app.route('/perform_action', methods=['POST'])
def perform_action():
    data = request.json
    user_address = data['userAddress']
    signature = data['signature']
    action = data['action']
    action_value = data['actionValue']

    # Verify the signature (signing the message for authentication)
    message = f"I want to perform the action: {action_value}"
    message_hash = encode_defunct(text=message)
    recovered_address = web3.eth.account.recover_message(message_hash,signature = signature)
    if recovered_address.lower() == user_address.lower():
        user_address = Web3.to_checksum_address(user_address)
        is_authorized = contract.functions.isUserAuthorized(user_address).call()
        #If user authorized then allow api calls
        if is_authorized:
            print("User Authorised")
            if action == 'aircon':
                #Depends on form submitted from flask
                if action_value =="on":
                    print("FLASK SERVER: Telling Main Pi to Turn On aircon")
                    try:
                        response = iot_client.publish(
                            TopicArn=SNS_TOPIC_ARN_AIRPORT,
                            Message='ON',
                            Subject='Aircon Control'
                        )
                    except Exception as e:
                        print("Error publishing to SNS:", e)
                elif action_value== 'off':
                    print("FLASK SERVER: Telling Main Pi to Turn Off Aircon ")
                    try:
                        response = iot_client.publish(
                            TopicArn=SNS_TOPIC_ARN_AIRPORT,
                            Message='OFF',
                            Subject='Aircon Control'
                        )
                    except Exception as e:
                        print("Error publishing to SNS:", e)
                return jsonify({"success": True, "message": "Signal Sent!"})
            #Manual medication to be dispensed
            elif action == 'medication':
                if action_value == 'dispense':
                    print("Telling MAIN PI: Dispense Medication")
                    try:
                        response = iot_client.publish(
                            TopicArn=SNS_TOPIC_ARN_MEDICATION,
                            Message='MANUAL',
                            Subject='MEDICATION DISPENSER'
                        )
                    except Exception as e:
                        print("Error publishing to SNS:", e)
                #Start auto dispensing logic
                elif action_value == 'start_auto_dispense':
                    print("Telling MAIN PI: Start Automatic Dispense Medication")
                    try:
                        response = iot_client.publish(
                            TopicArn=SNS_TOPIC_ARN_MEDICATION,
                            Message='START_AUTOMATIC',
                            Subject='MEDICATION DISPENSER'
                        )
                    except Exception as e:
                        print("Error publishing to SNS:", e) 
                elif action_value == 'stop_auto_dispense':
                    print("Telling MAIN PI: Stop Automatic Dispense Medication")
                    try:
                        response = iot_client.publish(
                            TopicArn=SNS_TOPIC_ARN_MEDICATION,
                            Message='STOP_AUTOMATIC',
                            Subject='MEDICATION DISPENSER'
                        )
                    except Exception as e:
                        print("Error publishing to SNS:", e)
                return jsonify({"success": True, "message": "Signal Sent !"})

        else:
            return jsonify({"success": False, "error": "User not authorized"})
    else:
        return jsonify({"success": False, "error": "Invalid signature"})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
