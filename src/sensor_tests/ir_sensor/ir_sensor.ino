 /*    // IR Obstacle/Proximity Sensor — detect state changes only
  
  *    
  *    *  *** IR Sensor ***
   Connections:
   IR Sensor         MACX32630 FTHR
   GND             -   GND
   VCC             -   3V3 
   SIG             -   P3_3 

  Note: The module i used is active-HIGH (HIGH = object detected, LOW = clear)

   Note: These modules have a small trimmer pot to adjust detection distance/sensitivity. 
   If it's turned too far, it can trigger constantly even with nothing in range (picking up ambient IR
   or its own reflected light off nearby surfaces). Try turning it (usually counter-clockwise) to reduce sensitivity, 
   and watch the module's own onboard LED (most have one) — it lights up whenever the module itself thinks it's 
   detecting something, independent of your code. If that LED is always on, it's a hardware/sensitivity issue, not a code issue.


   */
#define IR_PIN P3_3

int lastState = LOW; // assume "no object" at start

void setup() {
  Serial.begin(9600);

  useVDDIOH(IR_PIN);
  pinMode(IR_PIN, INPUT);

  lastState = digitalRead(IR_PIN);
}

void loop() {
  int currentState = digitalRead(IR_PIN);

  if (currentState != lastState) {
    if (currentState == HIGH) {
      Serial.println("Hand/Object detected!");
    } else {
      Serial.println("Object removed / No object");
    }
    lastState = currentState;
  }

  delay(50); // small debounce delay
}
