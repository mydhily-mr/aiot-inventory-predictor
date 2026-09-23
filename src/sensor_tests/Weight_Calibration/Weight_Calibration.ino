/*
  @file Weight_Calibration.ino
  @brief Interfacing HX711 Load Sensor to ARIES V2 Board
  @detail First use a known weight to calibrate the sensor and then you can see the weight measurements of any object in serial monitor.

   Reference arduino code: https://randomnerdtutorials.com/arduino-load-cell-hx711/ 
   Reference aries board : https://vegaprocessors.in/blog/interfacing-8x8-led-dot-matrix-to-aries-v2-board/
   
   Libraries Used:
   *  Library Name : HX711_ADC
   *  Library Version : 1.2.12  
   
   *** Load Sensor ***
   Connections:
   HX711            Aries Board
   VCC          -   3.3V
   GND          -   GND
   Dout         -   P5_5 (pin 45 in software)
   sck          -   P5_4 (pin 45 in software)

   Steps for Weight Calibration:
   1) Prepare an object with a known weight. I used my power bank(201.0g for phone).

   2) Connect the weight sensor to Aries board,and Open the following code in your Arduino IDE.

   3) Inside the code search for the line "known_mass = 1000;" and Substitute this value with the value of your known weight( in GRAMS )
   
   4) After uploading the code, open the Serial Monitor at a baud rate of 9600.

   5) Place the load cell at a level stable surface

   6) Follow the instructions on the Serial Monitor: remove any weights from the scale (it will tare automatically). 

   7) Then Send 't' from serial monitor to set the tare offset.
   
   8) Then, place your known mass on the loadcell.

   9) Then send the weight of this mass (in this example: 1000.0) from serial monitor.

  10)  Now the calibration using a known weight is completed. 
  
  11)  Now you can remove the known weight from the load cell and You can measure the weight of any object, by placing the object on the load cell. 

*/

#include <HX711_ADC.h>

//pins:
const int HX711_dout = 45; //Connect dout of sensor to GPIO-2 of aries board
const int HX711_sck = 44; //Connect sck of sensor to GPIO-3 of aries board

//HX711 constructor:
HX711_ADC LoadCell(HX711_dout, HX711_sck);

unsigned long t = 0;

void setup() {
  delay(2000);
  Serial.begin(9600); delay(10);
  Serial.println();
  Serial.println("Starting...");

  LoadCell.begin();
  //LoadCell.setReverseOutput(); //uncomment to turn a negative output value to positive
  unsigned long stabilizingtime = 2000; // preciscion right after power-up can be improved by adding a few seconds of stabilizing time
  boolean _tare = true; //set this to false if you don't want tare to be performed in the next step
  LoadCell.start(stabilizingtime, _tare);
  if (LoadCell.getTareTimeoutFlag() || LoadCell.getSignalTimeoutFlag()) {
    Serial.println("Timeout, check MCU>HX711 wiring and pin designations");
    while (1);
  }
  else {
    LoadCell.setCalFactor(1.0); // user set calibration value (float), initial value 1.0 may be used for this sketch
    Serial.println("Startup is complete");
  }
  while (!LoadCell.update());
  calibrate(); //start calibration procedure
}

void loop() {
  static boolean newDataReady = 0;
  const int serialPrintInterval = 0; //increase value to slow down serial print activity

  // check for new data/start next conversion:
  if (LoadCell.update()) newDataReady = true;

  // get smoothed value from the dataset:
  if (newDataReady) {
    if (millis() > t + serialPrintInterval) {
      float i = LoadCell.getData();
      Serial.print("Load_cell output val: ");
      Serial.println(i);
      newDataReady = 0;
      t = millis();
    }
  }

  // receive command from serial terminal
  if (Serial.available() > 0) {
    char inByte = Serial.read();
    if (inByte == 't') LoadCell.tareNoDelay(); //tare
    else if (inByte == 'r') calibrate(); //calibrate

  }

  // check if last tare operation is complete
  if (LoadCell.getTareStatus() == true) {
    Serial.println("Tare complete");
  }

}

void calibrate() {
  Serial.println("***");
  Serial.println("Start calibration:");
  Serial.println("Place the load cell an a level stable surface.");
  Serial.println("Remove any load applied to the load cell.");
  Serial.println("Send 't' from serial monitor to set the tare offset.");

  boolean _resume = false;
  while (_resume == false) {
    LoadCell.update();
    if (Serial.available() > 0) {
      if (Serial.available() > 0) {
        char inByte = Serial.read();
        if (inByte == 't') LoadCell.tareNoDelay();
      }
    }
    if (LoadCell.getTareStatus() == true) {
      Serial.println("Tare complete");
      _resume = true;
    }
  }

  Serial.println("Now, place your known mass on the loadcell.");
  Serial.println("Then send the weight of this mass (i.e. 201.0) from serial monitor.");

  float known_mass = 0;
  _resume = false;
  while (_resume == false) {
    LoadCell.update();
    if (Serial.available() > 0) {
      
      known_mass = 201.0; //Substitute this value with the value of your known weight( in GRAMS ) ////////////////////////////////
      
      if (known_mass != 0) {
        Serial.print("Known mass is: ");
        Serial.println(known_mass);
        _resume = true;
      }
    }
  }

  LoadCell.refreshDataSet(); //refresh the dataset to be sure that the known mass is measured correct
  float newCalibrationValue = LoadCell.getNewCalibration(known_mass); //get the new calibration value

  Serial.print("New calibration value has been set to: ");
  Serial.print(newCalibrationValue);
  

  Serial.println("End calibration");
  Serial.println("***");
  Serial.println("To re-calibrate, send 'r' from serial monitor.");
  Serial.println("***");
}
