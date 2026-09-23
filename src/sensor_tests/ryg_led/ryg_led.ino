/*
 * // RYG LED blink — MAX32630FTHR, ADI/Maxim Arduino core

 *  *** RYG LED ***
   Connections:
   HX711            MACX32630 FTHR
   GND          -   GND
   R            -   P5_0 
   Y            -   P5_1 
   G            -   P5_2
   

 */
#define LED_RED    P5_0
#define LED_YELLOW P5_1
#define LED_GREEN  P5_2

void setup() {
  // Puts these pins on the VDDIOH rail (3.3V, via the on-board LDO2).
  // It's the default on this core, but set it explicitly in case these
  // pins came up on VDDIO (1.8V) instead.
  useVDDIOH(LED_RED);
  useVDDIOH(LED_YELLOW);
  useVDDIOH(LED_GREEN);

  pinMode(LED_RED, OUTPUT);
  pinMode(LED_YELLOW, OUTPUT);
  pinMode(LED_GREEN, OUTPUT);
}

void loop() {
  digitalWrite(LED_RED, HIGH);
  digitalWrite(LED_YELLOW, HIGH);
  digitalWrite(LED_GREEN, HIGH);
  delay(1000);

  digitalWrite(LED_RED, LOW);
  digitalWrite(LED_YELLOW, LOW);
  digitalWrite(LED_GREEN, LOW);
  delay(1000);
}
