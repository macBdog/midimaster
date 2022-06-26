#version 430

in vec2 OutTexCoord;
uniform float Time;
uniform sampler2D SamplerTex;
uniform vec4 Colour;
out vec4 outColour;

void main() 
{
    vec2 scroll = OutTexCoord + vec2(Time*0.05, Time*0.05);
    outColour = texture(SamplerTex, scroll) * Colour;
}