/*
   MAX32630FTHR -> NodeMCU sensor bridge (UART, push-based)

   No handshake, no request/response: this board just pushes a fresh
   sensor reading over Serial2 every 2 seconds, unprompted. NodeMCU only
   ever needs to listen and relay - removing the request/response
   pattern removes the deadlock risk it had (both sides silently
   waiting to hear from the other before speaking first).

   Builds on two things already confirmed working in this project:
    - Serial2's hardware genuinely initializes (UART_Init returns 0),
      once the debug console and Serial2 are matched to the same baud
      rate - this chip shares one clock divider across every UART.
    - Default Serial2 pins: P3_0 (RX), P3_1 (TX).

 *     *** Load Sensor ***
   Connections:
   HX711            Aries Board
   VCC          -   3.3V
   GND          -   GND
   Dout         -   P5_5 (pin 45 in software)
   sck          -   P5_4 (pin 44 in software)
*/



#include <HX711_ADC.h> //weight sensor 


//weight sensor pins:
const int HX711_dout = 45; //Connect dout of sensor to GPIO-2 of aries board
const int HX711_sck = 44; //Connect dout of sensor to GPIO-3 of aries board

//HX711 constructor:
HX711_ADC LoadCell(HX711_dout, HX711_sck);

unsigned long t = 0;

void hx711_setup() {
  //weight sensor
  float calibrationValue; // calibration value
  calibrationValue = 530.0; // we need to calculate this before to get correct weight measurement

  LoadCell.begin();
  unsigned long stabilizingtime = 2000; // tare preciscion can be improved by adding a few seconds of stabilizing time
  boolean _tare = true; //set this to false if you don't want tare to be performed in the next step
  LoadCell.start(stabilizingtime, _tare);
  if (LoadCell.getTareTimeoutFlag()) {
    Serial.println("Timeout, check MCU>HX711 wiring and pin designations");
  }
  else {
    LoadCell.setCalFactor(calibrationValue); // set calibration factor (float)
    Serial.println("Startup is complete");
  }

  while (!LoadCell.update());
  Serial.print("Calibration value: ");
  Serial.println(LoadCell.getCalFactor());
  Serial.print("HX711 measured conversion time ms: ");
  Serial.println(LoadCell.getConversionTime());
  Serial.print("HX711 measured sampling rate HZ: ");
  Serial.println(LoadCell.getSPS());
  Serial.print("HX711 measured settlingtime ms: ");
  Serial.println(LoadCell.getSettlingTime());
  Serial.println("Note that the settling time may increase significantly if you use delay() in your sketch!");
  if (LoadCell.getSPS() < 7) {
    Serial.println("!!Sampling rate is lower than specification, check MCU>HX711 wiring and pin designations");
  }
  else if (LoadCell.getSPS() > 100) {
    Serial.println("!!Sampling rate is higher than specification, check MCU>HX711 wiring and pin designations");
  }
}


float getSensorData() {
  float weight;
  // TEMPORARY, for verifying the pipeline end-to-end: an incrementing
  // counter instead of random(1000). A predictable, ever-increasing
  // sequence (1, 2, 3, 4...) is easy to visually match across the
  // MAX32630FTHR monitor, the NodeMCU monitor, and Firebase, with no
  // ambiguity about whether what you're looking at lines up - unlike
  // random values, where three separately-scrolling views with no
  // shared timestamp are genuinely hard to eyeball-correlate even when
  // everything is working correctly. Swap back to a real sensor (or
  // back to random(1000) for testing) once you've confirmed the chain.
  //static int counter = 0;
  //counter++;
  //return counter;

  static boolean newDataReady = 0;
  const int serialPrintInterval = 500; //increase value to slow down serial print activity

  // check for new data/start next conversion:
  if (LoadCell.update())
    newDataReady = true;

  // get smoothed value from the dataset:
  if (newDataReady) {
    if (millis() > t + serialPrintInterval) {
      weight = LoadCell.getData();
      Serial.print("Load_cell output val: ");
      Serial.println(weight);
      newDataReady = 0;
      t = millis();
    }
  }

  // receive command from serial terminal, send 't' to initiate tare operation:
  if (Serial.available() > 0) {
    char inByte = Serial.read();
    if (inByte == 't') LoadCell.tareNoDelay();
  }

  // check if last tare operation is complete:
  if (LoadCell.getTareStatus() == true) {
    Serial.println("Tare complete");
  }

  return weight;
}

void setup() {
  Serial.begin(9600);   // matches Serial2's baud - required, see note above
  Serial2.begin(9600);  // UART link to NodeMCU
  Serial.println("\nMAX32630FTHR UART bridge starting...");
  hx711_setup();

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
