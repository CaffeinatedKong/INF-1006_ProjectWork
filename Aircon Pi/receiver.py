import time
import pigpio

# GPIO Pin that the IR receiver is connected to
IR_PIN = 18  # Replace with your GPIO pin number

# Create a pigpio instance
pi = pigpio.pi()

if not pi.connected:
    print("Failed to connect to pigpio daemon!")
    exit()

# Set up the GPIO pin for input
pi.set_mode(IR_PIN, pigpio.INPUT)

# Function to capture the IR signal
def capture_signal(gpio, level, tick):
    print(f"Edge detected at {tick}")

# Register callback for detecting edges
pi.callback(IR_PIN, pigpio.EITHER_EDGE, capture_signal)

try:
    print("Press a button on your remote...")
    time.sleep(30)  # Wait for 30 seconds to capture the signal
except KeyboardInterrupt:
    print("Program interrupted")

pi.stop()
