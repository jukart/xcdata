from subprocess import call

import urwid

import settings
import run
from ipdetect import get_ip_address


def runXCSoar(*params):
    if settings.DEVELOPING:
        pars = ['/Applications/XCSoar.app/Contents/MacOS/xcsoar',
                  '-1024x600']
    else:
        pars = ['xcsoar']
    pars.extend(params)
    call(pars)
    if not settings.DEVELOPING:
        call(['sudo', 'reboot'])


def fly_18m(button, params):
    runXCSoar('-fly')


def fly_15m(button, params):
    runXCSoar('-fly')


def simulator(button, params):
    runXCSoar('-simulator')


def update_data(button, params):
    run.run(['git', 'pull'], loop)


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


def getLoop():
    return loop


choices = [
    (u'Fly LAK-17a 18m', buttonCreator(fly_18m)),
    (u'Fly LAK-17a 15m', buttonCreator(fly_15m)),
    (u'', None),
    (u'Change Setting [%s]',
     popupCreator(settings.ButtonWithSettingsSelectorPopUp)),
    (u'', None),
    (u'Simulator', buttonCreator(simulator)),
    (u'', None),
    (u'Update Data [via git pull]',
     popupCreator(run.runCreator(['git', 'pull'], getLoop))),
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


footer_text = 'wlan-ip: %s'
footer = urwid.Text(footer_text % 'starting')

ip = ''


def update_ip(loop=None, user_data=None):
    """Update the current ip in the footer
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
    footer.set_text(footer_text % ip)


palette = [
    ('header', 'black,underline', 'light gray', 'standout,underline',
     'black,underline', '#88a'),
    ('panel', 'light gray', 'dark blue', '', '#000', 'white'),
    ('focus', 'light gray', 'dark cyan', 'standout', 'white', 'light green'),
    ('reversed', 'standout', ''),
    ('popbg', 'white', 'black', '', 'black', 'white'),
    ('bg', 'white', 'black', '', 'black', 'white'),
]

placeholder = urwid.SolidFill()
loop = urwid.MainLoop(
    placeholder,
    palette,
    pop_ups=True,
)
loop.screen.set_terminal_properties(256)
loop.widget = urwid.AttrMap(placeholder, 'bg')


main = urwid.Frame(
    urwid.Padding(menu(u'LAK 17a / D - 5461', choices), left=1, right=1),
    footer=footer
)
page = urwid.Overlay(
    main,
    urwid.SolidFill(u' '),
    align='center',
    width=('relative', 90),
    valign='middle',
    height=('relative', 90),
    min_width=20,
    min_height=9,
)
loop.widget.original_widget = page

# start the ip updater in the footer
update_ip(loop)

loop.run()
