// Define X-axis stepper motor connections:
#define dirPinX 8
#define stepPinX 9
#define limitPinX A4

// Define Y-axis stepper motor connections:
#define dirPinY 4
#define stepPinY 3
#define limitPinY A5

// Define OPTO pin
#define OPTO 7

String tempString = "temp";

int PWM = 70;   // Delay between pin on and off, in microseconds
int PPR = 1600;  // Pulses per revolution, set using switches on driver

// Initiate variables for X revolutions and pulses
int revX = 0;
int modX = 0;

// Initiate variables for Y revolutions and pulses
int revY = 0;
int modY = 0;

void setup() {
  // Declare the X pins as output:
  pinMode(stepPinX, OUTPUT);
  pinMode(dirPinX, OUTPUT);
  pinMode(limitPinX, INPUT);

  // Declare the Y pins as output
  pinMode(stepPinY, OUTPUT);
  pinMode(dirPinY, OUTPUT);
  pinMode(limitPinY, INPUT);

  // Declare OPTO pin as output
  pinMode(OPTO, OUTPUT);

  // Set the spinning direction CW/CCW:
  digitalWrite(dirPinX, HIGH);
  digitalWrite(dirPinY, HIGH);
  digitalWrite(OPTO, HIGH);

  Serial.begin(115200);
}

void checkLimit() {
  // Function to check limit switches and stop motor at maximum position

  digitalWrite(dirPinX, HIGH);
  while (analogRead(limitPinX) != 1023) {
    digitalWrite(stepPinX, HIGH);
    delayMicroseconds(PWM);
    digitalWrite(stepPinX, LOW);
    delayMicroseconds(PWM);
  }

  digitalWrite(dirPinY, HIGH);
  while (analogRead(limitPinY) != 1023) {
    digitalWrite(stepPinY, HIGH);
    delayMicroseconds(PWM);
    digitalWrite(stepPinY, LOW);
    delayMicroseconds(PWM);
  }
}

void moveTo() {
  // Function to move the stepper motors based on received commands

  readMove();

  // Set direction for X position
  if (revX < 0 || modX < 0) {
    digitalWrite(dirPinX, LOW);
    revX *= -1;
    modX *= -1;
  } else if (revX > 0 || modX > 0) {
    digitalWrite(dirPinX, HIGH);
  }

  // Set direction for Y position
  if (revY < 0 || modY < 0) {
    digitalWrite(dirPinY, LOW);
    revY *= -1;
    modY *= -1;
  } else if (revY > 0 || modY > 0) {
    digitalWrite(dirPinY, HIGH);
  }

  // Move X axis
  while (revX != 0) {
    int i = PPR;
    while (i != 0) {
      digitalWrite(stepPinX, HIGH);
      delayMicroseconds(PWM);
      digitalWrite(stepPinX, LOW);
      delayMicroseconds(PWM);
      i -= 1;
    }
    revX -= 1;
  }
  while (modX != 0) {
    digitalWrite(stepPinX, HIGH);
    delayMicroseconds(PWM);
    digitalWrite(stepPinX, LOW);
    delayMicroseconds(PWM);
    modX -= 1;
  }

  // Move Y axis
  while (revY != 0) {
    int i = PPR;
    while (i != 0) {
      digitalWrite(stepPinY, HIGH);
      delayMicroseconds(PWM);
      digitalWrite(stepPinY, LOW);
      delayMicroseconds(PWM);
      i -= 1;
    }
    revY -= 1;
  }
  while (modY != 0) {
    digitalWrite(stepPinY, HIGH);
    delayMicroseconds(PWM);
    digitalWrite(stepPinY, LOW);
    delayMicroseconds(PWM);
    modY -= 1;
  }
}

void readMove() {
  // Function to read and parse movement commands from serial

  while (Serial.available() == 0) {
    continue;  // Wait for serial input
  }
  delayMicroseconds(1000);
  tempString = Serial.readStringUntil('\n');

  if (tempString == "HOME") {
    checkLimit();  // If command is HOME, execute homing procedure
    Serial.println(String("HOME"));
  } else {
    int spaceIndex = tempString.indexOf(' ');
    if (spaceIndex != -1) {
      String x_str = tempString.substring(0, spaceIndex);
      String y_str = tempString.substring(spaceIndex + 1);

      int commaIndexX = x_str.indexOf(',');
      revX = x_str.substring(0, commaIndexX).toInt();
      modX = x_str.substring(commaIndexX + 1).toInt();

      int commaIndexY = y_str.indexOf(',');
      revY = y_str.substring(0, commaIndexY).toInt();
      modY = y_str.substring(commaIndexY + 1).toInt();

      Serial.println(revX);
      Serial.println(modX);
      Serial.println(revY);
      Serial.println(modY);
    }
  }
}

void loop() {
  moveTo();  // Continuously execute movement based on serial commands
}
