import unittest
import tempfile
import shutil
import os

import inspect


class ZdsFixCmdTestCase(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.tests_files_directory = os.path.join(os.path.dirname(__file__))
        self.temporary_directory = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temporary_directory)

    def copy_to_temporary_directory(self, path, new_name=''):
        """Copy the content of a file to the temporary directory

        :param path: path to the file to copy
        :type path: str
        :param new_name: the new name of the file in the temporary directory (if blank, the one from path is used)
        :type new_name: str
        :rtype: str
        """

        path_in_test = os.path.join(self.tests_files_directory, path)

        if not os.path.exists(path_in_test):
            raise FileNotFoundError(path_in_test)

        if not new_name:
            new_name = os.path.basename(path)

        path_in_temp = os.path.join(self.temporary_directory, new_name)

        if os.path.exists(path_in_temp):
            raise FileExistsError(path_in_temp)

        shutil.copy(os.path.join(self.tests_files_directory, path), path_in_temp)
        return path_in_temp

    def match_expected(self, name, content):

        n = inspect.stack()[1][3]
        path = os.path.join(os.path.dirname(__file__), 'expected', n + '.' + name + '.expected')

        if not os.path.exists(path):
            raise Exception('file {} does not exists'.format(path))

        with open(path, 'rb') as f:
            expected = f.read().decode('utf-8')

        p = self.maxDiff
        self.maxDiff = 10000
        self.assertEqual(expected, content)
        self.maxDiff = p
