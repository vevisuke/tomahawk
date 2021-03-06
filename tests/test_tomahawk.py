from nose.tools import assert_equal, ok_
import os
import pexpect
from subprocess import call, PIPE, Popen
import sys
import utils

# TODO: mock_ssh.py --prompt enabled, so we can test -s -l options.
TOMAHAWK_PATH = os.path.join(utils.get_bin_dir(__file__), 'tomahawk')
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
MOCK_SSH_PATH = os.path.join(TESTS_DIR, 'bin', 'mock_ssh.py')
MOCK_SSH_OPTION = '--ssh=' + MOCK_SSH_PATH

def test_01_basic():
    status = call(
        [ TOMAHAWK_PATH, MOCK_SSH_OPTION, '--hosts=localhost,localhost', 'uptime' ],
#        stdout = PIPE, stderr = PIPE
    )
    assert_equal(status, 0, 'execute (basic)')

def test_02_hosts_files():
    hosts_files = os.path.join(TESTS_DIR, 'localhost_2.hosts')
    status = call(
        [ TOMAHAWK_PATH, MOCK_SSH_OPTION, '--hosts-files=' + hosts_files, 'uptime' ],
#        stdout = PIPE, stderr = PIPE
    )
    assert_equal(status, 0, 'execute (--hosts-files)')

def test_03_continue_on_error():
    p = Popen(
        [ TOMAHAWK_PATH, MOCK_SSH_OPTION, '--hosts=localhost,localhost', 'doesnotexist' ],
        stdout = PIPE, stderr = PIPE
    )
    out, error = p.communicate()

    p_with_c = Popen(
        [ TOMAHAWK_PATH, MOCK_SSH_OPTION, '--hosts=localhost,localhost', '-c', 'doesnotexist' ],
        stdout = PIPE, stderr = PIPE
    )
    out_c, error_c = p_with_c.communicate()
    # error_c's length must be longer because the command continues even when error
    ok_(len(error_c) > len(error), 'execute (--continue-on-error)')

# TODO: ssh_options should be deprecated.
def test_04_ssh_options():
    status = call(
        [ TOMAHAWK_PATH, MOCK_SSH_OPTION, '--hosts=localhost,localhost', "--ssh-options=-c arcfour", 'uptime' ],
#        stdout = PIPE, stderr = PIPE
    )
    assert_equal(status, 0, 'execute (--ssh-options)')

def test_05_prompt_sudo_password():
    status = call(
        [
            TOMAHAWK_PATH,
            "--ssh=%s --prompt='Password: '" % (MOCK_SSH_PATH),
            '--hosts=localhost',
            'uptime'
        ],
#        stdout = PIPE, stderr = PIPE
    )
    assert_equal(status, 0, 'execute (--ssh)')

def test_10_confirm_execution_on_production():
    command = '%s %s --hosts=localhost,localhost uptime' % (TOMAHAWK_PATH, MOCK_SSH_OPTION)
    env = os.environ
    env['TOMAHAWK_ENV'] = 'production'
    child = pexpect.spawn(
        command,
        timeout = 5,
#        logfile = sys.stdout,
        env = env
    )
    i = child.expect([ pexpect.EOF, pexpect.TIMEOUT, 'Command "uptime" will be executed to 2 hosts.' ])
    if i == 0: # EOF
        print 'EOF'
        print child.before
    elif i == 1: # timeout
        print 'TIMEOUT'
        print child.before, child.after
        ok_(False, 'Failure: confirm_execution_on_production with "TOMAHAWK_ENV"')
    elif i == 2:
        child.sendline('yes')
        child.expect(pexpect.EOF)
        print child.before
        ok_(True, 'confirm_execution_on_production with "TOMAHAWK_ENV"')
