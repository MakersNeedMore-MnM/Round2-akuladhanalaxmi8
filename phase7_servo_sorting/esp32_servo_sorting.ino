/*
  =========================================================
  PHASE 7 - ESP32 + SERVO SORTING GATE CONTROL
  AI-Based Smart Drainage Waste Detection and Automatic
  Segregation System

  PIPELINE:
  Python (Phase 4/5 detection) 
      -> USB Serial (Phase 6) 
      -> ESP32 receives category text (this phase)
      -> Servo rotates sorting gate to correct position
      -> Waste falls into the correct container

  This sketch listens for one of three text commands sent
  over USB Serial from the existing Phase 6 Python program:

      PLASTIC
      ORGANIC
      METAL

  On receiving a valid command, it rotates a single servo
  motor (acting as the sorting flap/gate) to the angle
  configured for that category, then prints a confirmation
  message back over Serial.

  This phase does NOT modify Phases 1-6 and does NOT add
  any extra sensors, pumps, or actuators - only the sorting
  servo described in the project goal.
  =========================================================
*/

#include <ESP32Servo.h>

// ==========================================================
// EASY-TO-EDIT SETTINGS
// ==========================================================

// Change this if you wire the servo to a different GPIO pin
#define SERVO_PIN 18

// Servo angle for each waste category.
// Adjust these to match the real physical position of your
// sorting gate for each container (see README.md, section 11).
int PLASTIC_ANGLE = 30;
int ORGANIC_ANGLE = 90;
int METAL_ANGLE   = 150;

// Optional: a neutral/idle angle the gate returns to (or
// stays at) when no valid command has been received yet.
// Set equal to ORGANIC_ANGLE, or any angle you prefer.
int IDLE_ANGLE = 90;

// Motion smoothing settings (keeps movement gentle instead
// of a sudden snap, same idea as servo_test.ino)
const int STEP_DEGREES = 1;
const int STEP_DELAY_MS = 15;

// ==========================================================

Servo sortingServo;
int currentAngle = IDLE_ANGLE;

// Buffer used to build up an incoming line of text from
// Serial until a newline character is received.
String inputBuffer = "";

// Moves the servo gradually to the target angle instead of
// snapping instantly, which is gentler on the servo and the
// physical gate mechanism.
void moveServoTo(int targetAngle) {
  if (targetAngle == currentAngle) {
    return; // already there, nothing to do
  }

  if (targetAngle > currentAngle) {
    for (int pos = currentAngle; pos <= targetAngle; pos += STEP_DEGREES) {
      sortingServo.write(pos);
      delay(STEP_DELAY_MS);
    }
  } else {
    for (int pos = currentAngle; pos >= targetAngle; pos -= STEP_DEGREES) {
      sortingServo.write(pos);
      delay(STEP_DELAY_MS);
    }
  }

  currentAngle = targetAngle;
}

// Handles one fully-received command line (already trimmed
// of whitespace/newline characters).
void handleCommand(String command) {
  command.trim();
  command.toUpperCase();

  if (command.length() == 0) {
    // Ignore empty lines (e.g. stray newline characters)
    return;
  }

  Serial.print("Received: ");
  Serial.println(command);

  if (command == "PLASTIC") {
    moveServoTo(PLASTIC_ANGLE);
    Serial.println("Servo moved to Plastic position");
  } else if (command == "ORGANIC") {
    moveServoTo(ORGANIC_ANGLE);
    Serial.println("Servo moved to Organic position");
  } else if (command == "METAL") {
    moveServoTo(METAL_ANGLE);
    Serial.println("Servo moved to Metal position");
  } else {
    // Handle invalid/unrecognized commands safely -
    // do not move the servo, just report the problem.
    Serial.print("Unknown command ignored: ");
    Serial.println(command);
  }

  Serial.println();
}

void setup() {
  Serial.begin(115200);
  delay(500);

  Serial.println("=========================================");
  Serial.println("Phase 7 - ESP32 Servo Sorting Gate Control");
  Serial.println("=========================================");
  Serial.print("Servo signal pin: GPIO ");
  Serial.println(SERVO_PIN);
  Serial.println("Waiting for commands: PLASTIC / ORGANIC / METAL");
  Serial.println();

  // Allow standard PWM timers to be used for the servo
  ESP32PWM::allocateTimer(0);

  sortingServo.setPeriodHertz(50); // standard 50Hz servo signal
  sortingServo.attach(SERVO_PIN, 500, 2400); // min/max pulse width in microseconds
                                              // (typical safe range for most hobby servos)

  // Move to the idle/starting position
  sortingServo.write(currentAngle);
  delay(1000);
}

void loop() {
  // Read characters as they arrive and build up a line.
  // Commands are terminated by a newline character ('\n'),
  // matching the Phase 6 Python program's serial writes.
  while (Serial.available() > 0) {
    char incomingChar = Serial.read();

    if (incomingChar == '\n') {
      handleCommand(inputBuffer);
      inputBuffer = ""; // reset for the next command
    } else if (incomingChar != '\r') {
      // Ignore carriage return characters; append everything else
      inputBuffer += incomingChar;
    }
  }
}
