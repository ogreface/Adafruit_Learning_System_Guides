#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Ogre for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
Detects the frontmost macOS application and sends its name
over USB serial to the MacroPad once per second (only on change).
Also reads serial commands from the MacroPad (e.g. MIC_TOGGLE).

Retries automatically if the MacroPad is not connected.

Usage:
    python3 macropad_appname.py                        # auto-detect /dev/cu.usbmodem*
    python3 macropad_appname.py /dev/cu.usbmodem1234   # explicit port
"""

import fcntl
import glob
import os
import select
import subprocess
import sys
import time

RETRY_INTERVAL = 5  # seconds between connection retries

saved_input_volume = None

def toggle_mic():
    """Toggle macOS microphone mute via input volume."""
    global saved_input_volume
    if saved_input_volume is None:
        # Read current volume and mute in a single osascript call
        result = subprocess.run(
            ["osascript", "-e",
             "set vol to input volume of (get volume settings)\n"
             "set volume input volume 0\n"
             "return vol"],
            capture_output=True, text=True
        )
        saved_input_volume = int(result.stdout.strip())
        print(f"Mic: MUTED (was {saved_input_volume})")
    else:
        # Fire-and-forget unmute — no need to wait
        restore = saved_input_volume
        saved_input_volume = None
        subprocess.Popen(["osascript", "-e", f"set volume input volume {restore}"])
        print(f"Mic: UNMUTED (restored to {restore})")

def handle_serial_command(cmd):
    """Process a command received from the MacroPad."""
    if cmd == "MIC_TOGGLE":
        toggle_mic()
    else:
        print(f"Unknown command: {cmd!r}")

def find_port():
    """Return explicit port from argv, or auto-detect. Returns None if not found."""
    if len(sys.argv) >= 2:
        return sys.argv[1]
    ports = sorted(glob.glob("/dev/cu.usbmodem*"))
    if ports:
        return ports[0]
    return None

def open_port(port):
    """Configure and open the serial port. Returns fd or None on failure."""
    try:
        os.system(f"stty -f '{port}' 115200 raw -echo")
        fd = os.open(port, os.O_RDWR | os.O_NONBLOCK)
        # Flush startup gibberish (CircuitPython terminal escape sequences)
        while True:
            readable, _, _ = select.select([fd], [], [], 0.5)
            if readable:
                os.read(fd, 4096)
            else:
                break
        # Clear non-blocking for writes, we'll use select() for reads
        flags = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, flags & ~os.O_NONBLOCK)
        return fd
    except OSError as e:
        print(f"Failed to open {port}: {e}")
        return None

def run_session(fd):
    """Main loop for an active serial session. Returns on disconnect."""
    last_app = ""
    read_buf = b""
    try:
        while True:
            # Check for data from MacroPad (non-blocking via select)
            readable, _, _ = select.select([fd], [], [], 0)
            if readable:
                try:
                    chunk = os.read(fd, 256)
                    if not chunk:
                        print("MacroPad disconnected (EOF).")
                        return
                    read_buf += chunk
                    while b'\n' in read_buf:
                        line, read_buf = read_buf.split(b'\n', 1)
                        cmd = line.decode("utf-8", errors="replace").strip()
                        if cmd:
                            handle_serial_command(cmd)
                except OSError:
                    print("MacroPad disconnected (error).")
                    return

            # Detect frontmost app and send to MacroPad
            result = subprocess.run(
                ["osascript", "-e",
                 'tell application "System Events" to get name of '
                 'first application process whose frontmost is true'],
                capture_output=True, text=True
            )
            app = result.stdout.strip()
            if app and app != last_app:
                try:
                    os.write(fd, f"{app}\n".encode())
                except OSError:
                    print("MacroPad disconnected (write error).")
                    return
                last_app = app
                print(f"Sent: {app}")
            time.sleep(1)
    except KeyboardInterrupt:
        raise

def main():
    while True:
        port = find_port()
        if port is None:
            print(f"No MacroPad found. Retrying in {RETRY_INTERVAL}s...")
            time.sleep(RETRY_INTERVAL)
            continue

        print(f"Connecting to {port}...")
        fd = open_port(port)
        if fd is None:
            time.sleep(RETRY_INTERVAL)
            continue

        print(f"Connected to {port}")
        try:
            run_session(fd)
        except KeyboardInterrupt:
            print("\nStopped.")
            break
        finally:
            try:
                os.close(fd)
            except OSError:
                pass

        print(f"Reconnecting in {RETRY_INTERVAL}s...")
        time.sleep(RETRY_INTERVAL)

if __name__ == "__main__":
    main()
