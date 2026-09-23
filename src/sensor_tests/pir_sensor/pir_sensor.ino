/* PIR Motion Sensor — MAX32630FTHR, ADI/Maxim Arduino core
 *  
 *  
 *   *    *  *** PIR Sensor ***
   Connections:
   PIR Sensor         MACX32630 FTHR
   VCC             -   VBUS (5V)
   GND             -   GND 
   OUT             -   1kΩ resistor 
 1kΩ resistor jn   -   P3_2
 1kΩ resistor last end - GND
   
                 PIR Module
              ┌─────────────┐
   5V (VBUS)──┤ VCC         │
       GND────┤ GND         │
              │         OUT ├───┐
              └─────────────┘   │
                                 │
                              1kΩ resistor
                                 │
                                 ├────────── P3_2 (to board)
                                 │
                              1kΩ resistor
                                 │
                                GND
   
 */
#define PIR_PIN P3_2

int lastState = LOW; // assume "no motion" at start

void setup() {
  Serial.begin(9600);

  useVDDIOH(PIR_PIN);
  pinMode(PIR_PIN, INPUT);

  Serial.println("PIR warming up...");
  delay(30000); // PIR sensors need ~30-60s to stabilize after power-up
  Serial.println("PIR ready");

  lastState = digitalRead(PIR_PIN);
}

void loop() {
  int currentState = digitalRead(PIR_PIN);

  if (currentState != lastState) {
    if (currentState == HIGH) {
      Serial.println("Motion detected!");
    } else {
      Serial.println("Motion stopped");
    }
    lastState = currentState;
  }

  delay(50);
}
