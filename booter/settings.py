import json
import os.path
import subprocess

import urwid


SETTINGS_FILE = os.path.expanduser('~/.xcsoar/booter.json')

ACTIVE_SETTINGS = {
    'xcsoar_setting_name': '???'
}


def getSetting(name, default=None):
    global ACTIVE_SETTINGS
    return ACTIVE_SETTINGS.get(name, default)


def setSetting(name, value):
    global ACTIVE_SETTINGS, SETTINGS_FILE
    ACTIVE_SETTINGS[name] = value
    with open(SETTINGS_FILE, 'w') as f:
        f.write(json.dumps(ACTIVE_SETTINGS))


class SettingsSelectorPopUp(urwid.WidgetWrap):
    """Reads the settings using the fabric script and provides a selection
    """
    signals = ['close']

    def __init__(self):
        proc = subprocess.Popen(['fab', 'xcsoar.list'], stdout=subprocess.PIPE)
        (out, err) = proc.communicate()
        close_button = urwid.Button("close")
        urwid.connect_signal(
            close_button, 'click', lambda button: self._emit("close"))
        body = [close_button, urwid.Divider()]
        for setting in sorted(json.loads(out.split('\n')[0])):
            button = urwid.Button(setting)
            urwid.connect_signal(
                button, 'click', self.settingSelected, setting)
            body.append(urwid.AttrMap(button, 'panel', focus_map='focus'))
        selector = urwid.ListBox(urwid.SimpleFocusListWalker(body))
        fill = urwid.Padding(selector, left=1, right=1)
        self.__super.__init__(urwid.AttrWrap(fill, 'popbg'))

    def settingSelected(self, button, params):
        global ACTIVE_SETTINGS
        setSetting('xcsoar_setting_name', button.get_label())
        self._emit("close")


class ButtonWithSettingsSelectorPopUp(urwid.PopUpLauncher):

    def __init__(self, thing):
        global ACTIVE_SETTINGS
        self.original_label = thing.get_label()
        thing.set_label(
            self.original_label % getSetting('xcsoar_setting_name', '???'))
        self.__super.__init__(thing)
        urwid.connect_signal(
            self.original_widget,
            'click',
            lambda button: self.open_pop_up())

    def create_pop_up(self):
        pop_up = SettingsSelectorPopUp()
        urwid.connect_signal(
            pop_up,
            'close',
            lambda button: self.close_pop_up())
        return pop_up

    def close_pop_up(self):
        global ACTIVE_SETTINGS
        self.original_widget.set_label(
                self.original_label % getSetting('xcsoar_setting_name', '???'))
        super(ButtonWithSettingsSelectorPopUp, self).close_pop_up()

    def get_pop_up_parameters(self):
        return {
            'left': 0,
            'top': 1,
            'overlay_width': 32,
            'overlay_height': 7,
        }


def initSettings():
    try:
        with open(SETTINGS_FILE, 'r') as f:
            ACTIVE_SETTINGS.update(json.loads(f.read()))
    except IOError:
        pass


initSettings()
