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
#define note_slant vec2(0.33,0.93496)
#define note_slant_alt vec2(0.73, 0.73)
#define note_spacing_32nd 0.015

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

float drawEllipse(in vec2 uv, in vec2 pos, vec2 dim) 
{
    vec2 d = (uv - pos) / (dim * dim);
    if (abs( d.x ) <= 1.0 && abs( d.y ) < 1.0 ) 
    {
        if (dot(d, d) < 1.0) return 1.0;
    }
    return 0.0;
}

float drawRotatedEllipse(vec2 uv, vec2 pos, float size, bool altRot)
{
    float dim = 70.0;
    pos *= vec2(dim, dim);
    vec2 diff = note_slant * size;
    if (altRot)
    {
        diff = note_slant_alt * size;
    }
    vec2 l = pos - diff;
    vec2 r = pos + diff;
    
    vec2 coord = uv * vec2(dim, dim);
    return smoothstep(0.0, antialias, distance(l, r) + 1.0 - (distance(coord, l) + distance(coord, r)));
}

float drawRect(in vec2 uv, in vec2 center, in vec2 wh)
{
    vec2 disRec = abs(uv - center) - wh * 0.5;
    float dis = max(disRec.x, disRec.y);
    return clamp(float(dis < 0.0), 0.0, 1.0);
}

float distanceToSegment(vec2 a, vec2 b, vec2 p)
{
    vec2 pa = p - a, ba = b - a;
    float h = clamp( dot(pa,ba)/dot(ba,ba), 0.0, 1.0 );
    return length( pa - ba*h );
}

float drawLineRounded(in vec2 uv, in vec2 start, in vec2 end, in float width)
{
    return mix(0.0, 1.0, 1.0-smoothstep(width-antialias*0.02,width, distanceToSegment(start, end, uv)));
}

float drawLineSquare(in vec2 uv, in vec2 start, in vec2 end, in float width, bool vertical)
{
    float col = drawLineRounded(uv, start, end, width);
    vec2 clip_box = vec2(0.015, width * 4.0);
    float leftBox = drawRect(uv, start + vec2(clip_box.x * -0.5, 0.0), clip_box);
    float rightBox = drawRect(uv, end + vec2(clip_box.x * 0.5, 0.0), clip_box);
    if (vertical)
    {
        clip_box = vec2(width * 4.0, 0.02);
        leftBox = drawRect(uv, start, clip_box);
        rightBox = drawRect(uv, end, clip_box);
    }
    col -= leftBox + rightBox;
    return clamp(col, 0.0, 1.0);
}

float drawAccidental(in vec2 uv, in vec2 p, int val, bool note_relative_pos)
{
    float col = 0.0;
    float width = 0.055;
    float thickness = 0.002;
    vec2 acc_pos = p;
    if (note_relative_pos)
    {
        acc_pos = p - vec2(0.02, 0.0);
    }
    if (val == 0)
    {
        // Natural
        float boxX = 0.01;
        float boxY = 0.01;
        col += drawRect(uv, acc_pos + vec2(0.0, -0.005), vec2(0.001, width));
        col += drawRect(uv, acc_pos - vec2(boxX, -0.02), vec2(0.001, width));
        col += drawLineSquare(uv, acc_pos + vec2(-boxX, -boxY), acc_pos + vec2(0.0, -0.00), thickness, false);
        col += drawLineSquare(uv, acc_pos + vec2(-boxX, boxY), acc_pos + vec2(0.0, 0.02), thickness, false);
    }
    else if (val == 1)
    {
        // Sharp
        float hashX = 0.02;
        float hashY = 0.01;
        col += drawRect(uv, acc_pos - vec2(0.004, 0.0), vec2(0.0025, width));
        col += drawRect(uv, acc_pos - vec2(0.012, 0.005), vec2(0.0025, width));
        col += drawLineSquare(uv, acc_pos - vec2(hashX, -0.002), acc_pos + vec2(0.005, 0.023), thickness, false);
        col += drawLineSquare(uv, acc_pos - vec2(hashX, 0.022), acc_pos + vec2(0.005, -0.003), thickness, false);
    }
    
    else if (val == -1)
    {
        // Flat
        float little_b = drawRect(uv, acc_pos - vec2(0.015, -0.018), vec2(0.002, width));
        little_b += drawRotatedEllipse(uv, acc_pos - vec2(0.015, 0.0), 0.5, true);
        little_b -= drawRotatedEllipse(uv, acc_pos - vec2(0.015, 0.0), 0.15, false);
        little_b -= drawRect(uv, acc_pos - vec2(0.031, 0.0), vec2(0.03, 0.05));
        col += little_b;
    }
    return col;
}

float drawKeySignature(in vec2 uv)
{
    float key = 0.0;
    for (int i = 0; i < NUM_KEY_SIG; ++i)
    {
        if (abs(KeyPositions[i].x) + abs(KeyPositions[i].y) > 0.0)
        {
            vec2 p = (KeyPositions[i] + 1.0) * 0.5;
            key += drawAccidental(uv, p, i < NUM_KEY_SIG / 2 ? 1 : -1, false);
        }
    }
    return key;
}

float drawTie(in vec2 uv, in vec2 start, in vec2 end, bool above)
{
    float col = 0.0;
    vec2 dir = (end - start);
    float elen = length(dir);
    vec2 mid = start + (dir * 0.5) + vec2(-0.004, clamp(elen - 0.2, 0.0, 0.1) - 0.035);
    vec2 dim_lo = vec2(elen * 1.45, elen * 0.99);
    vec2 dim_hi = vec2(dim_lo.x * 1.15, dim_lo.y * 1.15);
    vec2 offset_inner = vec2(0.0, elen * 0.12);
    if (above)
    {
        offset_inner = vec2(0.0, elen * -0.12);
    }
    col += drawEllipse(uv, mid, dim_lo) - drawEllipse(uv, mid + offset_inner, dim_hi);
    return clamp(col, 0.0, 1.0);
}

// hat-size denotes joining between eigth and sixteenth notes
// hat_size.x component is the length,Y component is the end heigh difference
// hat_size.x of zero and negative Y means the note has been tied into and does not require a tail

// extra_geo denotes extending the stalk length of a note or forcing it's stalk a direction
// extra_geo.x of absolute value greater than zero will force the stalk direction, +ve for up, -ve for down
// extra_geo.y is added onto the default stalk lenghth
float drawNote(in vec2 uv, in vec2 p, in int note_type, in int dec, in vec2 hat_size, in float tie_32s, in vec2 extra_geo) 
{
    if (note_type == note_type_rest_whole)
    {
        return drawRect(uv, vec2(p.x, staff_pos_y + staff_note_spacing * 5.6), vec2(0.04, 0.03));
    }
    else if (note_type == note_type_rest_half)
    {
        return drawRect(uv, vec2(p.x, staff_pos_y + staff_note_spacing * 4.4), vec2(0.04, 0.03));
    }
    else if (note_type == note_type_rest_quarter)
    {
        float col = drawLineRounded(uv, vec2(p.x - 0.015, staff_pos_y + 0.22), vec2(p.x - 0.001, staff_pos_y + 0.18), 0.0025);
        col += drawLineSquare(uv, vec2(p.x-0.006, staff_pos_y + 0.19), vec2(p.x - 0.02, staff_pos_y + 0.11), 0.009, true);
        col += drawLineRounded(uv, vec2(p.x - 0.025, staff_pos_y + 0.12), vec2(p.x - 0.011, staff_pos_y + 0.072), 0.0025);
        col += drawEllipse(uv, vec2(p.x - 0.022, staff_pos_y + 0.07), vec2(0.11, 0.14));
        col -= drawEllipse(uv, vec2(p.x - 0.019, staff_pos_y + 0.062), vec2(0.1, 0.13));
        return clamp(col, 0.0, 1.0);
    }
    else if (note_type >= note_type_rest_eighth)
    {
        float col = drawLineRounded(uv, vec2(p.x - 0.001, staff_pos_y + 0.173), vec2(p.x - 0.02, staff_pos_y + 0.06), 0.0025);
        col += drawEllipse(uv, vec2(p.x - 0.024, staff_pos_y + 0.15), vec2(0.105, 0.135));
        col += drawLineRounded(uv, vec2(p.x - 0.016, staff_pos_y + 0.14), vec2(p.x - 0.003, staff_pos_y + 0.167), 0.003);
        return clamp(col, 0.0, 1.0);
    }

    vec2 stalk_size = vec2(0.0025, 0.2 + extra_geo.y);
    float blob_size = staff_note_spacing * 45.0;
    float blob = drawRotatedEllipse(uv, p, blob_size, false);
    float decoration = 0.0;
    float lines = 0.0;
    int lines_over = 0;
    int lines_under = 0;
    bool dotted = dec >= decoration_dotted;
    bool stalk_dir_down = p.y > staff_pos_y + (staff_note_spacing * 2.0);
    if (extra_geo.x > 0.0)
    {
        stalk_dir_down = false;
    }
    else if (extra_geo.x < 0.0)
    {
        stalk_dir_down = true;
    }

    if (dotted)
    {
        decoration += drawEllipse(uv, p + vec2(0.04, 0.0), vec2(0.07, 0.1));
    }
    
    int acc = dec >= decoration_dotted_flat ? dec - decoration_dotted_natural : dec - decoration_natural;
    if (abs(acc) <= 1)
    {
        decoration += drawAccidental(uv, p, acc, true);
    }
    
    float tie = 0.0;
    if (tie_32s > 0.0)
    {
        tie = drawTie(uv, p, p + vec2(note_spacing_32nd * tie_32s, 0.0), stalk_dir_down);
    }
    
    if (note_type <= note_type_half)
    {
        blob -= drawRotatedEllipse(uv, p, blob_size * 0.5, true);
    }
    
    float staff_above = (staff_pos_y + staff_note_spacing * 9.0);
    float staff_below = (staff_pos_y - staff_note_spacing * 2.0);
    float dist_below = staff_below - p.y;
    float dist_above = p.y - staff_above;
    vec2 line_size = vec2(0.055, staff_line_width * 2.0);
    if (dist_below >= 0.0)
    {
        vec2 line_pos = vec2(p.x, staff_below);
        int num_lines = 1 + int(dist_below / staff_note_spacing / 1.9);
        for (int i = 0; i < num_lines; ++i)
        {
            lines += drawRect(uv, line_pos, line_size);
            line_pos.y -= staff_note_spacing * 2.0;
        }
    }
    else if (dist_above >= 0.0)
    {
        vec2 line_pos = vec2(p.x, staff_above);
        int num_lines = 1 + int(dist_above / staff_note_spacing / 1.9);
        for (int i = 0; i < num_lines; ++i)
        {
            lines += drawRect(uv, line_pos, line_size);
            line_pos.y += staff_note_spacing * 2.0;
        }
    }
    
    if (note_type == note_type_whole)
    {
        return clamp(blob + lines + tie + decoration, 0.0, 1.0);
    }

    float stalk_width = note_size * 0.2;
    vec2 stalk_pos = vec2(stalk_width - 0.002, stalk_size.y * 0.5);
    if (stalk_dir_down)
    {
        stalk_pos.x -= blob_size * 0.03;
        stalk_pos.y -= stalk_size.y;
    }
    float stalk = drawRect(uv, p + stalk_pos, stalk_size);
                
    if (note_type >= note_type_eighth && hat_size.x <= 0.0 && hat_size.y >= 0.0)
    {
        float tail = 0.0;
        
        // Single tail
        if (note_type >= note_type_eighth)
        {
            vec2 tail_dim = vec2(0.18, 0.3);
            vec2 tail_pos = p + stalk_pos + vec2(0.0, (tail_dim.y - stalk_size.y) * 0.1);
            if (stalk_dir_down)
            {
                tail_pos = p + stalk_pos - vec2(0.0, (tail_dim.y - stalk_size.y) * 0.1);
                tail += drawEllipse(uv, tail_pos, tail_dim);
                tail -= drawEllipse(uv, tail_pos + vec2(0.0, 0.01), tail_dim - vec2(0.01, 0.008));
                tail -= drawRect(uv, p + stalk_pos - vec2(0.05, 0.0), vec2(0.1, stalk_size.y)); 
            }
            else
            {
                tail += drawEllipse(uv, tail_pos, tail_dim);
                tail -= drawEllipse(uv, tail_pos - vec2(0.0, 0.01), tail_dim - vec2(0.01, 0.008));
                tail -= drawRect(uv, p + stalk_pos - vec2(0.05, 0.0), vec2(0.1, stalk_size.y)); 
            }
            tail = clamp(tail, 0.0, 1.0);
        }
        
        // Double tail
        if (note_type >= note_type_sixteenth)
        {
        
        }
        return clamp(blob + lines + tie + stalk + decoration + tail, 0.0, 1.0);
    }
    
    if (note_type <= note_type_quarter)
    {
        return clamp(blob + lines + tie + stalk + decoration, 0.0, 1.0);
    }
    
    // Lines joining quavers and semi quavers
    float hat = 0.0;
    if (hat_size.x > 0.0)
    {
        float stalk_y_mult = stalk_dir_down ? -0.44 : 0.51;
        float hat_width = 0.012;
        vec2 hat_start = p + stalk_pos + vec2(stalk_width * -0.05, (stalk_size.y * stalk_y_mult) - hat_width);
        vec2 hat_end = hat_start + hat_size + vec2(0.002, 0.0);
        hat = drawLineSquare(uv, hat_start, hat_end, hat_width, false);
    }
    
    return clamp(blob + lines + tie + stalk + hat + decoration, 0.0, 1.0);   
}

float drawStaff(in vec2 uv, in vec2 p)
{
    float col = drawRect(uv, p + vec2(0.5 * staff_width, staff_spacing * 2.0), vec2(staff_width, staff_spacing * 4.0)) * 0.25;
    for (int i = 0; i < 5; ++i)
    {
        vec2 start = p + vec2(0.0, float(i) * staff_spacing);
        vec2 end = start + vec2(staff_width, 0.0);
        col += mix(0.0, 1.0, 1.0-smoothstep(staff_line_width-antialias*0.01, staff_line_width, distanceToSegment(start, end, uv)));
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
        float note = drawNote(uv, note_pos, NoteTypes[i], NoteDecoration[i], NoteHats[i], tie, extra_geo);
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
