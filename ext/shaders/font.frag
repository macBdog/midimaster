#version 430

in vec2 OutTexCoord;     
uniform sampler2D SamplerTex;
uniform vec4 Colour;
out vec4 outColour;

void main() 
{
    vec4 char_col = Colour;
    char_col.a = texture(SamplerTex, OutTexCoord).r;
    outColour = char_col;
}