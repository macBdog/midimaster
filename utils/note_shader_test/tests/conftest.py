"""Pytest fixtures for note_shader_test."""

from __future__ import annotations

import pytest

from note_shader_test.harness import GLContextError, NoteShaderHarness, gl_available
from note_shader_test.paths import notes_frag_path


def pytest_configure(config):
    config.addinivalue_line("markers", "gpu: needs OpenGL context")


@pytest.fixture(scope="session")
def shader_path():
    path = notes_frag_path()
    if not path.is_file():
        pytest.skip(f"notes.frag not found at {path} (set MIDIMASTER_ROOT?)")
    return path


@pytest.fixture(scope="session")
def gpu_ok():
    return gl_available()


@pytest.fixture(scope="session")
def harness(shader_path, gpu_ok):
    if not gpu_ok:
        pytest.skip("OpenGL context not available")
    h = NoteShaderHarness(width=960, height=540)
    try:
        h.initialize()
    except GLContextError as e:
        pytest.skip(str(e))
    yield h
    h.shutdown()
