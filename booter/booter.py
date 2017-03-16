import json
from subprocess import call
import subprocess

import urwid

from ipdetect import get_ip_address


def fly_18m(button, params):
    call(['xcsoar', '-fly'])
    call(['sudo', 'reboot'])


def fly_15m(button, params):
    call(['xcsoar', '-fly'])
    call(['sudo', 'reboot'])


def simulator(button, params):
    call(['xcsoar', '-simulator'])
    call(['sudo', 'reboot'])


def activate_settings(button, params):
    proc = subprocess.Popen(['fab', 'xcsoar.list'], stdout=subprocess.PIPE)
    (out, err) = proc.communicate()
    settings = json.loads(out.split('\n')[0])
    print settings


def update_data(button, params):
    proc = subprocess.Popen(['git', 'pull'], stdout=subprocess.PIPE)
    (out, err) = proc.communicate()
    # print out


def exit(button, params):
    raise urwid.ExitMainLoop()


choices = [
    (u'Fly LAK-17a 18m', fly_18m),
    (u'Fly LAK-17a 15m', fly_15m),
    (u'', None),
    (u'Update Data', update_data),
    (u'Activate Settings', activate_settings),
    (u'', None),
    (u'Simulator', simulator),
    (u'', None),
    (u'Exit', exit),
]


def menu(title, choices):
    body = [urwid.Text(title), urwid.Divider()]
    for choice, connector in choices:
        if choice == '':
            body.append(urwid.Divider())
        else:
            button = urwid.Button(choice)
            urwid.connect_signal(button, 'click', connector, choice)
            body.append(urwid.AttrMap(button, 'panel', focus_map='focus'))
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
]

screen.register_palette(palette)

loop = urwid.MainLoop(
    page,
    screen=screen,
)

# start the ip updater in the footer
update_ip(loop)

loop.run()
