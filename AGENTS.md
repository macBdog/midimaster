# MidiMaster - Agent Development Notes

## Project Overview
MidiMaster is a rhythm game written in Python that uses musical score notation for display. Note rendering is done in GLSL shaders for performance. The game reads MIDI files and displays them as musical notation on a staff, allowing players to learn and play along.

## Technology Stack
- **Language**: Python 3.13
- **Graphics**: OpenGL with custom GLSL shaders
- **MIDI**: mido library for MIDI file parsing and device I/O
- **UI**: Custom UI system (gamejam framework - git submodule)
- **Rendering**: GPU-accelerated note rendering via fragment shaders

## Project Structure

### Core Components

#### 1. SongBook ([song_book.py](song_book.py))
- Persistent storage for game data and settings
- Stores:
  - Albums collection
  - Default song selection
  - MIDI device preferences
  - Game options (including `show_note_names` bool)
  - Output latency settings
- Serialized using Python pickle to `ext/songs.pkl`
- Version controlled with migration support

**Key Settings:**
- `show_note_names` (bool, line 52): Controls whether note letters (A-G) are displayed on notes during gameplay

#### 2. NoteRender ([note_render.py](note_render.py))
- Manages GPU-based note rendering
- Handles up to 32 simultaneous notes on screen
- Uses shader preprocessing to inject runtime values into GLSL code

**Shader Preprocessing System:**
- Line 36-46: Creates `shader_substitutes` dictionary
- Replaces preprocessor macros in shader source before compilation
- Current substitutions:
  - `NUM_NOTES`: Number of notes to render (32)
  - `NUM_KEY_SIG`: Number of key signature accidentals
  - Staff positioning and spacing values
- Uses `Graphics.process_shader_source()` to apply substitutions

**Note Lifecycle:**
1. Notes assigned to slots via `assign()` method
2. Note data uploaded to GPU uniforms every frame via `draw()`
3. Shader renders all notes in parallel
4. Notes recycled when they scroll off screen

#### 3. Notes Fragment Shader ([ext/shaders/notes.frag](ext/shaders/notes.frag))
- GLSL fragment shader that draws musical notation
- Renders:
  - Note heads (whole, half, quarter, eighth, sixteenth, etc.)
  - Note stems and flags
  - Accidentals (sharps, flats, naturals)
  - Ties and slurs
  - Staff lines
  - Key signatures
  - **Note letters (A-G)** when enabled

**Note Name Display:**
- Line 25: `#define note_names 1` - Preprocessor macro controlling note letter display
- Line 302-307: Conditional rendering of note letters based on `note_names` value
- `drawLetter()` function (lines 178-273): Renders A-G letters using procedural geometry
- Letters positioned at `note_name_y` (0.988) with size `note_name_size` (0.035)

#### 4. MidiMaster ([midimaster.py](midimaster.py))
- Main game controller and event loop
- Initialization flow (prepare method, lines 67-122):
  1. Load songbook from disk
  2. Process command-line song additions
  3. Open MIDI input/output devices
  4. Create Staff, Menu, and Font systems
  5. Create NoteRender instance (line 111)
  6. Create Music player
  7. Setup input handlers

**Component Initialization:**
```python
self.staff = Staff()
self.note_render = NoteRender(self.graphics, self.staff)  # Line 111
self.music = Music(self.graphics, self.note_render, self.staff)
```

## Data Flow: SongBook Settings to Shader

### Current Issue
The `SongBook.show_note_names` boolean exists but is not connected to the shader's `note_names` preprocessor macro. The shader currently always shows note letters because `note_names` is hardcoded to `1`.

### Required Connection Points

1. **Source**: `SongBook.show_note_names` (bool)
   - Location: [song_book.py:52](song_book.py:52)
   - Default: False

2. **Intermediate**: `NoteRender.__init__()` shader preprocessing
   - Location: [note_render.py:36-46](note_render.py:36-46)
   - Currently: No substitution for `note_names`

3. **Target**: Shader preprocessor macro
   - Location: [ext/shaders/notes.frag:25](ext/shaders/notes.frag:25)
   - Currently: `#define note_names 1` (hardcoded)
   - Should be: `#define note_names {0 or 1}` based on setting

### Implementation Plan (IMPLEMENTED ✅)

**Approach**: Runtime uniform (allows dynamic setting changes between songs)

#### Step 1: Change Shader Macro to Uniform ✅
**File**: [ext/shaders/notes.frag:25](ext/shaders/notes.frag:25)

Changed:
```glsl
#define note_names 1
```

To:
```glsl
uniform int note_names;
```

The existing conditional at line 302 works without modification:
```glsl
if (note_names > 0 && note_type < note_type_rest_whole)
```

#### Step 2: Add Uniform Location ✅
**File**: [note_render.py:53](note_render.py:53)

Added after existing uniform locations:
```python
self.note_names_id = glGetUniformLocation(self.shader, "note_names")
```

Also added `glUniform1i` import to OpenGL.GL imports.

#### Step 3: Store SongBook Reference ✅
**File**: [note_render.py:27-28](note_render.py:27-28)

Changed constructor signature and stored reference:
```python
def __init__(self, graphics: Graphics, staff: Staff, songbook: SongBook):
    self.staff = staff
    self.songbook = songbook
    # ... rest of init
```

Added import: `from song_book import SongBook`

#### Step 4: Update Uniform Each Frame ✅
**File**: [note_render.py:189](note_render.py:189)

Added to `note_uniforms()` function inside `draw()`:
```python
glUniform1i(self.note_names_id, 1 if self.songbook.show_note_names else 0)
```

This reads the current value from songbook each frame, enabling dynamic updates.

#### Step 5: Update MidiMaster Instantiation ✅
**File**: [midimaster.py:111](midimaster.py:111)

Changed:
```python
self.note_render = NoteRender(self.graphics, self.staff, self.songbook)
```

### Why Runtime Uniform Approach?

**Chosen because**:
✅ Setting changes take effect immediately (no restart required)
✅ Player can change setting between songs in same session
✅ Minimal performance overhead (one int uniform + one branch per fragment)
✅ Simpler than shader recompilation approach

**Not using preprocessor substitution because**:
❌ Would require shader recompilation when setting changes
❌ Setting would be locked at game startup
❌ Player would need to restart game to see changes

## Shader Preprocessing System Details

The `Graphics.process_shader_source()` function (from gamejam framework):
- Takes shader source string and substitution dictionary
- Performs string replacement for each key-value pair
- Returns modified shader source for compilation

**Pattern for substitutions**:
```python
{
    "MACRO_NAME": value,                    # Simple value substitution
    "#define name old": "#define name new", # Full define line replacement
}
```

## Testing Checklist

After implementing the change:

1. **Verify with show_note_names = True**:
   - [ ] Note letters (A-G) appear on notes during gameplay
   - [ ] Letters positioned correctly under each note
   - [ ] All 7 letters render correctly (A, B, C, D, E, F, G)

2. **Verify with show_note_names = False**:
   - [ ] No note letters appear on notes
   - [ ] Note heads, stems, and other notation still render correctly
   - [ ] No visual artifacts where letters would be

3. **Verify persistence**:
   - [ ] Setting saved in songbook persists across sessions
   - [ ] Setting loaded correctly on startup

4. **Edge cases**:
   - [ ] Rest notes don't show letters (already handled in shader, line 302)
   - [ ] Performance impact negligible

## GameJam Framework Dependency

MidiMaster is built on the **GameJam** rendering framework located at `C:\projects\gamejam`.

**See**: [C:\projects\gamejam\AGENTS.md](C:\projects\gamejam\AGENTS.md) for complete framework documentation.

### Key Components Used by MidiMaster:

1. **Graphics.process_shader_source()** - String substitution for shader preprocessing
   - Used in [note_render.py:38-46](note_render.py:38-46) to inject staff positioning constants
   - Simple find/replace before shader compilation

2. **SpriteTexture** - Custom shader-based sprite rendering
   - Used for note rendering with custom `notes.frag` shader
   - Supports custom uniform callbacks

3. **Font** - GPU-accelerated text rendering
   - FreeType-based glyph atlas
   - Used for UI text and note letters

4. **Input** - Event-driven keyboard/MIDI handling
   - Key mapping system for game controls
   - MIDI device integration

5. **Gui/Widget** - Hierarchical UI system
   - Menu system and dialogs
   - YAML-based layout persistence

6. **GameJam** - Main game loop base class
   - MidiMaster extends this for core loop
   - Built-in profiler and debug mode

## Additional Notes

- The shader uses procedural geometry to draw letters (no texture atlas)
- Letter drawing code is quite extensive (lines 178-273) with each letter defined as strokes and ellipses
- The note letter calculation uses modulo arithmetic to map staff position to letter (line 305)
- Gamejam framework is located at C:\projects\gamejam (separate repository)
- The game supports both performance mode and "pause & learn" mode

## Menu System Integration

For future work, the `show_note_names` setting could be exposed in the options menu:
- Menu system: [menu.py](menu.py)
- Menu functions: [menu_func.py](menu_func.py)
- Could add a checkbox/toggle in options menu
- Would require adding UI widget and callback to modify `songbook.show_note_names`
- Callback would need to rebuild shader with new setting (recreate NoteRender instance)
