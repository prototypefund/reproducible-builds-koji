from __future__ import absolute_import
import unittest

import koji
import sys
import threading
import traceback
from six.moves import range
import six

# XXX remove skip when Fedora bug is fixed
@unittest.skipIf(six.PY3, "coverage bug Fedora, see rhbz#1452339")
class ProfilesTestCase(unittest.TestCase):

    def test_profile_threading(self):
        """ Test that profiles thread safe"""
        # see: https://pagure.io/koji/issue/58 and https://pagure.io/pungi/issue/253
        # loop a few times to increase chances of hitting race conditions
        for i in range(20):
            errors = {}
            threads = [threading.Thread(target=stress, args=(errors, _)) for _ in range(100)]
            for t in threads:
                t.start()
            for t in threads:
                t.join(30)
            for n in errors:
                err = errors[n]
                if err is not None:
                    print(err)
                    assert False


def stress(errors, n):
    errors[n] = "Failed to start"
    try:
        koji.get_profile_module('koji')
    except Exception:
        # if we don't catch this, nose seems to ignore the test
        errors[n] = ''.join(traceback.format_exception(*sys.exc_info()))
        return
    else:
        errors[n] = None



