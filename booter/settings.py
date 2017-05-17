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
    USB_PATH = os.path.expanduser('~/XCSoarUSB')
else:
    XCSOAR_BASE = os.path.expanduser('~/.xcsoar')
    USB_PATH = '/mnt/usb'

USB_SETTINGS_PATH = os.path.join(USB_PATH, 'settings')
BOOTER_SETTINGS_FILE = os.path.join(XCSOAR_BASE, 'booter.json')

HERE = os.path.dirname(__file__)
XCDATA_BASE = os.path.dirname(HERE)


ACTIVE_SETTINGS = {
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
            for name in name.split('.')[:-1]:
                next = container.get(name, object)
                if next is object:
                    container = container.setdefault(name, {})
                elif isinstance(next, dict):
                    container = next
                else:
                    raise KeyError('path exists')
    container[path[-1]] = value


def commitSetting():
    global BOOTER_SETTINGS_FILE, ACTIVE_SETTINGS
    with open(BOOTER_SETTINGS_FILE, 'w') as f:
        f.write(
            json.dumps(
                ACTIVE_SETTINGS,
                indent=2,
                sort_keys=True,
                ))


def getDecoratedSettingsName():
    name = getSetting('name')
    if name is None:
        name = 'NOT SET!'
    else:
        name += ' ' + getSetting('source', '')
        name += '-' + getSetting('created', '-')
    return name


class SettingsSelectorPopUp(urwid.WidgetWrap):
    """Allows the user to select a setting
    """
    signals = ['close']

    def __init__(self):
        close_button = urwid.Button("close")
        urwid.connect_signal(
            close_button, 'click', lambda button: self._emit("close"))

        force_update_button = urwid.Button(
            "update: " + getDecoratedSettingsName())
        urwid.connect_signal(
            force_update_button, 'click', self.forceUpdate)

        to_usb_copy_button = urwid.Button(
            "to USB: " + getDecoratedSettingsName())
        urwid.connect_signal(
            to_usb_copy_button, 'click', self.toUSBCopy)

        body = [
            close_button,
            to_usb_copy_button,
            force_update_button,
            urwid.Divider(),
        ]
        for setting in sorted(setup.settings.keys()):
            button = urwid.Button(setting + ' (git)')
            urwid.connect_signal(
                button, 'click', self.settingSelected, setting)
            body.append(urwid.AttrMap(button, 'panel', focus_map='focus'))
        body.append(urwid.Divider())
        for filename in USBFiles():
            button = urwid.Button(filename + ' (USB)')
            urwid.connect_signal(
                button, 'click', self.USBSettingSelected, filename)
            body.append(urwid.AttrMap(button, 'panel', focus_map='focus'))
        selector = urwid.ListBox(urwid.SimpleFocusListWalker(body))
        fill = urwid.LineBox(selector)
        self.__super.__init__(urwid.AttrWrap(fill, 'popbg'))

    def settingSelected(self, button, params):
        global ACTIVE_SETTINGS
        ACTIVE_SETTINGS.clear()
        data = setup.settings.get(params)
        setSetting('name', params)
        setSetting('created', time.strftime('%d.%m.%Y %H:%M:%S'))
        setSetting('source', 'git')
        setSetting('git.data', data)
        commitSetting()
        buildXCSoar()
        self._emit("close")

    def USBSettingSelected(self, button, params):
        global ACTIVE_SETTINGS
        ACTIVE_SETTINGS.clear()
        setSetting('name', params)
        setSetting('created', time.strftime('%d.%m.%Y %H:%M:%S'))
        setSetting('source', 'USB')
        setSetting('USB.dirname', params)
        commitSetting()
        buildXCSoar()
        self._emit("close")

    def forceUpdate(self, button):
        setSetting('created', time.strftime('%d.%m.%Y %H:%M:%S'))
        commitSetting()
        buildXCSoar()
        self._emit("close")

    def toUSBCopy(self, button):
        createUSBSetting()
        self._emit("close")


class ButtonWithSettingsSelectorPopUp(urwid.PopUpLauncher):

    def __init__(self, thing):
        self.original_label = thing.get_label()
        thing.set_label(
            self.original_label % getDecoratedSettingsName())
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
        self.original_widget.set_label(
                self.original_label % getDecoratedSettingsName())
        super(ButtonWithSettingsSelectorPopUp, self).close_pop_up()

    def get_pop_up_parameters(self):
        return {
            'left': 0,
            'top': 1,
            'overlay_width': ('relative', 100),
            'overlay_height': 7,
        }


def buildXCSoar(*args, **kwargs):
    buildType = getSetting('source')
    if buildType == 'git':
        buildXCSoarFromGit(*args, **kwargs)
    elif buildType == 'USB':
        buildXCSoarFromUSB(*args, **kwargs)


def buildXCSoarFromGit():
    """Create the XCSoar settings based on the active setting
    """
    backupDest = None
    sourceBase = os.path.join(XCDATA_BASE, 'data')
    # create the symlinks
    links = getSetting('git.data.links', {})
    files = []
    for name, link in links.iteritems():
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
        targetBase = os.path.dirname(target)
        if not os.path.exists(targetBase):
            os.makedirs(targetBase)
        try:
            linkTo = os.path.join(sourceBase, link)
            files.append(name)
            os.symlink(linkTo, target)
        except:
            pass
    # copy files
    copy = getSetting('git.data.copy', {})
    for name, source in copy.iteritems():
        target = os.path.join(XCSOAR_BASE, name)
        files.append(name)
        if os.path.exists(target):
            os.remove(target)
            targetDir = os.path.dirname(target)
            if not os.path.exists(targetDir):
                os.makedirs(targetDir)
        if source is None:
            continue
        sourcePath = os.path.join(XCDATA_BASE, 'data', source)
        shutil.copyfile(sourcePath, target)
    setSetting('files', files)
    commitSetting()


def buildXCSoarFromUSB(*args, **kwargs):
    if not USBConnected():
        return
    dirname = getSetting('USB.dirname')
    if not dirname:
        return
    sourcePath = os.path.join(USB_SETTINGS_PATH, dirname)
    if not os.path.isdir(sourcePath):
        return


def createUSBSetting(name=None):
    """Create or update a setting on the USB path from current settings

    This will create a copy of all setting related files on the
    USB_SETTINGS_PATH with the given name. If no name is provided the name in
    the settings is used.
    """
    if not USBConnected():
        return
    if name is None:
        name = getSetting('name')
    if not name:
        return
    name += time.strftime('-%Y%m%d-%H%M%S')
    files = getSetting('files', [])
    baseTargetPath = os.path.join(USB_SETTINGS_PATH, name)
    if os.path.exists(baseTargetPath):
        shutil.rmtree(baseTargetPath)
    if not os.path.exists(baseTargetPath):
        os.makedirs(baseTargetPath)
    for source in files:
        sourcePath = os.path.join(XCSOAR_BASE, source)
        if not os.path.exists(sourcePath):
            continue
        targetPath = os.path.join(baseTargetPath, source)
        if os.path.isdir(sourcePath):
            if os.path.exists(targetPath):
                if os.path.isdir(targetPath):
                    os.remove(targetPath)
                else:
                    shutil.rmtree(targetPath)
            shutil.copytree(sourcePath, targetPath)
        else:
            # copy a single file
            targetDir = os.path.dirname(targetPath)
            if not os.path.exists(targetDir):
                os.makedirs(targetDir)
            shutil.copy(sourcePath, targetPath)


def USBFiles():
    if USBConnected():
        for filename in os.listdir(USB_SETTINGS_PATH):
            if not filename.startswith('.'):
                yield filename


def USBConnected():
    return os.path.exists(USB_PATH) # and os.path.isdir(USB_PATH)


def initSettings():
    global BOOTER_SETTINGS_FILE, ACTIVE_SETTINGS
    # create the XCSOAR_BASE if not present
    if not os.path.exists(XCSOAR_BASE):
        os.makedirs(XCSOAR_BASE)
    # read the current booter settings
    try:
        with open(BOOTER_SETTINGS_FILE, 'r') as f:
            settings = json.loads(f.read())
        ACTIVE_SETTINGS.clear()
        ACTIVE_SETTINGS.update(settings)
    except IOError:
        pass


initSettings()
