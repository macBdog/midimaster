from enum import Enum, auto

class NoteType(Enum):
    NONE = 0
    WHOLE = auto()
    HALF = auto()
    QUARTER = auto()
    EIGHTH = auto()
    SIXTEENTH = auto()
    THIRTYSECOND = auto()
    REST_WHOLE = auto()
    REST_HALF = auto()
    REST_QUARTER = auto()
    REST_EIGHTH = auto()
    REST_SIXTEENTH = auto()
    REST_THIRTYSECOND = auto()


class NoteDecoration(Enum):
    """Fit all note decoration types into an int matching values in the shader."""
    NONE = 0
    FLAT = auto()
    NATURAL = auto()
    SHARP = auto()
    DOTTED = auto()
    DOTTED_FLAT = auto()
    DOTTED_NATURAL = auto()
    DOTTED_SHARP = auto()


class Note():
    """Note is a POD style container for a note in a piece of music with representation."""

    NoteLengthTypes = {
        32: 1,    # Semibreve/Whole-note
        16: 2,    # Minum/Half-note
        8: 3,     # Crotchet/Quarter-note
        4: 4,     # Quaver/Eighth-note
        2: 5,     # Semi-quaver/Sixteenth-note
        1: 6,     # Demi-quaver/Thirty-second-note
    }
    
    @staticmethod
    def get_quantized_length(note_length):
        for _, k in enumerate(Note.NoteLengthTypes):
            if note_length >= k:
                remainder = note_length - k
                dotted = remainder >= k / 2
                return k, dotted
        return 1, False


    @staticmethod
    def get_quanitized_rest(note_length):
        for _, k in enumerate(Note.NoteLengthTypes):
            if note_length >= k:
                return k
        return 1


    @staticmethod
    def get_note_type(length) -> NoteType:
        return NoteType(Note.NoteLengthTypes[length])


    @staticmethod
    def get_rest_type(length) -> NoteType:
        return NoteType(Note.NoteLengthTypes[length] + NoteType.THIRTYSECOND.value)


    def __init__(self, note: int, time: int, length: int):
        # These fields come from the music file and are required for playing
        self.note = note
        self.time = time
        self.length = length
        
        # These fields are for drawing notation are post-processed
        self.pos = [0.0, 0.0]
        self.type = NoteType.NONE
        self.decoration = NoteDecoration.NONE
        self.hat = [0.0, 0.0]
        self.tie = 0.0

    def is_decorated(self) -> bool: return self.type.value > 0

    def decorate(self, pos: list, type: NoteType, decoration: NoteDecoration, hat: list, tie: float):
        self.pos = pos
        self.type = type
        if decoration is not None:
            self.decoration = decoration

        if hat is not None:
            self.hat = hat

        if tie is not None:
            self.tie = tie
