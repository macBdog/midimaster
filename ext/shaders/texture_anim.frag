#version 430

in vec2 OutTexCoord;     
uniform sampler2D SamplerTex;
uniform vec4 Colour;
out vec4 outColour;

float iTime = 0.0;

void main() 
{
    vec2 scroll = OutTexCoord + vec2(iTime, iTime);
    outColour = texture(SamplerTex, scroll) * Colour;
    iTime += 0.0015;
}