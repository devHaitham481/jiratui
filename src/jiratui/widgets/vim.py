"""This module contains the building blocks of the Vim-style key bindings of the application.

The Vim key bindings are opt-in. Users enable them by setting the config variable `enable_vim_keybindings` to `True`.
The module provides:

- [vim_keybindings_enabled](#jiratui.widgets.vim.vim_keybindings_enabled): a helper to check whether the user enabled
  the Vim key bindings. Widgets use it in their `check_action()` method so that the Vim bindings are only active when
  the user asked for them.
- [VIM_KEYMAP](#jiratui.widgets.vim.VIM_KEYMAP): a keymap that re-assigns some of the default bindings of the app so
  they do not clash with the Vim bindings.
- [VimScrollBindings](#jiratui.widgets.vim.VimScrollBindings) and
  [VimDataTableBindings](#jiratui.widgets.vim.VimDataTableBindings): mixins that add Vim motions to scrollable
  containers and to data tables respectively.
- [VimCommandScreen](#jiratui.widgets.vim.VimCommandScreen): the `:` command line that supports commands such as `:q`
  and `:q!`.

**See Also**:
- [Use Case: Vim Key Bindings](#use-case-vim-keybindings)
"""

from typing import cast

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Horizontal
from textual.screen import ModalScreen
from textual.widgets import Input, Static

from jiratui.config import CONFIGURATION

VIM_KEYMAP: dict[str, str] = {
    # `k` and `j` are used by Vim to move up/down so the widgets that use them by default are moved out of the way
    'main_screen.focus_work_item_key': 'w',
    'main_screen.focus_jql_expression': 'e',
    # in Vim `/` searches within the thing you are looking at; `.` is kept so existing muscle memory keeps working
    'search_results.filter': '/,.',
}
"""The keymap applied to the default bindings of the app when `enable_vim_keybindings` is `True`.

It maps the ID of a binding into the key (or comma-separated list of keys) that should trigger it.
"""


def vim_keybindings_enabled() -> bool:
    """Indicates whether the user enabled the Vim-style key bindings.

    Returns:
        `True` if the config variable `enable_vim_keybindings` is enabled; `False` otherwise.
    """

    return bool(CONFIGURATION.get().enable_vim_keybindings)


VIM_SCROLL_BINDINGS: list[BindingType] = [
    Binding('j', 'vim_scroll_down', 'Scroll down', show=False),
    Binding('k', 'vim_scroll_up', 'Scroll up', show=False),
    Binding('g', 'vim_scroll_home', 'Top', show=False),
    Binding('G', 'vim_scroll_end', 'Bottom', show=False),
    Binding('ctrl+d', 'vim_page_down', 'Page down', show=False),
    Binding('ctrl+u', 'vim_page_up', 'Page up', show=False),
]
"""The Vim motions of a scrollable container. Widgets add these to their own `BINDINGS`."""

VIM_DATA_TABLE_BINDINGS: list[BindingType] = [
    Binding('j', 'vim_cursor_down', 'Cursor down', show=False),
    Binding('k', 'vim_cursor_up', 'Cursor up', show=False),
    Binding('g', 'vim_scroll_top', 'Top', show=False),
    Binding('G', 'vim_scroll_bottom', 'Bottom', show=False),
    Binding('ctrl+d', 'vim_page_down', 'Page down', show=False),
    Binding('ctrl+u', 'vim_page_up', 'Page up', show=False),
]
"""The Vim motions of a data table. Widgets add these to their own `BINDINGS`."""


class VimScrollBindings:
    """A mixin that implements the Vim motions of a scrollable container.

    The motions are only active when the user enables `enable_vim_keybindings`. The mixin deliberately uses action
    names prefixed with `vim_` so that enabling/disabling them does not affect the equivalent bindings that the widget
    provides by default, e.g. the arrow keys.

    ```{important}
    Textual only merges the `BINDINGS` of the classes in the MRO that are `DOMNode` subclasses, so widgets using this
    mixin need to add [VIM_SCROLL_BINDINGS](#jiratui.widgets.vim.VIM_SCROLL_BINDINGS) to their own `BINDINGS`, e.g.
    `BINDINGS = [Binding('n', 'add_item', 'Add'), *VIM_SCROLL_BINDINGS]`.
    ```
    """

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        if action.startswith('vim_') and not vim_keybindings_enabled():
            return False
        return super().check_action(action, parameters)  # type:ignore[misc]

    def action_vim_scroll_down(self) -> None:
        self.action_scroll_down()  # type:ignore[attr-defined]

    def action_vim_scroll_up(self) -> None:
        self.action_scroll_up()  # type:ignore[attr-defined]

    def action_vim_scroll_home(self) -> None:
        self.action_scroll_home()  # type:ignore[attr-defined]

    def action_vim_scroll_end(self) -> None:
        self.action_scroll_end()  # type:ignore[attr-defined]

    def action_vim_page_down(self) -> None:
        self.action_page_down()  # type:ignore[attr-defined]

    def action_vim_page_up(self) -> None:
        self.action_page_up()  # type:ignore[attr-defined]


class VimDataTableBindings:
    """A mixin that implements the Vim motions of a `DataTable`.

    The motions are only active when the user enables `enable_vim_keybindings`. The mixin deliberately uses action
    names prefixed with `vim_` so that enabling/disabling them does not affect the equivalent bindings that the widget
    provides by default, e.g. the arrow keys.

    ```{important}
    Textual only merges the `BINDINGS` of the classes in the MRO that are `DOMNode` subclasses, so tables using this
    mixin need to add [VIM_DATA_TABLE_BINDINGS](#jiratui.widgets.vim.VIM_DATA_TABLE_BINDINGS) to their own `BINDINGS`,
    e.g. `BINDINGS = [Binding('d', 'delete_item', 'Delete'), *VIM_DATA_TABLE_BINDINGS]`.
    ```
    """

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        if action.startswith('vim_') and not vim_keybindings_enabled():
            return False
        return super().check_action(action, parameters)  # type:ignore[misc]

    def action_vim_cursor_down(self) -> None:
        self.action_cursor_down()  # type:ignore[attr-defined]

    def action_vim_cursor_up(self) -> None:
        self.action_cursor_up()  # type:ignore[attr-defined]

    def action_vim_scroll_top(self) -> None:
        self.action_scroll_top()  # type:ignore[attr-defined]

    def action_vim_scroll_bottom(self) -> None:
        self.action_scroll_bottom()  # type:ignore[attr-defined]

    def action_vim_page_down(self) -> None:
        self.action_page_down()  # type:ignore[attr-defined]

    def action_vim_page_up(self) -> None:
        self.action_page_up()  # type:ignore[attr-defined]


class VimCommandScreen(ModalScreen):
    """A Vim-style command line.

    The screen is opened by pressing `:` when the Vim key bindings are enabled. It understands the commands used to
    quit the app, `:q`, `:q!`, `:qa`, `:wq`, `:x` and `:exit`, and the command to open the help, `:h`. The commands
    ending with `!` quit the app without asking for confirmation; even when `confirm_before_quit` is enabled.
    """

    BINDINGS = [Binding('escape', 'app.pop_screen', 'Close', show=False)]

    QUIT_COMMANDS = {'q', 'qa', 'qall', 'quit', 'wq', 'x', 'exit'}
    """The commands that quit the app. These honour the `confirm_before_quit` setting."""

    HELP_COMMANDS = {'h', 'help'}
    """The commands that open the in-app help."""

    def compose(self) -> ComposeResult:
        with Horizontal(id='vim-command-container'):
            yield Static(':', id='vim-command-prompt')
            yield Input(id='vim-command-input', compact=True)

    def on_mount(self) -> None:
        self.query_one('#vim-command-input', expect_type=Input).focus()

    @on(Input.Submitted, '#vim-command-input')
    async def run_command(self, event: Input.Submitted) -> None:
        """Runs the command typed by the user.

        Args:
            event: the event with the command typed by the user.

        Returns:
            None
        """

        command = event.value.strip().lstrip(':')
        self.dismiss()
        if not command:
            return

        forced = command.endswith('!')
        command = command.rstrip('!').lower()
        app = cast('JiraApp', self.app)  # type:ignore[name-defined] # noqa: F821

        if command in self.QUIT_COMMANDS:
            if forced:
                await app.force_quit()
            else:
                await app.action_quit()
        elif command in self.HELP_COMMANDS:
            await app.action_help()
        else:
            self.notify(f'Not a JiraTUI command: :{command}', severity='error')
