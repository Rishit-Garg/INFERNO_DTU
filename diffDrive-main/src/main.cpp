#include <Arduino.h>
#include <PID_v1.h>
#include <STM32FreeRTOS.h>


// Constants
#define pi 3.14
#define ENCPR 1320 // not correct
#define WHEEL_RADIUS 0.12


double setWl = 0;
double setWr = 0;


uint32_t dirPins[6] = {PB1, PB14, PB2, PC4, PB15, PB13};
uint32_t pwmPins[6] = {PB10, PB5, PA8, PA10, PB4, PB3};


void setMotor(int i, int pwm){
    if(pwm >= 0){
        digitalWrite(dirPins[i], LOW);
        analogWrite(pwmPins[i], pwm);
    }
    else{
        digitalWrite(dirPins[i], HIGH);
        analogWrite(pwmPins[i], -pwm);
    }
}



// Encoder Pin definitions
uint32_t encaPins[6]={PC10, PC7, PC12, PC5, PC6, PC8};
uint32_t encbPins[6]={PD2, PA13, PA14, PA15, PB7, PA0};

// Encoder Data
volatile long tickCount[6] = {0};
volatile long pos[6] = {0};
double tps[6] = {0};
unsigned long prevT = 0;

// Encoder Read Functions
void readEncoder(int i) {
    int b = digitalRead(encbPins[i]);
    int increment = (b > 0) ? 1 : -1;
    pos[i] += increment;
    tickCount[i] += increment;
}   
void readEncoder0(){readEncoder(0);}
void readEncoder1(){readEncoder(1);}
void readEncoder2(){readEncoder(2);}
void readEncoder3(){readEncoder(3);}
void readEncoder4(){readEncoder(4);}
void readEncoder5(){readEncoder(5);}


// PID
double pwm[6] = {0};
double setTps[6];
double Kp = 0.025, Ki = 0.2, Kd = 0.0;

PID motor0(&tps[0], &pwm[0], &setTps[0], Kp, Ki, Kd, DIRECT);
PID motor1(&tps[1], &pwm[1], &setTps[1], Kp, Ki, Kd, DIRECT);
PID motor2(&tps[2], &pwm[2], &setTps[2], Kp, Ki, Kd, DIRECT);
PID motor3(&tps[3], &pwm[3], &setTps[3], Kp, Ki, Kd, DIRECT);
PID motor4(&tps[4], &pwm[4], &setTps[4], Kp, Ki, Kd, DIRECT);
PID motor5(&tps[5], &pwm[5], &setTps[5], Kp, Ki, Kd, DIRECT);


void ctrl(void *pvParameters){
    while (true){
        // Update tps of every motor
        unsigned long currT = millis();
        if (currT - prevT >= 10){ // every 10 ms
            noInterrupts();
            long ticks[6];
            for (int i = 0; i < 6; i++){
                ticks[i] = tickCount[i];
                tickCount[i] = 0; 
            }
            interrupts();


            double dt = (currT - prevT) / 1000.0;
            prevT = currT;
            for (int i = 0; i < 6; i++){
                tps[i] = ticks[i] / dt; // ticks/sec
            }

            for (int i = 0; i < 6; i++){
                if (i < 3){setTps[i] = setWl*ENCPR/(2*pi);}
                else{setTps[i] = setWr*ENCPR/(2*pi);}
            }
            

            // Computes the output for motors
            motor0.Compute();
            motor1.Compute();
            motor2.Compute();
            motor3.Compute();
            motor4.Compute();
            motor5.Compute();

            for(int i = 0; i < 6; i++){
                setMotor(i, pwm[i]);
            }

        }
    }    
}


void logic(void *pvParameters){
    while (true){
        if (Serial.available()) {
            String msg = Serial.readStringUntil('>');
            
            if (msg.startsWith("<")) {
                float left, right;
                

                int spaceIndex = msg.indexOf(' ');
                String numStr = msg.substring(1, spaceIndex);
                left = numStr.toFloat();
                numStr = msg.substring(spaceIndex+1, msg.length()
            );
                right = numStr.toFloat();

                Serial.println(msg);
                Serial.println(right);

                setWl = left;
                setWr = -right;
            }
        }
        vTaskDelay(10/portTICK_PERIOD_MS);
    }
}


void setup(){
    delay(1000);
    Serial.begin(115200);

    // PinMode Setup
    for (int i = 0; i < 6; i++){
        pinMode(dirPins[i], OUTPUT);
        pinMode(pwmPins[i], OUTPUT);
        pinMode(encaPins[i], INPUT_PULLUP);
        pinMode(encbPins[i], INPUT_PULLUP);
    }
    // Encoder Interrupts
    attachInterrupt(digitalPinToInterrupt(encaPins[0]), readEncoder0, RISING);
    attachInterrupt(digitalPinToInterrupt(encaPins[1]), readEncoder1, RISING);
    attachInterrupt(digitalPinToInterrupt(encaPins[2]), readEncoder2, RISING);
    attachInterrupt(digitalPinToInterrupt(encaPins[3]), readEncoder3, RISING);
    attachInterrupt(digitalPinToInterrupt(encaPins[4]), readEncoder4, RISING);
    attachInterrupt(digitalPinToInterrupt(encaPins[5]), readEncoder5, RISING);


    motor0.SetMode(AUTOMATIC);
    motor1.SetMode(AUTOMATIC);
    motor2.SetMode(AUTOMATIC);
    motor3.SetMode(AUTOMATIC);
    motor4.SetMode(AUTOMATIC);
    motor5.SetMode(AUTOMATIC);
    
    // Output
    motor0.SetOutputLimits(-255, 255);
    motor1.SetOutputLimits(-255, 255);
    motor2.SetOutputLimits(-255, 255);
    motor3.SetOutputLimits(-255, 255);
    motor4.SetOutputLimits(-255, 255);
    motor5.SetOutputLimits(-255, 255);

    xTaskCreate(ctrl, "Control", 10000, NULL, 1, NULL);
    xTaskCreate(logic, "Logic", 10000, NULL, 1, NULL);
    vTaskStartScheduler();   
}

void loop(){}