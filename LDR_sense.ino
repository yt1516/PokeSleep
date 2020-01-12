// Arduino code for converting the analog LDR data to digital //
// and send to the Pi.

int lightPin = A1;
int lightSwitch = 9;
int lightLevel = 0;

void setup() {
  digitalWrite(lightSwitch, LOW);
  Serial.begin(9600);
}

void loop() {
  if (analogRead(lightPin) >= 300) {
    digitalWrite(lightSwitch, HIGH);
  }
  else {
    digitalWrite(lightSwitch, LOW);
  }

  delay(1000);
}
