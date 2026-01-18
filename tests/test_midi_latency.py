"""Test script for measuring MIDI output latency.

This script initializes MidiDevices and plays random notes every second,
printing to console for audio latency comparison.
"""

import sys
from pathlib import Path
import time
import numpy.random as rng
import mido

sys.path.insert(0, str(Path(__file__).parent.parent))

from midi_devices import MidiDevices
from notes import Notes


def main():
    print("=== MIDI Latency Test ===")
    print("This test plays random notes every second.")
    print("Compare console timestamps with audio output to measure latency.\n")
    
    # Initialize MIDI devices
    midi = MidiDevices()
    
    # Display available devices
    print("Available MIDI output devices:")
    for i, device in enumerate(midi.output_devices):
        print(f"  {i}: {device}")
    print()
    
    # Open default output device
    if midi.output_devices:
        midi.open_output_default()
    else:
        print("ERROR: No MIDI output devices found!")
        return
    
    print("\nStarting note playback (Ctrl+C to stop)...\n")
    
    try:
        note_count = 0
        while True:
            # Generate random note (MIDI notes 36-84 = C2 to C6)
            note_num = rng.randint(36, 85)
            note_name = Notes.note_number_to_name(note_num)
            velocity = rng.randint(80, 120)
            
            # Get timestamp for latency measurement
            timestamp = time.time()
            timestamp_ms = int((timestamp % 1) * 1000)
            time_str = time.strftime("%H:%M:%S", time.localtime(timestamp))
            
            # Create and send note_on message
            note_on = mido.Message("note_on", note=note_num, velocity=velocity)
            midi.output(note_on)
            midi.update()
            
            note_count += 1
            print(f"[{time_str}.{timestamp_ms:03d}] Note #{note_count}: {note_name} (MIDI {note_num}) velocity={velocity}")
            
            # Wait a short duration
            time.sleep(0.15)
            
            # Send note_off message
            note_off = mido.Message("note_off", note=note_num, velocity=0)
            midi.output(note_off)
            midi.update()
            
            # Wait until next second
            time.sleep(0.85)
            
    except KeyboardInterrupt:
        print("\n\nStopping test...")
    
    finally:
        # Clean up - send all notes off
        print("Sending all notes off...")
        for note in range(128):
            note_off = mido.Message("note_off", note=note, velocity=0)
            midi.output(note_off)
        midi.update()
        
        # Close MIDI devices
        midi.end()
        print("MIDI devices closed. Test complete.")


if __name__ == "__main__":
    main()
