/*
 * NodeMCU <-> MAX32630FTHR <-> Firebase bridge (simplified, push-based)
 *
 * MAX32630FTHR pushes a fresh reading every 2 seconds, unprompted -
 * this sketch just listens continuously and relays whatever arrives to
 * Firebase. No "Start" request, no waiting for available() > 0 before
 * speaking - that pattern could deadlock if both sides ended up waiting
 * on each other; this version can't, since NodeMCU never needs to send
 * anything to keep the exchange going.
 *
 * Wiring (unchanged from the original project):
 * NodeMCU D7 (GPIO13, RX) <- MAX32630FTHR P3_1 (Serial2 TX)
 * NodeMCU D8 (GPIO15, TX) -> MAX32630FTHR P3_0 (Serial2 RX) - unused by
 *   this simplified version, but fine to leave wired for future use
 * NodeMCU 3.3V -> MAX32630FTHR 3V3, NodeMCU GND -> MAX32630FTHR GND
 */

#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClientSecure.h>
#include <SoftwareSerial.h>

// ---------- Wi-Fi credentials ----------
#define WIFI_SSID       "GNXXXXXXXXXX"   //put your wifi/hotspot name here
#define WIFI_PASSWORD   "XXXXXXXX"        //put your wifi/hotspot password here
// ---------- Firebase Realtime Database ----------
#define FIREBASE_HOST   "randomdata-643f2-default-rtdb.asia-southeast1.firebasedatabase.app"
#define FIREBASE_AUTH   ""

// ---------- UART link to MAX32630FTHR ----------
SoftwareSerial MaxSerial(13, 15); // RX, TX

const int BUF_SIZE = 32;
char rxBuffer[BUF_SIZE];
long eventCounter = 0;

// ---------------------------------------------------------
// Reads one line (ending in '\n') from MaxSerial into rxBuffer.
// Only called once available() > 0, i.e. a line is already arriving,
// so the timeout here just guards against a partial/corrupted line
// missing its terminator, not against normal idle time.
// ---------------------------------------------------------
bool readLine() {
  int idx = 0;
  unsigned long startTime = millis();

  while (true) {
    if (MaxSerial.available() > 0) {
      char c = MaxSerial.read();
      if (c == '\n') {
        rxBuffer[idx] = '\0';
        return true;
      }
      if (idx < BUF_SIZE - 1) {
        rxBuffer[idx] = c;
        idx++;
      }
    }

    if (millis() - startTime > 3000) { // safety timeout - a full line should arrive well within this
      rxBuffer[idx] = '\0';
      return false;
    }
  }
}

void sendToFirebase(const String &path, const String &jsonValue) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi not connected, skipping Firebase write");
    return;
  }

  WiFiClientSecure client;
  client.setInsecure(); // skips certificate check - fine for bench testing only

  HTTPClient https;
  String url = String("https://") + FIREBASE_HOST + "/" + path + ".json";
  if (strlen(FIREBASE_AUTH) > 0) {
    url += "?auth=" + String(FIREBASE_AUTH);
  }

  if (https.begin(client, url)) {
    https.addHeader("Content-Type", "application/json");
    int httpCode = https.PUT(jsonValue);

    Serial.print(path);
    Serial.print(" -> HTTP ");
    Serial.println(httpCode);

    if (httpCode <= 0) {
      Serial.print("PUT failed: ");
      Serial.println(https.errorToString(httpCode));
    }
    https.end();
  } else {
    Serial.println("Unable to open HTTPS connection to Firebase");
  }
}

void setup() {
  Serial.begin(9600);
  MaxSerial.begin(9600);
  delay(1000);

  Serial.println();
  Serial.println("NodeMCU <-> MAX32630FTHR <-> Firebase bridge starting...");

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();
  Serial.print("Connected. IP address: ");
  Serial.println(WiFi.localIP());

  sendToFirebase("CONNECTION_STATUS", "\"ON\"");
}

void loop() {
  if (MaxSerial.available() > 0) {
    if (readLine()) {
      Serial.print("Received from MAX32630FTHR: ");
      Serial.println(rxBuffer);

      sendToFirebase("SensorValue", String(rxBuffer));
      sendToFirebase("Event", String(eventCounter));
      eventCounter++;
    } else {
      Serial.println("Line read timed out (partial data received)");
    }
  }

  delay(100); // small idle delay, avoids busy-looping when nothing's arriving
}
