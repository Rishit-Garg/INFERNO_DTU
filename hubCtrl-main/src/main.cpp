#include <Arduino.h>
#include <PID_v1.h>
#include <ESP32Encoder.h>
#include <Wire.h>

#define pi 3.14159

#define encTurnCPR 781560
#define encMotionCPR 5281


// For Communication with Master
#define I2C_SDA 21
#define I2C_SCL 22
#define SLAVE_ADDR 0x14
#define BUFFER_SIZE 10

bool flag = true;

char vel[BUFFER_SIZE] = {};
char ang[BUFFER_SIZE] = {};
int vel_idx = 0;
int ang_idx = 0;


// Pin Definitions
uint32_t encaPins[2] = {4, 18};
uint32_t encbPins[2] = {2, 5};
// Create encoder objects
ESP32Encoder encoder0;
ESP32Encoder encoder1;


// Motor Control Dfinitions
uint32_t dirPins[2] = {27, 12};
uint32_t pwmPins[2] = {14,13};

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


// PID
// Turning
double pos = 0;
double setPos = 0;
float theta = 0; // Angle for Motor 0

// Motion
double tps = 0;
double setTps = 0;
long prevTicks = 0;
unsigned long prevTime = 0;
float omega = 0; // Angular Velocity for Motor 1

double pwm[2] = {0};
double Kpt = 0.005, Kit = 0.0, Kdt = 0.0;
double Kp = 0.0125, Ki = 0.2, Kd = 0.0;

PID motor0(&pos, &pwm[0], &setPos, Kpt, Kit, Kdt, DIRECT);
PID motor1(&tps, &pwm[1], &setTps, Kp, Ki, Kd, DIRECT);



void onReceive(int len) {
    vel_idx = 0;
    ang_idx = 0;
    flag = true;

    while (Wire.available()) {
        char rxValue = Wire.read();

        if (rxValue == '\n' || rxValue == '\r') {
            continue; // Skip newline characters
        }

        if (rxValue != ' ') {
            if (flag) {
                if (vel_idx < BUFFER_SIZE - 1) {
                    vel[vel_idx++] = rxValue;
                }
            }
            else {
                if (ang_idx < BUFFER_SIZE - 1) {
                    ang[ang_idx++] = rxValue;
                }
            }
        }
        else {
            flag = !flag;
        }
    }

    vel[vel_idx] = '\0';
    ang[ang_idx] = '\0';

    if (vel_idx > 0) {
        omega = atof(vel);
        setTps = (omega*encMotionCPR)/(2*pi);
        Serial.println(omega);
    }
    if (ang_idx > 0) {
        theta = atof(ang);
        setPos = -2171*theta*180/pi;
        Serial.println(theta);
    }
}


void setup(){
    delay(1000);
    Serial.begin(115200);

    // I2C
    Wire.setPins(I2C_SDA, I2C_SCL); // Set custom I2C pins first
    Wire.begin(SLAVE_ADDR);         // Initialize as I2C slave at address 0x08
    Wire.onReceive(onReceive);
    
    // PinMode Setup
    for (int i = 0; i < 2; i++){
        pinMode(dirPins[i], OUTPUT);
        pinMode(pwmPins[i], OUTPUT);
    }
    // Enable the weak pull resistors
    ESP32Encoder::useInternalWeakPullResistors = puType::up;

    // Attach pins for Encoder
    encoder0.attachFullQuad(encaPins[0], encbPins[0]);
    encoder0.clearCount();
    encoder1.attachFullQuad(encaPins[1], encbPins[1]);
    encoder1.clearCount();


    // PID setup
    motor0.SetMode(AUTOMATIC);
    motor1.SetMode(AUTOMATIC);

    motor0.SetOutputLimits(-255, 255);
    motor1.SetOutputLimits(-255, 255);

    //xTaskCreate(ctrl, "Control", 1024, NULL, 1, NULL);
    prevTime = millis();
}


void loop(){
    unsigned long now = millis();
    if (now-prevTime >= 10){
        // Motor 1
        long currentTicks = encoder1.getCount();
        long deltaTicks = currentTicks - prevTicks;
        float deltaTimeSec = (now - prevTime) / 1000.0;

        tps = deltaTicks / deltaTimeSec;

        motor1.Compute();
        setMotor(1, pwm[1]);
        
        // Motor 0
        pos = encoder0.getCount();
        if(setPos-pos > encTurnCPR/360 || setPos-pos < -encTurnCPR/360){
            motor0.Compute();
            setMotor(0, pwm[0]);
        }
        else{
            setMotor(0, 0);
        }

        prevTicks = currentTicks;
        prevTime = now;
    }
}