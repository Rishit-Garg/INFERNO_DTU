import pygame
import serial
import time

# ---------- SERIAL CONFIG ----------
PORT = "/dev/ttyUSB0"   # Linux
# PORT = "COM5"         # Windows
BAUD = 115200

ser = serial.Serial(PORT, BAUD, timeout=1)
time.sleep(2)

# ---------- PYGAME INIT ----------
pygame.init()
pygame.joystick.init()

if pygame.joystick.get_count() == 0:
    raise RuntimeError("No joystick detected")

joy = pygame.joystick.Joystick(0)
joy.init()

print("Joystick:", joy.get_name())
print("ESP32 connected")
nums = [0] * 6
def map_axis(val):
    # Axis is -1.0 to +1.0 → map to 0–255
    return int(val*255)

def setState(xData, yData):
    if xData:
        nums[0] = xData
        nums[1] = xData
        nums[2] = xData
        nums[3] = xData
        nums[4] = xData
        nums[5] = xData
    
    elif yData :
        nums[0] = yData
        nums[1] = yData
        nums[2] = yData
        nums[3] = -yData
        nums[4] = -yData
        nums[5] = -yData
    else:
        nums[0] = 0
        nums[1] = 0
        nums[2] = 0
        nums[3] = 0
        nums[4] = 0
        nums[5] = 0
    payload = "<" + " ".join(map(str, nums)) + ">"

    ser.write(payload.encode())
    print("Sent:", payload.strip())


while True:
    pygame.event.pump()

    

    # -------- AXES (example) --------
    
    setState(map_axis(joy.get_axis(0)), map_axis(joy.get_axis(4)))
    time.sleep(0.1)  # 20 Hz update