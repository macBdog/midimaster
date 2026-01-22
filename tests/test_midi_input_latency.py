"""Test script for measuring MIDI input latency.

This script listens for MIDI input (note on and note off messages),
mirrors them to the output device, and prints them to the console.
Compare the timing of physical input with audio output to measure latency.
"""

import sys
from pathlib import Path
import time
import mido

sys.path.insert(0, str(Path(__file__).parent.parent))

from midi_devices import MidiDevices
from notes import Notes


def main():
    print("=== MIDI Input Latency Test ===")
    print("This test mirrors MIDI input to output.")
    print("Play notes on your MIDI input device to measure latency.\n")

    midi = MidiDevices()

    # Display available devices
    print("Available MIDI input devices:")
    for i, device in enumerate(midi.input_devices):
        print(f"  {i}: {device}")
    print()

    print("Available MIDI output devices:")
    for i, device in enumerate(midi.output_devices):
        print(f"  {i}: {device}")
    print()

    # Open devices
    if midi.input_devices:
        midi.open_input_default()
    else:
        print("ERROR: No MIDI input devices found!")
        return

    if midi.output_devices:
        midi.open_output_default()
    else:
        print("ERROR: No MIDI output devices found!")
        return
    
    print("\nListening for MIDI input (Ctrl+C to stop)...\n")
    
    try:
        while True:
            #midi.update()

            # Check for incoming MIDI messages
            if midi.input_device_name:
                for msg in midi._input_port.iter_pending():
                    # Get timestamp for latency measurement
                    timestamp = time.time()
                    timestamp_ms = int((timestamp % 1) * 1000)
                    time_str = time.strftime("%H:%M:%S", time.localtime(timestamp))

                    # Handle note_on messages
                    if msg.type == "note_on":
                        note_name = Notes.note_number_to_name(msg.note)
                        print(f"[{time_str}.{timestamp_ms:03d}] Note ON:  {note_name} (MIDI {msg.note}) velocity={msg.velocity}")

                        # Mirror to output
                        midi.output(msg)

                    # Handle note_off messages
                    elif msg.type == "note_off":
                        note_name = Notes.note_number_to_name(msg.note)
                        print(f"[{time_str}.{timestamp_ms:03d}] Note OFF: {note_name} (MIDI {msg.note}) velocity={msg.velocity}")

                        # Mirror to output
                        midi.output(msg)

            # Small sleep to prevent busy-waiting
            time.sleep(0.001)

    except KeyboardInterrupt:
        print("\n\nStopping test...")

    finally:
        print("Sending all notes off...")
        for note in range(128):
            note_off = mido.Message("note_off", note=note, velocity=0)
            midi.output(note_off)
        midi.update()

        midi.end()
        print("MIDI devices closed. Test complete.")


if __name__ == "__main__":
    main()
