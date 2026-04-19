#include <Arduino.h>
#include <STM32FreeRTOS.h>


#define frontRatio 1
#define middleRatio 0.4
#define backRatio 1


uint8_t leftFront[] = {PB1,PB10}; // MotorDriver1 {dir1,pwm1};
uint8_t leftBack[] = {PB2,PA8};

uint8_t leftMiddle[] = {PB14,PB5}; //MotorDriver2 {dir1,pwm1};
uint8_t rightMiddle[] = {PB15,PB4};

uint8_t rightFront[] = {PC4,PA10}; //MotorDriver3 {dir1,pwm1};
uint8_t rightBack[] = {PB13,PB3};


void setMotor(uint8_t motor[]) {
    pinMode(motor[0], OUTPUT);
    pinMode(motor[1], OUTPUT); 
}
void motorCtrl(uint8_t motor[], uint8_t dir, uint8_t pwm) {
    digitalWrite(motor[0], dir); // Set direction
    analogWrite(motor[1], pwm);  // Set speed (PWM)
}

void linear(int dir, int pwm){
    motorCtrl(leftFront, dir, pwm);
    motorCtrl(leftBack, dir, pwm);
    motorCtrl(leftMiddle, dir, pwm);

    motorCtrl(rightFront, dir, pwm);
    motorCtrl(rightBack, dir, pwm);
    motorCtrl(rightMiddle, dir, pwm);
}

void turn(int dir, int pwm){
    motorCtrl(leftFront, !dir, pwm*frontRatio);
    motorCtrl(leftBack, !dir, pwm*backRatio);
    motorCtrl(leftMiddle, !dir, pwm*middleRatio);
    
    motorCtrl(rightFront, dir, pwm*frontRatio);
    motorCtrl(rightBack, dir, pwm*backRatio);
    motorCtrl(rightMiddle, dir, pwm*middleRatio);
}


void ctrl(void *pvParameters) {
    while (true) {
        if (Serial.available() >= 2) {
            uint8_t command = (uint8_t)Serial.read(); // First byte is the command (direction)
            uint8_t speed = (uint8_t)Serial.read(); // Second byte is speed as an 8-bit integer
            
            Serial.print(command);
            Serial.print(" ");
            Serial.println(speed);
            // Control logic
            switch(command) {
                // Forward
                case 1:
                    linear(0, speed);
                    break;
                // Backward
                case 2:
                    linear(1, speed);
                    break;
                // Left turn
                case 3:
                    turn(0, speed);
                    break;
                // Right turn
                case 4:
                    turn(1, speed);
                    break;
                // Stop
                case 5:
                    linear(0, 0);
                    break;
            }
        }
    }
}

void print(void *pvParameters){
    while (true){
        Serial.println("drive");
        vTaskDelay(1000/ portTICK_PERIOD_MS);
    }
}


void setup() {
    setMotor(leftFront);
    setMotor(leftBack);
    setMotor(leftMiddle);
    setMotor(rightFront);
    setMotor(rightBack);
    setMotor(rightMiddle);
    Serial.begin(115200);

    xTaskCreate(ctrl, "Control", 1024, NULL, 1, NULL);
    xTaskCreate(print, "Prints Drive", 1024, NULL, 1, NULL);
    vTaskStartScheduler();
}

void loop() {}