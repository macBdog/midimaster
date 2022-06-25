#version 430

in vec2 OutTexCoord;
out vec4 outColour;

uniform sampler2D SamplerTex;
uniform vec4 Colour;
uniform float DisplayRatio;
uniform float Emitters[NUM_PARTICLE_EMITTERS];
uniform vec2 EmitterPositions[NUM_PARTICLE_EMITTERS];
uniform vec3 EmitterColours[NUM_PARTICLE_EMITTERS];

#define num_particles 32
#define grav -0.01
#define psize 0.05

vec2 rand_minus1_to_1(vec2 p)
{
    p = vec2( dot(p, vec2(127.1, 311.7)), dot(p, vec2(269.5, 183.3)) );
    return -1. + 2.*fract(sin(p) * 53758.5453123);
}

float rand(vec2 c) 
{
    return fract(sin(dot(c.xy , vec2(12.9898, 78.233))) * 43758.5453);
}

vec2 noise(vec2 tc)
{
    return (2.0 * texture(SamplerTex, tc).xy - 1.0).xy;
}

vec2 getPos(in vec2 o, in float time, in vec2 dir) 
{
    return vec2(o.x + dir.x * time, o.y + dir.y * time - grav * time * time);
}

vec4 drawParticle(in vec2 pos, in float size, in vec4 col) 
{
    return mix(col, vec4(0.0), smoothstep(0.0, size, dot(pos, pos) * 90.0));
}

void main() 
{
    vec2 uv = OutTexCoord;
    uv.y *= DisplayRatio;
    vec4 screen_col = vec4(0.0);

    for (int e = 0; e < NUM_PARTICLE_EMITTERS; ++e)
    {
        float life = max(Emitters[e], 0.0);
        vec2 start_pos = (EmitterPositions[e] + vec2(1.0)) * vec2(0.5);
        start_pos.y = 1.0 - start_pos.y;
        start_pos.y *= DisplayRatio;
        vec3 col = EmitterColours[e];

        for (int i = 0; i < num_particles; ++i)
        {
            float c = (((float(i) / float(num_particles)) + 1.0) * 0.25) + (sin(float(e) / float(NUM_PARTICLE_EMITTERS)));
            vec2 rdir = noise(vec2(sin(c), cos(c))) * 0.2;
            vec2 pos = getPos(start_pos, 1.0 - life, rdir);
            screen_col += drawParticle(uv - pos, psize * life, vec4(col.xyz, life));
        }
    }
    outColour = screen_col;
}