#!/usr/bin/env python3

__author__ = 'Bradley Frank'

import argparse
import json
import logging
import os
import shutil
import subprocess
import sys
import urllib.request

PROJECTS = {
    'Mailspring': ['Foundry376', 'Mailspring'],
    'VSCodium': ['VSCodium', 'vscodium'],
}

REPO_ROOT_DIR = '/srv/repos'
REPO_COLO = 'colo'
REPOSITORIES = {
    'CentOS': '7',
    'Fedora': '29'
}

PACKAGES = {}


class rpm2repo:

    def __init__(self, name, owner, repo, colo_dir, repolog):
        self.releases_url = 'https://api.github.com/repos/' + \
            owner + '/' + repo + '/releases/latest'
        self.colo_dir = colo_dir
        self.name = name
        self.repolog = repolog

    def get_latest_release(self):
        # Download release feed from GitHub
        try:
            response = urllib.request.urlopen(self.releases_url)
        except HTTPError as e:
            print(self.name + ': could not download release information.')
            self.repolog.log('error', e.code)
            return False
        except URLError as e:
            print(self.name + ': could not download release information.')
            self.repolog.log('error', e.reason)
            return False

        self.data = response.readall().decode('utf-8')
        self.feed = json.loads(self.data)

        # Check that feed actually has releases
        if 'assets' not in self.feed:
            print(self.name + ': could not find release information.')
            return False
        else:
            self.repolog.log('info',
                             self.name + ': downloaded release information.')

        # Search releases for RPM file
        for asset in self.feed['assets']:
            if asset['name'].endswith('.rpm'):
                self.download_url = asset['browser_download_url']
                self.rpm_name = asset['name']
                self.repolog.log('info',
                                 self.name + ': found latest release RPM.')
                break
        else:
            print('RPM file not found.')
            return False

        # Append new version filename to repo directory
        self.filename = os.path.join(self.colo_dir, self.rpm_name)

        # Create repo directory if it doesn't exist
        if not os.path.isdir(self.colo_dir):
            os.makedirs(self.colo_dir, exist_ok=True)

        # Skip if file already exists
        if os.path.isfile(self.filename):
            print(self.name + ': RPM is already at latest release.')
            return False

        # Download the actual RPM file
        try:
            response = urllib.request.urlopen(self.download_url)
        except HTTPError as e:
            print('Could not download release.')
            self.repolog.log('error', e.code)
            return False
        except URLError as e:
            print('Could not download release.')
            self.repolog.log('error', e.reason)
            return False

        # Save the RPM file to disk
        try:
            with open(self.filename, 'wb') as f:
                shutil.copyfileobj(response, f)
        except IOError as e:
            print(self.name + ': could not save ' + self.rpm_name + '.')
            self.repolog.log('error', e)
            return False

        print(self.name + ': updated to latest release.')
        return True


class reposyncer:

    def __init__(self, os, version, repolog):
        self.repo_name = os + ' ' + version
        self.os = os.lower()
        self.version = version
        self.repolog = repolog

    def reposync(self):
        # Build reposync command
        self.conf = os.path.join('/etc/reposyncer.d/',
                                 self.os + '_' + self.version)
        self.repo = os.path.join('/srv/repos/', self.os, self.version)

        reposync_command = [
            'reposync',
            '-c',  + self.conf,
            '-p',  + self.repo,
            '--gpgcheck',
            '--delete',
            '--downloadcomps',
            '--download-metadata',
            '--quiet',
        ]

        # Run the reposync process
        try:
            subprocess.call(reposync_command,
                            stdout=open(os.devnull, 'wb'),
                            stderr=open(os.devnull, 'wb'))
        except OSError as e:
            print(self.repo_name + ': error syncing repository.')
            self.repolog.log('error', e)
            return False

        print(self.repo_name + ': successfully synced repository.')
        return True


class repocreator:

    def __init__(self, name, repo_dir, repolog):
        self.name = name
        self.colo_dir = repo_dir
        self.repolog = repolog

    def createrepo(self):
        try:
            subprocess.call(['createrepo', self.colo_dir],
                            stdout=open(os.devnull, 'wb'),
                            stderr=open(os.devnull, 'wb'))
        except OSError as e:
            print(self.name + ': error creating repository.')
            self.repolog.log('error', e)
            return False

        print(self.name + ': successfully created repository.')
        return True


class myLogger:

    def __init__(self, debug=False):
        # Logging settings
        self.logger = logging.getLogger('reposyncer')
        if not debug:
            log_level = 0
        else:
            log_level = 10
        self.logger.setLevel(log_level)

        # Logging formats
        _log_format = '[%(asctime)s] [%(levelname)8s] %(message)s'
        log_format = logging.Formatter(_log_format, '%H:%M:%S')

        # Adds a console handler to the logger
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(log_level)
        ch.setFormatter(log_format)
        self.logger.addHandler(ch)

    def log(self, lvl, msg):
        level = logging.getLevelName(lvl.upper())
        self.logger.log(level, msg)


if __name__ == '__main__':
    def _rpm2repo():
        # Handle individual RPM updates
        colo_dir = os.path.join(REPO_ROOT_DIR, REPO_COLO)

        for name, repo in PROJECTS.items():
            PACKAGES[name] = rpm2repo(name, repo[0], repo[1], colo_dir, repolog)
            PACKAGES[name].get_latest_release()

        cr = repocreator('Colo', colo_dir, repolog)
        cr.createrepo()

    def _reposyncer():
        # Sync all configured repositories
        pass

    def _repocreator():
        # Run createrepo across all repositories
        pass

    # Set available arguments
    parser = argparse.ArgumentParser(
        description='Wrapper for reposync and createrepo.')
    parser.add_argument('-d', '--debug', action='store_true',
                        help='enables debug messages')
    args = parser.parse_args()

    # Configure debugging
    if args.debug:
        repolog = myLogger(True)
    else:
        repolog = myLogger(False)

    # Execute desired processes
    _rpm2repo()
    _reposyncer()
    _repocreator()
