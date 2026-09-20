"""
Phase 6 - Python to ESP32 Serial Communication
================================================

This script sends waste category commands (PLASTIC, ORGANIC, METAL) from
the Python AI application to an ESP32 board over a USB serial connection.

This phase ONLY proves the communication link:

    Laptop Python Program
            |
        USB Cable
            |
          ESP32
            |
    Correct category received

No servo motors, water pumps, or sensors are added in this phase.

Usage:
    1. Update SERIAL_PORT and BAUD_RATE below if needed.
    2. Run this script directly to enter TEST MODE:
           python python_sender.py
    3. Or import send_to_esp32() from your YOLO/detection project:
           from python_sender import send_to_esp32
           send_to_esp32("PLASTIC")
"""

import sys
import time

# ============================================================
# EASY-TO-CHANGE SETTINGS
# ============================================================
SERIAL_PORT = "COM3"      # Change this to match your ESP32's COM port
BAUD_RATE = 115200        # Must match Serial.begin() in esp32_receiver.ino
# ============================================================

# Try importing pyserial early so we can give a clear, friendly error
# message if it is not installed, instead of a raw traceback.
try:
    import serial
    from serial import SerialException
except ImportError:
    print("=" * 60)
    print("ERROR: The 'pyserial' package is not installed.")
    print("Install it by running:")
    print("    pip install pyserial")
    print("=" * 60)
    sys.exit(1)


# Only these commands are allowed to be sent to the ESP32.
VALID_CATEGORIES = {
    "PLASTIC": "PLASTIC",
    "ORGANIC": "ORGANIC",
    "METAL": "METAL",
}

# Module-level serial connection (created on first use, reused afterwards).
_serial_connection = None


def _open_connection():
    """
    Opens (or reuses) the serial connection to the ESP32.
    Returns the open serial.Serial object, or None if the connection
    could not be opened.
    """
    global _serial_connection

    # Reuse an already-open, healthy connection.
    if _serial_connection is not None and _serial_connection.is_open:
        return _serial_connection

    try:
        _serial_connection = serial.Serial(
            port=SERIAL_PORT,
            baudrate=BAUD_RATE,
            timeout=2,
        )
        # Give the ESP32 time to reset after the serial port opens
        # (opening a serial port triggers an auto-reset on most ESP32 boards).
        time.sleep(2)
        print(f"Connected to ESP32 on {SERIAL_PORT} at {BAUD_RATE} baud.")
        return _serial_connection

    except SerialException as e:
        error_text = str(e).lower()

        print("=" * 60)
        print("ERROR: Could not open the serial connection to the ESP32.")

        if "could not open port" in error_text or "no such file" in error_text:
            print(f"-> The port '{SERIAL_PORT}' was not found.")
            print("   Possible causes:")
            print("   - The ESP32 is not connected via USB.")
            print("   - You selected the wrong COM port.")
            print("   - The USB cable is charge-only (no data lines).")
            print("   Check Device Manager (Windows) for the correct COM port.")
        elif "permission" in error_text or "access is denied" in error_text or "in use" in error_text:
            print(f"-> The port '{SERIAL_PORT}' appears to be in use.")
            print("   Possible causes:")
            print("   - The Arduino IDE Serial Monitor is open on this port.")
            print("   - Another program is already using this port.")
            print("   Close other programs using the port and try again.")
        else:
            print(f"-> Wrong COM port, or the ESP32 is not connected.")
            print(f"   Details: {e}")

        print("=" * 60)
        _serial_connection = None
        return None


def send_to_esp32(category):
    """
    Sends a waste category command to the ESP32 over USB serial.

    Args:
        category (str): One of "PLASTIC", "ORGANIC", "METAL"
                         (case-insensitive).

    Returns:
        bool: True if the command was sent successfully, False otherwise.
    """
    if not isinstance(category, str):
        print(f"ERROR: Invalid category type: {type(category)}")
        return False

    normalized = category.strip().upper()

    if normalized not in VALID_CATEGORIES:
        print(f"ERROR: '{category}' is not a valid category. "
              f"Allowed commands: {', '.join(VALID_CATEGORIES.keys())}")
        return False

    connection = _open_connection()
    if connection is None:
        return False

    command = VALID_CATEGORIES[normalized]

    try:
        connection.write(f"{command}\n".encode("utf-8"))
        connection.flush()
        print(f"Sent: {command}")
        return True

    except SerialException as e:
        print("=" * 60)
        print("ERROR: Lost connection to the ESP32 while sending data.")
        print("Possible causes:")
        print("  - The USB cable was unplugged.")
        print("  - The ESP32 lost power or restarted.")
        print(f"  Details: {e}")
        print("=" * 60)

        # Close and clear the broken connection so the next call retries.
        try:
            connection.close()
        except Exception:
            pass
        global _serial_connection
        _serial_connection = None
        return False


def close_connection():
    """Closes the serial connection to the ESP32, if open."""
    global _serial_connection
    if _serial_connection is not None and _serial_connection.is_open:
        _serial_connection.close()
        print("Serial connection closed.")
    _serial_connection = None


def run_test_mode():
    """
    Interactive TEST MODE.

    Lets you manually trigger commands to verify the ESP32 link
    before wiring this into the YOLO detection project.

        1 -> PLASTIC
        2 -> ORGANIC
        3 -> METAL
        Q -> Quit
    """
    print("=" * 60)
    print("PHASE 6 - ESP32 SERIAL COMMUNICATION - TEST MODE")
    print("=" * 60)
    print(f"Port: {SERIAL_PORT}   Baud rate: {BAUD_RATE}")
    print()
    print("Select a category to send to the ESP32:")
    print("  1 -> PLASTIC")
    print("  2 -> ORGANIC")
    print("  3 -> METAL")
    print("  Q -> Quit")
    print("=" * 60)

    menu = {
        "1": "PLASTIC",
        "2": "ORGANIC",
        "3": "METAL",
    }

    while True:
        choice = input("\nEnter choice (1/2/3/Q): ").strip().upper()

        if choice == "Q":
            print("Exiting test mode.")
            break

        if choice in menu:
            send_to_esp32(menu[choice])
        else:
            print("Invalid choice. Please enter 1, 2, 3, or Q.")

    close_connection()


if __name__ == "__main__":
    try:
        run_test_mode()
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        close_connection()
