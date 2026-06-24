from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gio, Gtk  # noqa: E402

from hyprtablet.hyprland import (  # noqa: E402
    HyprlandError,
    Monitor,
    apply_output,
    get_current_output,
    is_hyprland_session,
    list_monitors,
    list_tablets,
)


class HyprtabletWindow(Adw.ApplicationWindow):
    def __init__(self, app: Adw.Application) -> None:
        super().__init__(application=app, title="Hyprtablet")
        self.set_default_size(520, 460)

        self.monitors: list[Monitor] = []
        self.tablet_rows: list[Adw.ActionRow] = []

        toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar()
        toolbar.add_top_bar(header)

        refresh_button = Gtk.Button(icon_name="view-refresh-symbolic")
        refresh_button.set_tooltip_text("Refresh devices")
        refresh_button.connect("clicked", lambda _button: self.refresh())
        header.pack_end(refresh_button)

        self.toast_overlay = Adw.ToastOverlay()
        toolbar.set_content(self.toast_overlay)

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        main_box.set_margin_top(20)
        main_box.set_margin_bottom(20)
        main_box.set_margin_start(20)
        main_box.set_margin_end(20)
        self.toast_overlay.set_child(main_box)

        title = Gtk.Label(label="Map your tablet to a monitor")
        title.add_css_class("title-2")
        title.set_halign(Gtk.Align.START)
        main_box.append(title)

        self.status = Gtk.Label()
        self.status.set_wrap(True)
        self.status.set_halign(Gtk.Align.START)
        main_box.append(self.status)

        self.tablet_group = Adw.PreferencesGroup(title="Detected Tablets")
        main_box.append(self.tablet_group)

        self.monitor_group = Adw.PreferencesGroup(title="Mapping Target")
        main_box.append(self.monitor_group)

        self.monitor_dropdown = Gtk.DropDown()
        self.monitor_dropdown.set_hexpand(True)
        monitor_row = Adw.ActionRow(title="Output")
        monitor_row.add_suffix(self.monitor_dropdown)
        monitor_row.set_activatable_widget(self.monitor_dropdown)
        self.monitor_group.add(monitor_row)

        self.apply_button = Gtk.Button(label="Apply Mapping")
        self.apply_button.add_css_class("suggested-action")
        self.apply_button.set_halign(Gtk.Align.END)
        self.apply_button.connect("clicked", self.on_apply_clicked)
        main_box.append(self.apply_button)

        self.set_content(toolbar)
        self.refresh()

    def refresh(self) -> None:
        self.apply_button.set_sensitive(False)

        if not is_hyprland_session():
            self.status.set_text("This does not look like a Hyprland session. hyprctl may still work if HYPRLAND_INSTANCE_SIGNATURE is available elsewhere.")

        try:
            tablets = list_tablets()
            monitors = list_monitors()
            current_output = get_current_output()
        except HyprlandError as exc:
            self.clear_tablet_rows()
            self.monitors = []
            self.status.set_text(str(exc))
            self.monitor_dropdown.set_model(Gtk.StringList.new([]))
            self.apply_button.set_sensitive(False)
            return

        self.clear_tablet_rows()
        self.monitors = monitors

        if tablets:
            for tablet in tablets:
                self.add_tablet_row(Adw.ActionRow(title=tablet.name, subtitle=tablet.kind))
        else:
            self.add_tablet_row(Adw.ActionRow(title="No tablets detected", subtitle="Connect a tablet and refresh."))

        labels = ["Full desktop / all monitors"] + [monitor.label for monitor in self.monitors]
        self.monitor_dropdown.set_model(Gtk.StringList.new(labels))

        selected_index = 0
        if current_output:
            for index, monitor in enumerate(self.monitors, start=1):
                if monitor.name == current_output:
                    selected_index = index
                    break
        self.monitor_dropdown.set_selected(selected_index)

        mapping = current_output or "full desktop / all monitors"
        self.status.set_text(f"Current mapping: {mapping}")
        self.apply_button.set_sensitive(bool(self.monitors))

    def on_apply_clicked(self, _button: Gtk.Button) -> None:
        selected = self.monitor_dropdown.get_selected()
        if not self.monitors or selected == Gtk.INVALID_LIST_POSITION or selected > len(self.monitors):
            message = "Select a valid output before applying."
            self.status.set_text(message)
            self.toast_overlay.add_toast(Adw.Toast(title=message))
            return

        output = None if selected == 0 else self.monitors[selected - 1].name

        try:
            apply_output(output)
        except HyprlandError as exc:
            self.status.set_text(str(exc))
            self.toast_overlay.add_toast(Adw.Toast(title=str(exc)))
            return

        label = output or "full desktop / all monitors"
        self.toast_overlay.add_toast(Adw.Toast(title=f"Mapped tablet to {label}"))
        self.refresh()

    def add_tablet_row(self, row: Adw.ActionRow) -> None:
        self.tablet_group.add(row)
        self.tablet_rows.append(row)

    def clear_tablet_rows(self) -> None:
        for row in self.tablet_rows:
            self.tablet_group.remove(row)
        self.tablet_rows = []


class HyprtabletApp(Adw.Application):
    def __init__(self) -> None:
        super().__init__(application_id="dev.hyprtablet.Hyprtablet")
        self.create_action("quit", lambda *_args: self.quit(), ["<primary>q"])

    def do_activate(self) -> None:
        window = self.props.active_window
        if window is None:
            window = HyprtabletWindow(self)
        window.present()

    def create_action(self, name: str, callback, shortcuts: list[str] | None = None) -> None:
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)


def main() -> int:
    app = HyprtabletApp()
    return app.run(None)


if __name__ == "__main__":
    raise SystemExit(main())
