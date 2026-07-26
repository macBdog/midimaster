"""
Offscreen OpenGL harness for notes.frag.

Creates a hidden GLFW window, compiles the note shader with the same
preprocessor substitutions as MidiMaster NoteRender, draws a fullscreen
quad, and returns an RGBA numpy image.
"""

from __future__ import annotations

import atexit
from pathlib import Path
from typing import Optional

import numpy as np

from note_shader_test.paths import notes_frag_path, texture_vert_path
from note_shader_test.staff_layout import (
    NUM_KEY_SIG,
    NUM_NOTES_SLOTS,
    ShaderLayout,
    empty_uniform_buffers,
    pack_notes,
)


class GLContextError(RuntimeError):
    pass


class NoteShaderHarness:
    """Lazy singleton-friendly offscreen renderer."""

    def __init__(
        self,
        width: int = 960,
        height: int = 540,
        layout: Optional[ShaderLayout] = None,
        frag_path: Optional[Path] = None,
        vert_path: Optional[Path] = None,
    ):
        self.width = width
        self.height = height
        self.layout = layout or ShaderLayout.from_midimaster_defaults()
        self.frag_path = Path(frag_path) if frag_path else notes_frag_path()
        self.vert_path = Path(vert_path) if vert_path else texture_vert_path()

        self._initialized = False
        self._window = None
        self._program = None
        self._fbo = None
        self._color_tex = None
        self._vao = None
        self._vbo = None
        self._ebo = None
        self._dummy_tex = None
        self._uniform_locs: dict = {}

    # ------------------------------------------------------------------ lifecycle

    def initialize(self) -> None:
        if self._initialized:
            return

        try:
            import glfw
            from OpenGL.GL import (
                GL_COLOR_BUFFER_BIT,
                GL_COMPILE_STATUS,
                GL_ELEMENT_ARRAY_BUFFER,
                GL_FALSE,
                GL_FLOAT,
                GL_FRAGMENT_SHADER,
                GL_FRAMEBUFFER,
                GL_LINK_STATUS,
                GL_RGBA,
                GL_RGBA8,
                GL_STATIC_DRAW,
                GL_TEXTURE_2D,
                GL_TRIANGLES,
                GL_UNSIGNED_BYTE,
                GL_UNSIGNED_INT,
                GL_VERTEX_SHADER,
                glAttachShader,
                glBindBuffer,
                glBindFramebuffer,
                glBindTexture,
                glBindVertexArray,
                glBufferData,
                glCheckFramebufferStatus,
                glClear,
                glClearColor,
                glCompileShader,
                glCreateProgram,
                glCreateShader,
                glDeleteProgram,
                glDeleteShader,
                glEnableVertexAttribArray,
                glFramebufferTexture2D,
                glGenBuffers,
                glGenFramebuffers,
                glGenTextures,
                glGenVertexArrays,
                glGetProgramInfoLog,
                glGetProgramiv,
                glGetShaderInfoLog,
                glGetShaderiv,
                glGetUniformLocation,
                glLinkProgram,
                glShaderSource,
                glTexImage2D,
                glTexParameteri,
                glUseProgram,
                glVertexAttribPointer,
                glViewport,
                GL_ARRAY_BUFFER,
                GL_CLAMP_TO_EDGE,
                GL_COLOR_ATTACHMENT0,
                GL_FRAMEBUFFER_COMPLETE,
                GL_LINEAR,
                GL_TEXTURE_MAG_FILTER,
                GL_TEXTURE_MIN_FILTER,
                GL_TEXTURE_WRAP_S,
                GL_TEXTURE_WRAP_T,
            )
        except ImportError as e:
            raise GLContextError(f"OpenGL / glfw not available: {e}") from e

        if not glfw.init():
            raise GLContextError("glfw.init() failed")

        glfw.window_hint(glfw.VISIBLE, glfw.FALSE)
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 4)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        # Allow compatibility on older drivers if core fails
        window = glfw.create_window(self.width, self.height, "note_shader_test", None, None)
        if window is None:
            glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_ANY_PROFILE)
            glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
            glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
            window = glfw.create_window(self.width, self.height, "note_shader_test", None, None)
        if window is None:
            glfw.terminate()
            raise GLContextError("Could not create OpenGL window (no GPU / driver?)")

        glfw.make_context_current(window)
        self._window = window
        self._glfw = glfw

        # Import GL symbols into instance after context exists
        from OpenGL import GL as gl

        self._gl = gl

        vert_src = self.vert_path.read_text(encoding="utf-8")
        frag_src = self._preprocess_fragment(self.frag_path.read_text(encoding="utf-8"))
        self._program = self._compile_program(vert_src, frag_src)
        self._cache_uniform_locations()
        self._create_fullscreen_quad()
        self._create_fbo()
        self._create_dummy_texture()

        self._initialized = True
        atexit.register(self.shutdown)

    def shutdown(self) -> None:
        if not self._initialized:
            return
        gl = self._gl
        glfw = self._glfw
        try:
            if self._program:
                gl.glDeleteProgram(self._program)
            if self._window:
                glfw.destroy_window(self._window)
        finally:
            try:
                glfw.terminate()
            except Exception:
                pass
            self._initialized = False
            self._window = None

    # ------------------------------------------------------------------ shader

    def _preprocess_fragment(self, src: str) -> str:
        """Apply NoteRender-style string substitutions."""
        for key, sub in self.layout.substitutes().items():
            if key in src:
                src = src.replace(key, str(sub))
            else:
                # NUM_NOTES / NUM_KEY_SIG appear only as array sizes — still required
                if key in ("NUM_NOTES", "NUM_KEY_SIG") and key not in src:
                    raise RuntimeError(f"Shader missing substitute key {key!r}")
        return src

    def _compile_program(self, vert_src: str, frag_src: str):
        gl = self._gl

        def compile_shader(source: str, shader_type: int) -> int:
            sh = gl.glCreateShader(shader_type)
            gl.glShaderSource(sh, source)
            gl.glCompileShader(sh)
            if not gl.glGetShaderiv(sh, gl.GL_COMPILE_STATUS):
                log = gl.glGetShaderInfoLog(sh)
                if isinstance(log, bytes):
                    log = log.decode("utf-8", errors="replace")
                kind = "vertex" if shader_type == gl.GL_VERTEX_SHADER else "fragment"
                raise RuntimeError(f"{kind} shader compile failed:\n{log}\n--- source head ---\n{source[:800]}")
            return sh

        vs = compile_shader(vert_src, gl.GL_VERTEX_SHADER)
        fs = compile_shader(frag_src, gl.GL_FRAGMENT_SHADER)
        prog = gl.glCreateProgram()
        gl.glAttachShader(prog, vs)
        gl.glAttachShader(prog, fs)

        # Bind attribute locations explicitly (core profile)
        gl.glBindAttribLocation(prog, 0, "VertexPosition")
        gl.glBindAttribLocation(prog, 1, "TexCoord")

        gl.glLinkProgram(prog)
        if not gl.glGetProgramiv(prog, gl.GL_LINK_STATUS):
            log = gl.glGetProgramInfoLog(prog)
            if isinstance(log, bytes):
                log = log.decode("utf-8", errors="replace")
            raise RuntimeError(f"program link failed:\n{log}")

        gl.glDeleteShader(vs)
        gl.glDeleteShader(fs)
        return prog

    def _cache_uniform_locations(self) -> None:
        gl = self._gl
        names = [
            "Position", "Size", "Colour", "SamplerTex", "DisplayRatio", "MusicTime",
            "note_names", "KeyPositions", "NotePositions", "NoteColours",
            "NoteTypes", "NoteDecoration", "NoteHats", "NoteTies", "NoteExtra",
            "ObjectMatrix", "ViewMatrix", "ProjectionMatrix",
        ]
        for name in names:
            self._uniform_locs[name] = gl.glGetUniformLocation(self._program, name)

    # ------------------------------------------------------------------ geometry / FBO

    def _create_fullscreen_quad(self) -> None:
        gl = self._gl
        # VertexPosition (x,y) + TexCoord (u,v) — matches Graphics.DEFAULT_RECTANGLE layout
        # corners: BL, BR, TR, TL in NDC local [-0.5,0.5]; sprite size 2 → full screen
        verts = np.array(
            [
                -0.5, -0.5, 0.0, 1.0,
                 0.5, -0.5, 1.0, 1.0,
                 0.5,  0.5, 1.0, 0.0,
                -0.5,  0.5, 0.0, 0.0,
            ],
            dtype=np.float32,
        )
        indices = np.array([0, 1, 2, 2, 3, 0], dtype=np.uint32)

        self._vao = gl.glGenVertexArrays(1)
        gl.glBindVertexArray(self._vao)

        self._vbo = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self._vbo)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, verts.nbytes, verts, gl.GL_STATIC_DRAW)

        self._ebo = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self._ebo)
        gl.glBufferData(gl.GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, gl.GL_STATIC_DRAW)

        stride = 4 * 4
        gl.glEnableVertexAttribArray(0)
        gl.glVertexAttribPointer(0, 2, gl.GL_FLOAT, gl.GL_FALSE, stride, gl.ctypes.c_void_p(0))
        gl.glEnableVertexAttribArray(1)
        gl.glVertexAttribPointer(1, 2, gl.GL_FLOAT, gl.GL_FALSE, stride, gl.ctypes.c_void_p(8))

        gl.glBindVertexArray(0)

    def _create_fbo(self) -> None:
        gl = self._gl
        self._color_tex = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self._color_tex)
        gl.glTexImage2D(
            gl.GL_TEXTURE_2D, 0, gl.GL_RGBA8, self.width, self.height, 0,
            gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None,
        )
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)

        self._fbo = gl.glGenFramebuffers(1)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self._fbo)
        gl.glFramebufferTexture2D(
            gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0, gl.GL_TEXTURE_2D, self._color_tex, 0
        )
        status = gl.glCheckFramebufferStatus(gl.GL_FRAMEBUFFER)
        if status != gl.GL_FRAMEBUFFER_COMPLETE:
            raise GLContextError(f"FBO incomplete: {status}")
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

    def _create_dummy_texture(self) -> None:
        gl = self._gl
        pixel = np.array([255, 255, 255, 255], dtype=np.uint8)
        self._dummy_tex = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self._dummy_tex)
        gl.glTexImage2D(
            gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, 1, 1, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, pixel
        )
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)

    # ------------------------------------------------------------------ render

    def render(
        self,
        notes: list | None = None,
        uniforms: dict | None = None,
        music_time: float = 0.0,
        note_names: bool = False,
        clear_rgba: tuple = (1.0, 1.0, 1.0, 1.0),
    ) -> np.ndarray:
        """
        Render notes and return HxWx4 uint8 RGBA image (origin top-left for PNG).

        Provide either `notes` (list of dicts → pack_notes) or a prebuilt `uniforms` dict.
        """
        self.initialize()
        gl = self._gl

        if uniforms is None:
            uniforms = pack_notes(notes or [])

        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self._fbo)
        gl.glViewport(0, 0, self.width, self.height)
        # notes.frag writes vec4(0) where empty; MidiMaster composites with alpha.
        # Enable blending over an opaque clear so empty pixels keep the page colour.
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        gl.glClearColor(*clear_rgba)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

        gl.glUseProgram(self._program)
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self._dummy_tex)

        loc = self._uniform_locs
        identity = np.eye(4, dtype=np.float32)

        def u1f(name, v):
            if loc[name] >= 0:
                gl.glUniform1f(loc[name], float(v))

        def u1i(name, v):
            if loc[name] >= 0:
                gl.glUniform1i(loc[name], int(v))

        def u2f(name, x, y):
            if loc[name] >= 0:
                gl.glUniform2f(loc[name], float(x), float(y))

        def u4f(name, *vals):
            if loc[name] >= 0:
                gl.glUniform4f(loc[name], *[float(v) for v in vals])

        def um4(name, mat):
            if loc[name] >= 0:
                gl.glUniformMatrix4fv(loc[name], 1, gl.GL_FALSE, mat)

        # Fullscreen sprite: centre 0, size 2 → covers NDC [-1,1]
        u2f("Position", 0.0, 0.0)
        u2f("Size", 2.0, 2.0)
        u4f("Colour", 1.0, 1.0, 1.0, 1.0)
        u1i("SamplerTex", 0)
        u1f("DisplayRatio", self.height / max(self.width, 1))
        u1f("MusicTime", music_time)
        u1i("note_names", 1 if note_names else 0)
        um4("ObjectMatrix", identity)
        um4("ViewMatrix", identity)
        um4("ProjectionMatrix", identity)

        n = self.layout.num_notes
        pos = np.asarray(uniforms["positions"], dtype=np.float32)
        col = np.asarray(uniforms["colours"], dtype=np.float32)
        types = np.asarray(uniforms["types"], dtype=np.int32)
        dec = np.asarray(uniforms["decoration"], dtype=np.int32)
        hats = np.asarray(uniforms["hats"], dtype=np.float32)
        ties = np.asarray(uniforms["ties"], dtype=np.float32)
        extra = np.asarray(uniforms["extra"], dtype=np.float32)
        keys = np.asarray(uniforms.get("key_positions", [0.0] * (NUM_KEY_SIG * 2)), dtype=np.float32)

        if loc["NotePositions"] >= 0:
            gl.glUniform2fv(loc["NotePositions"], n, pos)
        if loc["NoteColours"] >= 0:
            gl.glUniform4fv(loc["NoteColours"], n, col)
        if loc["NoteTypes"] >= 0:
            gl.glUniform1iv(loc["NoteTypes"], n, types)
        if loc["NoteDecoration"] >= 0:
            gl.glUniform1iv(loc["NoteDecoration"], n, dec)
        if loc["NoteHats"] >= 0:
            gl.glUniform2fv(loc["NoteHats"], n, hats)
        if loc["NoteTies"] >= 0:
            gl.glUniform1fv(loc["NoteTies"], n, ties)
        if loc["NoteExtra"] >= 0:
            gl.glUniform2fv(loc["NoteExtra"], n, extra)
        if loc["KeyPositions"] >= 0:
            gl.glUniform2fv(loc["KeyPositions"], NUM_KEY_SIG, keys)

        gl.glBindVertexArray(self._vao)
        gl.glDrawElements(gl.GL_TRIANGLES, 6, gl.GL_UNSIGNED_INT, None)
        gl.glBindVertexArray(0)

        # Read pixels (bottom-left origin in GL → flip for image top-left)
        gl.glPixelStorei(gl.GL_PACK_ALIGNMENT, 1)
        raw = gl.glReadPixels(0, 0, self.width, self.height, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE)
        img = np.frombuffer(raw, dtype=np.uint8).reshape(self.height, self.width, 4)
        img = np.flipud(img).copy()
        # Force opaque page alpha for PNG / comparison convenience
        img[..., 3] = 255

        gl.glDisable(gl.GL_BLEND)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        gl.glUseProgram(0)
        return img

    def render_case(self, case: dict) -> np.ndarray:
        """Render a fixture case dict (see fixtures/cases/*.json)."""
        return self.render(
            notes=case.get("notes", []),
            music_time=float(case.get("music_time", 0.0)),
            note_names=bool(case.get("note_names", False)),
        )


# Module-level shared harness (one context per process)
_shared: Optional[NoteShaderHarness] = None


def get_harness(width: int = 960, height: int = 540) -> NoteShaderHarness:
    global _shared
    if _shared is None or _shared.width != width or _shared.height != height:
        if _shared is not None:
            _shared.shutdown()
        _shared = NoteShaderHarness(width=width, height=height)
        _shared.initialize()
    return _shared


def gl_available() -> bool:
    try:
        h = NoteShaderHarness(width=64, height=64)
        h.initialize()
        h.shutdown()
        return True
    except Exception:
        return False
