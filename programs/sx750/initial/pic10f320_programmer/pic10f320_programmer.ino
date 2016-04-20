/*
  SETEC PIC10F320 Device Programmer.

  The command interface is like the ARM processor consoles, so the same Python
  driver can be used.

  Measurements have shown that digitalWrite() takes 6usec to complete, so any required
  delay under that can be ignored.
 */

// Response to the version query command
const char *RES_VER = "\"DEVICE=1,PWRSW=2A,5VSB=1A\"";

#include <avr/pgmspace.h>        // To access the firmware image data
#include "pic10f320_images.h"    // The device firmware images

// Digital I/O
#define PIN_VPP         2                // Vpp control. Write 1 to apply 8.5V to Vpp
#define PIN_CLOCK       3                // PIC ICSPCLK (PIC10F320 pin 3)
#define PIN_DATA        4                // PIC ICSPDATA (PIC10F320 pin 1)
#define PIN_POT_UD      5                // Digital Pot Up/Down
#define PIN_POT_CS12    6                // Digital Pot 12V Chip Select
#define PIN_POT_CS24    7                // Digital Pot 24V Chip Select
#define PIN_LED        13                // Arduino LED

const char *PROMPT    = "\r\n> ";        // Command prompt
// Commands are:
const char *CMD_NONE = "";               // Empty command
const char *CMD_VER   = "VERSION?";      // Show the versions
const char *CMD_PWSW  = "PROGRAM-PWRSW"; // Program using the PWRSW firmware image
const char *CMD_5VSB  = "PROGRAM-5VSB";  // Program using the 5VSB firmware image
const char *CMD_DEBUG = "1 DEBUG";       // Switch ON debug messages
const char *CMD_QUIET = "0 DEBUG";       // Switch OFF debug messages

// Debug level storage
boolean debug = false;

// Variables for the LED flasher.
// It does not use delay(), but it may pause during device programming
int ledState = LOW;               // ledState used to set the LED
unsigned long previousMillis = 0; // will store last time LED was updated
const long interval = 500;        // interval at which to blink (milliseconds)

// PIC device programming commands
const byte PIC_CONFIG    = 0x00;  // Load Configuration
const byte PIC_LOAD      = 0x02;  // Load Data For Program Memory
const byte PIC_READ      = 0x04;  // Read Data From Program Memory
const byte PIC_INCREMENT = 0x06;  // Increment Address
const byte PIC_RESET     = 0x16;  // Reset Address
const byte PIC_PROGRAM   = 0x08;  // Begin Internally Timed Programming
const byte PIC_ERASE     = 0x09;  // Bulk Erase Program Memory
#define    PIC_320_ID    0x29A0   // Device ID of a PIC10F320

// PIC device delays
#define DELAY_TENTH     250       // usec, Vpp to clock/data
#define DELAY_TPINTP    2500      // Time for a program memory write to complete
#define DELAY_TPINTC    5000      // Time for a configuration memory write to complete
#define DELAY_TERAB     5000      // Time for a bulk erase

// The setup function runs once when you press reset or power the board
void setup() {
    pinMode(PIN_VPP, OUTPUT);
    pinMode(PIN_DATA, OUTPUT);
    pinMode(PIN_CLOCK, OUTPUT);
    pinMode(PIN_LED, OUTPUT);
    pinMode(PIN_POT_UD, OUTPUT);
    pinMode(PIN_POT_CS12, OUTPUT);
    pinMode(PIN_POT_CS24, OUTPUT);
    Serial.begin(9600);
    Serial.println("SETEC PIC10F320 Programmer");
    Serial.println(RES_VER);
    Serial.print("Ready for commands");
    Serial.print(PROMPT);
}

// The loop function runs over and over again forever
void loop() {
    String cmd;

    ledFlasher();
    while(Serial.available() > 0) {
        cmd = Serial.readStringUntil('\r');
        Serial.print(cmd);      // Echo back the command
        if (debug)
            Serial.println();
        cmd.toUpperCase();      // Uppercase for the command lookup
        if (cmd == CMD_VER)
            Serial.print(RES_VER);
        else if (cmd == CMD_5VSB) {
            if (debug)
                Serial.println("PROGRAM 5VSB");
            process(v5sb_config, v5sb_rows, v5sb_data);
        }
        else if (cmd == CMD_PWSW) {
            if (debug)
                Serial.println("PROGRAM PWRSW");
            process(pwrsw_config, pwrsw_rows, pwrsw_data);
        }
        else if (cmd == CMD_DEBUG) {
            debug = true;
            Serial.println("Debug messages ON");
        }
        else if (cmd == CMD_QUIET)
            debug = false;
        else if (cmd == CMD_NONE)
            debug = debug;
        else
            Serial.print("Unknown command");
        // Always turn off the outputs
        digitalWrite(PIN_VPP, LOW);
        digitalWrite(PIN_DATA, LOW);
        digitalWrite(PIN_CLOCK, LOW);
        Serial.print(PROMPT);   // Lastly, send the command prompt
    }
}

// Blink the LED without using delay()
void ledFlasher() {
    unsigned long currentMillis = millis();
    if (currentMillis - previousMillis >= interval) {
        previousMillis = currentMillis;
        if (ledState == LOW)
            ledState = HIGH;
        else
            ledState = LOW;
        digitalWrite(PIN_LED, ledState);
    }
}

// Process a device
void process(const unsigned configuration, const unsigned rowCount, const unsigned *image) {
    digitalWrite(PIN_VPP, HIGH);    // Apply Vpp
    delayMicroseconds(DELAY_TENTH); // Wait before clock/data
    if (detect())
        return;
    if (erase())
        return;
    if (program(rowCount, image))
        return;
    if (verify(rowCount, image))
        return;
    if (configure(configuration))
        return;
    Serial.print("Success");
}

// Detect the device
boolean detect() {
    unsigned data;
  
    if (debug)
        Serial.println("D");
    sendWriteCommand(PIC_CONFIG, 0x0);  // Load Configuration (Address = 0x2000)
    sendCommand(PIC_INCREMENT);         // (Address = 0x2001)
    sendCommand(PIC_INCREMENT);         // (Address = 0x2002)
    sendCommand(PIC_INCREMENT);         // (Address = 0x2003)
    sendCommand(PIC_INCREMENT);         // (Address = 0x2004)
    sendCommand(PIC_INCREMENT);         // (Address = 0x2005)
    sendCommand(PIC_INCREMENT);         // (Address = 0x2006)
    data = sendReadCommand(PIC_READ);
    if ((data & 0x3FE0) == PIC_320_ID) {
        if (debug) {
            Serial.print(data, HEX);
            Serial.print(" 10F320 Rev ");
            Serial.println(data & 0x001F);
        }
        return false;
    }
    else {
        Serial.print("Device not detected");
        return true;
    }
}

// Erase the device
boolean erase() {
    if (debug)
        Serial.println("E");
    sendCommand(PIC_ERASE);             // Bulk Erase
    delayMicroseconds(DELAY_TERAB);     // Wait for erase
    return false;
}

// Program the device
boolean program(const unsigned rowCount, const unsigned *image) {
    unsigned data;

    if (debug)
        Serial.println("P");
    sendCommand(PIC_RESET);             // Set address to 0x0000
    for (unsigned row = 0; row < rowCount; ++row) {     // For each row of 16 words...
        for (unsigned offset = 0; offset < 16; offset++) {  // Load the row into the device
            data = pgm_read_word_near(image + (row * 16) + offset);
            sendWriteCommand(PIC_LOAD, data); // Load a data word
            if (offset < 15)
                sendCommand(PIC_INCREMENT);   // Next address, but don't leave the row
        }
        if (debug)
            Serial.print(".");
        sendCommand(PIC_PROGRAM);           // Write a row of data
        delayMicroseconds(DELAY_TPINTP);    // Wait for write to complete
        sendCommand(PIC_INCREMENT);         // Now move onto the next row
    }
    if (debug)
        Serial.println("");
    return false;
}

// Verify the device
boolean verify(const unsigned rowCount, const unsigned *image) {
    unsigned data;
    unsigned device;

    if (debug)
        Serial.println("V");
    sendCommand(PIC_RESET);             // Reset address to 0x0000
    for (unsigned offset = 0; offset < (rowCount * 16); offset++) {
        data = pgm_read_word_near(image + offset);  // What it should be
        device = sendReadCommand(PIC_READ);         // What is in the device
        if (device != data) {
            Serial.print("Verify error at ");
            Serial.print(*(image + offset), HEX);
            Serial.print(" Data=");
            Serial.print(data, HEX);
            Serial.print(" Device=");
            Serial.print(device, HEX);
            return true;
        }
        sendCommand(PIC_INCREMENT);       // Next address
    }
    return false;
}

// Configure the device
boolean configure(const unsigned configuration) {
    unsigned data;

    if (debug)
        Serial.println("C");
    sendWriteCommand(PIC_CONFIG, 0x0);  // Load Configuration (Address = 0x2000)
    sendCommand(PIC_INCREMENT);         // (Address = 0x2001)
    sendCommand(PIC_INCREMENT);         // (Address = 0x2002)
    sendCommand(PIC_INCREMENT);         // (Address = 0x2003)
    sendCommand(PIC_INCREMENT);         // (Address = 0x2004)
    sendCommand(PIC_INCREMENT);         // (Address = 0x2005)
    sendCommand(PIC_INCREMENT);         // (Address = 0x2006)
    sendCommand(PIC_INCREMENT);         // (Address = 0x2007)
    sendWriteCommand(PIC_LOAD, configuration);
    sendCommand(PIC_PROGRAM);
    delayMicroseconds(DELAY_TPINTC);    // Wait for write to complete
    data = sendReadCommand(PIC_READ);
    if (data != configuration) {
        Serial.print("Config error. Config=");
        Serial.print(configuration, HEX);
        Serial.print(" Device=");
        Serial.print(data, HEX);
        return true;
    }
    return false;
}

// Send a command to the PIC.
void sendCommand(byte cmd) {
    for (byte bit = 0; bit < 6; ++bit)  {
        digitalWrite(PIN_CLOCK, HIGH);
        if (cmd & 1)
            digitalWrite(PIN_DATA, HIGH);
        else
            digitalWrite(PIN_DATA, LOW);
        digitalWrite(PIN_CLOCK, LOW);
        cmd >>= 1;
    }
}

// Send a command to the PIC that writes a data argument.
void sendWriteCommand(byte cmd, unsigned int data) {
    sendCommand(cmd);
    data = (data << 1) & 0x7FFE;  // add a zero LSB, and mask to 14-bits
    for (byte bit = 0; bit < 16; ++bit) {
        digitalWrite(PIN_CLOCK, HIGH);
        if (data & 1)
            digitalWrite(PIN_DATA, HIGH);
        else
            digitalWrite(PIN_DATA, LOW);
        digitalWrite(PIN_CLOCK, LOW);
        data >>= 1;
    }
}

// Send a command to the PIC that reads back a data value.
unsigned int sendReadCommand(byte cmd)
{
    unsigned int data = 0;
    sendCommand(cmd);
    digitalWrite(PIN_DATA, LOW);
    pinMode(PIN_DATA, INPUT);
    for (byte bit = 0; bit < 16; ++bit) {
        data >>= 1;
        digitalWrite(PIN_CLOCK, HIGH);
        if (digitalRead(PIN_DATA))
            data |= 0x8000;
        digitalWrite(PIN_CLOCK, LOW);
    }
    pinMode(PIN_DATA, OUTPUT);
    return (data >> 1) & 0x3FFF;    // remove the zero LSB, and mask to 14-bits
}

