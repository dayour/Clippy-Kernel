#!/usr/bin/env python3

"""This helper command is used to parse and print flake8 output."""

import json
import os
import subprocess
from pathlib import Path


class _JsonRegistry:
    def __init__(self) -> None:
        env_file = os.environ.get("clippybot_ENV_FILE")
        self._path = Path(env_file) if env_file else None

    def _read(self) -> dict:
        if self._path is None or not self._path.exists():
            return {}
        text = self._path.read_text()
        if not text.strip():
            return {}
        return json.loads(text)

    def get(self, key: str, default=None):
        return self._read().get(key, default)


registry = _JsonRegistry()


class Flake8Error:
    """A class to represent a single flake8 error"""

    def __init__(self, filename: str, line_number: int, col_number: int, problem: str):
        self.filename = filename
        self.line_number = line_number
        self.col_number = col_number
        self.problem = problem

    @classmethod
    def from_line(cls, line: str):
        try:
            prefix, _sep, problem = line.partition(": ")
            filename, line_number, col_number = prefix.split(":")
        except (ValueError, IndexError) as e:
            msg = f"Invalid flake8 error line: {line}"
            raise ValueError(msg) from e
        return cls(filename, int(line_number), int(col_number), problem)

    def __eq__(self, other):
        if not isinstance(other, Flake8Error):
            return NotImplemented
        return (
            self.filename == other.filename
            and self.line_number == other.line_number
            and self.col_number == other.col_number
            and self.problem == other.problem
        )

    def __repr__(self):
        return (
            "Flake8Error("
            f"filename={self.filename}, "
            f"line_number={self.line_number}, "
            f"col_number={self.col_number}, "
            f"problem={self.problem})"
        )


def _update_previous_errors(
    previous_errors: list[Flake8Error], replacement_window: tuple[int, int], replacement_n_lines: int
) -> list[Flake8Error]:
    updated = []
    lines_added = replacement_n_lines - (replacement_window[1] - replacement_window[0] + 1)
    for error in previous_errors:
        if error.line_number < replacement_window[0]:
            updated.append(error)
            continue
        if replacement_window[0] <= error.line_number <= replacement_window[1]:
            continue
        updated.append(Flake8Error(error.filename, error.line_number + lines_added, error.col_number, error.problem))
    return updated


def format_flake8_output(
    input_string: str,
    show_line_numbers: bool = False,
    *,
    previous_errors_string: str = "",
    replacement_window: tuple[int, int] | None = None,
    replacement_n_lines: int | None = None,
) -> str:
    errors = [Flake8Error.from_line(line.strip()) for line in input_string.split("\n") if line.strip()]
    lines = []
    if previous_errors_string:
        assert replacement_window is not None
        assert replacement_n_lines is not None
        previous_errors = [
            Flake8Error.from_line(line.strip()) for line in previous_errors_string.split("\n") if line.strip()
        ]
        previous_errors = _update_previous_errors(previous_errors, replacement_window, replacement_n_lines)
        errors = [error for error in errors if error not in previous_errors]
        errors = [error for error in errors if error.line_number >= replacement_window[0]]
    for error in errors:
        if not show_line_numbers:
            lines.append(f"- {error.problem}")
        else:
            lines.append(f"- line {error.line_number} col {error.col_number}: {error.problem}")
    return "\n".join(lines)


def flake8(file_path: str) -> str:
    if Path(file_path).suffix != ".py":
        return ""
    cmd = registry.get("LINT_COMMAND", "flake8 --isolated --select=F821,F822,F831,E111,E112,E113,E999,E902 {file_path}")
    out = subprocess.run(cmd.format(file_path=file_path), shell=True, capture_output=True)
    return out.stdout.decode()
