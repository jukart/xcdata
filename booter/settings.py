import time
import json
import os
import os.path
import shutil

import urwid

import setup


sysInfo = os.uname()
DEVELOPING = sysInfo[0] == 'Darwin'

if DEVELOPING:
    XCSOAR_BASE = os.path.expanduser('~/XCSoarData')
else:
    XCSOAR_BASE = os.path.expanduser('~/.xcsoar')
BOOTER_SETTINGS_FILE = os.path.join(XCSOAR_BASE, 'booter.json')

HERE = os.path.dirname(__file__)
XCDATA_BASE = os.path.dirname(HERE)

ACTIVE_SETTINGS = {
    'xcsoar': {
        'setting': {
        },
    },
}


def getSetting(name, default=None):
    """Read settings using dottet names

    It is possible to use a path which doesn't exist.
    """
    global ACTIVE_SETTINGS
    result = ACTIVE_SETTINGS
    for name in name.split('.'):
        result = result.get(name, object)
        if result is object:
            return default
    return result


def setSetting(name, value):
    global ACTIVE_SETTINGS
    container = ACTIVE_SETTINGS
    path = name.split('.')
    if len(path) > 1:
        container = getSetting('.'.join(path[:-1]))
        if container is None:
            # create the container path
            container = ACTIVE_SETTINGS
            for name in name.split('.'):
                next = container.get(name, object)
                if next is object:
                    container = container.setdefault(name, {})
                elif isinstance(next, dict):
                    container = next
                else:
                    raise KeyError('path exists')
    container[path[-1]] = value


def commitSetting():
    global BOOTER_SETTINGS_FILE
    with open(BOOTER_SETTINGS_FILE, 'w') as f:
        f.write(
            json.dumps(
                ACTIVE_SETTINGS,
                indent=2,
                sort_keys=True,
                ))


class SettingsSelectorPopUp(urwid.WidgetWrap):
    """Allows the user to select a setting
    """
    signals = ['close']

    def __init__(self):
        close_button = urwid.Button("close")
        urwid.connect_signal(
            close_button, 'click', lambda button: self._emit("close"))
        force_update_button = urwid.Button("force update")
        urwid.connect_signal(
            force_update_button, 'click', self.forceUpdate)
        body = [close_button, force_update_button, urwid.Divider()]
        for setting in sorted(setup.settings.keys()):
            button = urwid.Button(setting)
            urwid.connect_signal(
                button, 'click', self.settingSelected, setting)
            body.append(urwid.AttrMap(button, 'panel', focus_map='focus'))
        selector = urwid.ListBox(urwid.SimpleFocusListWalker(body))
        cols = urwid.Columns([
            selector,
            urwid.Filler(urwid.Text('Some text'))])
        fill = urwid.LineBox(cols)
        self.__super.__init__(urwid.AttrWrap(fill, 'popbg'))

    def settingSelected(self, button, params):
        global ACTIVE_SETTINGS
        name = button.get_label()
        data = setup.settings.get(name)
        setSetting('xcsoar.setting.name', name)
        setSetting('xcsoar.setting.data', data)
        commitSetting()
        buildXCSoar()
        self._emit("close")

    def forceUpdate(self, button):
        buildXCSoar(True)
        self._emit("close")


class ButtonWithSettingsSelectorPopUp(urwid.PopUpLauncher):

    def __init__(self, thing):
        global ACTIVE_SETTINGS
        self.original_label = thing.get_label()
        thing.set_label(
            self.original_label % getSetting('xcsoar.setting.name', 'NOT SET!'))
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
                self.original_label % getSetting('xcsoar.setting.name',
                                                 'NOT SET!'))
        super(ButtonWithSettingsSelectorPopUp, self).close_pop_up()

    def get_pop_up_parameters(self):
        return {
            'left': 0,
            'top': 1,
            'overlay_width': ('relative', 100),
            'overlay_height': 7,
        }


def initSettings():
    global BOOTER_SETTINGS_FILE
    # create the XCSOAR_BASE if not present
    if not os.path.exists(XCSOAR_BASE):
        os.makedirs(XCSOAR_BASE)
    # read the current booter settings
    try:
        with open(BOOTER_SETTINGS_FILE, 'r') as f:
            ACTIVE_SETTINGS.update(json.loads(f.read()))
    except IOError:
        pass


def buildXCSoar(forceCopy=False):
    """Create the XCSoar settings based on the active setting
    """
    backupDest = None
    # create the symlinks
    links = getSetting('xcsoar.setting.data.links', {})
    for name, link in links.iteritems():
        sourceBase = os.path.join(XCDATA_BASE, 'data')
        target = os.path.join(XCSOAR_BASE, name)
        if os.path.exists(target):
            # remove existing data
            #  - if it is a symlink just remove it
            #  - everything else is just moved away to have a backup
            if os.path.islink(target):
                os.remove(target)
            else:
                if backupDest is None:
                    now = time.strftime('%Y%m%d-%H%M%S')
                    backupDest = os.path.join(
                        XCSOAR_BASE,
                        'xcdata_backup',
                        now)
                    if not os.path.exists(backupDest):
                        os.makedirs(backupDest)
                os.rename(
                    target,
                    os.path.join(
                        backupDest,
                        os.path.basename(target)
                    )
                )
        if link is None:
            continue
        try:
            os.symlink(os.path.join(sourceBase, link),
                       target)
        except:
            pass
    # copy files
    links = getSetting('xcsoar.setting.data.copy', {})
    for name, link in links.iteritems():
        sourceBase = os.path.join(XCDATA_BASE, 'data')
        target = os.path.join(XCSOAR_BASE, name)
        if os.path.exists(target):
            if not forceCopy:
                continue
            os.remove(target)
            targetDir = os.path.dirname(target)
            if not os.path.exists(targetDir):
                os.makedirs(targetDir)
        shutil.copyfile(sourceBase, target)


initSettings()
buildXCSoar()
