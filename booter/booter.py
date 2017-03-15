from subprocess import call
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
    pass


def update_data(button, params):
    proc = subprocess.Popen(['git', 'status'], stdout=subprocess.PIPE)
    (out, err) = proc.communicate()
    print out


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

footer = urwid.Text('wlan-ip: ' + get_ip_address('wlan0'))

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

urwid.MainLoop(
    page,
    screen=screen,
).run()
