#include <TinyGPS++.h>
#include <WiFi.h> //Connect to WiFi Network
#include <TFT_eSPI.h> // Graphics and font library for ST7735 driver chip
#include <SPI.h> //Used in support of TFT Display
#include <string.h>  //used for some string handling and processing.
#include "FS.h"
#include "SD.h"
#include <OneWire.h>


#define SD_CS 26 //can be changed
#define ONE_WIRE_BUS 21 //data wire

#define PRIVATE 0
#define PRESS_PRIV 1
#define UNPRESS_PRIV 2
#define PUBLIC 3
#define PRESS_PUB 4
#define UNPRESS_PUB 5

TFT_eSPI tft = TFT_eSPI();  // Invoke library, pins defined in User_Setup.h
OneWire oneWire(ONE_WIRE_BUS); // Setup a oneWire instance to communicate with a OneWire device


char network[] = "MIT";
char password[] = "";

const int BUTTON_TIMEOUT = 1000; //button timeout in milliseconds
const uint8_t LOOP_PERIOD = 10; //milliseconds
const uint32_t GET_GPS_CYCLE = 1000 * 60;
uint32_t primary_timer = 0;
uint32_t posting_timer = 0;
float x, y, z; //variables for grabbing x,y,and z values

const char USER[] = "hey_you_dingus";
const float temp_lat = 42.62512;
const float temp_lon = -71.14477;

//Some constants and some resources:
const int RESPONSE_TIMEOUT = 6000; //ms to wait for response from host

const uint16_t IN_BUFFER_SIZE = 1000; //size of buffer to hold HTTP request
const uint16_t OUT_BUFFER_SIZE = 1000; //size of buffer to hold HTTP response
char request_buffer[IN_BUFFER_SIZE]; //char array buffer to hold HTTP request
char response_buffer[OUT_BUFFER_SIZE]; //char array buffer to hold HTTP response

const uint8_t PIN_1 = 5; //button 1

HardwareSerial gps_serial(2);
TinyGPSPlus gps;

uint8_t old_val; //for button edge detection!
uint32_t timer;
uint8_t state;

//FSM and store data parameters
int presscount = 0;
boolean store_data = false;
boolean confirmed_case = false;
int msgCursorX;
int msgCursorY;

void setup() {
  Serial.begin(115200);
  gps_serial.begin(9600, SERIAL_8N1, 32, 33);
  tft.init();  //init screen
  tft.setRotation(1); //adjust rotation
  tft.setTextSize(1); //default font size
  tft.fillScreen(TFT_BLACK); //fill background
  tft.setTextColor(TFT_GREEN, TFT_BLACK); //set color of font to green foreground, black background
  Serial.begin(115200); //begin serial comms
  delay(100); //wait a bit (100 ms)
  pinMode(PIN_1, INPUT_PULLUP);

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

  WiFi.begin(network, password); //attempt to connect to wifi
  uint8_t count = 0; //count used for Wifi check times
  Serial.print("Attempting to connect to ");
  //  Serial.println(network, password);
  while (WiFi.status() != WL_CONNECTED && count < 12) {
    delay(500);
    Serial.print(".");
    count++;
  }
  delay(2000);
  if (WiFi.isConnected()) { //if we connected then print our IP, Mac, and SSID we're on
    Serial.println("CONNECTED!");
    Serial.printf("%d:%d:%d:%d (%s) (%s)\n", WiFi.localIP()[3], WiFi.localIP()[2],
                  WiFi.localIP()[1], WiFi.localIP()[0],
                  WiFi.macAddress().c_str() , WiFi.SSID().c_str());
    offloadData();
    getDanger();
    delay(500);
  } else { //if we failed to connect just Try again.
    Serial.println("Failed to Connect :/  Going to restart");
    Serial.println(WiFi.status());
    ESP.restart(); // restart the ESP (proper way)
  }

  timer = millis();
  old_val = digitalRead(PIN_1);
  tft.fillScreen(TFT_BLACK); //fill background
  tft.setCursor(0, 0, 1); // set the cursor
  tft.println("Press button __ times to: \n");
  tft.println("1: Enter public mode.");
  tft.println("2: Enter offline mode.");
  tft.println("3: Alert system that I have a confirmed case of COVID-19.");
}

int tempTimer = 0;
void loop() {
  if (gps_serial.available()) {
    while (gps_serial.available())
      gps.encode(gps_serial.read());      // Check GPS
  }
  
 
  if(millis()-tempTimer>2000){
  bool danger = checkDanger();
  Serial.println(danger);
  if (danger) {
    Serial.println("danger bois");
    for(int j = 0; j<200; j++){
    for(int i=0;i<256;i+=2)
    dacWrite(25,i);
  for(int i=254;i>=0;i-=2)
    dacWrite(25,i);
  for(int i=1;i<75;i+=2)
    dacWrite(25,i);
  for(int i=74;i>0;i-=2)
    dacWrite(25,i);}
    tempTimer = millis();
  }
  }
  uint8_t val = digitalRead(PIN_1);
  fsm(val); // call fsm

  if (store_data && (millis() - timer >= GET_GPS_CYCLE)) {
    storeData();
    timer = millis();
    Serial.println("stored data");
  }
}



void fsm(uint8_t input) {
  switch (state) {
    case PRIVATE: {
        if (input == 0) {
          state = PRESS_PRIV;
          presscount = 0;
        }
        break; //don't forget break statements
      }
    case PRESS_PRIV: {
        if (input == 1) {
          presscount += 1;
          timer = millis();
          state = UNPRESS_PRIV;
        }
        break;
      }
    case UNPRESS_PRIV: {
        if (millis() - timer < BUTTON_TIMEOUT) {
          if (input == 0) {
            state = PRESS_PRIV;
          }
        }
        else if (presscount == 1) {
          state = PUBLIC;
          tft.fillScreen(TFT_BLACK); //fill background
          tft.setCursor(0, 0, 1); // set the cursor
          tft.println("Press button __ times to: \n");
          tft.println("1: Enter private mode.");
          if (store_data) {
            tft.println("2: Enter online mode.");
          } else {
            tft.println("2: Enter offline mode.");
          }
          if (confirmed_case) {
            tft.println("3: Alert system that I no longer have a confirmed case of COVID-19.");
          } else {
            tft.println("3: Alert system that I have a confirmed case of COVID-19.");
          }
          timer = millis() - GET_GPS_CYCLE;
        } else if (presscount == 2) {
          state = PRIVATE;
          store_data = !store_data;

          // Display notification
          tft.fillScreen(TFT_BLACK); //fill background
          tft.setCursor(0, 0, 1); // set the cursor
          if (store_data) {
            tft.println("User has entered offline mode.");
          } else {
            //upload values in sd card
            tft.println( "User has entered online mode.");
          }
          delay(1000 * 2);

          timer = millis() - GET_GPS_CYCLE;
          tft.fillScreen(TFT_BLACK); //fill background
          tft.setCursor(0, 0, 1); // set the cursor
          tft.println("Press button __ times to: \n");
          tft.println("1: Enter public mode.");
          if (store_data) {
            tft.println("2: Enter online mode.");
          } else {
            tft.println("2: Enter offline mode.");
          }
          if (confirmed_case) {
            tft.println("3: Alert system that I no longer have a confirmed case of COVID-19.");
          } else {
            tft.println("3: Alert system that I have a confirmed case of COVID-19.");
          }

        } else if (presscount == 3) {
          state = PRIVATE;
          confirmed_case = !confirmed_case;


          // Display notification
          tft.fillScreen(TFT_BLACK); //fill background
          tft.setCursor(0, 0, 1); // set the cursor
          if (confirmed_case) {
            tft.println("User has confirmed COVID-19.");
          } else {
            tft.println( "User has recovered from COVID-19.");
          }
          delay(1000 * 2);

          tft.fillScreen(TFT_BLACK); //fill background
          tft.setCursor(0, 0, 1); // set the cursor
          tft.println("Press button __ times to: \n");
          tft.println("1: Enter public mode.");
          if (store_data) {
            tft.println("2: Enter online mode.");
          } else {
            tft.println("2: Enter offline mode.");
          }
          if (confirmed_case) {
            tft.println("3: Alert system that I no longer have a confirmed case of COVID-19.");
          } else {
            tft.println("3: Alert system that I have a confirmed case of COVID-19.");
          }
        } else {
          state = PRIVATE;
        }
        tft.println();
        msgCursorX = tft.getCursorX();
        msgCursorY = tft.getCursorY();
        break;
      }
    case PUBLIC: {
        Serial.println("hi");

        if (input == 0) {
          state = PRESS_PUB;
          presscount = 0;
        }
        Serial.println(millis() - timer);
        if (millis() - timer >= GET_GPS_CYCLE) {
          Serial.println("Trying to get signal");
          Serial.println(gps.location.isValid());
          Serial.println(gps.location.lat());
          char body[200]; //for body;
          if (gps.location.isValid()) {
            Serial.println("obtained good data");
            sprintf(body, "user=%s&lat=%f&lon=%f&confirmed=%b", USER, gps.location.lat(), gps.location.lng(), confirmed_case); //generate body, posting to User, 1 step
          } else {
            sprintf(body, "user=%s&lat=%f&lon=%f", USER, temp_lat, temp_lon); //generate body, posting to User, 1 step
          }
          int body_len = strlen(body); //calculate body length (for header reporting)
          sprintf(request_buffer, "POST http://608dev-2.net/sandbox/sc/team106/database.py HTTP/1.1\r\n");
          strcat(request_buffer, "Host: 608dev-2.net\r\n");
          strcat(request_buffer, "Content-Type: application/x-www-form-urlencoded\r\n");
          sprintf(request_buffer + strlen(request_buffer), "Content-Length: %d\r\n", body_len); //append string formatted to end of request buffer
          strcat(request_buffer, "\r\n"); //new line from header to body
          strcat(request_buffer, body); //body
          strcat(request_buffer, "\r\n"); //header
          Serial.println(request_buffer);
          do_http_request("608dev-2.net", request_buffer, response_buffer, OUT_BUFFER_SIZE, RESPONSE_TIMEOUT, true);
          tft.setCursor(msgCursorX, msgCursorY);
          tft.println(response_buffer); //print the result
          tft.println();
          timer = millis();
        }
        break;
      }
    case PRESS_PUB: {
        if (input == 1) {
          presscount += 1;
          timer = millis();
          state = UNPRESS_PUB;
        }
        break;
      }
    case UNPRESS_PUB: {
        if (millis() - timer < BUTTON_TIMEOUT) {
          if (input == 0) {
            state = PRESS_PUB;
          }
        }
        else if (presscount == 1) {
          state = PRIVATE;
          tft.fillScreen(TFT_BLACK); //fill background
          tft.setCursor(0, 0, 1); // set the cursor
          tft.println("Press button __ times to: \n");
          tft.println("1: Enter public mode.");
          if (store_data) {
            tft.println("2: Enter online mode.");
          } else {
            tft.println("2: Enter offline mode.");
          }
          if (confirmed_case) {
            tft.println("3: Alert system that I no longer have a confirmed case of COVID-19.");
          } else {
            tft.println("3: Alert system that I have a confirmed case of COVID-19.");
          }
        } else if (presscount == 2) {
          timer = millis();
          store_data = !store_data;

          // Display notification
          tft.fillScreen(TFT_BLACK); //fill background
          tft.setCursor(0, 0, 1); // set the cursor
          if (store_data) {
            tft.println("User has entered offline mode.");
          } else {
            tft.println( "User has entered online mode.");
          }
          delay(1000 * 2);

          state = PUBLIC;
          timer = millis() - GET_GPS_CYCLE;
          tft.fillScreen(TFT_BLACK); //fill background
          tft.setCursor(0, 0, 1); // set the cursor
          tft.println("Press button __ times to: \n");
          tft.println("1: Enter private mode.");
          if (store_data) {
            tft.println("2: Enter online mode.");
          } else {
            tft.println("2: Enter offline mode.");
          }
          if (confirmed_case) {
            tft.println("3: Alert system that I no longer have a confirmed case of COVID-19.");
          } else {
            tft.println("3: Alert system that I have a confirmed case of COVID-19.");
          }
        } else if (presscount == 3) {
          state = PUBLIC;
          timer = millis() - GET_GPS_CYCLE;
          confirmed_case = !confirmed_case;

          // Display notification
          tft.fillScreen(TFT_BLACK); //fill background
          tft.setCursor(0, 0, 1); // set the cursor
          if (confirmed_case) {
            tft.println("User has confirmed COVID-19.");
          } else {
            tft.println( "User has recovered from COVID-19.");
          }
          delay(1000 * 2);

          tft.fillScreen(TFT_BLACK); //fill background
          tft.setCursor(0, 0, 1); // set the cursor
          tft.println("Press button __ times to: \n");
          tft.println("1: Enter private mode.");
          if (store_data) {
            tft.println("2: Enter online mode.");
          } else {
            tft.println("2: Enter offline mode.");
          }
          if (confirmed_case) {
            tft.println("3: Alert system that I no longer have a confirmed case of COVID-19.");
          } else {
            tft.println("3: Alert system that I have a confirmed case of COVID-19.");
          }
        } else {
          state = PUBLIC;
          timer = millis() - GET_GPS_CYCLE;
        }
        tft.println();
        msgCursorX = tft.getCursorX();
        msgCursorY = tft.getCursorY();
        break;
      }
  }
}



/*----------------------------------
   char_append Function:
   Arguments:
      char* buff: pointer to character array which we will append a
      char c:
      uint16_t buff_size: size of buffer buff

   Return value:
      boolean: True if character appended, False if not appended (indicating buffer full)
*/
uint8_t char_append(char* buff, char c, uint16_t buff_size) {
  int len = strlen(buff);
  if (len > buff_size) return false;
  buff[len] = c;
  buff[len + 1] = '\0';
  return true;
}

/*----------------------------------
   do_http_request Function:
   Arguments:
      char* host: null-terminated char-array containing host to connect to
      char* request: null-terminated char-arry containing properly formatted HTTP request
      char* response: char-array used as output for function to contain response
      uint16_t response_size: size of response buffer (in bytes)
      uint16_t response_timeout: duration we'll wait (in ms) for a response from server
      uint8_t serial: used for printing debug information to terminal (true prints, false doesn't)
   Return value:
      void (none)
*/
void do_http_request(char* host, char* request, char* response, uint16_t response_size, uint16_t response_timeout, uint8_t serial) {
  WiFiClient client; //instantiate a client object
  if (client.connect(host, 80)) { //try to connect to host on port 80
    if (serial) Serial.print(request);//Can do one-line if statements in C without curly braces
    client.print(request);
    memset(response, 0, response_size); //Null out (0 is the value of the null terminator '\0') entire buffer
    uint32_t count = millis();
    while (client.connected()) { //while we remain connected read out data coming back
      client.readBytesUntil('\n', response, response_size);
      if (serial) Serial.println(response);
      if (strcmp(response, "\r") == 0) { //found a blank line!
        break;
      }
      memset(response, 0, response_size);
      if (millis() - count > response_timeout) break;
    }
    memset(response, 0, response_size);
    count = millis();
    while (client.available()) { //read out remaining text (body of response)
      char_append(response, client.read(), OUT_BUFFER_SIZE);
    }
    if (serial) Serial.println(response);
    client.stop();
    if (serial) Serial.println("-----------");
  } else {
    if (serial) Serial.println("connection failed :/");
    if (serial) Serial.println("wait 0.5 sec...");
    client.stop();
  }
}

//stores gps data to sd card
void storeData() {
  File file = SD.open("/data.txt");
  if (!file) {
    Serial.println("File doens't exist");
    Serial.println("Creating file...");
    writeFile(SD, "/data.txt", "");
  }
  else {
    Serial.println("File already exists");
  }
  char body[200] = "";
  if (gps.location.isValid()) {
    Serial.println("obtained good data");
    sprintf(body, "user=%s&lat=%f&lon=%f&confirmed=%b\n", USER, gps.location.lat(), gps.location.lng(), confirmed_case); //generate body, posting to User, 1 step
  } else {
    sprintf(body, "user=%s&lat=%f&lon=%f\n", USER, temp_lat, temp_lon); //generate body, posting to User, 1 step
  }
  appendFile(SD, "/data.txt", body);
  file.close();

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
//send all data on sd card to server
void offloadData() {
  File root = SD.open("/data.txt");
  if (root) {
    /* read from the file until there's nothing else in it */
    while (root.available()) {

      const char* body = root.readStringUntil('\n').c_str();
      int body_len = strlen(body); //calculate body length (for header reporting)
      sprintf(request_buffer, "POST http://608dev-2.net/sandbox/sc/team106/database.py HTTP/1.1\r\n");
      strcat(request_buffer, "Host: 608dev-2.net\r\n");
      strcat(request_buffer, "Content-Type: application/x-www-form-urlencoded\r\n");
      sprintf(request_buffer + strlen(request_buffer), "Content-Length: %d\r\n", body_len); //append string formatted to end of request buffer
      strcat(request_buffer, "\r\n"); //new line from header to body
      strcat(request_buffer, body); //body
      strcat(request_buffer, "\r\n"); //header
      Serial.println(request_buffer);
      do_http_request("608dev-2.net", request_buffer, response_buffer, OUT_BUFFER_SIZE, RESPONSE_TIMEOUT, true);
      Serial.println("request sent");
    }
  }
  root.close();
  SD.remove("/data.txt");
  Serial.println("data offloaded");
}

//get closest 5 danger
void getDanger() {
  File root = SD.open("/points.txt");
  if (root) {
    root.close();
    SD.remove("/points.txt");
  }else{root.close();}
  char sexy_response[300] = "42.3562,-71.1007\n42.3563,-71.1008\n42.3562,-71.1008\n42.3562,-71.1006";

  Serial.println("File doens't exist");
  Serial.println("Creating file...");
  writeFile(SD, "/points.txt", "");
  appendFile(SD, "/points.txt", sexy_response);

}




bool checkDanger() {
  File root = SD.open("/points.txt");
  bool danger = false;
  //TODO based on return format
  char fileContents0[25]; // Probably can be smaller
  char fileContents1[25]; // Probably can be smaller
  byte index = 0;
  bool flag = false;
  bool flag0 = false;

  if (gps.location.isValid()) {
    float curLat = gps.location.lat();
    float curLon = gps.location.lng();
    while (root.available()) {

      char aChar = root.read();
      if (aChar != '\n' && aChar != '\r')
      {
        if (aChar == ',') {
          flag = true;
          flag0=true;
          index = 0;
        }
        if (!flag) {
          fileContents0[index++] = aChar;
          fileContents0[index] = '\0'; // NULL terminate the array
        } else {
          if(!flag0){
          fileContents1[index++] = aChar;
          fileContents1[index] = '\0'; // NULL terminate the array
          }
          flag0=false;

        }}
        else { // the character is CR or LF
          if (strlen(fileContents0) > 0)
          {

            float checkLat = atof(fileContents0);
            float checkLon = atof(fileContents1);
            float dist = pow(pow(checkLat - curLat, 2.0) + pow(checkLon - curLon, 2.0), 0.5) * 111195./2.0;
            Serial.println("files");
            Serial.println(fileContents1);
            Serial.println("coords0:");
            Serial.println(checkLat);
            Serial.println(checkLon);
            Serial.println("coords:");
            Serial.println(curLat);
            Serial.println(curLon);
            Serial.println("dinstance:");
            Serial.println(dist);
            if (dist < 250) {
              danger = true;
              Serial.println("flag hit!!!");
            }
          }

          fileContents0[0] = '\0';
          fileContents1[0] = '\0';
          index = 0;
          flag = false;
          flag0=false;
        }
      }

    }
    root.close();
    return danger;
  }
