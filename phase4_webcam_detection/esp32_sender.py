"""ESP32 command sender preparation for the Phase 4 detector.

Simulation is enabled by default, so this module does not require an ESP32,
serial port, or pyserial package to run.
"""

# Keep simulation enabled until the ESP32 is connected.
SIMULATION_MODE = True

# Configure these values later when switching to real serial communication.
# Example Windows value: "COM3"
SERIAL_PORT = "COM3"
BAUD_RATE = 115200

VALID_COMMANDS = {"P", "O", "M"}
_last_command = None
_serial_connection = None


def send_command(command):
    """Send a changed waste command, or simulate sending it.

    Args:
        command: "P" for Plastic, "O" for Organic, "M" for Metal, or None.

    Returns:
        True when a new command was sent or simulated, otherwise False.
    """
    global _last_command

    if command is None:
        _last_command = None
        return False

    normalized_command = str(command).strip().upper()
    if normalized_command not in VALID_COMMANDS:
        raise ValueError(
            f"Invalid command {command!r}; expected P, O, M, or None."
        )

    if normalized_command == _last_command:
        return False

    if SIMULATION_MODE:
        print(f"[SIMULATION] Sending command to ESP32: {normalized_command}")
    else:
        _send_serial_command(normalized_command)

    _last_command = normalized_command
    return True


def _send_serial_command(command):
    """Send one command over serial when simulation mode is disabled."""
    global _serial_connection

    if _serial_connection is None or not _serial_connection.is_open:
        import serial

        _serial_connection = serial.Serial(
            port=SERIAL_PORT,
            baudrate=BAUD_RATE,
            timeout=2,
        )

    _serial_connection.write(f"{command}\n".encode("utf-8"))
    _serial_connection.flush()


def close_connection():
    """Close the optional serial connection."""
    global _serial_connection

    if _serial_connection is not None and _serial_connection.is_open:
        _serial_connection.close()
    _serial_connection = None


if __name__ == "__main__":
    send_command("P")
    send_command("P")
    send_command("M")
    close_connection()
