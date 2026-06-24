from __future__ import annotations

import json
import subprocess

import pytest

from hyprtablet import hyprland


def test_run_hyprctl_reports_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    def run_timeout(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(cmd=["hyprctl", "monitors", "-j"], timeout=2)

    monkeypatch.setattr(hyprland.subprocess, "run", run_timeout)

    with pytest.raises(hyprland.HyprlandError, match="timed out"):
        hyprland.run_hyprctl("monitors", "-j")


def test_list_monitors_skips_invalid_entries_and_defaults_bad_values(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = [
        {"name": "HDMI-A-1", "width": "1920", "height": "bad", "scale": "bad"},
        {"width": 1280},
        "not a monitor",
    ]
    monkeypatch.setattr(hyprland, "run_hyprctl", lambda *_args: json.dumps(payload))

    monitors = hyprland.list_monitors()

    assert len(monitors) == 1
    assert monitors[0].name == "HDMI-A-1"
    assert monitors[0].width == 1920
    assert monitors[0].height == 0
    assert monitors[0].scale == 1.0


def test_list_tablets_rejects_unexpected_devices_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(hyprland, "run_hyprctl", lambda *_args: "[]")

    with pytest.raises(hyprland.HyprlandError, match="Unexpected hyprctl devices"):
        hyprland.list_tablets()


def test_apply_output_rejects_unknown_output_before_keyword(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, ...]] = []

    def fake_run_hyprctl(*args: str) -> str:
        calls.append(args)
        if args == ("monitors", "-j"):
            return json.dumps([{"name": "HDMI-A-1"}])
        raise AssertionError(f"unexpected hyprctl call: {args}")

    monkeypatch.setattr(hyprland, "run_hyprctl", fake_run_hyprctl)

    with pytest.raises(hyprland.HyprlandError, match="not currently connected"):
        hyprland.apply_output("DP-9")

    assert calls == [("monitors", "-j")]


def test_apply_output_skips_keyword_when_mapping_already_matches(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, ...]] = []

    def fake_run_hyprctl(*args: str) -> str:
        calls.append(args)
        if args == ("monitors", "-j"):
            return json.dumps([{"name": "HDMI-A-1"}])
        if args == ("getoption", "input:tablet:output"):
            return "str: HDMI-A-1\n"
        raise AssertionError(f"unexpected hyprctl call: {args}")

    monkeypatch.setattr(hyprland, "run_hyprctl", fake_run_hyprctl)

    hyprland.apply_output("HDMI-A-1")

    assert calls == [("monitors", "-j"), ("getoption", "input:tablet:output")]


def test_apply_output_clears_mapping_only_when_needed(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, ...]] = []

    def fake_run_hyprctl(*args: str) -> str:
        calls.append(args)
        if args == ("getoption", "input:tablet:output"):
            return "str: HDMI-A-1\n"
        if args == ("keyword", "input:tablet:output", ""):
            return "ok\n"
        raise AssertionError(f"unexpected hyprctl call: {args}")

    monkeypatch.setattr(hyprland, "run_hyprctl", fake_run_hyprctl)

    hyprland.apply_output(None)

    assert calls == [
        ("getoption", "input:tablet:output"),
        ("keyword", "input:tablet:output", ""),
    ]
