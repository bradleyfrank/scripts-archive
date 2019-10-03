#!/usr/bin/env python

__author__ = 'Bradley Frank'

import errno
import getpass
import os
import subprocess
import sys
import urllib2
import zipfile

class FBUtils:

    def download(self, name, source):
        """File download wrapper function."""

        self._log('info', 'Downloading ' + name + ' from: ' + source)
        try:
            f = urllib2.urlopen(source)
            downloaded_file = f.read()
        except URLError:
            self._log('critical', 'Failed to download ' + name + '.')
            return False

        self._log('info', 'Successfully downloaded ' + name + '.')
        return downloaded_file

    def mkdir(self, path, mode=0755):
        """Directory creation wrapper function."""
        try:
            os.makedirs(path, mode)
            self._log('info', 'Created directory: ' + path)
        except OSError as e:
            _logstr = 'Directory \"' + path + '\" exists, aborting.'
            self._log('info', _logstr)
            if e.errno != errno.EEXIST:
                raise

    def read(self, filename):
        """File read wrapper function."""
        try:
            with open(filename, 'r') as f:
                stream = f.read()
        except IOError:
            _logstr = 'Unable to read \"' + filename + '\"'
            self._log('warning', _logstr)
            return None

        self._log('info', 'Read file: ' + filename)
        return stream

    def rmfile(self, path):
        """File removal wrapper function."""
        try:
            os.remove(path)
            self._log('info', 'Deleted file: ' + path)
        except IOError:
            _logstr = 'Error deleting file \"' + path + '\"'
            self._log('warning', _logstr)

    def shell(self, cmd):
        """Wrapper function for shell commands; suppresses all output."""
        self._log('debug', 'Calling: ' + ' '.join(cmd))
        try:
            return_code = subprocess.call(cmd,
                                          stdout=open(os.devnull, 'wb'),
                                          stderr=open(os.devnull, 'wb'))
        except OSError:
            self._log('debug', 'Shell returned error.')
            return 1
        return return_code

    def unzip(self, filename, filepath):
        """Unzip wrapper function."""
        _filename = '\"' + filename + '\"'
        _filepath = '\"' + filepath + '\"'
        try:
            with zipfile.ZipFile(filename, 'r') as z:
                z.extractall(filepath)
                _logstr = 'Extracted' + _filename + ' to ' + _filepath
                self._log('info', _logstr)
        except zipfile:
            _logstr = 'Unable to extract ' + _filename + ' to ' + _filepath
            self._log('critical', _logstr)

    def write(self, filename, stream, binary=False):
        """File write wrapper function."""
        mode = 'wb' if binary else 'w'
        try:
            with open(filename, mode) as f:
                f.write(stream)
                self._log('info', 'Wrote file: ' + filename)
        except IOError:
            _logstr = 'Unable to write to \"' + filename + '\"'
            self._log('critical', _logstr)
            sys.exit(1)

if __name__ == '__main__':
    pass