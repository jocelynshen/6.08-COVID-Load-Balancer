#include <TinyGPS++.h>
#include <WiFi.h> //Connect to WiFi Network
#include <TFT_eSPI.h> // Graphics and font library for ST7735 driver chip
#include <SPI.h> //Used in support of TFT Display
#include <string.h>  //used for some string handling and processing.

#define PRIVATE 0
#define PRESS_PRIV 1
#define UNPRESS_PRIV 2 
#define PUBLIC 3
#define PRESS_PUB 4
#define UNPRESS_PUB 5

TFT_eSPI tft = TFT_eSPI();  // Invoke library, pins defined in User_Setup.h

char network[] = "rock3";  
char password[] = "aamd1234"; 

const int BUTTON_TIMEOUT = 1000; //button timeout in milliseconds
const uint8_t LOOP_PERIOD = 10; //milliseconds
const uint32_t GET_GPS_CYCLE = 1000 * 60;
uint32_t primary_timer = 0;
uint32_t posting_timer = 0;
float x, y, z; //variables for grabbing x,y,and z values

const char USER[] = "amandali";
const float temp_lat = 42.62512;
const float temp_lon = -71.14477;

//Some constants and some resources:
const int RESPONSE_TIMEOUT = 6000; //ms to wait for response from host

const uint16_t IN_BUFFER_SIZE = 1000; //size of buffer to hold HTTP request
const uint16_t OUT_BUFFER_SIZE = 1000; //size of buffer to hold HTTP response
char request_buffer[IN_BUFFER_SIZE]; //char array buffer to hold HTTP request
char response_buffer[OUT_BUFFER_SIZE]; //char array buffer to hold HTTP response

const uint8_t PIN_1 = 16; //button 1

HardwareSerial gps_serial(2);
TinyGPSPlus gps;

uint8_t old_val; //for button edge detection!
uint32_t timer;
uint8_t state;

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

void loop() {
  if (gps_serial.available()) {
    while (gps_serial.available())
      gps.encode(gps_serial.read());      // Check GPS
  }
  uint8_t val = digitalRead(PIN_1);
  fsm(val); // call fsm
  Serial.println("hey");

}
int presscount = 0;
boolean store_data = false;
boolean confirmed_case = false;
int msgCursorX;
int msgCursorY;

void fsm(uint8_t input) {
  switch(state) {
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
 * char_append Function:
 * Arguments:
 *    char* buff: pointer to character array which we will append a
 *    char c: 
 *    uint16_t buff_size: size of buffer buff
 *    
 * Return value: 
 *    boolean: True if character appended, False if not appended (indicating buffer full)
 */
uint8_t char_append(char* buff, char c, uint16_t buff_size) {
        int len = strlen(buff);
        if (len>buff_size) return false;
        buff[len] = c;
        buff[len+1] = '\0';
        return true;
}

/*----------------------------------
 * do_http_request Function:
 * Arguments:
 *    char* host: null-terminated char-array containing host to connect to
 *    char* request: null-terminated char-arry containing properly formatted HTTP request
 *    char* response: char-array used as output for function to contain response
 *    uint16_t response_size: size of response buffer (in bytes)
 *    uint16_t response_timeout: duration we'll wait (in ms) for a response from server
 *    uint8_t serial: used for printing debug information to terminal (true prints, false doesn't)
 * Return value:
 *    void (none)
 */
void do_http_request(char* host, char* request, char* response, uint16_t response_size, uint16_t response_timeout, uint8_t serial){
  WiFiClient client; //instantiate a client object
  if (client.connect(host, 80)) { //try to connect to host on port 80
    if (serial) Serial.print(request);//Can do one-line if statements in C without curly braces
    client.print(request);
    memset(response, 0, response_size); //Null out (0 is the value of the null terminator '\0') entire buffer
    uint32_t count = millis();
    while (client.connected()) { //while we remain connected read out data coming back
      client.readBytesUntil('\n',response,response_size);
      if (serial) Serial.println(response);
      if (strcmp(response,"\r")==0) { //found a blank line!
        break;
      }
      memset(response, 0, response_size);
      if (millis()-count>response_timeout) break;
    }
    memset(response, 0, response_size);  
    count = millis();
    while (client.available()) { //read out remaining text (body of response)
      char_append(response,client.read(),OUT_BUFFER_SIZE);
    }
    if (serial) Serial.println(response);
    client.stop();
    if (serial) Serial.println("-----------");  
  }else{
    if (serial) Serial.println("connection failed :/");
    if (serial) Serial.println("wait 0.5 sec...");
    client.stop();
  }
}        
