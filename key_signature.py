class KeySignature:
    """Store and draw params of music key in reference to the midi meta-message for key signature."""

    NumAccidentals = 14
    SharpsAndFlats = {1: True, 3: True, 6: True, 8: True, 10: True, 13: True, 15: True, 18: True, 20: True}
    LookupTableKeyToIndex = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 8, 'A': 9, 'B': 11}
    OriginNote = 60

    def __init__(self):
        self._set_key('C')
        self.positions = [0.0] * KeySignature.NumAccidentals * 2

    def set(self, key:str, note_positions: list):
        self._set_key(key)
        self._set_accidental_positions(note_positions)

    def _set_key(self, key: str):
        self.sharps = []
        self.flats = []
        self.major = key.find("m") < 0
        self.key = key

        def add_sharps_and_flats(table):
            for _, acc in enumerate(table):
                if acc[1:] == 'b':
                    self.flats.append(KeySignature.LookupTableKeyToIndex[acc[0:1]])
                elif acc[1:] == '#':
                    self.sharps.append(KeySignature.LookupTableKeyToIndex[acc[0:1]])

        tonic = key.replace('m', '')
        if self.major:
            add_sharps_and_flats(KeySignature.LookupTableMajor[tonic])
        else:
            add_sharps_and_flats(KeySignature.LookupTableMinor[tonic])

    
    def _set_accidental_positions(self, note_positions: list):
        self.positions = [0.0 for x in self.positions]

        def set_key_pos(notes, offset: int):
            num_notes = len(notes)
            draw_count = 0
            pos_count = offset
            acc_pos_x = -0.69
            hspacing = 0.056

            if num_notes == 1:
                draw_index = 0
            else:
                draw_index = num_notes - 2

            while draw_index >= 0 and draw_index < num_notes:
                acc = KeySignature.OriginNote + notes[draw_index]
                # Key signatures are traditionally drawn in the upper registers
                if acc < 68:
                    acc += 12
                self.positions[pos_count] = acc_pos_x
                self.positions[pos_count+1] = note_positions[acc]
                pos_count += 2
                draw_count += 1
                acc_pos_x += hspacing
                if draw_count % 2 == 0:
                    draw_index -= 3
                    acc_pos_x -= hspacing * 1.333
                else:
                    draw_index += 1

        set_key_pos(self.sharps, 0)
        set_key_pos(self.flats, KeySignature.NumAccidentals)


    def get_accidental(self, note:int, prev_note:int, bar_accidentals:list) -> int:
        """Return the drawn note and the accidental character or None if extra notation is not required.
           If a note is a flat or sharp and not included in the key signature it should be draw with an accidental.
           If a note is included in a key signature's sharps or flats it should be drawn as the original note."""

        melody_dir_up = prev_note < note
        playable_note = note % 12
        if playable_note in KeySignature.SharpsAndFlats:
            if melody_dir_up:
                mod_note = playable_note - 1
                if mod_note in self.sharps:
                    return note - 1, None
                else:
                    return note - 1, 1
            else:
                mod_note = playable_note + 1
                if mod_note in self.flats:
                    return note + 1, None
                else:
                    return note - 1, -1
        elif playable_note in self.sharps:
            return note, 0
        elif playable_note in self.flats:
            return note, 0
        return note, None

    def __str__(self):
        return self.key

    LookupTableMajor = {
        'Cb':   ['Cb', 'Db', 'Eb', 'Fb', 'Gb', 'Ab', 'Bb'], # 7 flats
        'Gb':   ['Gb','Ab', 'Bb', 'Cb', 'Db',	'Eb'], # 6 flats
        'Db':   ['Db', 'Eb', 'Gb', 'Ab', 'Bb'], # 5 flats
        'Ab':   ['Ab', 'Bb', 'Db', 'Eb', ], # 4 flats
        'Eb':   ['Eb', 'Ab', 'Bb',], # 3 flats
        'Bb':   ['Bb', 'Eb',], # 2 flats
        'F':    ['Bb'], # 1 flat
        'C':    [], # no flats or sharps
        'G':    ['F#'], # 1 sharp
        'D':    ['F#', 'C#'], # 2 sharps
        'A':    ['C#', 'F#', 'G#'], # 3 sharps
        'E':    ['F#',	'G#', 'C#', 'D#'], # 4 sharps
        'B':    ['C#',	'D#', 'F#', 'G#', 'A#'], # 5 sharps
        'F#':   ['F#', 'G#','A#', 'C#','D#','E#'], # 6 sharps
        'C#':   ['C#', 'D#', 'E#', 'F#', 'G#', 'A#', 'B#'], # 7 sharps
    }

    LookupTableMinor = {
        'Ab':   ['Ab', 'Bb', 'Cb', 'Db', 'Eb', 'Fb', 'Gb'], # 7 flats
        'Eb':   ['Eb', 'Gb', 'Ab', 'Bb', 'Cb', 'Db'], # 6 flats
        'Bb':   ['Bb', 'Db', 'Eb', 'Gb', 'Ab'], # 5 flats
        'F':    ['Ab', 'Bb', 'Db', 'Eb'], # 4 flats
        'C':    ['Eb',	'Ab', 'Bb'], # 3 flats
        'G':    ['Bb', 'Eb'], # 2 flats
        'D':    ['Bb'], # 1 flat
        'A':    [], # no flats or sharps
        'E':    ['F#'], # 1 sharp
        'B':    ['C#', 'F#'], # 2 sharps
        'F#':   ['F#', 'G#', 'C#'], # 3 sharps
        'C#':   ['C#', 'D#', 'F#', 'G#'], # 4 sharps
        'G#':   ['G#', 'A#', 'C#', 'D#', 'F#'], # 5 sharps
        'D#':   ['D#', 'E#', 'F#', 'G#', 'A#', 'C#'], # 6 sharps
        'A#':   ['A#', 'B#', 'C#', 'D#', 'E#', 'F#', 'G#'], # 7 sharps
    }
