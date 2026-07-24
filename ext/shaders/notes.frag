// Notes fragment shader — GPU musical notation (staff, keys, notes, letters)
// Coordinates: UV 0→1, origin bottom-left after main() flips Y.

#version 430

in vec2 OutTexCoord;
out vec4 outColour;

uniform sampler2D SamplerTex;
uniform vec4 Colour;
uniform float DisplayRatio;

uniform vec2 KeyPositions[NUM_KEY_SIG]; // 0-6 # Sharp, 7-13 b Flat
uniform vec2 NotePositions[NUM_NOTES];
uniform vec4 NoteColours[NUM_NOTES];
uniform int NoteTypes[NUM_NOTES];
uniform int NoteDecoration[NUM_NOTES];
uniform vec2 NoteHats[NUM_NOTES];
uniform float NoteTies[NUM_NOTES];
uniform vec2 NoteExtra[NUM_NOTES];

#define antialias 0.08
#define note_size 0.1
#define note_slant vec2(0.33, 0.93496)
#define note_slant_alt vec2(0.73, 0.73)
#define note_spacing_32nd 0.015
#define stalk_length_base 0.2
#define stalk_length_max 0.399
#define stalk_length_min 0.10
#define beam_gap 0.022
#define flag_gap 0.032

uniform int note_names;
#define note_name_y 0.989
#define note_name_size 0.035

// --- note type ids (must match Python) ---------------------------------------
#define note_type_whole 1
#define note_type_half 2
#define note_type_quarter 3
#define note_type_eighth 4
#define note_type_sixteenth 5
#define note_type_thirtysecond 6
#define note_type_rest_whole 7
#define note_type_rest_half 8
#define note_type_rest_quarter 9
#define note_type_rest_eighth 10
#define note_type_rest_sixteenth 11
#define note_type_rest_thirtysecond 12

// --- staff layout (values replaced by NoteRender shader_substitutes) ---------
#define staff_note_spacing 0.03
#define staff_spacing staff_note_spacing * 2.0
#define staff_octave_spacing staff_note_spacing * 7.0
#define staff_pos_x 0.0
#define staff_pos_y 0.5
#define staff_pos vec2(staff_pos_x, staff_pos_y)
#define staff_width 1.0
#define staff_line_width 0.002

#define decoration_none 0
#define decoration_flat 1
#define decoration_natural 2
#define decoration_sharp 3
#define decoration_dotted 4
#define decoration_dotted_flat 5
#define decoration_dotted_natural 6
#define decoration_dotted_sharp 7

float sat(float x)
{
    return clamp(x, 0.0, 1.0);
}

float drawEllipse(in vec2 uv, in vec2 pos, vec2 dim)
{
    vec2 d = (uv - pos) / (dim * dim);
    if (abs(d.x) <= 1.0 && abs(d.y) < 1.0 && dot(d, d) < 1.0)
        return 1.0;
    return 0.0;
}

// Outer ellipse minus inner — used for rings, bowls, tails, ties
float drawRing(in vec2 uv, in vec2 outer_pos, in vec2 outer_dim,
               in vec2 inner_pos, in vec2 inner_dim)
{
    return sat(drawEllipse(uv, outer_pos, outer_dim) - drawEllipse(uv, inner_pos, inner_dim));
}

float drawRotatedEllipse(vec2 uv, vec2 pos, float size, bool altRot)
{
    float dim = 70.0;
    pos *= dim;
    vec2 diff = (altRot ? note_slant_alt : note_slant) * size;
    vec2 l = pos - diff;
    vec2 r = pos + diff;
    vec2 coord = uv * dim;
    return smoothstep(0.0, antialias, distance(l, r) + 1.0 - (distance(coord, l) + distance(coord, r)));
}

float drawRect(in vec2 uv, in vec2 center, in vec2 wh)
{
    vec2 disRec = abs(uv - center) - wh * 0.5;
    return sat(float(max(disRec.x, disRec.y) < 0.0));
}

float distanceToSegment(vec2 a, vec2 b, vec2 p)
{
    vec2 pa = p - a, ba = b - a;
    float h = sat(dot(pa, ba) / dot(ba, ba));
    return length(pa - ba * h);
}

float drawLineRounded(in vec2 uv, in vec2 start, in vec2 end, in float width)
{
    return 1.0 - smoothstep(width - antialias * 0.02, width, distanceToSegment(start, end, uv));
}

float drawLineSquare(in vec2 uv, in vec2 start, in vec2 end, in float width, bool vertical)
{
    float col = drawLineRounded(uv, start, end, width);
    vec2 clip_box;
    vec2 left_c, right_c;
    if (vertical)
    {
        clip_box = vec2(width * 4.0, 0.02);
        left_c = start;
        right_c = end;
    }
    else
    {
        clip_box = vec2(0.015, width * 4.0);
        left_c = start + vec2(clip_box.x * -0.5, 0.0);
        right_c = end + vec2(clip_box.x * 0.5, 0.0);
    }
    return sat(col - drawRect(uv, left_c, clip_box) - drawRect(uv, right_c, clip_box));
}

float drawAccidental(in vec2 uv, in vec2 p, int val, bool note_relative_pos)
{
    float width = 0.055;
    float thickness = 0.002;
    vec2 acc_pos = note_relative_pos ? p - vec2(0.02, 0.0) : p;

    if (val == 0)
    {
        // Natural
        float boxX = 0.01, boxY = 0.01;
        return drawRect(uv, acc_pos + vec2(0.0, -0.005), vec2(0.001, width))
             + drawRect(uv, acc_pos - vec2(boxX, -0.02), vec2(0.001, width))
             + drawLineSquare(uv, acc_pos + vec2(-boxX, -boxY), acc_pos + vec2(0.0, 0.0), thickness, false)
             + drawLineSquare(uv, acc_pos + vec2(-boxX, boxY),  acc_pos + vec2(0.0, 0.02), thickness, false);
    }
    if (val == 1)
    {
        // Sharp
        float hashX = 0.02;
        return drawRect(uv, acc_pos - vec2(0.004, 0.0), vec2(0.0025, width))
             + drawRect(uv, acc_pos - vec2(0.012, 0.005), vec2(0.0025, width))
             + drawLineSquare(uv, acc_pos - vec2(hashX, -0.002), acc_pos + vec2(0.005, 0.023), thickness, false)
             + drawLineSquare(uv, acc_pos - vec2(hashX, 0.022),  acc_pos + vec2(0.005, -0.003), thickness, false);
    }
    if (val == -1)
    {
        // Flat — stem + open bowl, clipped on the left
        vec2 bowl = acc_pos - vec2(0.015, 0.0);
        float little_b = drawRect(uv, acc_pos - vec2(0.015, -0.018), vec2(0.002, width));
        little_b += drawRotatedEllipse(uv, bowl, 0.5, true);
        little_b -= drawRotatedEllipse(uv, bowl, 0.15, false);
        little_b -= drawRect(uv, acc_pos - vec2(0.031, 0.0), vec2(0.03, 0.05));
        return little_b;
    }
    return 0.0;
}

float drawKeySignature(in vec2 uv)
{
    float key = 0.0;
    for (int i = 0; i < NUM_KEY_SIG; ++i)
    {
        if (abs(KeyPositions[i].x) + abs(KeyPositions[i].y) > 0.0)
        {
            vec2 p = (KeyPositions[i] + 1.0) * 0.5;
            int acc = i < NUM_KEY_SIG / 2 ? 1 : -1;
            key += drawAccidental(uv, p, acc, false);
        }
    }
    return key;
}

// Open bowl: outer ellipse with inner hole shifted by open_dx (opening direction)
float drawLetterBowl(in vec2 uv, in vec2 center, in vec2 dim, float open_dx)
{
    return drawRing(uv, center, dim, center + vec2(open_dx, 0.0), dim - vec2(0.0, 0.011));
}

// Vertical spine + horizontal bars at fractions of height (E / F / B)
float drawSpineBars(in vec2 uv, in vec2 top, float height, float bar_len,
                    float width, int bar_count, float bar_step)
{
    float col = drawLineRounded(uv, top, top + vec2(0.0, -height), width);
    for (int i = 0; i < bar_count; ++i)
    {
        vec2 s = top + vec2(0.0, -bar_step * float(i));
        col += drawLineRounded(uv, s, s + vec2(bar_len, 0.0), width);
    }
    return col;
}

float drawLetter(in vec2 uv, in vec2 p, int l)
{
    float l_width = note_name_size * 0.1;
    float h = note_name_size;
    float hr = 0.4; // horizontal stroke length ratio
    float open = h * hr * 0.35;
    vec2 top = vec2(p.x, note_name_y);
    float strokes = 0.0;

    switch (l)
    {
        case 0: // A — inverted V + crossbar
        {
            vec2 apex = top + vec2(h * hr, 0.0);
            strokes += drawLineRounded(uv, apex, apex + vec2(h * hr * 0.75, -h), l_width);
            strokes += drawLineRounded(uv, apex, apex + vec2(-h * hr * 0.75, -h), l_width);
            strokes += drawLineRounded(uv,
                apex + vec2(-h * hr * 0.35, h * -0.5),
                apex + vec2( h * hr * 0.35, h * -0.5), l_width);
            break;
        }
        case 1: // B — spine, three bars, two bowls
        {
            vec2 cs = vec2(h * 2.5, h * 3.0);
            float y1 = top.y - h * 0.25;
            float y2 = top.y - h * 0.75;
            strokes += drawLetterBowl(uv, vec2(top.x + 0.005, y1), cs, -open);
            strokes += drawLetterBowl(uv, vec2(top.x + 0.005, y2), cs * 1.05, -open);
            strokes += drawSpineBars(uv, top, h, h * hr * 0.5, l_width, 3, h * 0.5);
            strokes += drawEllipse(uv, top, vec2(h));
            break;
        }
        case 2: // C — open bowl to the right
        {
            strokes += drawLetterBowl(uv, vec2(top.x, top.y - h * 0.5),
                                      vec2(h * 3.0, h * 4.0), open);
            break;
        }
        case 3: // D — open bowl to the left + spine
        {
            strokes += drawLetterBowl(uv, vec2(top.x + 0.003, top.y - h * 0.5),
                                      vec2(h * 3.0, h * 4.0), -open);
            strokes += drawLineRounded(uv, top, top - vec2(0.0, h), l_width);
            break;
        }
        case 4: // E
            strokes += drawSpineBars(uv, top, h, h * hr, l_width, 3, h * 0.5);
            break;
        case 5: // F
            strokes += drawSpineBars(uv, top, h, h * hr, l_width, 2, h * 0.5);
            break;
        case 6: // G — C bowl + spur
        {
            strokes += drawLetterBowl(uv, vec2(top.x, top.y - h * 0.5),
                                      vec2(h * 3.0, h * 4.0), open);
            vec2 spur = top + vec2(h * 0.130, -h * 0.5);
            strokes += drawLineRounded(uv, spur, spur - vec2(h * 0.25, 0.0), l_width);
            strokes += drawLineRounded(uv, spur, spur - vec2(0.0, h * 0.5), l_width);
            break;
        }
    }
    return strokes;
}

float drawTie(in vec2 uv, in vec2 start, in vec2 end, bool above)
{
    vec2 dir = end - start;
    float elen = length(dir);
    vec2 mid = start + dir * 0.5 + vec2(-0.004, clamp(elen - 0.2, 0.0, 0.1) - 0.035);
    vec2 dim_lo = vec2(elen * 1.45, elen * 0.99);
    vec2 dim_hi = dim_lo * 1.15;
    float y_inner = above ? elen * -0.12 : elen * 0.12;
    return drawRing(uv, mid, dim_lo, mid + vec2(0.0, y_inner), dim_hi);
}

// Note parts: rests, ledger lines, tails, full note
// hat_size: joining beam between 8th/16th/32nd notes
//   .x = length; .y = end height delta
//   .x == 0 and .y < 0 → note is tied-into (no tail)
//   16ths draw a second beam; 32nds a third (toward the note head)
//
// extra_geo: stalk overrides
//   .x abs > 0 forces direction (+up / -down); .y added to stalk length
//   stalk length is clamped to [stalk_length_min, stalk_length_max]
float drawRest(in vec2 uv, in vec2 p, int note_type)
{
    if (note_type == note_type_rest_whole)
        return drawRect(uv, vec2(p.x, staff_pos_y + staff_note_spacing * 5.6), vec2(0.04, 0.03));

    if (note_type == note_type_rest_half)
        return drawRect(uv, vec2(p.x, staff_pos_y + staff_note_spacing * 4.4), vec2(0.04, 0.03));

    if (note_type == note_type_rest_quarter)
    {
        float col = drawLineRounded(uv, vec2(p.x - 0.015, staff_pos_y + 0.22),
                                        vec2(p.x - 0.001, staff_pos_y + 0.18), 0.0025);
        col += drawLineSquare(uv, vec2(p.x - 0.006, staff_pos_y + 0.19),
                                  vec2(p.x - 0.02,  staff_pos_y + 0.11), 0.009, true);
        col += drawLineRounded(uv, vec2(p.x - 0.025, staff_pos_y + 0.12),
                                   vec2(p.x - 0.011, staff_pos_y + 0.072), 0.0025);
        col += drawRing(uv,
            vec2(p.x - 0.022, staff_pos_y + 0.07), vec2(0.11, 0.14),
            vec2(p.x - 0.019, staff_pos_y + 0.062), vec2(0.1, 0.13));
        return sat(col);
    }

    // 8th / 16th / 32nd rests share the same glyph
    float col = drawLineRounded(uv, vec2(p.x - 0.001, staff_pos_y + 0.173),
                                    vec2(p.x - 0.02,  staff_pos_y + 0.06), 0.0025);
    col += drawEllipse(uv, vec2(p.x - 0.024, staff_pos_y + 0.15), vec2(0.105, 0.135));
    col += drawLineRounded(uv, vec2(p.x - 0.016, staff_pos_y + 0.14),
                               vec2(p.x - 0.003, staff_pos_y + 0.167), 0.003);
    return sat(col);
}

float drawLedgerLines(in vec2 uv, in vec2 p)
{
    float staff_above = staff_pos_y + staff_note_spacing * 9.0;
    float staff_below = staff_pos_y - staff_note_spacing * 2.0;
    float dist_below = staff_below - p.y;
    float dist_above = p.y - staff_above;

    if (dist_below < 0.0 && dist_above < 0.0)
        return 0.0;

    bool below = dist_below >= 0.0;
    float dist = below ? dist_below : dist_above;
    float y0 = below ? staff_below : staff_above;
    float step_y = staff_note_spacing * 2.0 * (below ? -1.0 : 1.0);
    vec2 line_size = vec2(0.055, staff_line_width * 2.0);

    float lines = 0.0;
    int num_lines = 1 + int(dist / staff_note_spacing / 1.9);
    vec2 line_pos = vec2(p.x, y0);
    for (int i = 0; i < num_lines; ++i)
    {
        lines += drawRect(uv, line_pos, line_size);
        line_pos.y += step_y;
    }
    return lines;
}

// One curved flag at the stem tip (8th-note style)
float drawSingleFlag(in vec2 uv, in vec2 p, in vec2 stalk_pos, in vec2 stalk_size, bool down)
{
    vec2 tail_dim = vec2(0.18, 0.3);
    float y_off = (tail_dim.y - stalk_size.y) * 0.1;
    vec2 tail_pos = p + stalk_pos + vec2(0.0, down ? -y_off : y_off);
    vec2 cut = vec2(0.0, down ? 0.01 : -0.01);

    float tail = drawEllipse(uv, tail_pos, tail_dim);
    tail -= drawEllipse(uv, tail_pos + cut, tail_dim - vec2(0.01, 0.008));
    tail -= drawRect(uv, p + stalk_pos - vec2(0.05, 0.0), vec2(0.1, stalk_size.y));
    return sat(tail);
}

// 8th = 1 flag, 16th = 2, 32nd = 3; stacked toward the note head
float drawNoteTail(in vec2 uv, in vec2 p, in vec2 stalk_pos, in vec2 stalk_size,
                   bool down, int note_type)
{
    float tail = drawSingleFlag(uv, p, stalk_pos, stalk_size, down);
    vec2 step = vec2(0.0, down ? flag_gap : -flag_gap);
    if (note_type >= note_type_sixteenth)
        tail += drawSingleFlag(uv, p, stalk_pos + step, stalk_size, down);
    if (note_type >= note_type_thirtysecond)
        tail += drawSingleFlag(uv, p, stalk_pos + step * 2.0, stalk_size, down);
    return sat(tail);
}

// Primary beam + secondary (16th) / tertiary (32nd) beams toward the note head
float drawNoteBeams(in vec2 uv, in vec2 hat_start, in vec2 hat_size,
                    float hat_width, bool down, int note_type)
{
    vec2 hat_end = hat_start + hat_size + vec2(0.002, 0.0);
    float hat = drawLineSquare(uv, hat_start, hat_end, hat_width, false);
    vec2 step = vec2(0.0, down ? beam_gap : -beam_gap);
    if (note_type >= note_type_sixteenth)
        hat += drawLineSquare(uv, hat_start + step, hat_end + step, hat_width, false);
    if (note_type >= note_type_thirtysecond)
        hat += drawLineSquare(uv, hat_start + step * 2.0, hat_end + step * 2.0, hat_width, false);
    return sat(hat);
}

float drawNote(in vec2 uv, in vec2 p, in int note_type, in int dec,
               in vec2 hat_size, in float tie_32s, in vec2 extra_geo)
{
    // Optional pitch letter under the note
    float letters = 0.0;
    if (note_names > 0 && note_type < note_type_rest_whole)
    {
        float letf = 1.0 - (p.y - staff_pos_y) / staff_note_spacing;
        int leti = abs(int(letf) - 5) % 7;
        letters = drawLetter(uv, p, leti);
    }

    if (note_type >= note_type_rest_whole)
        return letters + drawRest(uv, p, note_type);

    // Pitched note head
    float stalk_len = clamp(stalk_length_base + extra_geo.y, stalk_length_min, stalk_length_max);
    vec2 stalk_size = vec2(0.0025, stalk_len);
    float blob_size = staff_note_spacing * 45.0;
    float blob = drawRotatedEllipse(uv, p, blob_size, false);
    if (note_type <= note_type_half)
        blob -= drawRotatedEllipse(uv, p, blob_size * 0.5, true);

    bool dotted = dec >= decoration_dotted;
    bool stalk_down = p.y > staff_pos_y + staff_note_spacing * 2.0;
    if (extra_geo.x > 0.0) stalk_down = false;
    else if (extra_geo.x < 0.0) stalk_down = true;

    float decoration = 0.0;
    if (dotted)
        decoration += drawEllipse(uv, p + vec2(0.04, 0.0), vec2(0.07, 0.1));

    // Map decoration id → accidental value in {-1,0,1}; |acc|>1 means none
    int acc = (dotted ? dec - decoration_dotted : dec) - decoration_natural;
    if (abs(acc) <= 1)
        decoration += drawAccidental(uv, p, acc, true);

    float tie = 0.0;
    if (tie_32s > 0.0)
        tie = drawTie(uv, p, p + vec2(note_spacing_32nd * tie_32s, 0.0), stalk_down);

    float lines = drawLedgerLines(uv, p);
    float base = letters + blob + lines + tie + decoration;

    if (note_type == note_type_whole)
        return sat(base);

    // Stem (length capped so ledger notes / wide beams don't grow unbounded)
    float stalk_width = note_size * 0.2;
    vec2 stalk_pos = vec2(stalk_width - 0.002, stalk_size.y * 0.5);
    if (stalk_down)
    {
        stalk_pos.x -= blob_size * 0.03;
        stalk_pos.y -= stalk_size.y;
    }
    float stalk = drawRect(uv, p + stalk_pos, stalk_size);
    base += stalk;

    if (note_type <= note_type_quarter)
        return sat(base);

    // Flags when not beamed; beams when hat_size.x > 0
    if (hat_size.x <= 0.0 && hat_size.y >= 0.0)
        return sat(base + drawNoteTail(uv, p, stalk_pos, stalk_size, stalk_down, note_type));

    float hat = 0.0;
    if (hat_size.x > 0.0)
    {
        float stalk_y_mult = stalk_down ? -0.44 : 0.51;
        float hat_width = 0.012;
        vec2 hat_start = p + stalk_pos
            + vec2(stalk_width * -0.05, stalk_size.y * stalk_y_mult - hat_width);
        hat = drawNoteBeams(uv, hat_start, hat_size, hat_width, stalk_down, note_type);
    }
    return sat(base + hat);
}

float drawStaff(in vec2 uv, in vec2 p)
{
    float col = drawRect(uv, p + vec2(0.5 * staff_width, staff_spacing * 2.0),
                         vec2(staff_width, staff_spacing * 4.0)) * 0.25;
    for (int i = 0; i < 5; ++i)
    {
        vec2 start = p + vec2(0.0, float(i) * staff_spacing);
        vec2 end = start + vec2(staff_width, 0.0);
        col += 1.0 - smoothstep(staff_line_width - antialias * 0.01, staff_line_width,
                                distanceToSegment(start, end, uv));
    }
    return col;
}

vec4 drawNotes(in vec2 uv)
{
    vec4 all_notes = vec4(0.0);
    for (int i = 0; i < NUM_NOTES; ++i)
    {
        vec2 note_pos = (NotePositions[i] + 1.0) * 0.5;
        vec2 extra_geo = NoteExtra[i] * 0.5;
        float tie = (NoteTies[i] + 1.0) * 0.5;
        float note = drawNote(uv, note_pos, NoteTypes[i], NoteDecoration[i],
                              NoteHats[i], tie, extra_geo);
        float alpha = NoteColours[i].a;
        all_notes = max(all_notes, vec4(note * NoteColours[i].rgb, note * alpha));
    }
    return all_notes;
}

void main()
{
    vec2 uv = OutTexCoord;
    uv.y = 1.0 - uv.y;

    vec4 notes = drawNotes(uv);
    float s = drawStaff(uv, staff_pos);
    float k = drawKeySignature(uv);

    vec4 staff = vec4(vec3(s * 0.079), s);
    vec4 key = vec4(vec3(k * 0.08), k);
    notes = max(key, notes);
    outColour = max(staff, notes);
}
