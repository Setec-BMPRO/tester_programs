/*

Software for ...
GEN8 - PE Jig Assembly 025227

*/

// Timing values in milliSeconds
#define serialtime      1000
#define buttontime      1000
#define unitchangedebounce  1000
#define serialrate      9600

// Digital Pins
int red_led = 9;
int orange_led = 10;
int green_led = 2;
int button = 3;
int magnets = 4;
int sensor_back = 5;
int sensor_side = 6;
int sensor_bottom = 7;
int screw_leds = 8;
// Analoge Pins
int screw_0 = 3;
int screw_1 = 4;
int screw_2 = 5;

// Global Variables
int screw_init[3], screw_read[3];
bool screw_measure, screws, base_in, back_in, side_in, lid_on, assembly, completed;

// IO Setup
void setup() {
  pinMode(red_led, OUTPUT);
  pinMode(orange_led, OUTPUT);
  pinMode(green_led, OUTPUT);
  pinMode(button, INPUT_PULLUP);
  pinMode(magnets, OUTPUT);
  pinMode(sensor_back, INPUT);
  pinMode(sensor_side, INPUT);
  pinMode(sensor_bottom, INPUT);
  pinMode(screw_leds, OUTPUT);
  analogReference(EXTERNAL);
  Serial.begin(serialrate);
}

// Main Program
void loop() {
  digitalWrite(screw_leds,HIGH);    

  led();
  outputs();
  serial_write();
  
  back_in = digitalRead(sensor_back);
  side_in = digitalRead(sensor_side);
  lid_on = digitalRead(sensor_bottom);

//  back_in = 0;
//  side_in = 0;

  if(assembly == 1){
    screws = 0;
    screw_measure = 0;
    assembly = 0;
    completed = 0;
  }
  if((back_in == 0) & (side_in == 0)){
    screw_adc();
  }
  else{
    screw_measure = 0;
  }
  if(completed == 1){
    if((digitalRead(sensor_side) == 1) & (digitalRead(sensor_back) == 1)){
      delay(unitchangedebounce);
      if((digitalRead(sensor_side) == 1) & (digitalRead(sensor_back) == 1)){
        assembly = 1;
      }
    }
  }
  if((back_in == 0) & (side_in == 0) & (screws == 1) & (lid_on == 0)){
    completed = 1;
  }
  if(digitalRead(button) == 0){
    delay(buttontime);
    if(digitalRead(button) == 0){
      completed = 1;
    }
  }
}
void outputs(){
  if((back_in == 0) & (side_in == 0) & (completed == 0)){
    digitalWrite(magnets,HIGH);
  }
  else{
    digitalWrite(magnets,LOW);
  }
}

void screw_adc(){
  outputs();
  if(screw_measure == 0){
    screw_init[0] = analogRead(screw_0);
    screw_init[1] = analogRead(screw_1);
    screw_init[2] = analogRead(screw_2);
    screw_measure = 1;
  }
  else{
    screw_read[0] = analogRead(screw_0);
    screw_read[1] = analogRead(screw_1);
    screw_read[2] = analogRead(screw_2);

    screws = 1;
    if((screw_init[0]-10) < screw_read[0]){
      screws = 0;
    }
    if((screw_init[1]-10) < screw_read[1]){
      screws = 0;
    }
    if((screw_init[2]-10) < screw_read[2]){
      screws = 0;
    }
  }
}

void led(){
  digitalWrite(red_led,LOW);
  digitalWrite(orange_led,LOW);
  digitalWrite(green_led,LOW);
    
  if((back_in == 0) & (side_in == 0)){
    digitalWrite(red_led,HIGH);
  }
  if(screws == 1){
    digitalWrite(orange_led,HIGH);
  }
  if(completed == 1){
    digitalWrite(green_led,HIGH);
  }
}

void serial_write() {
  int x;

  delay(serialtime);
  if(completed == 0){    
    if(back_in == 0){
      Serial.print("Back, ");
    }
    if(side_in == 0){
      Serial.print("Side, ");
    }
    if(lid_on == 0){
      Serial.print("Bottom, ");
    }
    if(screws == 1){
      Serial.print("Screws, ");
    }
    if(digitalRead(button) == 0){
      Serial.print("Button, ");
    }
    for(x=0; x<3; x++){
      Serial.print(screw_init[x]);
      Serial.print(", ");
    }
    for(x=0; x<3; x++){
      Serial.print(screw_read[x]);
      Serial.print(", ");
    }
      Serial.print("\n");
  }   
  else{
    if(assembly == 0){
      Serial.print("Assemply Completed ... Please Remove Unit!\n");
    }
    else{
      Serial.print("Unit Removed, Thank You!\n");
    }
  }
}


