"""
AI-Based Smart Drainage Waste Detection and Automatic Segregation System
--------------------------------------------------------------------------
PHASE 8: Final Integration - ESP32 Serial Communication

This module reuses the exact communication conventions proven in
Phase 6 (phase6_esp32_communication/python_sender.py):

    - Same settings style (SERIAL_PORT, BAUD_RATE).
    - Same connect-once / reuse-connection approach.
    - Same 3 valid commands: PLASTIC, ORGANIC, METAL.
    - Same newline-terminated command format.
    - Same friendly error handling for disconnected / wrong port /
      busy port / lost-connection situations.

It only ADDS a USE_ESP32 on/off switch so main_final.py can keep
running normally (in "demo mode") on a laptop with no ESP32 attached.

No servo motors, sensors, or other hardware are added here - this
file only proves/handles the communication link, same as Phase 6.
"""

import sys
import time

# ============================================================
# EASY-TO-CHANGE SETTINGS
# ============================================================
USE_ESP32 = True          # Set to False to run main_final.py in DEMO MODE
                           # (no ESP32 required - commands are only printed).
SERIAL_PORT = "COM3"      # Change this to match your ESP32's COM port
BAUD_RATE = 115200        # Must match Serial.begin() in esp32_receiver.ino
# ============================================================

# pyserial is only required when USE_ESP32 = True. We import it lazily
# (inside connect_esp32) so that demo mode (USE_ESP32 = False) works
# even on a machine that never installed pyserial.
try:
    import serial
    from serial import SerialException
    _PYSERIAL_AVAILABLE = True
except ImportError:
    _PYSERIAL_AVAILABLE = False
    SerialException = Exception  # placeholder so type hints below don't break


# Only these commands are allowed to be sent to the ESP32
# (same set as Phase 6).
VALID_CATEGORIES = {
    "PLASTIC": "PLASTIC",
    "ORGANIC": "ORGANIC",
    "METAL": "METAL",
}

# Module-level serial connection (created on first use, reused afterwards).
_serial_connection = None


def connect_esp32():
    """
    Opens (or reuses) the serial connection to the ESP32.

    Returns the open serial.Serial object, or None if:
      - USE_ESP32 is False (demo mode - this is expected, not an error), or
      - the connection could not be opened (ESP32 disconnected, wrong
        COM port, port busy, etc. - a friendly message is printed).
    """
    global _serial_connection

    if not USE_ESP32:
        # Demo mode: the main AI program should keep running normally
        # without ever trying to open a serial port.
        return None

    if not _PYSERIAL_AVAILABLE:
        print("=" * 60)
        print("ERROR: The 'pyserial' package is not installed.")
        print("Install it by running:")
        print("    pip install pyserial")
        print("Continuing in DEMO MODE (no commands will be sent).")
        print("=" * 60)
        return None

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
        print(f"[ESP32] Connected on {SERIAL_PORT} at {BAUD_RATE} baud.")
        return _serial_connection

    except SerialException as e:
        error_text = str(e).lower()

        print("=" * 60)
        print("[ESP32] ERROR: Could not open the serial connection.")

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

        print("The AI program will keep running in DEMO MODE.")
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
        bool: True if the command was sent successfully, False otherwise
              (including when USE_ESP32 is False - demo mode - which is
              expected behavior, not a failure of the AI program).
    """
    if not isinstance(category, str):
        print(f"[ESP32] ERROR: Invalid category type: {type(category)}")
        return False

    normalized = category.strip().upper()

    if normalized not in VALID_CATEGORIES:
        print(f"[ESP32] ERROR: '{category}' is not a valid category. "
              f"Allowed commands: {', '.join(VALID_CATEGORIES.keys())}")
        return False

    if not USE_ESP32:
        # Demo mode: no hardware attached, just show what WOULD be sent.
        print(f"[DEMO MODE] Would send to ESP32: {normalized}")
        return False

    connection = connect_esp32()
    if connection is None:
        return False

    command = VALID_CATEGORIES[normalized]

    try:
        connection.write(f"{command}\n".encode("utf-8"))
        connection.flush()
        print(f"[ESP32] Sent: {command}")
        return True

    except SerialException as e:
        print("=" * 60)
        print("[ESP32] ERROR: Lost connection to the ESP32 while sending data.")
        print("Possible causes:")
        print("  - The USB cable was unplugged.")
        print("  - The ESP32 lost power or restarted.")
        print(f"  Details: {e}")
        print("The AI program will keep running in DEMO MODE.")
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
        print("[ESP32] Serial connection closed.")
    _serial_connection = None
