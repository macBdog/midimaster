#version 430

in vec2 OutTexCoord;     
uniform sampler2D SamplerTex;
uniform vec4 Colour;
out vec4 outColour;

void main() 
{
    outColour = texture(SamplerTex, OutTexCoord) * Colour;
}