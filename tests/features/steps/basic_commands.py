"""
Steps for behavioral style tests are defined in this module.
Each step is defined by the string decorating it.
This string is used to call the step in "*.feature" file.
"""

import pexpect
import subprocess
import tempfile

from behave import when, then
from textwrap import dedent
import wrappers


@when("we list databases")
def step_list_databases(context):
    cmd = ["pgcli", "--list"]
    context.cmd_output = subprocess.check_output(cmd, cwd=context.package_root)


@then("we see list of databases")
def step_see_list_databases(context):
    assert b"List of databases" in context.cmd_output
    assert b"postgres" in context.cmd_output
    context.cmd_output = None


@when("we run dbcli")
def step_run_cli(context):
    wrappers.run_cli(context)


@when("we launch dbcli using {arg}")
def step_run_cli_using_arg(context, arg):
    prompt_check = False
    currentdb = None
    if arg == "--username":
        arg = "--username={}".format(context.conf["user"])
    if arg == "--user":
        arg = "--user={}".format(context.conf["user"])
    if arg == "--port":
        arg = "--port={}".format(context.conf["port"])
    if arg == "--password":
        arg = "--password"
        prompt_check = False
    # This uses the mock_pg_service.conf file in fixtures folder.
    if arg == "dsn_password":
        arg = "service=mock_postgres --password"
        prompt_check = False
        currentdb = "postgres"
    wrappers.run_cli(
        context, run_args=[arg], prompt_check=prompt_check, currentdb=currentdb
    )


@when("we wait for prompt")
def step_wait_prompt(context):
    wrappers.wait_prompt(context)


@when('we send "ctrl + d"')
def step_ctrl_d(context):
    """
    Send Ctrl + D to hopefully exit.
    """
    # turn off pager before exiting
    context.cli.sendcontrol("c")
    context.cli.sendline(r"\pset pager off")
    wrappers.wait_prompt(context)
    context.cli.sendcontrol("d")
    context.cli.expect(pexpect.EOF, timeout=5)
    context.exit_sent = True


@when('we send "ctrl + c"')
def step_ctrl_c(context):
    """Send Ctrl + c to hopefully interrupt."""
    context.cli.sendcontrol("c")


@then("we see cancelled query warning")
def step_see_cancelled_query_warning(context):
    """
    Make sure we receive the warning that the current query was cancelled.
    """
    wrappers.expect_exact(context, "cancelled query", timeout=2)


@when("we send sleep query")
def step_send_sleep_15_seconds(context):
    """
    Send query to sleep for 15 seconds.
    """
    context.cli.sendline("select pg_sleep(15)")


@when("we check for any non-idle sleep queries")
def step_check_for_active_sleep_queries(context):
    """
    Send query to check for any non-idle pg_sleep queries.
    """
    context.cli.sendline(
        "select state from pg_stat_activity where query not like '%pg_stat_activity%' and query like '%pg_sleep%' and state != 'idle';"
    )


@then("we don't see any non-idle sleep queries")
def step_no_active_sleep_queries(context):
    """Confirm that any pg_sleep queries are either idle or not active."""
    wrappers.expect_exact(
        context,
        context.conf["pager_boundary"]
        + "\r"
        + dedent(
            """
            +-------+\r
            | state |\r
            |-------|\r
            +-------+\r
            SELECT 0\r
        """
        )
        + context.conf["pager_boundary"],
        timeout=5,
    )


@when(r'we send "\?" command')
def step_send_help(context):
    r"""
    Send \? to see help.
    """
    context.cli.sendline(r"\?")


@when("we send partial select command")
def step_send_partial_select_command(context):
    """
    Send `SELECT a` to see completion.
    """
    context.cli.sendline("SELECT a")


@then("we see error message")
def step_see_error_message(context):
    wrappers.expect_exact(context, 'column "a" does not exist', timeout=2)


@when("we send source command")
def step_send_source_command(context):
    context.tmpfile_sql_help = tempfile.NamedTemporaryFile(prefix="pgcli_")
    context.tmpfile_sql_help.write(rb"\?")
    context.tmpfile_sql_help.flush()
    context.cli.sendline(rf"\i {context.tmpfile_sql_help.name}")
    wrappers.expect_exact(context, context.conf["pager_boundary"] + "\r\n", timeout=5)


@when("we run query to check application_name")
def step_check_application_name(context):
    context.cli.sendline(
        "SELECT 'found' FROM pg_stat_activity WHERE application_name = 'pgcli' HAVING COUNT(*) > 0;"
    )


@then("we see found")
def step_see_found(context):
    wrappers.expect_exact(
        context,
        context.conf["pager_boundary"]
        + "\r"
        + dedent(
            """
            +----------+\r
            | ?column? |\r
            |----------|\r
            | found    |\r
            +----------+\r
            SELECT 1\r
        """
        )
        + context.conf["pager_boundary"],
        timeout=5,
    )


@then("we respond to the destructive warning: {response}")
def step_resppond_to_destructive_command(context, response):
    """Respond to destructive command."""
    wrappers.expect_exact(
        context,
        "You're about to run a destructive command.\r\nDo you want to proceed? (y/n):",
        timeout=2,
    )
    context.cli.sendline(response.strip())


@then("we send password")
def step_send_password(context):
    wrappers.expect_exact(context, "Password for", timeout=5)
    context.cli.sendline(context.conf["pass"] or "DOES NOT MATTER")
