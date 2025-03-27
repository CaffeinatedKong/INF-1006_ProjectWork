import boto3
import time
import paho.mqtt.client as mqtt
import threading
import json
from datetime import datetime, timedelta


# AWS credentials
aws_access_key = 'AKIA32FE4466CJJ33DYS'
aws_secret_key = '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'
region_name = 'us-east-2'

# Create the SQS client
sqs_client = boto3.client('sqs', 
                          aws_access_key_id=aws_access_key,
                          aws_secret_access_key=aws_secret_key,
                          region_name=region_name)


sns_client = boto3.client('sns',
                          aws_access_key_id=aws_access_key,
                          aws_secret_access_key=aws_secret_key,
                          region_name=region_name)

# SQS Queue URLs (from SQS Console)
queue_url_aircon = 'https://sqs.us-east-2.amazonaws.com/812094646204/AirconControllerQueue'
queue_url_medication = "https://sqs.us-east-2.amazonaws.com/812094646204/MedicationControllerQueue"

arn_touch = "arn:aws:sns:us-east-2:812094646204:TouchController"

#MQTT Broker settings (Main Pi's IP or hostname)
mqtt_broker = "172.20.10.11"  # Replace with Main Pi's IP or hostname
mqtt_port = 1883
mqtt_topic_medication_command = "medication/dispenser"  # Topic for commands
mqtt_topic_medication_status = "medication/status"  # Topic for status updates
mqtt_topic_aircon_command = "aircon/controller"  # Topic for commands
mqtt_topic_aircon_status = "aircon/status"
mqtt_topic_touch_status = "touch/help"
mqtt_topic_servo_status = "servo/status"
# Create MQTT client instance (only one instance)
mqtt_client = mqtt.Client()

# Global flag to control automatic dispensing
dispensing_active = False
dispensing_thread = None




# This will be called when the client connects to the broker
def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT Broker with result code " + str(rc))
    # Subscribe to the status topic to get updates from the Medication Dispenser Pi
    client.subscribe(mqtt_topic_medication_status)
    client.subscribe(mqtt_topic_aircon_status)
    client.subscribe(mqtt_topic_touch_status)
    client.subscribe(mqtt_topic_servo_status)

# This will be called when a message is received on the subscribed topic
def on_message(client, userdata, msg):
    print(f"Received MQTT message on {msg.topic}: {msg.payload.decode()}")
    if msg.topic == mqtt_topic_medication_status:
        # Process status update message
        status = msg.payload.decode()
        print(f"Medication Status update: {status}")
    elif msg.topic == mqtt_topic_aircon_status:
        status = msg.payload.decode()
        print(f"Aircon Status update: {status}")
    elif msg.topic == mqtt_topic_touch_status:
        status = msg.payload.decode()
        # Publish a message to the SNS topic
        response = sns_client.publish(
            TopicArn=arn_touch,
            Message=status,
            Subject='Test Message'  
        )
        print(f"Sending to AWS Cloud to request help")
    elif msg.topic == mqtt_topic_servo_status:
        status = msg.payload.decode()
        if status == "Medication dispensed successfully":
            # Publish a message to the SNS topic
            response = sns_client.publish(
                TopicArn=arn_touch,
                Message=status,
                Subject='Test Message'  
            )
            print(f"Sending to AWS Cloud that medication picked up successfully")
        else:
            # Publish a message to the SNS topic
            response = sns_client.publish(
                TopicArn=arn_touch,
                Message=status,
                Subject='Test Message'  
            )
            print(f"Sending to AWS Cloud that medication NOT picked up")



# Function to handle MQTT loop in a separate thread
def mqtt_loop():
    # Set up MQTT credentials 
    mqtt_client.username_pw_set(username="user1", password="user1")
    mqtt_client.connect(mqtt_broker, mqtt_port, 60)
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.loop_start()

# Function to handle Aircon message processing
def process_aircon_message(response_aircon):
    if 'Messages' in response_aircon:
        message_aircon = response_aircon['Messages'][0]
        message_body_aircon = message_aircon['Body']
        receipt_handle_aircon = message_aircon['ReceiptHandle']
        
        # Process the Aircon message
        if message_body_aircon == 'ON':
            print("Received from FLASK SERVER: Turn On Aircon")
            mqtt_client.publish(mqtt_topic_aircon_command, "on", qos=1)
            print("Sending to AIRCON PI: Turn On Aircon")
        elif message_body_aircon == 'OFF':
            print("Received from FLASK SERVER: Turn Off Aircon")
            mqtt_client.publish(mqtt_topic_aircon_command,"off",qos=1)
            print("Sending to AIRCON PI: Turn Off Aircon")
        
        # Delete the Aircon message from the queue after processing
        sqs_client.delete_message(
            QueueUrl=queue_url_aircon,
            ReceiptHandle=receipt_handle_aircon
        )
    else:
        print("")



def target_automatic_dispense():
    global dispensing_active
    print("Waiting for 6 PM to start automatic medication dispensing...")

    # Loop to run the dispensing task every day at 6 PM
    while True:
        now = datetime.now()
        print(now)
        target_time = datetime(now.year, now.month, now.day, 22, 2,0 )  # Target time
        print(target_time)
        # If it's already past time today, set the target to tomorrow
        if now > target_time:
            target_time += timedelta(days=1)

        # Calculate how much time 
        time_until_target= (target_time - now).total_seconds()
        print(f"Waiting for {time_until_target} seconds until set time")

        # Wait until time
        time.sleep(time_until_target)

        # Start dispensing once it's time
        automatic_dispense()

        # Wait 24 hours before dispensing again (for the next day)
        time.sleep(24 * 60 * 60)  # Wait for 24 hours (86400 seconds) before next dispensing

# Function to handle automatic dispensing
def automatic_dispense():
    global dispensing_active
    print("Automatic Medication Dispenser started...")

    # Send MQTT message to dispense medication once at 6 PM
    mqtt_client.publish(mqtt_topic_medication_command, "dispense", qos=1)
    print("Medication dispensed")

# Function to stop dispensing
def stop_automatic_dispense():
    global dispensing_active
    dispensing_active = False
    print("Automatic dispensing stopped!")

# Function to handle Medication message processing
def process_medication_message(response_medication):
    if 'Messages' in response_medication:
        message_medication = response_medication['Messages'][0]
        message_body_medication = message_medication['Body']
        receipt_handle_medication = message_medication['ReceiptHandle']
        
        
        try:
            # Parse the body of the message (which is typically JSON in SQS)
            parsed_message = json.loads(message_body_medication)
            
            actual_message = parsed_message.get('Message', '')
            
            if actual_message == "MANUAL":
                print("Received from FLASK server: Manual Dispense Medication")
                mqtt_client.publish(mqtt_topic_medication_command, "dispense", qos=1)
            elif actual_message == 'START_AUTOMATIC':
                global dispensing_active
                print("Received from FLASK server: Begin Automatic Dispense Medication")
                if not dispensing_active:
                    dispensing_active = True
                    dispensing_thread = threading.Thread(target=target_automatic_dispense)
                    dispensing_thread.start()
                else:
                    print("Automatic dispensing is already running.")
            elif actual_message == "STOP_AUTOMATIC":
                print("Received from FLASK server: Stop Automatic Dispense Medication")
                stop_automatic_dispense()
            
            # Delete the Medication message from the queue after processing
            sqs_client.delete_message(
                QueueUrl=queue_url_medication,
                ReceiptHandle=receipt_handle_medication
            )
        
        except json.JSONDecodeError as e:
            print(f"Error parsing message body as JSON: {e}")
    else:
        print("")

# Function to poll SQS and process messages
def poll_sqs():
    while True:
        # Poll Aircon Queue
        response_aircon = sqs_client.receive_message(
            QueueUrl=queue_url_aircon,
            AttributeNames=['All'],
            MaxNumberOfMessages=1,
            WaitTimeSeconds=5  # Long poll for up to 5 seconds
        )
        process_aircon_message(response_aircon)

        # Poll Medication Queue
        response_medication = sqs_client.receive_message(
            QueueUrl=queue_url_medication,
            AttributeNames=['All'],
            MaxNumberOfMessages=1,
            WaitTimeSeconds=5  # Long poll for up to 5 seconds
        )
        process_medication_message(response_medication)

# Main function to start MQTT loop and SQS polling
def main():
    # Start MQTT loop in a separate thread
    mqtt_thread = threading.Thread(target=mqtt_loop)
    mqtt_thread.daemon = True
    mqtt_thread.start()

    # Run the SQS polling loop
    poll_sqs()

# Run the main function
if __name__ == '__main__':
    main()
