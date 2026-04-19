#include <Arduino.h>
#include <SPI.h>
#include <Ethernet_Generic.h>
#include <daly-bms-uart.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

// ------------------- W5500 ETHERNET SETTINGS -------------------
#define W5500_CS 5
#define W5500_RST 4

byte mac[] = {0x02, 0x11, 0x22, 0x33, 0x44, 0x55};
IPAddress ip(192, 168, 1, 100);

// UDP server (PC)
IPAddress remoteIP(192, 168, 1, 7);
const uint16_t remotePort = 8888;

EthernetUDP udp;

// ------------------- DALY BMS SETTINGS -------------------
#define BMS_SERIAL Serial2
Daly_BMS_UART bms(BMS_SERIAL);

// ------------------- LCD SETTINGS -------------------
#define LCD_ADDR 0x27
#define LCD_COLS 16
#define LCD_ROWS 2

LiquidCrystal_I2C lcd(LCD_ADDR, LCD_COLS, LCD_ROWS);

// ------------------- TIMING -------------------
unsigned long lastUpdate = 0;
const unsigned long interval = 500; // ms

// ------------------- HARDWARE RESET -------------------
void resetW5500()
{
    pinMode(W5500_RST, OUTPUT);
    digitalWrite(W5500_RST, LOW);
    delay(100);
    digitalWrite(W5500_RST, HIGH);
    delay(500);
}

void setup()
{
    delay(2000);
    Serial.begin(115200);

    // ---- LCD INIT ----
    Wire.begin(21, 22);
    lcd.init();
    delay(500);
    lcd.backlight();
    lcd.setCursor(0, 0);
    lcd.print("Starting...");

    // ---- BMS INIT ----
    Serial.println("Initializing BMS...");
    bms.Init();

    // ---- ETHERNET INIT ----
    Serial.println("Initializing Ethernet...");
    resetW5500();

    SPI.begin(18, 19, 23, W5500_CS);
    Ethernet.init(W5500_CS);
    Ethernet.begin(mac, ip);

    udp.begin(8888);

    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("IP:");
    lcd.setCursor(0, 1);
    lcd.print(Ethernet.localIP());

    Serial.print("ESP32 Ready. IP: ");
    Serial.println(Ethernet.localIP());
}

void loop()
{
    if (millis() - lastUpdate >= interval)
    {
        lastUpdate = millis();

        // ---- UPDATE BMS ----
        bms.update();

        float voltage = bms.get.packVoltage;
        float current = bms.get.packCurrent;
        int soc = bms.get.packSOC;
        int temp = bms.get.tempAverage;

        // ---- UDP PACKET ----
        char dataPacket[128];

        snprintf(
            dataPacket,
            sizeof(dataPacket),
            "%.2f,%.2f,%.2f,%0.2f,%.3f,%.3f",
            bms.get.packVoltage,
            bms.get.packCurrent,
            bms.get.packSOC,
            bms.get.tempAverage,
            bms.get.maxCellmV / 1000.0,
            bms.get.minCellmV / 1000.0);

        udp.beginPacket(remoteIP, remotePort);
        udp.write((uint8_t *)dataPacket, strlen(dataPacket));
        udp.endPacket();

        // ---- LCD DISPLAY ----
        lcd.clear();

        char line1[17];
        char line2[17];

        snprintf(line1, sizeof(line1), "V:%5.1f I:%5.1f",
                 bms.get.packVoltage,
                 bms.get.packCurrent);

        snprintf(line2, sizeof(line2), "SOC:%0.1f%% T:%0.1fC",
                 bms.get.packSOC,
                 bms.get.tempAverage);

        lcd.setCursor(0, 0);
        lcd.print(line1);
        lcd.setCursor(0, 1);
        lcd.print(line2);

        // ---- SERIAL DEBUG ----
        Serial.println("Sent UDP:");
        Serial.println(dataPacket);
    }
}
