import enum
from collections import defaultdict

class NoteType(enum.Enum):
    Whole = 1
    Half = 2
    Quarter = 3
    Eight = 4
    Sixteenth = 5
    Thirtysecond = 5

class NoteDecoration(enum.Enum):
    Dotted = 1
    Accent = 2
    Natural = 3
    Sharp = 4
    Flat = 5

class Note():
    """Note is a POD style container for a note in a piece of music with representation."""

    NoteLengthTypes = {
        32: 1,    # Semibreve/Whole-note
        16: 2,    # Minum/Half-note
        8: 3,     # Crotchet/Quarter-note
        4: 4,     # Quaver/Eighth-note
        2: 5,     # Semi-quaver/Sixteenth-note
        1: 5,     # Demi-quaver/Thirty-second-note
    }
    RestCharacters = {
        32: "W",
        16: "H",
        8: "Q",
        4: "E",
        2: "S",
        1: "S",     
    }
    NoteOptions = {
        0: "Dotted",
        1: "Sharp",
        2: "Flat",
        3: "Natural",
        4: "Tie"
    }
    
    @staticmethod
    def get_quantized_length(note_length):
        for _, k in enumerate(Note.NoteLengthTypes):
            if note_length >= k:
                remainder = note_length - k
                dotted = remainder >= k / 2
                return k, dotted
        return 1, False

    def __init__(self, note: int, time: int, length: int):
        self.note = note
        self.time = time
        self.length = length