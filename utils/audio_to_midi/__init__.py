"""
Audio → MIDI melody extraction for MidiMaster.

Requires librosa (utility-only dependency)::

    pip install -r utils/audio_to_midi/requirements.txt

Usage:
    from audio_to_midi import convert
    result = convert("melody.wav", "melody.mid", clef="treble")
    print(result.bpm)  # auto-detected and pinned

CLI:
    python -m audio_to_midi convert song.wav -o song.mid --clef treble
"""

from audio_to_midi.convert import ConvertResult, convert
from audio_to_midi.quantize import CLEF_RANGES

__version__ = "0.2.0"
__all__ = ["convert", "ConvertResult", "CLEF_RANGES", "__version__"]
