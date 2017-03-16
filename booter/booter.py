import json
from subprocess import call
import subprocess

import urwid

from ipdetect import get_ip_address

ACTIVE_SETTING = '???'


class SettingsSelectorPopUp(urwid.WidgetWrap):
    """A dialog that appears with nothing but a close button """
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
        global ACTIVE_SETTING
        ACTIVE_SETTING = button.get_label()
        self._emit("close")


class ButtonWithAPopUp(urwid.PopUpLauncher):

    def __init__(self, thing):
        global ACTIVE_SETTING
        self.original_label = thing.get_label()
        thing.set_label(self.original_label % ACTIVE_SETTING)
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
        global ACTIVE_SETTING
        self.original_widget.set_label(self.original_label % ACTIVE_SETTING)
        super(ButtonWithAPopUp, self).close_pop_up()

    def get_pop_up_parameters(self):
        return {'left': 0, 'top': 1, 'overlay_width': 32, 'overlay_height': 7}


def fly_18m(button, params):
    call(['xcsoar', '-fly'])
    call(['sudo', 'reboot'])


def fly_15m(button, params):
    call(['xcsoar', '-fly'])
    call(['sudo', 'reboot'])


def simulator(button, params):
    call(['xcsoar', '-simulator'])
    call(['sudo', 'reboot'])


def update_data(button, params):
    proc = subprocess.Popen(['git', 'pull'], stdout=subprocess.PIPE)
    (out, err) = proc.communicate()
    # print out


def exit(button, params):
    raise urwid.ExitMainLoop()


def buttonCreator(onClick):
    def create(label):
        button = urwid.Button(label)
        urwid.connect_signal(button, 'click', onClick, label)
        return button
    return create


def popupCreator(popup):
    def create(label):
        return popup(urwid.Button(label))
    return create


choices = [
    (u'Fly LAK-17a 18m', buttonCreator(fly_18m)),
    (u'Fly LAK-17a 15m', buttonCreator(fly_15m)),
    (u'', None),
    (u'Update Data', buttonCreator(update_data)),
    (u'Change Setting [%s]', popupCreator(ButtonWithAPopUp)),
    (u'', None),
    (u'Simulator', buttonCreator(simulator)),
    (u'', None),
    (u'Exit', buttonCreator(exit)),
]


def menu(title, choices):
    body = [urwid.Text(title), urwid.Divider()]
    for choice, connector in choices:
        if choice == '':
            body.append(urwid.Divider())
        else:
            entry = connector(choice)
            body.append(urwid.AttrMap(entry, 'panel', focus_map='focus'))
    return urwid.ListBox(urwid.SimpleFocusListWalker(body))


footer = urwid.Text('wlan-ip: waiting')

ip = ''


def update_ip(loop=None, user_data=None):
    """Update the current in the footer
    """
    global footer, ip
    current_ip = get_ip_address('wlan0')
    if current_ip == '???':
        ip += '.'
        if len(ip) > 9:
            ip = '.'
        loop.set_alarm_in(1, update_ip)
    else:
        ip = current_ip
        loop.set_alarm_in(10, update_ip)
    footer.set_text('wlan-ip: %s' % ip)


main = urwid.Frame(
    urwid.Padding(menu(u'LAK 17a / D - 5461', choices), left=1, right=1),
    footer=footer
)
page = urwid.Overlay(
    main,
    urwid.SolidFill(u'\N{MEDIUM SHADE}'),
    align='center',
    width=('relative', 40),
    valign='middle',
    height=('relative', 80),
    min_width=20,
    min_height=9,
)

screen = urwid.raw_display.Screen()
screen.set_terminal_properties(256)

palette = [
    ('header',
     'black,underline', 'light gray',
     'standout,underline',
     'black,underline', '#88a'),
    ('panel',
     'light gray', 'dark blue',
     '',
     '#000', 'white'),
    ('focus',
     'light gray', 'dark cyan',
     'standout',
     'white', 'dark green'),
    ('reversed', 'standout', ''),
    ('popbg', 'white', 'dark blue'),
]

screen.register_palette(palette)

loop = urwid.MainLoop(
    page,
    screen=screen,
    pop_ups=True,
)

# start the ip updater in the footer
update_ip(loop)

loop.run()
