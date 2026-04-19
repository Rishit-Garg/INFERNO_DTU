#include <Arduino.h>
#include <Servo.h>
#include <AccelStepper.h>
#include <Ethernet_Generic.h>
#include <PID_v1.h>
#include <ESP32Encoder.h>

#define pi 3.141528
#define W5500_CS 5
#define W5500_RST 4
#define servo_pin 21
#define stepper_dir 14
#define stepper_step 27
#define encaPin 34
#define encbPin 35
#define encTurnCPR 781560

byte mac[] = {0x02, 0x11, 0x22, 0x33, 0x44, 0x55};
IPAddress ip(192, 168, 1, 103); // SCIENCE IP1 192.168.1.103

uint8_t pwmPin[] = {13, 25}; // pwm[0] for rotating hub
uint8_t dirPin[] = {12, 33};

// Instance Creation
Servo servo0;
AccelStepper stepper0(1, stepper_step, stepper_dir);
EthernetUDP udp;
const uint16_t localPort = 8888;
ESP32Encoder encoder0; // rotating assembly motor

double pos = 0;
double setPos = 0;

double pwm = 0;
double Kp = 0.0125, Ki = 0.2, Kd = 0.0;
PID motor0(&pos, &pwm, &setPos, Kp, Ki, Kd, DIRECT);

void resetW5500()
{
  pinMode(W5500_RST, OUTPUT);
  digitalWrite(W5500_RST, LOW);
  delay(100);
  digitalWrite(W5500_RST, HIGH);
  delay(500);
}

void setMotor(int motor_num, int pwm)
{
  if (pwm >= 0)
  {
    digitalWrite(dirPin[motor_num], LOW);
    analogWrite(pwmPin[motor_num], pwm);
  }
  else
  {
    digitalWrite(dirPin[motor_num], HIGH);
    analogWrite(pwmPin[motor_num], -pwm);
  }
}

void setup()
{
  delay(1000);
  Serial.begin(115200);

  for (int i = 0; i < 2; i++)
  {
    pinMode(dirPin[i], OUTPUT);
    pinMode(pwmPin[i], OUTPUT);
  }

  ESP32Encoder::useInternalWeakPullResistors = puType::up;

  encoder0.attachFullQuad(encaPin, encbPin);
  encoder0.clearCount();

  motor0.SetMode(AUTOMATIC);
  motor0.SetOutputLimits(-255, 255);

  servo0.attach(servo_pin);

  stepper0.setMaxSpeed(1000);
  stepper0.setAcceleration(50);
  stepper0.setSpeed(200);

  resetW5500(); // NOT MANDATORY

  SPI.begin(18, 19, 23, W5500_CS);
  Ethernet.init(W5500_CS);
  Ethernet.begin(mac, ip);

  Serial.print("ESP32 IP: ");
  Serial.println(Ethernet.localIP());

  udp.begin(localPort);
  Serial.println("UDP server listening...");
}

void loop()
{
  int packetSize = udp.parsePacket();
  if (packetSize)
  {
    char packetBuffer[128];
    int len = udp.read(packetBuffer, sizeof(packetBuffer) - 1);
    if (len > 0)
    {
      packetBuffer[len] = '\0';
    }

    Serial.print("Received: ");
    Serial.println(packetBuffer);

    float input[6] = {0}; //"{ANGLE(HUB)} {SPEED(PWM)} {ANGLE(SERVO)} {LEAD SCREW(mm)}"
    int count = 0;

    char *token = strtok(packetBuffer, " ");
    while (token != NULL && count < 6)
    {
      float val = atof(token);
      input[count] = val;
      count++;
      token = strtok(NULL, " ");
    }
    setPos = -2171 * input[0] * 180 / pi;
    pos = encoder0.getCount();
    if (setPos - pos > encTurnCPR / 360 || setPos - pos < -encTurnCPR / 360)
    {
      motor0.Compute();
      setMotor(0, pwm);
    }
    else
    {
      setMotor(0, 0);
    }
    setMotor(1, input[1]);
    servo0.write(input[2]);
    stepper0.moveTo(input[4] * 800);
    stepper0.run();
  }
}
