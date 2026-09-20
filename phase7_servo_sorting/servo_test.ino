/*
  =========================================================
  PHASE 7 - SERVO TEST PROGRAM
  AI-Based Smart Drainage Waste Detection and Automatic
  Segregation System

  PURPOSE:
  This is a simple, beginner-friendly test sketch to check
  that your servo motor and wiring are working correctly
  BEFORE connecting it to the full AI sorting system
  (esp32_servo_sorting.ino).

  It slowly moves the servo through three test angles:
    30 degrees
    90 degrees
    150 degrees
  with a delay between each position, so you can visually
  confirm the servo moves smoothly and to the correct spots.

  Upload THIS file first. Only move on to
  esp32_servo_sorting.ino once you are sure the servo
  moves correctly.
  =========================================================
*/

#include <ESP32Servo.h>

// ---------------------------------------------------------
// EASY-TO-EDIT SETTINGS
// ---------------------------------------------------------

// Change this if you wire the servo to a different GPIO pin
#define SERVO_PIN 18

// Test angles - edit these if you want to test different
// positions. These match the sorting angles used in
// esp32_servo_sorting.ino by default.
int TEST_ANGLE_1 = 30;   // e.g. Plastic position
int TEST_ANGLE_2 = 90;   // e.g. Organic position
int TEST_ANGLE_3 = 150;  // e.g. Metal position

// Delay (in milliseconds) the servo waits at each position
const int HOLD_DELAY_MS = 1500;

// How many degrees to step per move, and delay between
// steps, to make the motion slow and smooth instead of a
// sudden jump (gentler on the servo and easier to observe)
const int STEP_DEGREES = 1;
const int STEP_DELAY_MS = 15;

// ---------------------------------------------------------

Servo testServo;
int currentAngle = 90; // assumed starting position

// Moves the servo gradually from its current angle to a
// target angle, one degree at a time, instead of snapping
// instantly. This is easier on cheap servos and lets you
// see the motion clearly.
void moveServoSlowly(int targetAngle) {
  if (targetAngle > currentAngle) {
    for (int pos = currentAngle; pos <= targetAngle; pos += STEP_DEGREES) {
      testServo.write(pos);
      delay(STEP_DELAY_MS);
    }
  } else {
    for (int pos = currentAngle; pos >= targetAngle; pos -= STEP_DEGREES) {
      testServo.write(pos);
      delay(STEP_DELAY_MS);
    }
  }
  currentAngle = targetAngle;
}

void setup() {
  Serial.begin(115200);
  delay(500);

  Serial.println("=========================================");
  Serial.println("Phase 7 - Servo Test Program");
  Serial.println("=========================================");
  Serial.print("Servo signal pin: GPIO ");
  Serial.println(SERVO_PIN);
  Serial.println("Moving servo through test angles...");
  Serial.println();

  // Allow standard PWM timers to be used for the servo
  ESP32PWM::allocateTimer(0);

  testServo.setPeriodHertz(50); // standard 50Hz servo signal
  testServo.attach(SERVO_PIN, 500, 2400); // min/max pulse width in microseconds
                                           // (typical safe range for most hobby servos)

  // Move to a known starting position first
  testServo.write(currentAngle);
  delay(1000);
}

void loop() {
  Serial.print("Moving to angle 1: ");
  Serial.print(TEST_ANGLE_1);
  Serial.println(" degrees");
  moveServoSlowly(TEST_ANGLE_1);
  delay(HOLD_DELAY_MS);

  Serial.print("Moving to angle 2: ");
  Serial.print(TEST_ANGLE_2);
  Serial.println(" degrees");
  moveServoSlowly(TEST_ANGLE_2);
  delay(HOLD_DELAY_MS);

  Serial.print("Moving to angle 3: ");
  Serial.print(TEST_ANGLE_3);
  Serial.println(" degrees");
  moveServoSlowly(TEST_ANGLE_3);
  delay(HOLD_DELAY_MS);

  Serial.println("Cycle complete. Repeating...");
  Serial.println();
}
