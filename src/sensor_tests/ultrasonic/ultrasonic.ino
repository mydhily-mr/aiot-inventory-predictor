
/*
 * // HC-SR04 Ultrasonic Distance Sensor — MAX32630FTHR, ADI/Maxim Arduino core

 * // HC SR-04 Ultrasonic — MAX32630FTHR, ADI/Maxim Arduino core
 * Important wiring caution: the HC-SR04 is normally powered at 5V and its ECHO pin 
 * outputs a 5V pulse. The MAX32630FTHR's header GPIOs are only 3.3V/1.8V tolerant — feeding 
 * ECHO straight into P4_0 can damage that pin. Use a simple voltage divider on the ECHO line before it reaches P4_0, e.g.:
 * ECHO → 1kΩ resistor → P4_0
 * P4_0 → 2kΩ resistor → GND
 * 
 * That divides 5V down to ~3.3V, which is safe for the pin. 
 * TRIG is fine directly since it's an output from the board (3.3V logic is typically enough to trigger the sensor).
 * 
 *  *** RYG LED ***
   Connections:
   Ultrasonic       MACX32630 FTHR
   GND          -   GND
   VCC          -   3V3 
   ECHO         -   P4_0 
   TRIG         -   P5_6
   

 */

 
#define TRIG_PIN P5_6
#define ECHO_PIN P4_0

void setup() {
  Serial.begin(9600);

  useVDDIOH(TRIG_PIN);
  useVDDIOH(ECHO_PIN);

  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);

  digitalWrite(TRIG_PIN, LOW);
}

void loop() {
  // Send a 10us trigger pulse
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  // Measure echo pulse width (timeout ~25ms ≈ 4m range, avoids hanging if no echo)
  long duration = pulseIn(ECHO_PIN, HIGH, 25000);

  if (duration == 0) {
    Serial.println("No echo received (out of range or no object)");
  } else {
    // distance(cm) = duration(us) / 58  →  speed of sound ≈ 343 m/s
    float distanceCm = duration / 58.0;
    Serial.print("Distance: ");
    Serial.print(distanceCm);
    Serial.println(" cm");
  }

  delay(500); // small gap between readings
}
