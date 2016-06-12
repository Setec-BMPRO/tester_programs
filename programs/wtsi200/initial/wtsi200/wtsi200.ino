//Name:                 wtsi200
//By:                   Rajiv Fonn
//MCU:                  Arduino (ATmega328)
//Frequency:            X-TAL:16MHz
//Date:                 12/08/2013
//Description:          Serial Programming the flash memory of ATtiny1634 (target) using the SPI bus.

// include the SPI library:
#include <SPI.h>
#include <avr/pgmspace.h>
#include "myprogram.h"

//Definitions
//States
#define STATE_START     0               //Waiting for the start button to be pressed
#define STATE_PROGRAM   1               //Programs the target microprocessor
#define STATE_TEST      2               //Tests the unit
#define STATE_CLOSE     3               //Cleans up and switches power off

//Error codes
#define ERR_NONE        0               //No Error
#define ERR_PGMEN       1               //Enable Programming error
#define ERR_ERASE       2               //Erase Flash Error
#define ERR_WRITE       3               //Write Flash Error
#define ERR_VERIFY      4               //Verification Error
#define ERR_TEST        5               //Test Error

//Test limits
#define LIMIT1_LO       3.0             //Water level-1 low limit
#define LIMIT1_HI       3.5             //Water level-1 high limit
#define LIMIT2_LO       2.3370          //Water level-2 low limit
#define LIMIT2_HI       2.5830          //Water level-2 high limit
#define LIMIT3_LO       1.6245          //Water level-3 low limit
#define LIMIT3_HI       1.7955          //Water level-3 high limit
#define LIMIT4_LO       0               //Water level-4 low limit
#define LIMIT4_HI       0.5             //Water level-4 high limit
#define toadc(x)        ((int)(((x) * 1024.0) / 5.0)) //Floating point to ADC Integer conversion
#define tovolt(x)       (((x) * 5.0) / 1024.0) //ADC Integer to Floating point conversion

//Output pin numbers
#define PASS_LED        4               //Green
#define FAIL_LED        5               //Red
#define BUTTON          6               //Push button to start programming
#define VCC             7               //Switches on Vcc to the target via relay (red)
#define TRIGGER         8               //100mS pulse triggers response
#define RESET_PULSE     9               //Used to pulse the Reset pin when SPI is enabled
#define RESET           10              //Controls the Reset pin when SPI is disabled(red)
#define S3              11              //Simulates Sensor S3 contacting water (brown)
#define S2              12              //Simulates Sensor S2 contacting water (purple)
#define S1              13              //Simulates Sensor S1 contacting water (white)

#define PAGE_SIZE       16              //Flash memory page size of the target in words


//Functions
void button();
void spi_config();
void poweron_sequence();
char enable_programming();
char erase_flash();
byte load_instruction(byte byte1, byte byte2, byte byte3, byte byte4);
char write_flash();
char load_page();
char commit_page(int num);
char verify();
char read_compare(word addr, byte lbyte, byte hbyte);
void disable_spi();
void water_level(char bars);
char measure(char level, float low, float high);
int get_reading(int chan);
void result(char err);

//Global variables
int array_index;           //Stores the index when iterating through the byte array "mycode".
char state;


void setup() {
        // initializes digital pins as input/output.
        pinMode(VCC, OUTPUT);
        pinMode(BUTTON, INPUT);
        pinMode(PASS_LED, OUTPUT);
        pinMode(FAIL_LED, OUTPUT);
        pinMode(RESET, OUTPUT);
        pinMode(RESET_PULSE, OUTPUT);
        pinMode(TRIGGER, OUTPUT);
        pinMode(S1, OUTPUT);
        pinMode(S2, OUTPUT);
        pinMode(S3, OUTPUT);
        pinMode(A0, INPUT);       //Tank1 input
        pinMode(A1, INPUT);       //Tank2 input
        pinMode(A2, INPUT);       //Tank3 input
        state = STATE_START;      //Waiting for the start button to be pressed
        digitalWrite(TRIGGER, HIGH);
        spi_config();
        analogReference(DEFAULT);
        Serial.begin(115200);
}

void loop()
{
        static char error, count, i;
        static int limits[] = {
                toadc(LIMIT1_LO), toadc(LIMIT1_HI),
                toadc(LIMIT2_LO), toadc(LIMIT2_HI),
                toadc(LIMIT3_LO), toadc(LIMIT3_HI),
                toadc(LIMIT4_LO), toadc(LIMIT4_HI)
        };

        switch (state)  {
                case STATE_START:
                        Serial.write("#Press the start button to test\n");
                        button();
                        digitalWrite(PASS_LED, LOW);
                        digitalWrite(FAIL_LED, LOW);
                        state = STATE_PROGRAM;
                        break;
                case STATE_PROGRAM:
                        error = ERR_NONE;
                        poweron_sequence();            //Target power on, SPI bus enabled
                        error = enable_programming();
                        if (error != ERR_NONE)
                                state = STATE_CLOSE;
                        else  {
                                error = erase_flash();
                                if (error != ERR_NONE)
                                        state = STATE_CLOSE;
                                else  {
                                        error = write_flash();
                                        if (error != ERR_NONE)
                                                state = STATE_CLOSE;
                                        else
                                                error = verify();
                                }
                        }
                        disable_spi();                 //SPI bus disabled, reset pin high
                        state = error ? STATE_CLOSE : STATE_TEST;
                        break;
                case STATE_TEST:
                        Serial.write("#Testing\n");
                        for (i = 1, error = ERR_NONE, count = 0; i < 5; i++, count += 2)  {
                                error |= measure(i, limits[count], limits[count + 1]);
                        }
                        state = STATE_CLOSE;
                        break;
                case STATE_CLOSE:
                        result(error);
                        error = ERR_NONE;
                        digitalWrite(S1, LOW);
                        digitalWrite(S2, LOW);
                        digitalWrite(S3, LOW);
                        digitalWrite(VCC, LOW);              //Target power off
                        Serial.write("#Power off\n");
                        state = STATE_START;
                        break;
                default:
                        state = STATE_START;
                        break;
        }
}


//Waits for a button to be pressed or a charcter 'S' from the serial port
void button()
{
        char condition;
        char c;

        condition = digitalRead(BUTTON);
        Serial.flush();
        //Waits for a low or character 'S'.
        //Sends 'E0' to serial port if 'S' recieved, or sends 'E1' for any other character.
        while ((condition == HIGH) && (c != 'S'))  {
                                condition = digitalRead(BUTTON);
                                if(Serial.available() > 0)  {
                                        c = Serial.read();
                                        Serial.write('E');
                                        if (c == 'S')
                                                Serial.write('0');
                                        else
                                                Serial.write('1');
                                }
                                delay(100);
        }
        while(condition == LOW)                //Waits for a high
                condition = digitalRead(BUTTON);
        delay(20);                             //Debounce delay
}


//Configuration statements for SPI bus
void spi_config()
{
        SPI.setClockDivider(SPI_CLOCK_DIV128);
}

//Power on sequence. Enables the SPI bus.
void poweron_sequence()
{
        SPI.begin();              //Initializes the SPI bus, setting SCK, MOSI, and SS to outputs, pulling SCK and MOSI low and SS high.
        digitalWrite(VCC, HIGH);  //Powers up the target
        Serial.write("#Power on\n");
        delay(50);                //Delay after power on
}


//Enables serial programming - TODO: Fix code
char enable_programming()
{
        byte reply;
        char err = ERR_NONE;

        SPI.transfer(0xAC);
        SPI.transfer(0x53);
        reply = SPI.transfer(0x00);
        SPI.transfer(0x00);
        if (reply != 0x53)  {
                digitalWrite(RESET_PULSE, HIGH);
                delay(20);
                digitalWrite(RESET_PULSE, LOW);
                SPI.transfer(0xAC);
                SPI.transfer(0x53);
                reply = SPI.transfer(0x00);
                SPI.transfer(0x00);
                if (reply != 0x53)
                        err = ERR_PGMEN;
        }
        return err;
}


//Complete erase of flash memory
char erase_flash()
{
        char err = ERR_NONE;

        Serial.write("#Erasing\n");
        load_instruction(0xAC, 0x80, 0x00, 0x00);
        delay(20);
        return err;
}


//Sends a programming instruction to the target via the SPI bus.
//Returns the reply when the fourth byte is sent.
byte load_instruction(byte byte1, byte byte2, byte byte3, byte byte4)
{
        byte reply;

        SPI.transfer(byte1);
        SPI.transfer(byte2);
        SPI.transfer(byte3);
        reply = SPI.transfer(byte4);
        return reply;
}

//Writes flash memory with the program code stored in the byte array 'mycode[]'.
char write_flash()
{
        int page_bytes;
        int N;                                    //Number of pages to program
        char err;

        page_bytes = PAGE_SIZE << 1;
        N = program_size / page_bytes;
        if ((program_size % page_bytes) != 0)
                N++;
        Serial.write("#Programming\n");
        array_index = 0;                          //Reset to first index of byte array "mycode"
        for (int i = 0; i < N; i++){
                err = load_page();
                if (err != ERR_NONE)
                        break;
                err = commit_page(i);
                if (err != ERR_NONE)
                        break;
        }
        return err;
}


//Loads the 32 byte/16 word Page Buffer with data from a byte array, byte by byte.
char load_page()
{
        byte lbyte, hbyte;
        char err = 0;

        //Serial.write("\nLoad Page Buffer>");
        for (int i = 0; ((i < PAGE_SIZE) && (array_index < program_size)); i++)  {
                //Serial.write("\nArray index:");
                //Serial.print(array_index, DEC);
                //Serial.write(" Buffer addr> ");
                //Serial.print(i, HEX);
                lbyte = pgm_read_byte(mycode + array_index);    //Gets data low byte
                load_instruction(0x40, 0x00, 0x00 + i, lbyte);    //Loads data low byte
                //Serial.write(" Lbyte:");
                //Serial.print(lbyte, HEX);
                array_index++;
                hbyte = pgm_read_byte(mycode + array_index);    //Gets data high byte
                load_instruction(0x48, 0x00, 0x00 + i, hbyte);    //Loads data high byte
                //Serial.write(" Hbyte:");
                //Serial.print(hbyte, HEX);
                array_index++;
        }
        return err;
}


//Stores the 32 byte/16 word Page Buffer in the correct addresses of flash memory.
//Flash address (start) of the page is calculated from the page number "num".
char commit_page(int num)
{
        byte addrL, addrH;
        char err = ERR_NONE;

        addrL = (num << 4);
        addrH = (num >> 4);
        load_instruction(0x4C, addrH, addrL, 0x00);
        delay(20);
        //Serial.write("\nWrite Page> ");
        //Serial.print(num, HEX);
        //Serial.write(" Flash addr> ");
        //Serial.print(addrH, HEX);
        //Serial.write(":");
        //Serial.print(addrL, HEX);
        return err;
}


//Verifies that data in a byte array compares to that written into flash memory
//starting from address 0x0000.
char verify()
{
        word addr;
        byte lbyte, hbyte;
        int last_address = program_size >> 1;
        char err;

        Serial.write("#Verifying\n");
        array_index = 0;                          //Reset to first index of byte array "mycode"
        for (addr = 0; addr < last_address; addr++)  {
                //Serial.write("\nArray[");
                //Serial.print(array_index, DEC);
                //Serial.write("]<=>Flash(");
                //Serial.print(addr, HEX);
                //Serial.write(")>");
                lbyte = pgm_read_byte(mycode + array_index);    //Gets data low byte from byte array
                array_index++;
                hbyte = pgm_read_byte(mycode + array_index);    //Gets data high byte from byte array
                array_index++;
                err = read_compare(addr, lbyte, hbyte);
                if (err != ERR_NONE)
                        break;
        }
        if (err == ERR_NONE)  {
                //Serial.write("\nFlash(");
                //Serial.print(addr, HEX);
                //Serial.write(")>");
                err = read_compare(addr, 0xFF, 0xFF);
        }
        return err;
}


//Reads low & high data bytes of a flash memory address location and compares
//with lbyte & hbyte respectively.
char read_compare(word addr, byte lbyte, byte hbyte)
{
        byte addrL, addrH, dataL, dataH;
        char err = 0;

        addrL = addr & 0xFF;
        addrH = addr >> 8;
        dataL = load_instruction(0x20, addrH, addrL, 0x00);
        dataH = load_instruction(0x28, addrH, addrL, 0x00);
        //Serial.write(" Lbyte:");
        //Serial.print(lbyte, HEX);
        //Serial.write("<=>");
        //Serial.print(dataL, HEX);
        //Serial.write(" Hbyte:");
        //Serial.print(hbyte, HEX);
        //Serial.write("<=>");
        //Serial.print(dataH, HEX);
        if ((dataL != lbyte) || (dataH != hbyte))  {
                err = ERR_VERIFY;
        }
        return err;
}


//Disables the SPI bus
void disable_spi()
{
        SPI.end();
        digitalWrite(RESET, LOW);            //Disconnects programming pins, Reset pin high.
}


//Gives a 100mS pulse to Tank1, Tank2, and Tank3 inputs, measures the responses, and
//compares against a limit. Returns a result.
char measure(char level, int low, int high)
{
        int value;
        char err, i;
        int channel[] = { A0, A1, A2  };

        water_level(level);
        digitalWrite(TRIGGER, LOW);
        delay(30);
        for (i = 0, err = ERR_NONE; i < 3; i++)  {
                value = get_reading(channel[i]);
                Serial.write("\"Level");
                Serial.print(level, DEC);
                Serial.write("/Ch");
                Serial.print(i + 1, DEC);
                Serial.write("\",");
                Serial.print(tovolt(value), 2);
                Serial.write(",");
                Serial.print(tovolt(low), 2);
                Serial.write(",");
                Serial.print(tovolt(high), 2);
                Serial.write("\n");
                if ((value < low) || (value > high))
                        err = ERR_TEST;
        }
        digitalWrite(TRIGGER, HIGH);
        return err;
}


// Gets an average reading using a moving average digital filter
//
//        X.Vi + (N - X).Vo
//  Vo' = -----------------
//              N
//
//  We are using X = 1 and N = 32
//
int get_reading(int chan)
{
        int value, result, i;

        // Reset filter
        value = analogRead(chan);    // Vi
        result = value;              // Vo
        // Run the averaging filter
        for (i = 0; i < 200; i++)  {
                value = analogRead(chan);  // Vi
        result = (value + (result << 5) - result) >> 5;  // Vo'
        }
        return result;
}


//Simulates the water level in a tank. Value in 'bars' indicates the following:
//1: Water level not contacting Sensor S3
//2: Water contacting Sensor S3
//3: Water contacting Sensors S3 & S2
//4: Water contacting Sensors S3, S2 & S1
void water_level(char bars)
{
        switch (bars)  {
                case 1:
                        digitalWrite(S1, LOW);
                        digitalWrite(S2, LOW);
                        digitalWrite(S3, LOW);
                        break;
                case 2:
                        digitalWrite(S1, LOW);
                        digitalWrite(S2, LOW);
                        digitalWrite(S3, HIGH);
                        break;
                case 3:
                        digitalWrite(S1, LOW);
                        digitalWrite(S2, HIGH);
                        digitalWrite(S3, HIGH);
                        break;
                case 4:
                        digitalWrite(S1, HIGH);
                        digitalWrite(S2, HIGH);
                        digitalWrite(S3, HIGH);
                        break;
                default:
                        break;
        }
        delay(1000);
}


//Lights up the green LED or red LED to indicate a pass or fail condition.
void result(char err)
{
        char x;

        x = err ? FAIL_LED : PASS_LED;
        digitalWrite(x, HIGH);

        Serial.write("\"Result\",");
        Serial.print(err, DEC);
        Serial.write(",\"");

        switch (err)  {
                case 0:
                        Serial.write("Pass");
                        break;
                case 1:
                        Serial.write("Enable Programming Error");
                        break;
                case 2:
                        Serial.write("Erase Flash Error");
                        break;
                case 3:
                        Serial.write("Write Flash Error");
                        break;
                case 4:
                        Serial.write("Verification Error");
                        break;
                case 5:
                        Serial.write("Test Error");
                        break;
                default:
                        Serial.write("Unknown error");
                        break;
        }
        Serial.write("\"\n");
}

