import hashlib
import os
import secrets
import shutil
import time
from pathlib import Path

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.logger import Logger
from kivy.metrics import dp
from kivy.storage.jsonstore import JsonStore
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.videoplayer import VideoPlayer

PIN_LENGTH = 4
MAX_ATTEMPTS = 5
LOCKOUT_SECONDS = 30

IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
VIDEO_EXTS = {'.mp4', '.mov', '.mkv', '.3gp'}

KV = '''
#:import FadeTransition kivy.uix.screenmanager.FadeTransition

ScreenManager:
    transition: FadeTransition()
    LoginScreen:
    VaultScreen:

<CircleButton@Button>:
    background_color: 0, 0, 0, 0
    background_normal: ''
    background_down: ''
    font_size: '28sp'
    color: (1, 1, 1, 0.3) if self.disabled else (1, 1, 1, 1)
    size_hint: None, None
    size: dp(68), dp(68)
    canvas.before:
        Color:
            rgba: (1, 1, 1, 0.06) if self.disabled else ((1, 1, 1, 0.35) if self.state == 'down' else (1, 1, 1, 0.13))
        Ellipse:
            pos: self.pos
            size: self.size

<LoginScreen>:
    name: 'login'
    canvas.before:
        Color:
            rgba: 0, 0, 0, 1
        Rectangle:
            pos: self.pos
            size: self.size

    BoxLayout:
        orientation: 'vertical'
        padding: dp(24), dp(40), dp(24), dp(24)
        spacing: dp(14)

        Widget:
            size_hint_y: 0.06

        Label:
            text: '\\U0001F512'
            font_size: '36sp'
            size_hint_y: None
            height: dp(46)

        Label:
            id: title_label
            text: 'Enter Passcode'
            font_size: '20sp'
            color: 1, 1, 1, 1
            size_hint_y: None
            height: dp(36)

        BoxLayout:
            id: dots_row
            orientation: 'horizontal'
            size_hint_x: None
            width: self.minimum_width
            size_hint_y: None
            height: dp(28)
            spacing: dp(16)
            pos_hint: {'center_x': 0.5}

            Label:
                id: dot_0
                text: '\\u25CB'
                font_size: '22sp'
                color: 1, 1, 1, 1
                size_hint_x: None
                width: dp(26)
            Label:
                id: dot_1
                text: '\\u25CB'
                font_size: '22sp'
                color: 1, 1, 1, 1
                size_hint_x: None
                width: dp(26)
            Label:
                id: dot_2
                text: '\\u25CB'
                font_size: '22sp'
                color: 1, 1, 1, 1
                size_hint_x: None
                width: dp(26)
            Label:
                id: dot_3
                text: '\\u25CB'
                font_size: '22sp'
                color: 1, 1, 1, 1
                size_hint_x: None
                width: dp(26)

        Label:
            id: error_label
            text: ''
            color: 1, 0.35, 0.35, 1
            font_size: '14sp'
            size_hint_y: None
            height: dp(22)

        Widget:
            size_hint_y: 0.06

        GridLayout:
            id: keypad
            cols: 3
            spacing: dp(16)
            size_hint: None, None
            size: dp(3 * 68 + 2 * 16), dp(4 * 68 + 3 * 16)
            pos_hint: {'center_x': 0.5}

            CircleButton:
                text: '1'
                on_release: root.on_key_press('1')
            CircleButton:
                text: '2'
                on_release: root.on_key_press('2')
            CircleButton:
                text: '3'
                on_release: root.on_key_press('3')
            CircleButton:
                text: '4'
                on_release: root.on_key_press('4')
            CircleButton:
                text: '5'
                on_release: root.on_key_press('5')
            CircleButton:
                text: '6'
                on_release: root.on_key_press('6')
            CircleButton:
                text: '7'
                on_release: root.on_key_press('7')
            CircleButton:
                text: '8'
                on_release: root.on_key_press('8')
            CircleButton:
                text: '9'
                on_release: root.on_key_press('9')
            Widget:
            CircleButton:
                text: '0'
                on_release: root.on_key_press('0')
            CircleButton:
                text: '\\u232B'
                font_size: '20sp'
                on_release: root.on_backspace()

        Button:
            id: forgot_btn
            text: 'Forgot Passcode?'
            font_size: '13sp'
            color: 0.5, 0.72, 1, 1
            background_color: 0, 0, 0, 0
            background_normal: ''
            background_down: ''
            size_hint_y: None
            height: dp(30)
            opacity: 0
            disabled: True
            on_release: root.confirm_forgot_passcode()

        Widget:
            size_hint_y: 0.1

<VaultScreen>:
    name: 'vault'
    canvas.before:
        Color:
            rgba: 0, 0, 0, 1
        Rectangle:
            pos: self.pos
            size: self.size

    BoxLayout:
        orientation: 'vertical'
        padding: dp(20)
        spacing: dp(20)

        BoxLayout:
            size_hint_y: None
            height: dp(50)
            Label:
                text: 'My Hidden Files'
                font_size: '22sp'
                bold: True
                text_size: self.size
                halign: 'left'
                valign: 'middle'
            Button:
                text: 'Log Out'
                size_hint_x: None
                width: dp(90)
                on_release: root.log_out()

        ScrollView:
            GridLayout:
                id: file_list
                cols: 1
                spacing: dp(10)
                size_hint_y: None
                height: self.minimum_height

        Button:
            text: '+ Import File'
            size_hint_y: None
            height: dp(60)
            font_size: '18sp'
            background_color: 0.2, 0.6, 1, 1
            on_release: root.open_file_chooser()
'''


class PinManager:
    """Stores and verifies the vault PIN; tracks lockout state."""

    def __init__(self, store_path):
        self.store = JsonStore(store_path)
        if self.store.exists('lockout'):
            data = self.store.get('lockout')
            self.failed_attempts = data.get('failed_attempts', 0)
            self.locked_until = data.get('locked_until', 0)
        else:
            self.failed_attempts = 0
            self.locked_until = 0

    def has_pin(self):
        return self.store.exists('pin')

    @staticmethod
    def _hash(pin, salt):
        return hashlib.sha256((salt + pin).encode()).hexdigest()

    def set_pin(self, pin):
        salt = secrets.token_hex(16)
        self.store.put('pin', hash=self._hash(pin, salt), salt=salt)
        self.register_success()

    def verify_pin(self, pin):
        if not self.has_pin():
            return False
        data = self.store.get('pin')
        return self._hash(pin, data['salt']) == data['hash']

    def is_locked(self):
        return time.time() < self.locked_until

    def seconds_remaining(self):
        return max(0, int(self.locked_until - time.time()))

    def _save_lockout_state(self):
        self.store.put(
            'lockout',
            failed_attempts=self.failed_attempts,
            locked_until=self.locked_until,
        )

    def register_failure(self):
        self.failed_attempts += 1
        if self.failed_attempts >= MAX_ATTEMPTS:
            self.locked_until = time.time() + LOCKOUT_SECONDS
            self.failed_attempts = 0
        self._save_lockout_state()

    def register_success(self):
        self.failed_attempts = 0
        self.locked_until = 0
        self._save_lockout_state()

    def reset(self):
        """Erase the stored PIN and lockout state entirely.

        Used by the "forgot passcode" flow, which wipes the whole vault
        rather than trying to recover the old PIN (there's nothing to
        recover it from — only a hash + salt are ever stored).
        """
        if self.store.exists('pin'):
            self.store.delete('pin')
        if self.store.exists('lockout'):
            self.store.delete('lockout')
        self.failed_attempts = 0
        self.locked_until = 0


class LoginScreen(Screen):
    mode = 'login'  # 'login' | 'setup_create' | 'setup_confirm'
    pending_pin = ''
    current_pin = ''
    _lockout_event = None

    def on_pre_enter(self):
        Clock.schedule_once(self.setup_ui, 0)

    def setup_ui(self, dt):
        self.current_pin = ''
        self._update_dots()
        self.ids.error_label.text = ''
        self.pending_pin = ''

        pin_manager = App.get_running_app().pin_manager

        has_pin = pin_manager.has_pin()
        self.ids.forgot_btn.opacity = 1 if has_pin else 0
        self.ids.forgot_btn.disabled = not has_pin

        if pin_manager.is_locked():
            self.ids.title_label.text = 'Enter Passcode'
            self._start_lockout_countdown()
            return

        self.ids.keypad.disabled = False
        if pin_manager.has_pin():
            self.mode = 'login'
            self.ids.title_label.text = 'Enter Passcode'
        else:
            self.mode = 'setup_create'
            self.ids.title_label.text = 'Create Passcode'

    def on_key_press(self, digit):
        pin_manager = App.get_running_app().pin_manager
        if pin_manager.is_locked() or len(self.current_pin) >= PIN_LENGTH:
            return
        self.ids.error_label.text = ''
        self.current_pin += digit
        self._update_dots()
        if len(self.current_pin) == PIN_LENGTH:
            self._submit_pin(self.current_pin)

    def on_backspace(self):
        self.current_pin = self.current_pin[:-1]
        self._update_dots()

    def _update_dots(self):
        filled = len(self.current_pin)
        for i in range(PIN_LENGTH):
            self.ids[f'dot_{i}'].text = '\u25CF' if i < filled else '\u25CB'

    def _clear_entry(self):
        self.current_pin = ''
        self._update_dots()

    def _submit_pin(self, text):
        pin_manager = App.get_running_app().pin_manager

        if self.mode == 'setup_create':
            self.pending_pin = text
            self.mode = 'setup_confirm'
            self.ids.title_label.text = 'Confirm Passcode'
            self._clear_entry()
            return

        if self.mode == 'setup_confirm':
            if text == self.pending_pin:
                pin_manager.set_pin(text)
                self._go_to_vault()
            else:
                self.ids.error_label.text = "Passcodes didn't match. Try again."
                self.mode = 'setup_create'
                self.ids.title_label.text = 'Create Passcode'
                self.pending_pin = ''
                self._clear_entry()
            return

        if pin_manager.verify_pin(text):
            pin_manager.register_success()
            self._go_to_vault()
        else:
            pin_manager.register_failure()
            self._clear_entry()
            if pin_manager.is_locked():
                self._start_lockout_countdown()
            else:
                remaining = MAX_ATTEMPTS - pin_manager.failed_attempts
                self.ids.error_label.text = f'Incorrect passcode. {remaining} attempt(s) left.'

    def _go_to_vault(self):
        self.ids.error_label.text = ''
        self._clear_entry()
        self.manager.current = 'vault'

    def _start_lockout_countdown(self):
        self.ids.keypad.disabled = True
        pin_manager = App.get_running_app().pin_manager

        def tick(dt):
            remaining = pin_manager.seconds_remaining()
            if remaining <= 0:
                self.ids.error_label.text = ''
                self.ids.keypad.disabled = False
                self.ids.title_label.text = 'Enter Passcode'
                self.mode = 'login'
                return False
            self.ids.error_label.text = f'Too many attempts. Try again in {remaining}s.'

        tick(0)
        if self._lockout_event:
            self._lockout_event.cancel()
        self._lockout_event = Clock.schedule_interval(tick, 1)

    # ---- forgot passcode (wipes the vault) -----------------------------

    def confirm_forgot_passcode(self):
        if self.mode in ('setup_create', 'setup_confirm'):
            return

        content = BoxLayout(orientation='vertical', spacing=dp(14), padding=dp(16))

        warning = Label(
            text=(
                "This can't be undone.\n\n"
                "Resetting your passcode permanently erases every file "
                "in the vault, along with the passcode itself."
            ),
            color=(1, 1, 1, 1),
            halign='center',
            valign='middle',
        )
        warning.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        content.add_widget(warning)

        btn_row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(10))
        cancel_btn = Button(text='Cancel')
        erase_btn = Button(text='Erase Everything', background_color=(0.6, 0.15, 0.15, 1))
        btn_row.add_widget(cancel_btn)
        btn_row.add_widget(erase_btn)
        content.add_widget(btn_row)

        popup = Popup(title='Reset Vault?', content=content, size_hint=(0.85, 0.42),
                       auto_dismiss=False)
        cancel_btn.bind(on_release=popup.dismiss)

        def do_erase(_btn):
            popup.dismiss()
            self._erase_vault()

        erase_btn.bind(on_release=do_erase)
        popup.open()

    def _erase_vault(self):
        app = App.get_running_app()

        if app.hidden_dir and app.hidden_dir.exists():
            for f in app.hidden_dir.iterdir():
                if f.is_file() and f.name != '.nomedia':
                    try:
                        f.unlink()
                    except OSError as exc:
                        Logger.error('VaultApp: failed to erase %s during reset: %s', f, exc)

        app.pin_manager.reset()
        Logger.info('VaultApp: vault reset - all files and passcode erased')

        if self._lockout_event:
            self._lockout_event.cancel()
            self._lockout_event = None

        self.mode = 'setup_create'
        self.ids.keypad.disabled = False
        self.ids.title_label.text = 'Create Passcode'
        self.ids.error_label.text = 'Vault erased. Create a new passcode.'
        self._clear_entry()
        self.ids.forgot_btn.opacity = 0
        self.ids.forgot_btn.disabled = True


class VaultScreen(Screen):
    def on_enter(self):
        self.load_hidden_files()

    # ---- file list --------------------------------------------------

    def load_hidden_files(self):
        self.ids.file_list.clear_widgets()
        app = App.get_running_app()

        if not app.hidden_dir or not app.hidden_dir.exists():
            return

        filenames = sorted(
            f.name for f in app.hidden_dir.iterdir()
            if f.is_file() and f.name != '.nomedia'
        )

        for filename in filenames:
            self.ids.file_list.add_widget(self._build_file_row(filename))

    def _build_file_row(self, filename):
        row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))

        # The filename itself is the "open/view" control.
        name_btn = Button(
            text=filename, color=(1, 1, 1, 1), halign='left', valign='middle',
            shorten=True, background_color=(0, 0, 0, 0),
            background_normal='', background_down='',
        )
        name_btn.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        name_btn.bind(on_release=lambda _btn, fn=filename: self.view_file(fn))
        row.add_widget(name_btn)

        restore_btn = Button(text='Restore', size_hint_x=None, width=dp(78),
                              background_color=(0.15, 0.45, 0.2, 1))
        restore_btn.bind(on_release=lambda _btn, fn=filename: self.restore_file(fn))
        row.add_widget(restore_btn)

        remove_btn = Button(text='Remove', size_hint_x=None, width=dp(78),
                             background_color=(0.6, 0.15, 0.15, 1))
        remove_btn.bind(on_release=lambda _btn, fn=filename: self._confirm_remove_file(fn))
        row.add_widget(remove_btn)

        return row

    def _confirm_remove_file(self, filename):
        content = BoxLayout(orientation='vertical', spacing=dp(14), padding=dp(16))

        msg_label = Label(
            text=f'Permanently delete "{filename}" from the vault?',
            color=(1, 1, 1, 1),
            halign='center',
            valign='middle',
        )
        msg_label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        content.add_widget(msg_label)

        btn_row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(10))
        cancel_btn = Button(text='Cancel')
        delete_btn = Button(text='Delete', background_color=(0.6, 0.15, 0.15, 1))
        btn_row.add_widget(cancel_btn)
        btn_row.add_widget(delete_btn)
        content.add_widget(btn_row)

        popup = Popup(title='Remove File?', content=content, size_hint=(0.85, 0.35),
                       auto_dismiss=False)
        cancel_btn.bind(on_release=popup.dismiss)

        def do_delete(_btn):
            popup.dismiss()
            self._remove_file(filename)

        delete_btn.bind(on_release=do_delete)
        popup.open()

    def _remove_file(self, filename):
        app = App.get_running_app()
        if not app.hidden_dir:
            return
        try:
            (app.hidden_dir / filename).unlink()
            Logger.info('VaultApp: removed %s from vault', filename)
        except OSError as exc:
            Logger.error('VaultApp: failed to remove %s: %s', filename, exc)
            self._show_message(f'Could not remove "{filename}".')
            return
        self.load_hidden_files()

    # ---- viewing a file ----------------------------------------------

    def view_file(self, filename):
        app = App.get_running_app()
        if not app.hidden_dir:
            return
        path = app.hidden_dir / filename
        if not path.exists():
            self._show_message(f'"{filename}" is missing from the vault.')
            return

        ext = path.suffix.lower()
        if ext in IMAGE_EXTS:
            self._show_image_popup(path)
        elif ext in VIDEO_EXTS:
            self._show_video_popup(path)
        else:
            self._show_message("Can't preview this file type yet.")

    def _show_image_popup(self, path):
        content = BoxLayout(orientation='vertical', spacing=dp(8), padding=dp(8))
        content.add_widget(Image(source=str(path)))
        close_btn = Button(text='Close', size_hint_y=None, height=dp(48))
        content.add_widget(close_btn)

        popup = Popup(title=path.name, content=content, size_hint=(0.95, 0.9))
        close_btn.bind(on_release=popup.dismiss)
        popup.open()

    def _show_video_popup(self, path):
        content = BoxLayout(orientation='vertical', spacing=dp(8), padding=dp(8))
        player = VideoPlayer(source=str(path), state='play')
        content.add_widget(player)
        close_btn = Button(text='Close', size_hint_y=None, height=dp(48))
        content.add_widget(close_btn)

        popup = Popup(title=path.name, content=content, size_hint=(0.95, 0.9))

        def on_close(*_args):
            player.state = 'stop'
            popup.dismiss()

        close_btn.bind(on_release=on_close)
        popup.bind(on_dismiss=lambda *_a: setattr(player, 'state', 'stop'))
        popup.open()

    # ---- importing a file (hide) --------------------------------------

    def open_file_chooser(self):
        try:
            from plyer import filechooser
        except (ImportError, ModuleNotFoundError):
            Logger.error('VaultApp: plyer is not installed')
            self._show_message('File picker is unavailable (plyer not installed).')
            return

        try:
            filechooser.open_file(on_selection=self._on_file_selected, multiple=False)
        except NotImplementedError:
            Logger.error('VaultApp: no file chooser on this platform')
            self._show_message('File picker is not supported on this device.')

    def _on_file_selected(self, selection):
        if not selection:
            return
        Clock.schedule_once(lambda dt: self._hide_file(selection[0]))

    def _hide_file(self, source_path):
        app = App.get_running_app()
        if not app.hidden_dir:
            self._show_message("Vault storage isn't available right now.")
            return

        source = Path(source_path)
        dest = self._unique_destination(app.hidden_dir, source.name)

        try:
            shutil.copy2(source, dest)
        except OSError as exc:
            Logger.error('VaultApp: failed to copy %s: %s', source, exc)
            self._show_message('Could not hide that file.')
            return

        removed_original = False
        try:
            source.unlink()
            removed_original = True
        except OSError:
            pass

        Logger.info('VaultApp: hid %s as %s (original removed: %s)',
                    source, dest, removed_original)
        self.load_hidden_files()
        if removed_original:
            self._show_message(f'Hid "{dest.name}" and removed the original.')
        else:
            self._show_message(
                f'Hid "{dest.name}". Delete the original from your gallery '
                'manually if you want it gone from both places.'
            )

    @staticmethod
    def _unique_destination(directory, filename):
        dest = directory / filename
        if not dest.exists():
            return dest
        stem, suffix = Path(filename).stem, Path(filename).suffix
        counter = 1
        while dest.exists():
            dest = directory / f'{stem}_{counter}{suffix}'
            counter += 1
        return dest

    # ---- restoring a file back to phone storage ------------------------

    def restore_file(self, filename):
        app = App.get_running_app()
        if not app.hidden_dir:
            return
        source = app.hidden_dir / filename
        if not source.exists():
            self._show_message(f'"{filename}" is missing from the vault.')
            return

        try:
            from plyer import filechooser
        except (ImportError, ModuleNotFoundError):
            self._show_message('Restore is unavailable (plyer not installed).')
            return

        def write_to_stream(java_stream):
            # On Android, plyer's save_file() hands the callback an open
            # Java FileOutputStream at the location the user picked in the
            # system "Save As" dialog, and closes it for us afterwards —
            # we just need to write the bytes in. This runs off Kivy's
            # main thread, so UI updates are scheduled via Clock below.
            try:
                with open(source, 'rb') as f:
                    while True:
                        chunk = f.read(65536)
                        if not chunk:
                            break
                        java_stream.write(bytearray(chunk))
                source.unlink()
                Clock.schedule_once(lambda dt: self._on_restore_done(filename, True))
            except Exception as exc:
                Logger.error('VaultApp: restore failed for %s: %s', filename, exc)
                Clock.schedule_once(lambda dt: self._on_restore_done(filename, False))

        try:
            filechooser.save_file(title=filename, callback=write_to_stream)
        except (NotImplementedError, TypeError):
            # save_file's "callback receives a stream" contract above is
            # Android-specific; this covers desktop/unsupported platforms.
            Logger.error('VaultApp: restore is only supported on Android')
            self._show_message('Restore only works in the installed Android app.')

    def _on_restore_done(self, filename, success):
        if success:
            self.load_hidden_files()
            self._show_message(f'Restored "{filename}" to your chosen folder.')
        else:
            self._show_message(f'Could not restore "{filename}".')

    # ---- misc -----------------------------------------------------------

    def _show_message(self, text):
        popup = Popup(
            title='Vault',
            content=Label(text=text, color=(1, 1, 1, 1)),
            size_hint=(0.85, 0.3),
        )
        popup.open()
        Clock.schedule_once(lambda dt: popup.dismiss(), 2.5)

    def log_out(self):
        self.manager.current = 'login'


class VaultApp(App):
    def build(self):
        self.title = 'Secret Vault'

        self.hidden_dir = None
        try:
            self.hidden_dir = self._setup_hidden_directory()
        except OSError as exc:
            Logger.error('VaultApp: could not set up hidden directory: %s', exc)

        store_path = os.path.join(self.user_data_dir, 'vault_pin.json')
        self.pin_manager = PinManager(store_path)
        Window.bind(on_keyboard=self._handle_back_button)
        return Builder.load_string(KV)

    def _setup_hidden_directory(self):
        """Create the app-private folder that holds vault media.

        `user_data_dir` is already private to this app on Android — other
        apps, and Gallery/Files apps, can't see into it without root. The
        `.nomedia` marker is a belt-and-braces extra for older Android
        versions with a more permissive media scanner. Neither of these
        encrypts anything; real confidentiality would need the files
        themselves encrypted, not just hidden.
        """
        hidden_dir = Path(self.user_data_dir) / 'hidden_media'
        hidden_dir.mkdir(parents=True, exist_ok=True)
        (hidden_dir / '.nomedia').touch(exist_ok=True)

        Logger.info('VaultApp: hidden directory ready at %s', hidden_dir)
        return hidden_dir

    def _handle_back_button(self, window, key, *args):
        if key != 27:  # 27 = Android / ESC "back"
            return False
        if self.root.current == 'vault':
            self.root.current = 'login'
            return True  # consumed: don't exit the app
        return False  # on login screen, let back behave normally

    # ---- re-lock whenever the app leaves the foreground -----------------

    def on_pause(self):
        # Returning True tells Android to pause (not kill) the app while
        # it's backgrounded, instead of losing state. We re-lock in
        # on_resume so the vault is never left open behind other apps.
        return True

    def on_resume(self):
        if self.root and self.root.current == 'vault':
            self.root.current = 'login'


if __name__ == '__main__':
    VaultApp().run()
