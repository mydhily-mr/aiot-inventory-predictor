/* Piezo Buzzer Beep — MAX32630FTHR, ADI/Maxim Arduino core
 *  
 *   *  *** Piezo Buzzer ***
   Connections:
   Piezo Buzzer       MACX32630 FTHR
   GND             -   GND
   VCC             -   3V3 
   SIG             -   P5_3 
 */
#define BUZZER_PIN P5_3

void setup() {
  useVDDIOH(BUZZER_PIN);
  pinMode(BUZZER_PIN, OUTPUT);
}

void loop() {
  tone(BUZZER_PIN, 2000);  // 2kHz tone
  delay(200);              // beep duration
  noTone(BUZZER_PIN);

  delay(2000);             // gap before next beep
}
