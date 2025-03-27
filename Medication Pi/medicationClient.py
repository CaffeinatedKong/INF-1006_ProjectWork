import paho.mqtt.client as mqtt
import time
import threading
import RPi.GPIO as GPIO
import time

# GPIO Pin Assignments
SERVO_PIN = 18      # Servo Motor (PWM)
BUZZER_PIN = 24     # Buzzer
LED_GREEN = 8       # Green LED
TRIG_PIN = 17       # Ultrasonic Trigger
ECHO_PIN = 27       # Ultrasonic Echo

# GPIO Setup
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

GPIO.setup(SERVO_PIN, GPIO.OUT)
GPIO.setup(BUZZER_PIN, GPIO.OUT)
GPIO.setup(LED_GREEN, GPIO.OUT)
GPIO.setup(TRIG_PIN, GPIO.OUT)
GPIO.setup(ECHO_PIN, GPIO.IN)

# Initialize PWM for Servo
servo_pwm = GPIO.PWM(SERVO_PIN, 50)  # 50 Hz
servo_pwm.start(0)

# MQTT Broker settings (Main Pi's IP or hostname)
mqtt_broker = "172.20.10.11"  # Replace with your Main Pi's IP or hostname
mqtt_port = 1883
mqtt_topic_command = "medication/dispenser"  # Topic for receiving commands (e.g., dispense)
mqtt_topic_status = "medication/status"  # Topic for sending status updates
mqtt_topic_servo_status = "servo/status"

# This will be called when the client connects to the broker
def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT Broker with result code " + str(rc))
    # Subscribe to the command topic (medication/dispenser)
    client.subscribe(mqtt_topic_command)

# This will be called when a message is received on the subscribed topic
def on_message(client, userdata, msg):
    print(f"Received MQTT message on {msg.topic}: {msg.payload.decode()}")
    if msg.topic == mqtt_topic_command:
        if msg.payload.decode() == "dispense":
            # Call the method to dispense medication
            print("Dispensing Medication...")
            dispense_medication()
            print("Sending Main Pi: Medication Dispensed Successful")
            print("Is medication picked up?")
            medication_picked_up = check_and_notify_medication_removal()
            if medication_picked_up:
                print("Sending Main Pi:Medication Picked Up")
                client.publish(mqtt_topic_servo_status,"Medication picked up by patient", qos=1)
            else:
                print("Sending Main Pi:Medication NOT Picked Up")
                client.publish(mqtt_topic_servo_status,"Medication NOT picked up by patient", qos=1)
            # After dispensing, send a status update back
            client.publish(mqtt_topic_status, "Medication dispensed successfully", qos=1)

def check_and_notify_medication_removal():
    # Start the timer
    start_time = time.time()

    # Wait for 8 seconds or until the medication is picked up
    while time.time() - start_time < 8:
        distance = measure_distance()
        if distance < 5:  # User picked up the medication (within 5 cm)
            GPIO.output(LED_GREEN, GPIO.LOW)  # Turn off the LED
            GPIO.output(BUZZER_PIN, GPIO.LOW)  # Turn off the buzz
            return  True # Exit the function when medication is picked up
    
    # If not picked up within 8 seconds, set medication_picked_up to False
    print("Medication NOT Picked up")
    GPIO.output(BUZZER_PIN, GPIO.LOW)  # Turn off the buzzer
    return False

# Measure distance using ultrasonic sensor
def measure_distance():
    GPIO.output(TRIG_PIN, False)
    time.sleep(0.1)

    GPIO.output(TRIG_PIN, True)
    time.sleep(0.00001)
    GPIO.output(TRIG_PIN, False)

    start_time = time.time()
    end_time = time.time()

    while GPIO.input(ECHO_PIN) == 0:
        start_time = time.time()
    while GPIO.input(ECHO_PIN) == 1:
        end_time = time.time()

    pulse_duration = end_time - start_time
    distance = pulse_duration * 17150  # in cm
    return round(distance, 2)



# Dispense medication logic
def dispense_medication():

    def move_servo_to_angle(angle):
        # Convert angle to duty cycle: 0° = 2, 180° = 12
        duty = 2 + (angle / 180) * 10
        servo_pwm.ChangeDutyCycle(duty)
        time.sleep(1)
        servo_pwm.ChangeDutyCycle(0)
        time.sleep(0.5)

    # Step through 45° → 90° → 135°
    for angle in [45, 90, 135]:
        move_servo_to_angle(angle)

    # Reset to 0°
    move_servo_to_angle(0)

    # Turn on buzzer and LED to alert user
    GPIO.output(LED_GREEN, GPIO.HIGH)
    GPIO.output(BUZZER_PIN, GPIO.HIGH)     
# Create MQTT client instance
client = mqtt.Client()
client.username_pw_set(username="user1",password="user1")
# Set the on_connect and on_message callback functions
client.on_connect = on_connect
client.on_message = on_message

# Connect to the MQTT broker (Main Pi)
client.connect(mqtt_broker, mqtt_port, 60)

# Start the MQTT client loop (in blocking mode, which will keep the program running)
client.loop_forever()
