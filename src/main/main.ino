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

 *     *** OLED (SSD1306) ***
   Requires: Adafruit SSD1306, Adafruit GFX Library, Adafruit BusIO
   OLED       MAX32630 (Arduino pins 28/29)
   GND        GND
   VCC        3V3
   SDA        P3_4
   SCL        P3_5

 *     *** Ultrasonic (HC-SR04) ***
   Important: ECHO outputs 5V - use a voltage divider (ECHO -> 1k -> P4_0,
   P4_0 -> 2k -> GND) before connecting to the board. TRIG is fine direct.
   GND          -   GND
   VCC          -   3V3
   ECHO         -   P4_0
   TRIG         -   P5_6

 *     *** IR Sensor ***
   Active-HIGH module (HIGH = object detected, LOW = clear).
   Used here to estimate picks: on hand-arrival we snapshot the weight;
   on hand-departure we wait for the scale to settle, then the weight
   drop / weightPerPiece gives an estimated pick quantity.
   GND          -   GND
   VCC          -   3V3
   SIG          -   P3_3
*/



#include <HX711_ADC.h> //weight sensor 
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>


//weight sensor pins:
const int HX711_dout = 45; //Connect dout of sensor to GPIO-2 of aries board
const int HX711_sck = 44; //Connect dout of sensor to GPIO-3 of aries board

// --- OLED config ---
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64      // change to 32 if you have a 128x32 display instead
#define OLED_ADDR 0x3C        // common default - change if the scanner found a different address (e.g. 0x3D)
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1); // -1 = no dedicated reset pin
// -------------------

// --- Ultrasonic (HC-SR04) config ---
#define TRIG_PIN P5_6
#define ECHO_PIN P4_0

unsigned long lastDistanceReadTime = 0;
const unsigned long distanceReadInterval = 1000; // how often to trigger a new distance reading (ms)
float latestDistanceCm = 0; // cached, updated by getDistanceData()
// ------------------------------------

// --- IR sensor / pick estimation config ---
#define IR_PIN P3_3

int lastIrState = LOW;
unsigned long lastIrChangeTime = 0;
const unsigned long irDebounceMs = 50; // debounce for the raw IR signal itself

const unsigned long pickSettleMs = 1000; // time to let the scale restabilize after a hand leaves, before trusting the new weight
bool awaitingSettle = false;
unsigned long settleStartTime = 0;
float weightBeforePick = 0;
long irEventCount = 0;          // raw hand-detected events - diagnostic only, not sent
long picksEstimatedTotal = 0;   // cumulative estimated picks, derived from weight drop after each hand detection - this is what gets sent
long lastPickQty = 0;           // most recent single pick's estimate - diagnostic only, not sent
// -------------------------

// --- Bin identity & metadata (edit per deployment - sent to NodeMCU, which relays to Firebase) ---
const char* binId             = "BIN-RYG-08";
const char* binName           = "RYG LED Sensor - 0805";   // avoid special chars like Omega/middot - keep ASCII
const char* binCategory       = "Sensors";
const char* binDepartment     = "Assembly";
const char* binUnit           = "pcs";
const int   binRatePerDay     = 300;
const char* binSupplier       = "Digikey";
const float binPrice          = 0.4;
const char* batchId           = "B-3301";
const char* batchFirstScanned = "2026-07-20";
const long  batchInitialQty   = 1200;

unsigned long lastMetadataSendTime = 0;
const unsigned long metadataResendInterval = 30000; // resend periodically so NodeMCU catches it even if it missed the boot-time send
// ------------------------------------------------------------

// --- inventory calibration for THIS bin (fill these in) ---
const float containerTareGrams = 55.89;   // weight of the empty reel/box, measured once
const float weightPerPiece     = 3.55;   // ryg tested - grams per single component, measured once
const float noiseThreshold     = 0.5;    // grams - anything below this is treated as "no weight"
// ------------------------------------------------------------

//HX711 constructor:
HX711_ADC LoadCell(HX711_dout, HX711_sck);

unsigned long t = 0;  // paces the load-cell debug print
unsigned long lastSendTime = 0;
const unsigned long sendInterval = 2000; // how often to push over Serial2
float latestWeight = 0; // cached, updated by getSensorData() every loop pass
long lastSentCount = -1;   // tracks previous "Sent" value so OLED can show + or - on change

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

// Averages several readings into one stable value.
// Handy for one-off jobs like measuring containerTareGrams by hand
// (put the empty bin on the scale, call this, read the result off
// the serial monitor, then paste that number into containerTareGrams above).
float getAveragedWeight(int numReadings) {
  float sum = 0;
  int count = 0;
  while (count < numReadings) {
    if (LoadCell.update()) {
      sum += LoadCell.getData();
      count++;
    }
  }
  return sum / numReadings;
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
      float raw = LoadCell.getData();
      latestWeight = (fabs(raw) < noiseThreshold) ? 0.0 : raw;
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

//OLED setup function
void oled_setup() {
  Wire.begin(); // master mode, default pins (SDA = pin 28, SCL = pin 29)

  if (!display.begin(SSD1306_SWITCHCAPVCC, OLED_ADDR)) {
    Serial.println("SSD1306 not found - check wiring/address, or run the I2C scanner");
    while (true) {
      delay(1000);  // halt here rather than continue with a display that isn't there
    }
  }

  display.clearDisplay();
  display.setTextSize(2);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(10, 25);
  display.println("Ready");
  display.display();
}

void oled_showCount(long count) {
  char symbol = ' ';   // no symbol on the very first reading - nothing to compare against yet

  if (lastSentCount != -1) {
    if (count > lastSentCount) symbol = '+';
    else if (count < lastSentCount) symbol = '-';
  }
  lastSentCount = count;

  display.clearDisplay();
  display.setTextSize(4);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(60, 25);
  if (symbol != ' ') display.print(symbol);
  display.println(count);
  display.display();
}

void ultrasonic_setup() {
  useVDDIOH(TRIG_PIN);
  useVDDIOH(ECHO_PIN);

  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);

  digitalWrite(TRIG_PIN, LOW);
}

float getDistanceData() {
  if (millis() - lastDistanceReadTime >= distanceReadInterval) {
    lastDistanceReadTime = millis();

    // Send a 10us trigger pulse
    digitalWrite(TRIG_PIN, LOW);
    delayMicroseconds(2);
    digitalWrite(TRIG_PIN, HIGH);
    delayMicroseconds(10);
    digitalWrite(TRIG_PIN, LOW);

    // Measure echo pulse width (timeout ~25ms ≈ 4m range, avoids hanging if no echo)
    long duration = pulseIn(ECHO_PIN, HIGH, 25000);

    if (duration > 0) {
      // distance(cm) = duration(us) / 58  →  speed of sound ≈ 343 m/s
      latestDistanceCm = duration / 58.0;
      Serial.print("Distance: ");
      Serial.print(latestDistanceCm);
      Serial.println(" cm");
    } else {
      Serial.println("No echo received (out of range or no object)");
    }
  }

  return latestDistanceCm;
}

void ir_setup() {
  useVDDIOH(IR_PIN);
  pinMode(IR_PIN, INPUT);
  lastIrState = digitalRead(IR_PIN);
}

void pollPickEstimator() {
  int currentState = digitalRead(IR_PIN);

  if (currentState != lastIrState && millis() - lastIrChangeTime >= irDebounceMs) {
    lastIrChangeTime = millis();
    lastIrState = currentState;

    if (currentState == HIGH) {
      // hand just arrived - remember the weight right before it starts picking
      irEventCount++;
      weightBeforePick = latestWeight;
      awaitingSettle = false; // cancel any pending settle from a previous, unfinished pick
      Serial.println("Hand detected - capturing baseline weight");
    } else {
      // hand just left - start the settle timer before trusting the new weight
      settleStartTime = millis();
      awaitingSettle = true;
      Serial.println("Hand removed - waiting for scale to settle");
    }
  }

  if (awaitingSettle && millis() - settleStartTime >= pickSettleMs) {
    awaitingSettle = false;
    float weightDrop = weightBeforePick - latestWeight;

    if (weightDrop > (weightPerPiece / 2.0)) { // require at least half a piece's worth before counting anything
      long pickedCount = (long)round(weightDrop / weightPerPiece);
      if (pickedCount > 0) {
        picksEstimatedTotal += pickedCount;
        lastPickQty = pickedCount;
        Serial.print("Estimated pick: ");
        Serial.print(pickedCount);
        Serial.print(" piece(s). Running total: ");
        Serial.println(picksEstimatedTotal);
      }
    } else {
      Serial.println("No significant weight drop - not counted as a pick");
    }
  }
}

void sendBinMetadata() {
  Serial2.print("META|");
  Serial2.print(binId);             Serial2.print('|');
  Serial2.print(binName);           Serial2.print('|');
  Serial2.print(binCategory);       Serial2.print('|');
  Serial2.print(binDepartment);     Serial2.print('|');
  Serial2.print(binUnit);           Serial2.print('|');
  Serial2.print(binRatePerDay);     Serial2.print('|');
  Serial2.print(binSupplier);       Serial2.print('|');
  Serial2.print(binPrice);          Serial2.print('|');
  Serial2.print(batchId);           Serial2.print('|');
  Serial2.print(batchFirstScanned); Serial2.print('|');
  Serial2.println(batchInitialQty);
}

void setup() {
  Serial.begin(9600);   // matches Serial2's baud - required, see note above
  Serial2.begin(9600);  // UART link to NodeMCU
  Serial.println("\nMAX32630FTHR UART bridge starting...");
  hx711_setup();
  oled_setup();
  ultrasonic_setup();
  ir_setup();
  sendBinMetadata();
}


void loop() {
  getSensorData();          // poll load cell - every pass, no delay
  getDistanceData();        // poll ultrasonic - self-gated to distanceReadInterval internally
  pollPickEstimator();      // self-debounced/self-timed internally, no delay needed

  if (millis() - lastMetadataSendTime >= metadataResendInterval) {
    lastMetadataSendTime = millis();
    sendBinMetadata();
  }

  if (millis() - lastSendTime >= sendInterval) {
    lastSendTime = millis();

    long pieceCount = (long)((latestWeight - containerTareGrams) / weightPerPiece);
    if (pieceCount < 0) pieceCount = 0;

    char msg[64];
    sprintf(msg, "DATA|%s|%ld|%.1f|%ld", binId, pieceCount, latestDistanceCm, picksEstimatedTotal);
    oled_showCount(pieceCount);

    Serial2.println(msg);
    Serial.print("Sent: ");
    Serial.println(msg);
  }
}
