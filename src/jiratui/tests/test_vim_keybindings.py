from typing import cast
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from pydantic import SecretStr
import pytest

from jiratui.api_controller.controller import APIController
from jiratui.app import JiraApp
from jiratui.config import ApplicationConfiguration
from jiratui.models import JiraIssueSearchResponse, WorkItemsSearchOrderBy
from jiratui.widgets.comments.comments import IssueCommentsWidget
from jiratui.widgets.filters import JQLSearchWidget, WorkItemInputWidget
from jiratui.widgets.screen import MainScreen
from jiratui.widgets.search import DataTableSearchInput, IssuesSearchResultsTable
from jiratui.widgets.vim import VimCommandScreen


def build_app(**overrides) -> JiraApp:
    config_mock = Mock(spec=ApplicationConfiguration)
    settings = {
        'enable_vim_keybindings': True,
        'custom_keybindings': None,
        'jira_api_base_url': 'foo.bar',
        'jira_api_username': 'foo',
        'jira_api_token': SecretStr('bar'),
        'jira_api_version': 3,
        'use_bearer_authentication': False,
        'use_cert_authentication': False,
        'cloud': True,
        'ignore_users_without_email': True,
        'default_project_key_or_id': None,
        'fetch_single_project': False,
        'active_sprint_on_startup': False,
        'jira_account_id': None,
        'tui_title': None,
        'tui_custom_title': None,
        'tui_title_include_jira_server_title': False,
        'on_start_up_only_fetch_projects': False,
        'log_file': '',
        'log_level': 'ERROR',
        'enable_logging': False,
        'theme': None,
        'search_results_page_filtering_enabled': True,
        'search_results_page_filtering_minimum_term_length': 3,
        'ssl': None,
        'search_results_default_order': WorkItemsSearchOrderBy.CREATED_DESC,
        'search_results_truncate_work_item_summary': 15,
        'search_results_style_work_item_status': None,
        'search_results_style_work_item_type': None,
        'search_results_per_page': 10,
        'search_on_startup': False,
        'show_keybinding_hints': False,
        'enable_recent_history': False,
        'enable_goto': False,
        'confirm_before_quit': False,
    }
    settings.update(overrides)
    config_mock.configure_mock(**settings)
    app = JiraApp(config_mock)
    app.api = APIController(config_mock)
    app._setup_logging = MagicMock()  # type:ignore[method-assign]
    return app


@pytest.fixture()
def app_with_vim_keybindings() -> JiraApp:
    return build_app()


@pytest.fixture()
def app_without_vim_keybindings() -> JiraApp:
    return build_app(enable_vim_keybindings=False)


@pytest.fixture(autouse=True)
def patched_main_screen_workers():
    """Prevents the main screen from hitting the API when it is mounted."""

    with (
        patch('jiratui.widgets.screen.MainScreen.fetch_projects', new_callable=AsyncMock),
        patch('jiratui.widgets.screen.MainScreen.fetch_issue_types', new_callable=AsyncMock),
        patch('jiratui.widgets.screen.MainScreen.fetch_statuses', new_callable=AsyncMock),
    ):
        yield


@pytest.mark.parametrize(
    'key, widget',
    [
        ('w', WorkItemInputWidget),
        ('e', JQLSearchWidget),
    ],
)
@pytest.mark.asyncio
async def test_hot_keys_of_work_item_key_and_jql_inputs_are_re_assigned(
    key: str, widget, app_with_vim_keybindings: JiraApp
):
    """`j` and `k` are needed to move up/down so the widgets that used them move to `e` and `w`."""

    async with app_with_vim_keybindings.run_test() as pilot:
        await pilot.press(key)
        main_screen = cast(MainScreen, app_with_vim_keybindings.screen)
        assert isinstance(main_screen.focused, widget)


@pytest.mark.parametrize(
    'key, widget',
    [
        ('k', WorkItemInputWidget),
        ('j', JQLSearchWidget),
    ],
)
@pytest.mark.asyncio
async def test_hot_keys_of_work_item_key_and_jql_inputs_are_unchanged_by_default(
    key: str, widget, app_without_vim_keybindings: JiraApp
):
    async with app_without_vim_keybindings.run_test() as pilot:
        await pilot.press(key)
        main_screen = cast(MainScreen, app_without_vim_keybindings.screen)
        assert isinstance(main_screen.focused, widget)


@pytest.mark.parametrize('key', ['j', 'k'])
@pytest.mark.asyncio
async def test_border_subtitles_of_re_assigned_widgets(key: str, app_with_vim_keybindings: JiraApp):
    """The hints displayed by the widgets show the keys that are actually bound to them."""

    async with app_with_vim_keybindings.run_test():
        main_screen = cast(MainScreen, app_with_vim_keybindings.screen)
        assert main_screen.issue_key_input.border_subtitle == '(w)'
        assert main_screen.jql_expression_input.border_subtitle == '(e)'


@pytest.mark.asyncio
async def test_border_subtitles_of_re_assigned_widgets_are_unchanged_by_default(
    app_without_vim_keybindings: JiraApp,
):
    async with app_without_vim_keybindings.run_test():
        main_screen = cast(MainScreen, app_without_vim_keybindings.screen)
        assert main_screen.issue_key_input.border_subtitle == '(k)'
        assert main_screen.jql_expression_input.border_subtitle == '(j)'


@pytest.mark.asyncio
async def test_j_and_k_move_the_cursor_of_the_search_results(
    app_with_vim_keybindings: JiraApp, jira_issues
):
    async with app_with_vim_keybindings.run_test() as pilot:
        main_screen = cast(MainScreen, app_with_vim_keybindings.screen)
        table = main_screen.search_results_table
        table.search_results = JiraIssueSearchResponse(issues=jira_issues)
        await pilot.press('1')
        await pilot.pause()
        assert table.cursor_row == 0

        await pilot.press('j')
        assert table.cursor_row == 1

        await pilot.press('k')
        assert table.cursor_row == 0

        await pilot.press('G')
        assert table.cursor_row == len(jira_issues) - 1

        await pilot.press('g')
        assert table.cursor_row == 0


@pytest.mark.asyncio
async def test_j_and_k_do_not_move_the_cursor_of_the_search_results_by_default(
    app_without_vim_keybindings: JiraApp, jira_issues
):
    """Without the Vim bindings `j` keeps focusing the JQL input instead of moving the cursor."""

    async with app_without_vim_keybindings.run_test() as pilot:
        main_screen = cast(MainScreen, app_without_vim_keybindings.screen)
        table = main_screen.search_results_table
        table.search_results = JiraIssueSearchResponse(issues=jira_issues)
        await pilot.press('1')
        await pilot.pause()

        await pilot.press('j')
        assert table.cursor_row == 0
        assert isinstance(main_screen.focused, JQLSearchWidget)


@pytest.mark.asyncio
async def test_h_and_l_move_the_focus_between_panes(app_with_vim_keybindings: JiraApp):
    async with app_with_vim_keybindings.run_test() as pilot:
        main_screen = cast(MainScreen, app_with_vim_keybindings.screen)
        await pilot.press('1')
        await pilot.pause()
        assert isinstance(main_screen.focused, IssuesSearchResultsTable)

        await pilot.press('l')
        assert not isinstance(main_screen.focused, IssuesSearchResultsTable)

        await pilot.press('h')
        assert isinstance(main_screen.focused, IssuesSearchResultsTable)


@pytest.mark.asyncio
async def test_escape_moves_the_focus_back_to_the_search_results(
    app_with_vim_keybindings: JiraApp,
):
    async with app_with_vim_keybindings.run_test() as pilot:
        main_screen = cast(MainScreen, app_with_vim_keybindings.screen)
        await pilot.press('4')
        await pilot.pause()
        assert isinstance(main_screen.focused, IssueCommentsWidget)

        await pilot.press('escape')
        await pilot.pause()
        assert isinstance(main_screen.focused, IssuesSearchResultsTable)


@pytest.mark.asyncio
async def test_escape_moves_the_focus_back_to_the_search_results_from_an_input(
    app_with_vim_keybindings: JiraApp,
):
    """Input fields swallow the printable keys but not `esc`, so users can leave a field with it."""

    async with app_with_vim_keybindings.run_test() as pilot:
        main_screen = cast(MainScreen, app_with_vim_keybindings.screen)
        await pilot.press('e')
        await pilot.pause()
        assert isinstance(main_screen.focused, JQLSearchWidget)

        await pilot.press('escape')
        await pilot.pause()
        assert isinstance(main_screen.focused, IssuesSearchResultsTable)


@pytest.mark.asyncio
async def test_escape_does_not_move_the_focus_by_default(app_without_vim_keybindings: JiraApp):
    async with app_without_vim_keybindings.run_test() as pilot:
        main_screen = cast(MainScreen, app_without_vim_keybindings.screen)
        await pilot.press('4')
        await pilot.pause()
        assert isinstance(main_screen.focused, IssueCommentsWidget)

        await pilot.press('escape')
        await pilot.pause()
        assert isinstance(main_screen.focused, IssueCommentsWidget)


@pytest.mark.asyncio
async def test_slash_filters_the_current_page_of_search_results(
    app_with_vim_keybindings: JiraApp, jira_issues
):
    async with app_with_vim_keybindings.run_test() as pilot:
        main_screen = cast(MainScreen, app_with_vim_keybindings.screen)
        main_screen.search_results_table.search_results = JiraIssueSearchResponse(
            issues=jira_issues
        )
        await pilot.press('1')
        await pilot.pause()

        await pilot.press('/')
        await pilot.pause()
        assert isinstance(main_screen.focused, DataTableSearchInput)
        assert main_screen.search_results_filter_input.styles.display == 'block'


@pytest.mark.asyncio
async def test_q_quits_the_app(app_with_vim_keybindings: JiraApp):
    async with app_with_vim_keybindings.run_test() as pilot:
        app_with_vim_keybindings.force_quit = AsyncMock()  # type:ignore[method-assign]
        await pilot.press('q')
        await pilot.pause()
        app_with_vim_keybindings.force_quit.assert_awaited_once()


@pytest.mark.asyncio
async def test_q_does_not_quit_the_app_by_default(app_without_vim_keybindings: JiraApp):
    async with app_without_vim_keybindings.run_test() as pilot:
        app_without_vim_keybindings.force_quit = AsyncMock()  # type:ignore[method-assign]
        await pilot.press('q')
        await pilot.pause()
        app_without_vim_keybindings.force_quit.assert_not_awaited()


@pytest.mark.asyncio
async def test_colon_opens_the_command_line(app_with_vim_keybindings: JiraApp):
    async with app_with_vim_keybindings.run_test() as pilot:
        await pilot.press(':')
        await pilot.pause()
        assert isinstance(app_with_vim_keybindings.screen, VimCommandScreen)


@pytest.mark.asyncio
async def test_colon_does_not_open_the_command_line_by_default(
    app_without_vim_keybindings: JiraApp,
):
    async with app_without_vim_keybindings.run_test() as pilot:
        await pilot.press(':')
        await pilot.pause()
        assert not isinstance(app_without_vim_keybindings.screen, VimCommandScreen)


@pytest.mark.parametrize('command', ['q', 'qa', 'quit', 'wq', 'x', 'exit'])
@pytest.mark.asyncio
async def test_quit_commands(command: str, app_with_vim_keybindings: JiraApp):
    async with app_with_vim_keybindings.run_test() as pilot:
        app_with_vim_keybindings.action_quit = AsyncMock()  # type:ignore[method-assign]
        await pilot.press(':')
        await pilot.pause()
        await pilot.press(*command, 'enter')
        await pilot.pause()
        app_with_vim_keybindings.action_quit.assert_awaited_once()


@pytest.mark.asyncio
async def test_force_quit_command_ignores_the_confirmation_screen():
    """`:q!` quits right away; even when the app is configured to ask for confirmation."""

    app = build_app(confirm_before_quit=True)
    async with app.run_test() as pilot:
        app.force_quit = AsyncMock()  # type:ignore[method-assign]
        await pilot.press(':')
        await pilot.pause()
        await pilot.press('q', 'exclamation_mark', 'enter')
        await pilot.pause()
        app.force_quit.assert_awaited_once()


@pytest.mark.asyncio
async def test_unknown_command_notifies_the_user(app_with_vim_keybindings: JiraApp):
    async with app_with_vim_keybindings.run_test() as pilot:
        await pilot.press(':')
        await pilot.pause()
        command_screen = cast(VimCommandScreen, app_with_vim_keybindings.screen)
        command_screen.notify = MagicMock()  # type:ignore[method-assign]
        await pilot.press(*'nope', 'enter')
        await pilot.pause()
        command_screen.notify.assert_called_once_with(
            'Not a JiraTUI command: :nope', severity='error'
        )


@pytest.mark.asyncio
async def test_custom_keybindings_take_precedence_over_the_vim_bindings():
    app = build_app(custom_keybindings={'main_screen.focus_jql_expression': 'x'})
    async with app.run_test() as pilot:
        main_screen = cast(MainScreen, app.screen)
        await pilot.press('x')
        assert isinstance(main_screen.focused, JQLSearchWidget)


@pytest.mark.asyncio
async def test_custom_keybindings_are_applied_without_the_vim_bindings():
    app = build_app(
        enable_vim_keybindings=False,
        custom_keybindings={'main_screen.focus_project': 'x'},
    )
    async with app.run_test() as pilot:
        main_screen = cast(MainScreen, app.screen)
        await pilot.press('x')
        assert main_screen.focused is main_screen.project_selector
