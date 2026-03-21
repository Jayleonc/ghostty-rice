"""Tests for profile loading and application."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

from ghostty_rice.profile import Profile, _extract_base_config


def test_profile_from_file(tmp_path: Path) -> None:
    conf = tmp_path / "test.conf"
    conf.write_text(
        dedent("""\
        # @name: Test Theme
        # @description: A test profile
        # @author: tester
        # @tags: dark, test
        theme = Catppuccin Mocha
        background-opacity = 0.9
    """)
    )

    p = Profile.from_file(conf, source="builtin")
    assert p.name == "test"
    assert p.description == "A test profile"
    assert p.author == "tester"
    assert p.tags == ["dark", "test"]
    assert "theme = Catppuccin Mocha" in p.config_body()


def test_profile_config_body_excludes_header(tmp_path: Path) -> None:
    conf = tmp_path / "example.conf"
    conf.write_text(
        dedent("""\
        # @name: Example
        # @description: Example profile
        theme = Rose Pine
        cursor-style = bar
    """)
    )

    p = Profile.from_file(conf, source="user")
    body = p.config_body()
    assert "# @name" not in body
    assert "theme = Rose Pine" in body
    assert "cursor-style = bar" in body


def test_extract_base_config() -> None:
    text = dedent("""\
        # rice-profile: test
        # Managed by ghostty-rice
        # Do not edit the profile section below manually

        shell-integration = detect
        font-family = "JetBrains Mono"

        # --- Profile: test ---
        theme = Catppuccin Mocha
        background-opacity = 0.9
    """)
    base = _extract_base_config(text)
    assert "shell-integration = detect" in base
    assert "font-family" in base
    assert "theme = Catppuccin" not in base
    assert "Profile: test" not in base
