//Name:         spa_reset
//By:           Rajiv Fonn
//Target MCU:   Arduino (ATmega328)
//Frequency:    X-TAL:16MHz
//Date:         06/05/13
//Description:  Outputs either a Reset Sequence or Simple Reset on the
//              RESET pin when triggered with TRIGGER_SEQ or TRIGGER_RES
//              respectively.
//              The trigger must be pulsed low to high.
//              The RESET pin is normally low. The signal driving the reset
//              pin of the micro is the inverse of that on the RESET pin.
//              Reset Sequence is high for 1 second, then 3 pulses, then
//              low again.
//              Simple Reset is high for 20mS then low again.

#define TRIGGER_SEQ     2   //Trigger input for Reset Sequence
#define TRIGGER_RES     3   //Trigger input for Simple Reset
#define RESET           7   //Outputs Reset Sequence/Simple Reset when triggered

//Variables
byte i;
byte state1 = HIGH;
byte state2 = HIGH;

void setup() {
  // initializes digital pins as input/output.
  pinMode(TRIGGER_SEQ, INPUT);
  pinMode(TRIGGER_RES, INPUT);
  pinMode(RESET, OUTPUT);
}

void loop()
{
  while(1)
  {
    digitalWrite(RESET, LOW);           //Reset pin of micro normally high
    state1 = digitalRead(TRIGGER_SEQ);  //Reads the status of the two trigger
    state2 = digitalRead(TRIGGER_RES);  //inputs

    //Reset Sequence
    if (state1 == LOW)
    {
      delay(20);                        //20mS debounce delay
      while(state1 == LOW)              //Waits for high again
        state1 = digitalRead(TRIGGER_SEQ);
      delay(20);                        //20mS debounce delay
      digitalWrite(RESET, HIGH);        //Reset pin of micro driven low
      delay(1000);                      //tVR delay
      for(i=0; i<3; i++)                //Pulse RESET 3 times
      {
        digitalWrite(RESET, LOW);
        delayMicroseconds(10);          //tRH delay (14uS)
        digitalWrite(RESET, HIGH);
        delayMicroseconds(50);          //tRL delay (55uS)
      }
    }
    //Simple Reset
    else if (state2 == LOW)
    {
      delay(20);                        //20mS debounce delay
      while(state2 == LOW)              //Waits for high again
        state2 = digitalRead(TRIGGER_RES);
      delay(20);                        //20mS debounce delay
      digitalWrite(RESET, HIGH);        //Reset pin of micro driven low
      delay(20);
      digitalWrite(RESET, LOW);
    }
    else {}
  }
}
