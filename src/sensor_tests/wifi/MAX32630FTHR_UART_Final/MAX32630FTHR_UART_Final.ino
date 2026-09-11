/*
 * MAX32630FTHR -> NodeMCU sensor bridge (UART, push-based)
 *
 * No handshake, no request/response: this board just pushes a fresh
 * sensor reading over Serial2 every 2 seconds, unprompted. NodeMCU only
 * ever needs to listen and relay - removing the request/response
 * pattern removes the deadlock risk it had (both sides silently
 * waiting to hear from the other before speaking first).
 *
 * Builds on two things already confirmed working in this project:
 *  - Serial2's hardware genuinely initializes (UART_Init returns 0),
 *    once the debug console and Serial2 are matched to the same baud
 *    rate - this chip shares one clock divider across every UART.
 *  - Default Serial2 pins: P3_0 (RX), P3_1 (TX).
 */

void setup() {
  Serial.begin(9600);   // matches Serial2's baud - required, see note above
  Serial2.begin(9600);  // UART link to NodeMCU
  Serial.println("\nMAX32630FTHR UART bridge starting...");
}

float getSensorData() {
  // TEMPORARY, for verifying the pipeline end-to-end: an incrementing
  // counter instead of random(1000). A predictable, ever-increasing
  // sequence (1, 2, 3, 4...) is easy to visually match across the
  // MAX32630FTHR monitor, the NodeMCU monitor, and Firebase, with no
  // ambiguity about whether what you're looking at lines up - unlike
  // random values, where three separately-scrolling views with no
  // shared timestamp are genuinely hard to eyeball-correlate even when
  // everything is working correctly. Swap back to a real sensor (or
  // back to random(1000) for testing) once you've confirmed the chain.
  static int counter = 0;
  counter++;
  return counter;
}

void loop() {
  float value = getSensorData();
  char msg[32];
  sprintf(msg, "%.2f", value); // sprintf %f confirmed safe on this core (full newlib link)

  Serial2.println(msg);

  Serial.print("Sent: ");
  Serial.println(msg);

  delay(2000); // how often to push a fresh reading
}
