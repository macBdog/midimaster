# Backing stems

1-bar loops, **100 BPM**, **4/4**, **FLAC** 16-bit 44.1 kHz. Exact length **2.400 s**. Edit loop points at zero crossings. `.wav` is accepted as a fallback.

The mixer chains these by **scale degree** (1–6) for whatever key the song is in. Record a chord once; reuse it from other keys when the **root and quality** already exist.

## Layout

Keyless files stay in **`assets/backing/`**. Harmony lives in a **per-key folder**. The folder name is the key token: `C` → `c`, `G` → `g`, `Am` → `am`, `F#` → `fs`.

| Path | Role |
|------|------|
| `count_in.flac` | 1-bar count-in (shared, every key) |
| `drums.flac` | 1-bar drum groove (shared, every key) |
| `{key}/bass_{degree}.flac` | Bass, one scale degree |
| `{key}/comp_{instrument}_{degree}.flac` | Comp, one scale degree |

Examples: `c/bass_4.flac`, `c/comp_guitar_4.flac`, `g/bass_2.flac`.

`{degree}` is `1`–`6`. `{instrument}` is a short slug (`guitar`, `ep`). Options can pick Auto / Electric Piano / Guitar / Off.

A missing file for a degree is fine: that bar is **drums only** (and bass if bass exists). A new key can ship as a partial folder.

## What to play (every major key)

Use the **same qualities** as the C kit so loops stay interchangeable:

| Degree | Roman | Quality | In C |
|--------|-------|---------|------|
| 1 | I | maj6 | C6 |
| 2 | ii | min7 | Dm7 |
| 3 | iii | min7 | Em7 |
| 4 | IV | maj6 | F6 |
| 5 | V | **dom7** | G7 |
| 6 | vi | min7 | Am7 |

I and IV are **6** chords, not maj7. V is a **dominant 7**, not a 6. Do not “fix” V to match I — `G7` (V in C) is not `G6` (I in G). Only symlink when **both** root and quality match.

Same groove, register, and intensity on every hold. Bass is a 1-bar root ostinato (fifth is fine). No walk into the next chord. Comp stays on the chord — no destination-only voice leading.

## Session

100 BPM click + drums. **4 bars per new chord**, slice the best bar to 2.400 s.

Stand order is scale-degree order. Skip any degree you will symlink.

```
0     count-in (already recorded)
1–4   I   (maj6)
5–8   ii  (min7)
9–12  iii (min7)
13–16 IV  (maj6)
17–20 V   (dom7)
21–24 vi  (min7)
```

Export **bass + each comp** (`ep`, `guitar`) for every **new** chord. Do not re-export drums or count-in.

## Chord library on disk (C)

These six chords exist as bass + ep + guitar:

| File degree in `c/` | Chord |
|---------------------|-------|
| 1 | C6 |
| 2 | Dm7 |
| 3 | Em7 |
| 4 | F6 |
| 5 | G7 |
| 6 | Am7 |

Link to these. Record everything else.

## Next keys — link vs record

`link c/N` means all three files (`bass_N`, `comp_ep_N`, `comp_guitar_N`) → `../c/…_N`.

### G major (`g/`) — 3 new chords

| Deg | Roman | Need | Action |
|-----|-------|------|--------|
| 1 | I | G6 | **record** |
| 2 | ii | Am7 | link `c/6` |
| 3 | iii | Bm7 | **record** |
| 4 | IV | C6 | link `c/1` |
| 5 | V | D7 | **record** |
| 6 | vi | Em7 | link `c/3` |

### F major (`f/`) — 3 new chords

| Deg | Roman | Need | Action |
|-----|-------|------|--------|
| 1 | I | F6 | link `c/4` |
| 2 | ii | Gm7 | **record** |
| 3 | iii | Am7 | link `c/6` |
| 4 | IV | Bb6 | **record** |
| 5 | V | C7 | **record** (C6 is not C7) |
| 6 | vi | Dm7 | link `c/2` |

### D major (`d/`) — 5 new chords

| Deg | Roman | Need | Action |
|-----|-------|------|--------|
| 1 | I | D6 | **record** |
| 2 | ii | Em7 | link `c/3` |
| 3 | iii | F#m7 | **record** |
| 4 | IV | G6 | **record** |
| 5 | V | A7 | **record** |
| 6 | vi | Bm7 | **record** |

After G exists, `d/6` (Bm7) can link to `g/3` instead of a new take.

### A minor (`am/`) — natural minor, same file qualities

| Deg | Roman | Need | Action |
|-----|-------|------|--------|
| 1 | i | Am7 | link `c/6` |
| 2 | ii° | Bm7b5 | **record** (not in C) |
| 3 | III | C6 | link `c/1` |
| 4 | iv | Dm7 | link `c/2` |
| 5 | v | Em7 | link `c/3` (use `E7` / record if you want harmonic minor V) |
| 6 | VI | F6 | link `c/4` |

## Symlinks

Relative targets only. The mixer treats a symlink as a normal file.

Windows: enable **Developer Mode** (or run as admin) so Git can check links out.

From the new key folder (example: G ii → C vi):

```powershell
# assets/backing/g
foreach ($kind in @("bass", "comp_ep", "comp_guitar")) {
  New-Item -ItemType SymbolicLink -Path "$kind`_2.flac" -Target "..\c\$kind`_6.flac"
}
```

G’s three reusable degrees in one go:

```powershell
# assets/backing/g
$map = @{ 2 = 6; 4 = 1; 6 = 3 }
foreach ($deg in $map.Keys) {
  $src = $map[$deg]
  foreach ($kind in @("bass", "comp_ep", "comp_guitar")) {
    New-Item -ItemType SymbolicLink -Path "$kind`_$deg.flac" -Target "..\c\$kind`_$src.flac"
  }
}
```

Never link I to another key’s V (`g/1` ↛ `c/5`).

## After the files are on disk

The loader looks up `assets/backing/{key}/`. If any `bass_*` exists there, procedural songs in that key can use audio backing.

Venue albums are still generated in **C** (`procedural_songs.TIER_CONFIGS`). Adding `g/` does not switch career keys by itself — add `"G"` to a tier’s `"keys"` list when you want sets in G.

## Timing

| Spec | Value |
|------|--------|
| Tempo | **100 BPM** native |
| Length | 1 bar = 4 beats = **2.4 s** |
| Time signature | 4/4 |
| Stretch | game may time-stretch about **±10%** (≈90–110 BPM) |

## Progressions the game sequences

| Name | Degrees | In C | Style |
|------|---------|------|-------|
| `145` | 1 → 4 → 5 → 1 | C F G C | Classic |
| `1564` | 1 → 5 → 6 → 4 | C G Am F | Pop |
| `1645` | 1 → 6 → 4 → 5 | C Am F G | Doo-wop |
| `6415` | 6 → 4 → 1 → 5 | Am F C G | Minor pop |
| `251` | 2 → 5 → 1 | Dm G C | Jazz |
| `36251` | 3 → 6 → 2 → 5 → 1 | Em Am Dm G C | Turnaround |

Playback: bar 0 is `count_in.flac` only. Bar 1+ is drums + bass + one comp for the current degree.

## Current kit

- [x] `count_in.flac`, `drums.flac`
- [x] `c/` degrees 1–6, bass + ep + guitar
- [ ] `g/`, `f/`, `d/`, `am/` — record gaps, symlink the rest
