from __future__ import absolute_import
import mock
import six
import unittest

from mock import call
from koji_cli.commands import handle_enable_host
from . import utils


class TestEnableHost(utils.CliTestCase):

    # Show long diffs in error output...
    maxDiff = None

    @mock.patch('sys.stdout', new_callable=six.StringIO)
    @mock.patch('koji_cli.commands.activate_session')
    def test_handle_enable_host(
            self,
            activate_session_mock,
            stdout):
        """Test %s function""" % handle_enable_host.__name__
        arguments = []
        options = mock.MagicMock()
        session = mock.MagicMock()

        session.getHost.return_value = None
        session.enableHost.return_value = True
        session.editHost.return_value = True

        #
        # session.multiCall returns:
        #
        # [[{'comment': None,
        #    'capacity': 2.0,
        #    'name': 'kbuilder01',
        #    'enabled': True,
        #    'arches': 'x86_64',
        #    'task_load': 0.0,
        #    'ready': False,
        #    'user_id': 4,
        #    'id': 2, 'description': None}],
        #  [{'comment': None,
        #     'capacity': 2.0,
        #     'name': 'kbuilder02' ...}]
        #

        session.multiCall.return_value = [[None], [None]]

        arguments = ['host1', 'host2']
        self.assertEqual(1, handle_enable_host(options, session, arguments))
        activate_session_mock.assert_called_once()
        session.getHost.assert_has_calls([call('host1'), call('host2')])
        session.multiCall.assert_called_once()
        session.enableHost.assert_not_called()
        session.editHost.assert_not_called()
        expect = ''
        for host in arguments:
            expect += "Host %s does not exist\n" % host
        expect += "No changes made. Please correct the command line.\n"
        self.assert_console_message(stdout, expect)

        # reset session mocks
        activate_session_mock.reset_mock()
        session.multiCall.reset_mock()
        session.disableHost.reset_mock()
        session.editHost.reset_mock()

        session.multiCall.return_value = [
            [{'id': 1, 'name': 'host1'}], [{'id': 2, 'name': 'host2'}]
        ]

        arguments = ['host1', 'host2', '--comment', 'disable host test']
        handle_enable_host(options, session, arguments)
        activate_session_mock.assert_called_once()
        session.getHost.assert_has_calls([call('host1'), call('host2')])
        self.assertEqual(2, session.multiCall.call_count)
        session.enableHost.assert_has_calls([call('host1'), call('host2')])
        session.editHost.assert_has_calls(
            [call('host1', comment='disable host test'),
             call('host2', comment='disable host test')])
        self.assert_console_message(stdout, '')

    @mock.patch('sys.stdout', new_callable=six.StringIO)
    @mock.patch('koji_cli.commands.activate_session')
    def test_handle_enable_host_no_argument(self, activate_session_mock, stdout):
        """Test %s function without arguments""" % handle_enable_host.__name__
        options = mock.MagicMock()
        session = mock.MagicMock()

        session.getHost.return_value = None
        session.multiCall.return_value = [[None]]
        session.enableHost.return_value = True
        session.editHost.return_value = True

        handle_enable_host(options, session, [])
        activate_session_mock.assert_called_once()
        session.getHost.assert_not_called()
        session.multiCall.assert_called()
        session.enableHost.assert_not_called()
        session.editHost.assert_not_called()
        self.assert_console_message(stdout, '')

    def test_handle_enable_host_help(self):
        """Test %s help message""" % handle_enable_host.__name__
        self.assert_help(
            handle_enable_host,
            """Usage: %s enable-host [options] hostname ...
(Specify the --help global option for a list of other help options)

Options:
  -h, --help         show this help message and exit
  --comment=COMMENT  Comment indicating why the host(s) are being enabled
""" % self.progname)


if __name__ == '__main__':
    unittest.main()
