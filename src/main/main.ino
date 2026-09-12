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

// --- inventory calibration for THIS bin (fill these in) ---
const float containerTareGrams = 31.0;   // weight of the empty reel/box, measured once
const float weightPerPiece     = 0.18;   // grams per single component, measured once
// ------------------------------------------------------------

//HX711 constructor:
HX711_ADC LoadCell(HX711_dout, HX711_sck);

unsigned long t = 0;  // paces the load-cell debug print
unsigned long lastSendTime = 0;
const unsigned long sendInterval = 2000; // how often to push over Serial2
float latestWeight = 0; // cached, updated by getSensorData() every loop pass

void hx711_setup() {
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
  //float weight;
  static boolean newDataReady = 0;
  const int serialPrintInterval = 500; //increase value to slow down serial print activity

  // check for new data/start next conversion:
  if (LoadCell.update())
    newDataReady = true;

  // get smoothed value from the dataset:
  if (newDataReady) {
    if (millis() > t + serialPrintInterval) {
      latestWeight = LoadCell.getData();
      Serial.print("Load_cell output val: ");
      Serial.println(latestWeight);
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

  return latestWeight;
}

// -- when you add sensor #2, follow this exact shape --
// float latestOtherValue = 0;
// float getOtherSensorData() {
//   // poll its hardware here, cache into latestOtherValue, return it
//   // must NOT contain any delay() of its own
//   return latestOtherValue;
// }


void setup() {
  Serial.begin(9600);   // matches Serial2's baud - required, see note above
  Serial2.begin(9600);  // UART link to NodeMCU
  Serial.println("\nMAX32630FTHR UART bridge starting...");
  hx711_setup();

}


void loop() {
  getSensorData();          // poll load cell - every pass, no delay
  // getOtherSensorData();  // <- next sensor goes here, same way

  if (millis() - lastSendTime >= sendInterval) {
    lastSendTime = millis();

    long pieceCount = (long)((latestWeight - containerTareGrams) / weightPerPiece);
    if (pieceCount < 0) pieceCount = 0;

    char msg[32];
    sprintf(msg, "%ld", pieceCount); // extend this line later to include other sensors

    Serial2.println(msg);
    Serial.print("Sent: ");
    Serial.println(msg);
  }
}
