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

// --- Buzzer alert config ---
#define BUZZER_PIN P5_3
void setup() {
  Serial.begin(9600);
  useVDDIOH(BUZZER_PIN);
  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, LOW);
  delay(2000);
}

void loop() {
  Serial.println("Buzzer ON");
  digitalWrite(BUZZER_PIN, HIGH);
  delay(5000);

  digitalWrite(BUZZER_PIN, LOW);
  Serial.println("Buzzer OFF - should be dead silent now for 10s");
  delay(10000); // long, obvious silent gap - listen closely here
}
