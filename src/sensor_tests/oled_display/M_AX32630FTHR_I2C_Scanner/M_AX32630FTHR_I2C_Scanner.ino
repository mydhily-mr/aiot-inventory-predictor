/*
 * MAX32630FTHR - I2C bus scanner
 *
 * Run this first, before anything else, to confirm I2C hardware and
 * wiring are working. Prints the address of every device that responds
 * on the bus. An SSD1306 OLED will typically show up as 0x3C or 0x3D.
 */

#include <Wire.h>

void setup() {
  Serial.begin(115200);
  while (!Serial) { delay(10); }
  Serial.println("\nMAX32630FTHR I2C scanner starting...");

  Wire.begin(); // master mode, default pins (SDA = pin 28, SCL = pin 29)
}

void loop() {
  Serial.println("Scanning...");
  int found = 0;

  for (uint8_t addr = 1; addr < 127; addr++) {
    Wire.beginTransmission(addr);
    uint8_t result = Wire.endTransmission();
    if (result == 0) {
      Serial.print("  Found device at address 0x");
      if (addr < 16) Serial.print("0");
      Serial.println(addr, HEX);
      found++;
    }
  }

  if (found == 0) {
    Serial.println("  No devices found - check wiring and pull-up resistors");
  } else {
    Serial.print(found);
    Serial.println(" device(s) found");
  }

  delay(3000);
}
