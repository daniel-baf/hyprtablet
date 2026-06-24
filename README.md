# Hyprtablet

Native GTK/libadwaita utility for mapping graphics tablets to monitors on Hyprland.

Hyprtablet detects monitors and tablet devices through `hyprctl`, then applies the selected monitor with Hyprland's native tablet configuration:

```sh
hyprctl keyword input:tablet:output <monitor-name>
```

## Features

- Detects whether the current session is Hyprland.
- Lists connected monitors from `hyprctl monitors -j`.
- Lists detected tablets from `hyprctl devices -j`.
- Applies tablet mapping to a selected monitor.
- Supports a full-desktop mapping option by clearing `input:tablet:output`.
- Uses native GTK4/libadwaita UI.

## Requirements

- Arch Linux or an Arch-based distribution
- Hyprland
- `hyprctl`
- Python 3
- GTK4 and libadwaita Python bindings

Install runtime dependencies on Arch:

```sh
sudo pacman -S python-gobject gtk4 libadwaita
```

Install packaging dependencies if you want to build the Arch package:

```sh
sudo pacman -S python-build python-installer python-wheel python-setuptools
```

## Run From Source

```sh
./bin/hyprtablet
```

## Package From A Release Tag

```sh
makepkg -si
```

The included `PKGBUILD` expects a GitHub release tag matching `v0.1.0`.

## Current Scope

Hyprland exposes `input:tablet:output` as a global tablet setting. This means the current MVP maps all tablet tools together. Per-tablet mapping can be added later if Hyprland exposes stable per-device tablet options.
