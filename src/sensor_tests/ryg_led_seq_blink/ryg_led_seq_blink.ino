/*
 * // RYG LED sequential blink — MAX32630FTHR, ADI/Maxim Arduino core
  Note: All port pins labeled Pn_n are capable of GPIO and PWM.(https://www.analog.com/media/en/technical-documentation/data-sheets/MAX32630FTHR.pdf )
 *  *** RYG LED ***
   Connections:
   HX711            MACX32630 FTHR
   GND          -   GND
   R            -   P5_0 
   Y            -   P5_1 
   G            -   P5_2
   

 */
// RYG LED sequential blink — MAX32630FTHR, ADI/Maxim Arduino core
#define LED_RED    P5_0
#define LED_YELLOW P5_1
#define LED_GREEN  P5_2

void setup() {
  useVDDIOH(LED_RED);
  useVDDIOH(LED_YELLOW);
  useVDDIOH(LED_GREEN);

  pinMode(LED_RED, OUTPUT);
  pinMode(LED_YELLOW, OUTPUT);
  pinMode(LED_GREEN, OUTPUT);

  // start with all off
  digitalWrite(LED_RED, LOW);
  digitalWrite(LED_YELLOW, LOW);
  digitalWrite(LED_GREEN, LOW);
}

void loop() {
  digitalWrite(LED_RED, HIGH);
  delay(1000);
  digitalWrite(LED_RED, LOW);

  digitalWrite(LED_YELLOW, HIGH);
  delay(1000);
  digitalWrite(LED_YELLOW, LOW);

  digitalWrite(LED_GREEN, HIGH);
  delay(1000);
  digitalWrite(LED_GREEN, LOW);
}
