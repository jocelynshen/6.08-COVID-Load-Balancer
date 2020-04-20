// Libraries for SD card
#include "FS.h"
#include "SD.h"
#include <SPI.h>

#include <OneWire.h>
#define SD_CS 5 //can be changed

char dataMessage[100] = "Hi dingus";

// Data wire is connected to ESP32 GPIO 21
#define ONE_WIRE_BUS 21
// Setup a oneWire instance to communicate with a OneWire device
OneWire oneWire(ONE_WIRE_BUS);

void setup() {
  // Start serial communication for debugging purposes
  Serial.begin(115200);
  // Initialize SD card
  SD.begin(SD_CS);
  if (!SD.begin(SD_CS)) {
    Serial.println("Card Mount Failed");
    return;
  }
  uint8_t cardType = SD.cardType();
  if (cardType == CARD_NONE) {
    Serial.println("No SD card attached");
    return;
  }
  Serial.println("Initializing SD card...");
  if (!SD.begin(SD_CS)) {
    Serial.println("ERROR - SD card initialization failed!");
    return;    // init failed
  }

  // If the data.txt file doesn't exist
  // Create a file on the SD card and write the data labels
  File file = SD.open("/data.txt");
  if (!file) {
    Serial.println("File doens't exist");
    Serial.println("Creating file...");
    writeFile(SD, "/data.txt", dataMessage);
  }
  else {
    Serial.println("File already exists");
  }
  file.close();
}
int count = 0;
//char val[200] = "\0";
void loop() {    
  if(count<=50){
    sprintf(dataMessage, "sorry not sorry %i\n", count);
    appendFile(SD, "/data.txt", dataMessage);
    count++;
    }
  else{
    File root = SD.open("/data.txt");
    if (root) {    
    /* read from the file until there's nothing else in it */
    while (root.available()) {
      /* read the file and print to Terminal */
       const char* val= root.readStringUntil('\n').c_str();
      Serial.println(val);
    }}
    root.close();}

}




// Write to the SD card (DON'T MODIFY THIS FUNCTION)
void writeFile(fs::FS &fs, const char * path, const char * message) {
  Serial.printf("Writing file: %s\n", path);

  File file = fs.open(path, FILE_WRITE);
  if (!file) {
    Serial.println("Failed to open file for writing");
    return;
  }
  if (file.print(message)) {
    Serial.println("File written");
  } else {
    Serial.println("Write failed");
  }
  file.close();
}

// Append data to the SD card (DON'T MODIFY THIS FUNCTION)
void appendFile(fs::FS &fs, const char * path, const char * message) {
  Serial.printf("Appending to file: %s\n", path);

  File file = fs.open(path, FILE_APPEND);
  if (!file) {
    Serial.println("Failed to open file for appending");
    return;
  }
  if (file.print(message)) {
    Serial.println("Message appended");
  } else {
    Serial.println("Append failed");
  }
  file.close();
}
