# drive_uc

This project controls six motors using PWM signals, with commands sent over a serial interface. The system operates on a **skid-steering mechanism**, where motors are grouped into left and right sides. Each motor driver controls two motors.

The system also prints the status "drive" to the serial monitor every 1 second to indicate port.

## Features
- Control of 6 motors using PWM signals (skid steering).
- Data transferred via serial commands.
- Prints "drive" to the serial monitor every second.
- The first byte in the command represents the motor direction.
- The second byte in the command represents the motor speed (PWM value).

### Motor Pin Configuration
- **Left Motors**:
  - `leftFront`: {PB1, PB10} (MotorDriver1: {dir1, pwm1})
  - `leftBack`: {PB2, PA8} (MotorDriver1: {dir2, pwm2})
  - `leftMiddle`: {PB14, PB5} (MotorDriver2: {dir1, pwm1})

- **Right Motors**:
  - `rightMiddle`: {PB15, PB4} (MotorDriver2: {dir2, pwm2})
  - `rightFront`: {PC4, PA10} (MotorDriver3: {dir1, pwm1})
  - `rightBack`: {PB13, PB3} (MotorDriver3: {dir2, pwm2})

## Serial Command Format
Commands are received over the serial interface to control the motors. The format for the command is:
- `{direction}{pwm}`

Where:
- **direction** is a single byte (1-5):
  - `1` = forward
  - `2` = backward
  - `3` = left
  - `4` = right
  - `5` = stop
- **pwm** is a full 8-bit number (0-255) representing the motor speed.