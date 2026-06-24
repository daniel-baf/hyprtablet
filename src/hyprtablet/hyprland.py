from __future__ import annotations

from dataclasses import dataclass
import json
import os
import subprocess


class HyprlandError(RuntimeError):
    pass


@dataclass(frozen=True)
class Monitor:
    name: str
    description: str
    width: int
    height: int
    x: int
    y: int
    scale: float
    focused: bool

    @property
    def label(self) -> str:
        focused = " focused" if self.focused else ""
        return f"{self.name} - {self.width}x{self.height} at {self.x},{self.y}{focused}"


@dataclass(frozen=True)
class Tablet:
    name: str
    kind: str

    @property
    def label(self) -> str:
        return f"{self.name} ({self.kind})"


def is_hyprland_session() -> bool:
    return bool(os.environ.get("HYPRLAND_INSTANCE_SIGNATURE"))


def run_hyprctl(*args: str) -> str:
    try:
        completed = subprocess.run(
            ["hyprctl", *args],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise HyprlandError("hyprctl was not found in PATH.") from exc
    except subprocess.CalledProcessError as exc:
        message = exc.stderr.strip() or exc.stdout.strip() or "hyprctl command failed."
        raise HyprlandError(message) from exc

    return completed.stdout


def list_monitors() -> list[Monitor]:
    raw = run_hyprctl("monitors", "-j")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HyprlandError("Could not parse hyprctl monitors JSON.") from exc

    monitors: list[Monitor] = []
    for item in payload:
        monitors.append(
            Monitor(
                name=str(item.get("name", "")),
                description=str(item.get("description", "")),
                width=int(item.get("width", 0)),
                height=int(item.get("height", 0)),
                x=int(item.get("x", 0)),
                y=int(item.get("y", 0)),
                scale=float(item.get("scale", 1.0)),
                focused=bool(item.get("focused", False)),
            )
        )
    return [monitor for monitor in monitors if monitor.name]


def list_tablets() -> list[Tablet]:
    raw = run_hyprctl("devices", "-j")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HyprlandError("Could not parse hyprctl devices JSON.") from exc

    tablets: list[Tablet] = []
    for item in payload.get("tablets", []):
        name = str(item.get("name") or item.get("type") or "Unnamed tablet")
        kind = str(item.get("type") or "tablet")
        tablets.append(Tablet(name=name, kind=kind))
    return tablets


def get_current_output() -> str:
    raw = run_hyprctl("getoption", "input:tablet:output")
    for line in raw.splitlines():
        if line.startswith("str:"):
            value = line.removeprefix("str:").strip()
            return "" if value == "[[EMPTY]]" else value
    return ""


def apply_output(output: str | None) -> None:
    target = output or ""
    run_hyprctl("keyword", "input:tablet:output", target)
