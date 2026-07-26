#version 430

in vec2 VertexPosition;
in vec2 TexCoord;
uniform vec2 Position;
uniform vec2 Size;
out vec2 OutTexCoord;
uniform mat4 ObjectMatrix;
uniform mat4 ViewMatrix;
uniform mat4 ProjectionMatrix;
void main()
{
    gl_Position = vec4(Position.x + Size.x * VertexPosition.x, Position.y + Size.y * VertexPosition.y, 0.0, 1.0);
    OutTexCoord = TexCoord;
}
