/*
 * NodeMCU <-> MAX32630FTHR <-> Firebase bridge (push-based, generic relay)
 *
 * MAX32630FTHR owns all the bin identity/metadata and decides what gets
 * written where - this sketch just parses two message types it receives
 * over MaxSerial and relays fields to Firebase. It doesn't know or care
 * what a "resistor" or "category" is.
 *
 *  META|<binId>|<name>|<category>|<department>|<unit>|<ratePerDay>|<supplier>|<price>|<batchId>|<firstScanned>|<initialQty>
 *    -> static bin info, sent once at boot + resent periodically as a safety net
 *  DATA|<binId>|<qty>|<distanceCm>|<picksEstimated>
 *    -> live values, sent every 2s. picksEstimated is a running total of
 *       estimated picks, derived on the MAX32630FTHR side by correlating
 *       IR hand-detection events with the load-cell weight drop.
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
#define WIFI_SSID       "GNXS-2.4G-32E5B0"   //put your wifi/hotspot name here
#define WIFI_PASSWORD   "12345678@"        //put your wifi/hotspot password here
// ---------- Firebase Realtime Database ----------
#define FIREBASE_HOST   "randomdata-643f2-default-rtdb.asia-southeast1.firebasedatabase.app"
#define FIREBASE_AUTH   ""

// ---------- UART link to MAX32630FTHR ----------
SoftwareSerial MaxSerial(13, 15); // RX, TX

const int BUF_SIZE = 160;   // must comfortably fit the longest META line
char rxBuffer[BUF_SIZE];
long eventCounter = 0;

String currentBinId = "";
String currentBatchId = "";
bool metadataReceived = false;

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

void handleMetadata(char *data) {
  char *binId        = strtok(data, "|");
  char *name         = strtok(NULL, "|");
  char *category     = strtok(NULL, "|");
  char *department   = strtok(NULL, "|");
  char *unit         = strtok(NULL, "|");
  char *ratePerDay   = strtok(NULL, "|");
  char *supplier     = strtok(NULL, "|");
  char *price        = strtok(NULL, "|");
  char *batchId      = strtok(NULL, "|");
  char *firstScanned = strtok(NULL, "|");
  char *initialQty   = strtok(NULL, "|");

  if (binId == NULL || batchId == NULL) {
    Serial.println("Malformed META line, skipping");
    return;
  }

  currentBinId = String(binId);
  currentBatchId = String(batchId);

  String base = "bins/" + currentBinId;
  sendToFirebase(base + "/name", "\"" + String(name) + "\"");
  sendToFirebase(base + "/category", "\"" + String(category) + "\"");
  sendToFirebase(base + "/department", "\"" + String(department) + "\"");
  sendToFirebase(base + "/unit", "\"" + String(unit) + "\"");
  sendToFirebase(base + "/rate_per_day", String(ratePerDay));
  sendToFirebase(base + "/supplier", "\"" + String(supplier) + "\"");
  sendToFirebase(base + "/price", String(price));
  sendToFirebase(base + "/batches/" + currentBatchId + "/id", "\"" + currentBatchId + "\"");
  sendToFirebase(base + "/batches/" + currentBatchId + "/firstScanned", "\"" + String(firstScanned) + "\"");
  sendToFirebase(base + "/batches/" + currentBatchId + "/initial", String(initialQty));

  metadataReceived = true;
  Serial.println("Bin metadata written to Firebase");
}

void handleData(char *data) {
  char *binId      = strtok(data, "|");
  char *qty        = strtok(NULL, "|");
  char *distanceCm = strtok(NULL, "|");
  char *picks      = strtok(NULL, "|");

  if (binId == NULL || qty == NULL) {
    Serial.println("Malformed DATA line, skipping");
    return;
  }

  if (!metadataReceived || currentBinId != String(binId)) {
    Serial.println("Data received before metadata arrived - skipping this line");
    return;
  }

  String base = "bins/" + currentBinId;
  sendToFirebase(base + "/qty", String(qty));
  sendToFirebase(base + "/batches/" + currentBatchId + "/remaining", String(qty));
  if (distanceCm != NULL) {
    sendToFirebase(base + "/distanceCm", String(distanceCm));
  }
  if (picks != NULL) {
    sendToFirebase(base + "/picksEstimated", String(picks));
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
      Serial.print("Received: ");
      Serial.println(rxBuffer);

      if (strncmp(rxBuffer, "META|", 5) == 0) {
        handleMetadata(rxBuffer + 5);
      } else if (strncmp(rxBuffer, "DATA|", 5) == 0) {
        handleData(rxBuffer + 5);
        sendToFirebase("Event", String(eventCounter));
        eventCounter++;
      } else {
        Serial.println("Unrecognized message format, ignoring");
      }
    } else {
      Serial.println("Line read timed out (partial data received)");
    }
  }

  delay(100); // small idle delay, avoids busy-looping when nothing's arriving
}
