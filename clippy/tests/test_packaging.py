from __future__ import annotations

from clippybot import __version__


def test_version():
    assert __version__.count(".") == 2
