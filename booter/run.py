import subprocess
import urwid


class RunPopUp(urwid.WidgetWrap):
    """Runs a command in a subprocess and shows the output
    """
    signals = ['close']

    def __init__(self, cmd, loop):
        close_button = urwid.Button("close")
        urwid.connect_signal(
            close_button, 'click', lambda button: self._emit("close"))
        output_widget = urwid.Text(
            'Running command: ' + ' '.join(cmd) + '...\n\n')
        pile = urwid.Pile([
            ('weight', 1, close_button),
            ('weight', 18, output_widget),
            ])
        box = urwid.Filler(pile, valign='top')
        box = urwid.LineBox(box)
        self.__super.__init__(urwid.AttrWrap(box, 'popbg'))

        def received_output(data):
            output_widget.set_text(output_widget.text + data)
        write_fd = loop.watch_pipe(received_output)
        subprocess.Popen(cmd, stdout=write_fd, stderr=write_fd, close_fds=True)


class ButtonWithRunPopUp(urwid.PopUpLauncher):

    def __init__(self, button, cmd, loopGetter):
        self.cmd = cmd
        self.loopGetter = loopGetter
        self.__super.__init__(button)
        urwid.connect_signal(
            self.original_widget,
            'click',
            lambda button: self.open_pop_up())

    def create_pop_up(self):
        pop_up = RunPopUp(self.cmd, self.loopGetter())
        urwid.connect_signal(
            pop_up,
            'close',
            lambda button: self.close_pop_up())
        return pop_up

    def get_pop_up_parameters(self):
        return {
            'left': 0,
            'top': 0,
            'overlay_width': 80,
            'overlay_height': 20,
        }


def runCreator(cmd, loopGetter):
    def create(button):
        return ButtonWithRunPopUp(button, cmd, loopGetter)
    return create
