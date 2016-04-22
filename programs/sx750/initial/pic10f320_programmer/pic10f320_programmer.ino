/*
  SETEC PIC10F320 Device Programmer.

  The command interface is like the ARM processor consoles, so the same Python
  driver can be used.

  Measurements have shown that digitalWrite() takes 6usec to complete, so any required
  delay under that can be ignored.

  SX-750 Digital Pot Driver.
    12V and 24V OCP point adjustment.
    Both devices share UP/~DOWN pin.
    Each has a ~ChipSelect pin.
    Pins are driven by opto-couplers, driven by digital outputs.
    All lines have 22k pull up to '5Vcc' of the unit.
    Note that UP on the pots REDUCES the OCP point.
  Pot UP Procedure (OCP DOWN):
    Both CS and UD are high (off)
    Set UD off (off = UP)
    Set CS on
    Set UD on
    Pulse UD off-on (setting moves when turn off happens)
    Set CS off (UD on here causes a write to EEPROM)
    Set UD off
  Pot DOWN Procedure (OCP UP):
    Both CS and UD are high (off)
    Set UD on (on = DOWN)
    Set CS on
    Pulse UD on-off (setting moves when turn off happens)
    Set CS off (UD off here causes a write to EEPROM)
  WriteLock device function is not used or enabled.

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

const char *PROMPT    = "\r\n> ";        // Command prompt
const char *RESP_OK   = "OK";            // Command OK response
// Commands are:
const char *CMD_NONE  = "";              // Empty command
const char *CMD_VER   = "VERSION?";      // Show the versions
const char *CMD_DEBUG = "1 DEBUG";       // Switch ON debug messages
const char *CMD_QUIET = "0 DEBUG";       // Switch OFF debug messages

const char *CMD_PWSW  = "PROGRAM-PWRSW"; // Program using the PWRSW firmware image
const char *CMD_5VSB  = "PROGRAM-5VSB";  // Program using the 5VSB firmware image

const char *CMD_MAX   = "POT-MAX";       // Set both digital pots to maximum
const char *CMD_EN_12 = "12 POT-ENABLE"; // Enable 12V digital pot
const char *CMD_EN_24 = "24 POT-ENABLE"; // Enable 24V digital pot
const char *CMD_STEP  = "POT-STEP";      // Step digital pot down 1 step
const char *CMD_DIS   = "POT-DISABLE";   // Disable digital pots

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

// PIC device delays in usec
#define DELAY_TENTH     250       // Vpp to clock/data
#define DELAY_TPINTP    2500      // Time for a program memory write to complete
#define DELAY_TPINTC    5000      // Time for a configuration memory write to complete
#define DELAY_TERAB     5000      // Time for a bulk erase

// Digital Pot delays in usec
#define DELAY_POT       100       // Delay after each transition


// The setup function runs once when you press reset or power the board
void setup() {
    pinMode(PIN_VPP, OUTPUT);
    pinMode(PIN_DATA, OUTPUT);
    pinMode(PIN_CLOCK, OUTPUT);
    pinMode(LED_BUILTIN, OUTPUT);
    pinMode(PIN_POT_UD, OUTPUT);
    pinMode(PIN_POT_CS12, OUTPUT);
    pinMode(PIN_POT_CS24, OUTPUT);
    Serial.begin(115200);
    Serial.println("SETEC SX-750 Device Programmer");
    Serial.print(RES_VER);
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
        else if (cmd == CMD_MAX)
            potMaximum();
        else if (cmd == CMD_EN_12)
            potEnable(PIN_POT_CS12);
        else if (cmd == CMD_EN_24)
            potEnable(PIN_POT_CS24);
        else if (cmd == CMD_STEP)
            potStep();
        else if (cmd == CMD_DIS)
            potDisable();
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
        digitalWrite(LED_BUILTIN, ledState);
    }
}

// Set both Digital Pots UP to maximum
void potMaximum() {
    potWrite(PIN_POT_UD, LOW);
    potWrite(PIN_POT_CS12, HIGH);
    potWrite(PIN_POT_CS24, HIGH);
    for (byte i = 0; i < 64; i++) {     // Step UP 64 times
        potWrite(PIN_POT_UD, HIGH);
        potWrite(PIN_POT_UD, LOW);      // The setting changes here
    }
    potWrite(PIN_POT_CS12, LOW);
    potWrite(PIN_POT_CS24, LOW);
    Serial.print(RESP_OK);
}

// Enable a Digital Pot for DOWN adjustment
void potEnable(byte enablePin) {
    potWrite(PIN_POT_UD, HIGH);
    potWrite(enablePin, HIGH);
    Serial.print(RESP_OK);
}

// Step a digital Pot DOWN 1 step
void potStep() {
    if (digitalRead(PIN_POT_UD) == LOW)
        potWrite(PIN_POT_UD, HIGH);
    potWrite(PIN_POT_UD, LOW);          // The setting changes here
    Serial.print(RESP_OK);
}

// Disable DOWN adjustment of both Digital Pots
void potDisable() {
    potWrite(PIN_POT_UD, LOW);
    potWrite(PIN_POT_CS12, LOW);
    potWrite(PIN_POT_CS24, LOW);
    Serial.print(RESP_OK);
}

// Write a Digital Pot signal line, with subsequent delay
void potWrite(byte pin, byte state) {
    digitalWrite(pin, state);
    delayMicroseconds(DELAY_POT);   // Wait after a signal change
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
    Serial.print(RESP_OK);
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

