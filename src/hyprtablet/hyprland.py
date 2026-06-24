from __future__ import annotations

from dataclasses import dataclass
import json
import os
import subprocess


HYPRCTL_TIMEOUT_SECONDS = 2.0


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
            timeout=HYPRCTL_TIMEOUT_SECONDS,
        )
    except FileNotFoundError as exc:
        raise HyprlandError("hyprctl was not found in PATH.") from exc
    except subprocess.TimeoutExpired as exc:
        command = " ".join(("hyprctl", *args))
        raise HyprlandError(f"{command} timed out after {HYPRCTL_TIMEOUT_SECONDS:g} seconds.") from exc
    except subprocess.CalledProcessError as exc:
        message = exc.stderr.strip() or exc.stdout.strip() or "hyprctl command failed."
        raise HyprlandError(message) from exc

    return completed.stdout


def _as_int(value: object, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _as_float(value: object, default: float = 1.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def list_monitors() -> list[Monitor]:
    raw = run_hyprctl("monitors", "-j")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HyprlandError("Could not parse hyprctl monitors JSON.") from exc
    if not isinstance(payload, list):
        raise HyprlandError("Unexpected hyprctl monitors JSON format.")

    monitors: list[Monitor] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "")
        if not name:
            continue
        monitors.append(
            Monitor(
                name=name,
                description=str(item.get("description") or ""),
                width=_as_int(item.get("width")),
                height=_as_int(item.get("height")),
                x=_as_int(item.get("x")),
                y=_as_int(item.get("y")),
                scale=_as_float(item.get("scale")),
                focused=bool(item.get("focused", False)),
            )
        )
    return monitors


def list_tablets() -> list[Tablet]:
    raw = run_hyprctl("devices", "-j")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HyprlandError("Could not parse hyprctl devices JSON.") from exc
    if not isinstance(payload, dict):
        raise HyprlandError("Unexpected hyprctl devices JSON format.")

    tablets: list[Tablet] = []
    raw_tablets = payload.get("tablets", [])
    if not isinstance(raw_tablets, list):
        return tablets
    for item in raw_tablets:
        if not isinstance(item, dict):
            continue
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
    if output is not None:
        monitor_names = {monitor.name for monitor in list_monitors()}
        if output not in monitor_names:
            raise HyprlandError(f"Output is not currently connected: {output}")

    target = output if output is not None else ""
    if get_current_output() == target:
        return

    run_hyprctl("keyword", "input:tablet:output", target)
