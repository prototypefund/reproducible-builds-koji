from __future__ import absolute_import

import os
import unittest

import mock

import koji


class TestGSSAPI(unittest.TestCase):
    def setUp(self):
        self.session = koji.ClientSession('https://koji.example.com/kojihub',
                                          {})
        self.session._callMethod = mock.MagicMock(name='_callMethod')

    def tearDown(self):
        mock.patch.stopall()

    maxDiff = None

    @mock.patch('koji.requests_kerberos', new=None)
    def test_gssapi_disabled(self):
        with self.assertRaises(ImportError):
            self.session.gssapi_login()

    def test_gssapi_login(self):
        old_environ = dict(**os.environ)
        self.session.gssapi_login()
        self.session._callMethod.assert_called_once_with('sslLogin', [None],
                                                         retry=False)
        self.assertEqual(old_environ, dict(**os.environ))

    @mock.patch('requests_kerberos.HTTPKerberosAuth')
    def test_gssapi_login_keytab(self, HTTPKerberosAuth_mock):
        principal = 'user@EXAMPLE.COM'
        keytab = '/path/to/keytab'
        ccache = '/path/to/cache'
        old_environ = dict(**os.environ)
        current_version = koji.requests_kerberos.__version__
        accepted_versions = ['0.12.0.beta1',
                             '0.12.0dev',
                             '0.12.0a1',
                             '0.11.0',
                             '0.10.0',
                             '0.9.0']
        for accepted_version in accepted_versions:
            koji.requests_kerberos.__version__ = accepted_version
            rv = self.session.gssapi_login(principal, keytab, ccache)
            self.session._callMethod.assert_called_once_with('sslLogin',
                                                             [None],
                                                             retry=False)
            self.assertEqual(old_environ, dict(**os.environ))
            self.assertTrue(rv)
            self.session._callMethod.reset_mock()
        koji.requests_kerberos.__version__ = current_version

    def test_gssapi_login_keytab_unsupported_requests_kerberos_version(self):
        principal = 'user@EXAMPLE.COM'
        keytab = '/path/to/keytab'
        ccache = '/path/to/cache'
        old_environ = dict(**os.environ)
        current_version = koji.requests_kerberos.__version__
        old_versions = ['0.8.0',
                        '0.7.0',
                        '0.6.1',
                        '0.6',
                        '0.5',
                        '0.3',
                        '0.2',
                        '0.1']
        for old_version in old_versions:
            koji.requests_kerberos.__version__ = old_version
            with self.assertRaises(koji.PythonImportError) as cm:
                self.session.gssapi_login(principal, keytab, ccache)
            self.assertEqual(cm.exception.args[0],
                             'python-requests-kerberos >= 0.9.0 required for '
                             'keytab auth')
            self.session._callMethod.assert_not_called()
            self.assertEqual(old_environ, dict(**os.environ))
        koji.requests_kerberos.__version__ = current_version

    def test_gssapi_login_error(self):
        old_environ = dict(**os.environ)
        self.session._callMethod.side_effect = Exception('login failed')
        with self.assertRaises(koji.AuthError):
            self.session.gssapi_login()
        self.session._callMethod.assert_called_once_with('sslLogin', [None],
                                                         retry=False)
        self.assertEqual(old_environ, dict(**os.environ))

    def test_gssapi_login_http(self):
        old_environ = dict(**os.environ)
        url1 = 'http://koji.example.com/kojihub'
        url2 = 'https://koji.example.com/kojihub'

        # successful gssapi auth should force https
        self.session.baseurl = url1
        self.session.gssapi_login()
        self.assertEqual(self.session.baseurl, url2)

        # failed gssapi auth should leave the url alone
        self.session.baseurl = url1
        self.session._callMethod.side_effect = Exception('login failed')
        with self.assertRaises(koji.AuthError):
            self.session.gssapi_login()
        self.assertEqual(self.session.baseurl, url1)
        self.assertEqual(old_environ, dict(**os.environ))
