/*
 * MAX32630FTHR - SSD1306 OLED "Hello World"
 *
 * Requires: Adafruit SSD1306, Adafruit GFX Library, Adafruit BusIO
 * (install all three via Arduino IDE's Library Manager).
 *
 * Wiring: SSD1306 VCC -> 3.3V, GND -> GND, SDA -> pin 28, SCL -> pin 29.
 * Needs pull-up resistors on SDA/SCL (4.7k-10k to 3.3V) if your board
 * doesn't already have them.
 *
 * If nothing shows up: run MAX32630FTHR_I2C_Scanner.ino first to confirm
 * the display is actually responding on the bus, and to find its real
 * address if it's not the common default (0x3C) assumed below.
 * 
 * OLED       MAX32630 (Arduino pins 28/29.)
 * GND        GND
 * VCC        3V3
 * SDA        P3_4
 * SCL        P3_5
 * 
 */

#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64      // change to 32 if you have a 128x32 display instead
#define OLED_ADDR 0x3C        // common default - change if the scanner found a different address (e.g. 0x3D)

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1); // -1 = no dedicated reset pin

void setup() {
  Serial.begin(9600);
  while (!Serial) { delay(10); }
  Serial.println("\nMAX32630FTHR SSD1306 example starting...");

  Wire.begin(); // master mode, default pins (SDA = pin 28, SCL = pin 29)

  if (!display.begin(SSD1306_SWITCHCAPVCC, OLED_ADDR)) {
    Serial.println("SSD1306 not found - check wiring/address, or run the I2C scanner");
    while (true) { delay(1000); } // halt here rather than continue with a display that isn't there
  }

  display.clearDisplay();
  display.setTextSize(2);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(10, 25);
  display.println("Hello World123");
  display.display(); // nothing appears on the screen until this is called
}

void loop() {
  // Hello World is static - nothing to update here.
}
