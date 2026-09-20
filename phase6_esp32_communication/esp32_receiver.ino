/*
  Phase 6 - ESP32 Serial Receiver
  ================================

  Receives waste category commands sent from the Python application
  over USB serial and prints confirmation to the Serial Monitor.

  Recognized commands:
    PLASTIC
    ORGANIC
    METAL

  This phase ONLY proves the communication link:

      Laptop Python Program
              |
          USB Cable
              |
            ESP32
              |
      Correct category received

  IMPORTANT: This sketch does NOT control any servo motors, water pumps,
  or sensors. It only reads and prints the received category.
*/

// Must match BAUD_RATE in python_sender.py
const long BAUD_RATE = 115200;

// Buffer for building up the incoming command
String inputBuffer = "";

void setup() {
  // Start serial communication with the same baud rate as Python
  Serial.begin(BAUD_RATE);

  // Wait a moment for the serial connection to stabilize
  delay(1000);

  Serial.println("========================================");
  Serial.println("ESP32 Ready - Waiting for commands...");
  Serial.println("Recognized commands: PLASTIC, ORGANIC, METAL");
  Serial.println("========================================");
}

void loop() {
  // Read incoming serial data one character at a time
  while (Serial.available() > 0) {
    char incomingChar = Serial.read();

    if (incomingChar == '\n') {
      // Complete command received, process it
      processCommand(inputBuffer);
      inputBuffer = "";
    } else if (incomingChar != '\r') {
      // Ignore carriage return, build up the command otherwise
      inputBuffer += incomingChar;
    }
  }
}

void processCommand(String command) {
  // Trim any stray whitespace and normalize to uppercase
  command.trim();
  command.toUpperCase();

  if (command.length() == 0) {
    // Ignore empty lines
    return;
  }

  if (command == "PLASTIC") {
    Serial.println("Received: PLASTIC");
  } else if (command == "ORGANIC") {
    Serial.println("Received: ORGANIC");
  } else if (command == "METAL") {
    Serial.println("Received: METAL");
  } else {
    Serial.print("ERROR: Unknown command received: ");
    Serial.println(command);
  }
}
