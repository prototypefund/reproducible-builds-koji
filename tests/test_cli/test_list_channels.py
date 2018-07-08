from __future__ import absolute_import
import mock
import unittest
from six.moves import StringIO

import koji

from koji_cli.commands import anon_handle_list_channels

class TestListChannels(unittest.TestCase):
    def setUp(self):
        self.options = mock.MagicMock()
        self.options.quiet = True
        self.session = mock.MagicMock()
        self.session.getAPIVersion.return_value = koji.API_VERSION
        self.args = []

    @mock.patch('sys.stdout', new_callable=StringIO)
    @mock.patch('koji_cli.commands.activate_session')
    def test_list_channels(self, activate_session_mock, stdout):
        self.session.listChannels.return_value = [
            {'id': 1, 'name': 'default'},
            {'id': 2, 'name': 'test'},
        ]
        self.session.multiCall.return_value = [[[1,2,3]], [[4,5]]]

        anon_handle_list_channels(self.options, self.session, self.args)

        actual = stdout.getvalue()
        expected = 'default             3\ntest                2\n'
        self.assertMultiLineEqual(actual, expected)
        activate_session_mock.assert_called_once_with(self.session, self.options)
