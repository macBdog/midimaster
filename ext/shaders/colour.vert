#version 430

in vec2 VertexPosition;
uniform vec2 Position;
uniform vec2 Size;

void main() 
{
    gl_Position = vec4(Position.x + Size.x * VertexPosition.x, Position.y + Size.y * VertexPosition.y, 0.0, 1.0);
}