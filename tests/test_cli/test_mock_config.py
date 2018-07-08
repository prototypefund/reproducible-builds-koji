from __future__ import absolute_import
import mock
import six
import unittest

from koji_cli.commands import anon_handle_mock_config
from . import utils


class TestMockConfig(utils.CliTestCase):

    # Show long diffs in error output...
    maxDiff = None

    def setUp(self):
        self.common_args = [
            '--distribution', 'fedora',
            '--topdir', '/top-dir',
            '--topurl', '/top-url',
            '--yum-proxy', '/yum-proxy'
        ]
        self.common_opts = {
            'distribution': 'fedora',
            'mockdir': '/var/lib/mock',
            'topdir': '/top-dir',
            'topurl': '/top-url',
            'yum_proxy': '/yum-proxy',
        }
        self.mock_output = """# Auto-generated by the Koji build system

config_opts['chroot_setup_cmd'] = 'groupinstall build'
config_opts['use_host_resolv'] = False
config_opts['root'] = 'fedora26-build-repo_1'
config_opts['yum.conf'] = '[main]\ncachedir=/var/cache/yum\ndebuglevel=1\nlogfile=/var/log/yum.log\nreposdir=/dev/null\nretries=20\nobsoletes=1\ngpgcheck=0\nassumeyes=1\nkeepcache=1\ninstall_weak_deps=0\nstrict=1\n\n# repos\n\n[build]\nname=build\nbaseurl=https://fedora.local/kojifiles/repos/fedora26-build/1/x86_64\n'
config_opts['rpmbuild_timeout'] = 86400
config_opts['chroothome'] = '/builddir'
config_opts['target_arch'] = 'x86_64'
config_opts['basedir'] = '/var/lib/mock'

config_opts['plugin_conf']['yum_cache_enable'] = False
config_opts['plugin_conf']['root_cache_enable'] = False
config_opts['plugin_conf']['ccache_enable'] = False

config_opts['macros']['%_rpmfilename'] = '%%{NAME}-%%{VERSION}-%%{RELEASE}.%%{ARCH}.rpm'
config_opts['macros']['%_topdir'] = '/builddir/build'
config_opts['macros']['%packager'] = 'Koji'
config_opts['macros']['%_host'] = 'x86_64-koji-linux-gnu'
config_opts['macros']['%_host_cpu'] = 'x86_64'
config_opts['macros']['%vendor'] = 'Koji'
config_opts['macros']['%distribution'] = 'Koji Testing'
"""
        self.error_format = """Usage: %s mock-config [options]
(Specify the --help global option for a list of other help options)

%s: error: {message}
""" % (self.progname, self.progname)

    @mock.patch('sys.stderr', new_callable=six.StringIO)
    @mock.patch('sys.stdout', new_callable=six.StringIO)
    @mock.patch('koji.genMockConfig')
    @mock.patch('koji_cli.commands.activate_session')
    def test_handle_mock_config_buildroot_option(
            self, activate_session_mock, gen_config_mock, stdout, stderr):
        """Test anon_handle_mock_config buildroot options"""
        arguments = []
        options = mock.MagicMock()

        buildroot_info = {
            'repo_id': 101,
            'tag_name': 'tag_name',
            'arch': 'x86_64'
        }

        # Mock out the xmlrpc server
        session = mock.MagicMock()
        session.getBuildroot.return_value = buildroot_info

        # Mock config
        gen_config_mock.return_value = self.mock_output

        # buildroot check
        arguments = ['--buildroot', 'root', self.progname]
        expected = self.format_error_message("Buildroot id must be an integer")
        self.assert_system_exit(
            anon_handle_mock_config,
            options,
            session,
            arguments,
            stderr=expected)

        arguments = self.common_args + ['--buildroot', '1',
                                        '--name', self.progname]
        opts = self.common_opts.copy()
        opts.update({
            'repoid': buildroot_info['repo_id'],
            'tag_name': buildroot_info['tag_name']
        })
        anon_handle_mock_config(options, session, arguments)
        self.assert_console_message(
            stdout, "%s\n" % gen_config_mock.return_value)
        gen_config_mock.assert_called_with(
            self.progname, buildroot_info['arch'], **opts)

        arguments = self.common_args + ['--buildroot', '1',
                                        '--name', self.progname,
                                        '--latest']
        opts['repoid'] = 'latest'
        anon_handle_mock_config(options, session, arguments)
        self.assert_console_message(
            stdout, "%s\n" % gen_config_mock.return_value)
        gen_config_mock.assert_called_with(
            self.progname, buildroot_info['arch'], **opts)

    @mock.patch('sys.stderr', new_callable=six.StringIO)
    @mock.patch('sys.stdout', new_callable=six.StringIO)
    @mock.patch('koji.genMockConfig')
    @mock.patch('koji_cli.commands.activate_session')
    def test_handle_mock_config_task_option(
            self, activate_session_mock, gen_config_mock, stdout, stderr):
        """Test  anon_handle_mock_config task options"""
        arguments = []
        task_id = 1001
        options = mock.MagicMock()

        session = mock.MagicMock()
        session.listBuildroots.return_value = ''

        # Mock config
        gen_config_mock.return_value = ''

        arguments = ['--task', 'task']
        expected = self.format_error_message("Task id must be an integer")
        self.assert_system_exit(
            anon_handle_mock_config,
            options,
            session,
            arguments,
            stderr=expected)

        arguments = ['--task', str(task_id)]
        expected = "No buildroots for task %s (or no such task)\n" % str(task_id)
        self.assertEqual(1, anon_handle_mock_config(options, session, arguments))
        self.assert_console_message(stdout, expected)

        multi_broots = [
            {'id': 1101, 'repo_id': 101, 'tag_name': 'tag_101', 'arch': 'x86_64'},
            {'id': 1111, 'repo_id': 111, 'tag_name': 'tag_111', 'arch': 'x86_64'},
            {'id': 1121, 'repo_id': 121, 'tag_name': 'tag_121', 'arch': 'x86_64'}
        ]
        session.listBuildroots.return_value = multi_broots
        anon_handle_mock_config(options, session, arguments)
        expected = "Multiple buildroots found: %s" % [br['id'] for br in multi_broots]
        self.assert_console_message(stdout, "%s\n\n" % expected)

        opts = self.common_opts.copy()
        opts.update({
            'repoid': 'latest',
            'tag_name': multi_broots[0]['tag_name']
        })
        arguments = self.common_args + ['--task', str(task_id),
                                        '--name', self.progname,
                                        '--latest']
        session.listBuildroots.return_value = [multi_broots[0]]
        gen_config_mock.return_value = self.mock_output
        anon_handle_mock_config(options, session, arguments)
        self.assert_console_message(
            stdout, "%s\n" % gen_config_mock.return_value)
        gen_config_mock.assert_called_with(
            self.progname, multi_broots[0]['arch'], **opts)

    @mock.patch('sys.stderr', new_callable=six.StringIO)
    @mock.patch('sys.stdout', new_callable=six.StringIO)
    @mock.patch('koji.genMockConfig')
    @mock.patch('koji_cli.commands.activate_session')
    def test_handle_mock_config_tag_option(
            self, activate_session_mock, gen_config_mock, stdout, stderr):
        """Test anon_handle_mock_config with tag option"""
        arguments = []
        tag = 'tag'
        tag = {'id': 201, 'name': 'tag', 'arch': 'x86_64'}
        options = mock.MagicMock()

        # Mock out the xmlrpc server
        session = mock.MagicMock()
        session.getTag.return_value = None
        session.getBuildConfig.return_value = None
        session.getRepo.return_value = None

        arguments = ['--tag', tag['name']]
        expected = "Please specify an arch\n"
        self.assertEqual(1, anon_handle_mock_config(options, session, arguments))
        self.assert_console_message(stdout, expected)

        arguments = ['--tag', tag['name'], '--arch', tag['arch']]
        expected = self.format_error_message("Invalid tag: %s" % tag['name'])
        self.assert_system_exit(
            anon_handle_mock_config,
            options,
            session,
            arguments,
            stderr=expected)

        # return tag info
        session.getTag.return_value = tag
        expected = "Could not get config info for tag: %(name)s\n" % tag
        self.assertEqual(1, anon_handle_mock_config(options, session, arguments))
        self.assert_console_message(stdout, expected)

        # return build config
        session.getBuildConfig.return_value = {'id': 301}
        expected = "Could not get a repo for tag: %(name)s\n" % tag
        self.assertEqual(1, anon_handle_mock_config(options, session, arguments))
        self.assert_console_message(stdout, expected)

        # return repo
        session.getRepo.return_value = {'id': 101}
        gen_config_mock.return_value = self.mock_output
        anon_handle_mock_config(options, session, arguments)
        self.assert_console_message(
            stdout, "%s\n" % gen_config_mock.return_value)

        arguments = self.common_args + ['--tag', tag['name'],
                                        '--arch', tag['arch'],
                                        '--name', self.progname,
                                        '--latest']
        opts = self.common_opts.copy()
        opts.update({
            'repoid': 'latest',
            'tag_name': tag['name'],
        })
        anon_handle_mock_config(options, session, arguments)
        self.assert_console_message(
            stdout, "%s\n" % gen_config_mock.return_value)
        gen_config_mock.assert_called_with(
            self.progname, tag['arch'], **opts)

    @mock.patch('sys.stderr', new_callable=six.StringIO)
    @mock.patch('sys.stdout', new_callable=six.StringIO)
    @mock.patch('koji.genMockConfig')
    @mock.patch('koji_cli.commands.activate_session')
    def test_handle_mock_config_target_option(
            self, activate_session_mock, gen_config_mock, stdout, stderr):
        """Test anon_handle_mock_config with target option"""
        arguments = []
        arch = "x86_64"
        target = {'id': 1,
                  'name': 'target',
                  'dest_tag': 1,
                  'build_tag': 2,
                  'build_tag_name': 'target-build',
                  'dest_tag_name': 'target'}
        options = mock.MagicMock()

        # Mock out the xmlrpc server
        session = mock.MagicMock()
        session.getBuildTarget.return_value = None
        session.getRepo.return_value = None

        arguments = ['--target', target['name']]
        expected = "Please specify an arch\n"
        self.assertEqual(1, anon_handle_mock_config(options, session, arguments))
        self.assert_console_message(stdout, expected)

        arguments = ['--target', target['name'],
                     '--arch', arch]
        expected = self.format_error_message(
                "Invalid target: %s" % target['name'])
        self.assert_system_exit(
            anon_handle_mock_config,
            options,
            session,
            arguments,
            stderr=expected)

        session.getBuildTarget.return_value = target
        expected = "Could not get a repo for tag: %s\n" % target['build_tag_name']
        self.assertEqual(1, anon_handle_mock_config(options, session, arguments))
        self.assert_console_message(stdout, expected)

        arguments = self.common_args + ['--target', target['name'],
                                        '--arch', arch,
                                        '--name', self.progname]
        opts = self.common_opts.copy()
        opts.update({
            'repoid': 101,
            'tag_name': target['build_tag_name']
        })
        session.getRepo.return_value = {'id': 101}
        gen_config_mock.return_value = self.mock_output
        anon_handle_mock_config(options, session, arguments)
        self.assert_console_message(
            stdout, "%s\n" % gen_config_mock.return_value)
        gen_config_mock.assert_called_with(
            self.progname, arch, **opts)

        # --latest and -o (output) test
        opts['repoid'] = 'latest'
        arguments.extend(['--latest', '-o', '/tmp/mock.out'])
        with mock.patch('koji_cli.commands.open', create=True) as openf_mock:
            anon_handle_mock_config(options, session, arguments)
        openf_mock.assert_called_with('/tmp/mock.out', 'w')
        handle = openf_mock()
        handle.write.assert_called_once_with(self.mock_output)
        gen_config_mock.assert_called_with(
            self.progname, arch, **opts)

    @mock.patch('sys.stderr', new_callable=six.StringIO)
    def test_handle_mock_config_errors(self, stderr):
        """Test anon_handle_mock_config general error messages"""
        arguments = []
        options = mock.MagicMock()

        # Mock out the xmlrpc server
        session = mock.MagicMock()

        # Run it and check immediate output
        # argument is empty
        expected = self.format_error_message(
                "Please specify one of: --tag, --target, --task, --buildroot")
        self.assert_system_exit(
            anon_handle_mock_config,
            options,
            session,
            arguments,
            stderr=expected)

        # name is specified twice case
        arguments = [self.progname, '--name', 'name']
        expected = self.format_error_message(
                "Name already specified via option")
        self.assert_system_exit(
            anon_handle_mock_config,
            options,
            session,
            arguments,
            stderr=expected)

    def test_handle_mock_config_help(self):
        """Test anon_handle_mock_config help message full output"""
        self.assert_help(
            anon_handle_mock_config,
            """Usage: %s mock-config [options]
(Specify the --help global option for a list of other help options)

Options:
  -h, --help            show this help message and exit
  -a ARCH, --arch=ARCH  Specify the arch
  -n NAME, --name=NAME  Specify the name for the buildroot
  --tag=TAG             Create a mock config for a tag
  --target=TARGET       Create a mock config for a build target
  --task=TASK           Duplicate the mock config of a previous task
  --latest              use the latest redirect url
  --buildroot=BUILDROOT
                        Duplicate the mock config for the specified buildroot
                        id
  --mockdir=DIR         Specify mockdir
  --topdir=DIR          Specify topdir
  --topurl=URL          URL under which Koji files are accessible
  --distribution=DISTRIBUTION
                        Change the distribution macro
  --yum-proxy=YUM_PROXY
                        Specify a yum proxy
  -o FILE               Output to a file
""" % self.progname)


if __name__ == '__main__':
    unittest.main()
