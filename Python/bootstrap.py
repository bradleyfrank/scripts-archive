#!/usr/bin/env python

__author__ = 'Bradley Frank'

import argparse
import ConfigParser
import errno
import getpass
import glob
import grp
import logging
import os
import random
import re
import socket
import subprocess
import sys
import time
import urllib2
import zipfile
from platform import system


class Bootstrap:
    """
    Bootstraps a newly installed client machine with SSH keys and installs
    Puppet Agent so the client can be managed with Puppet. On Mac platforms,
    HomeBrew will also be installed.

    Run this script as your local user, not as root.

    ** A note about optional HomeBrew cask installs: since they cannot be
    guaranteed to be idempotent, you must explicity enable this feature
    at runtime. **


    Class variables:
        CONF_DIR (string): location to save/load config files
        HOME (string): path to user's home directory
        FQDN (string): client fully qualified domain name
        HOMEBREW_URL (string):
        HOSTNAME (string): client hostname (i.e. without ".local")
        PASSPHRASE_NUM_WORDS (int): number of words to use in a passphrase
        PASSPHRASE_WORD_LENGTH (tuple): format is (minimum, maximum)
        PUPPET_HB_BRANCH (string):
        PUPPET_HB_MANIFEST_URL (string):
        PUPPET_MODULES (tuple):
        SSH_KEY_DIR (string): directory (relative to HOME) to save SSH keys
        SSH_KEY_TYPES (tuple): which SSH key types to generate
        SSH_RSA_BITS (string): SSH key length
        SOURCE_DICTIONARY (string): location of valid system dictionary file
        USER (string): username
    """

    CONF_DIR = '.config/homebox'
    HOMEBREW_URL = ('https://raw.githubusercontent.com/'
                    'Homebrew/install/master/install')
    HOME = os.path.expanduser('~')
    PASSPHRASE_NUM_WORDS = 5
    PASSPHRASE_WORD_LENGTH = (3, 8)
    PUPPET_HB_BRANCH = 'alpha'
    PUPPET_HB_MANIFEST_URL = 'https://github.com/bradleyfrank/HomeBox/archive'
    PUPPET_MODULES = ('puppetlabs-vcsrepo',
                      'thekevjames-homebrew')
    SSH_KEY_DIR = '.ssh'
    SSH_KEY_TYPES = {'dsa': False,
                     'rsa': True,
                     'ecdsa': False,
                     'ed25519': True}
    SSH_RSA_BITS = '4096'
    SOURCE_DICTIONARY = '/usr/share/dict/words'
    USER = getpass.getuser()

    def __init__(self, debug=False, log_console=False, log_file=False):

        # Logging settings
        self.logger = logging.getLogger('bootstrap')
        if not debug:
            log_level = 0
        else:
            log_level = 10
        self.logger.setLevel(log_level)

        # Logging formats
        _format = '[%(asctime)s] [%(levelname)8s] %(message)s'
        log_format = logging.Formatter(_format, '%H:%M:%S')

        # Create logging handler
        if log_console:
            self._log_to_console(log_level, log_format)

        if log_file:
            self._log_to_file(log_level, log_format)

        if not log_console and not log_file:
            self._log_to_null(log_level, log_format)

        # Get hostname
        self.FQDN = socket.getfqdn()
        _fqdn = self.FQDN.split('.')

        if len(_fqdn) == 1:
            self.HOSTNAME = _fqdn[0]
        elif _fqdn[1] == 'local':
            self.HOSTNAME = _fqdn[0]
        else:
            self.HOSTNAME = self.FQDN

        # Prompt for user password
        self.passwd = getpass.getpass('Enter your password: ')

        # Make config directory
        self.HB_CONFDIR = os.path.join(self.HOME, self.CONF_DIR)
        self._log('debug', 'Full path to config directory: ' + self.HB_CONFDIR)
        self._mkdir(self.HB_CONFDIR)

    def create_dictionary(self):
        """
        """

        # Read in full system dictionary
        with open(self.SOURCE_DICTIONARY, 'r') as fp:
            words = fp.read()
        full_dictionary = words.splitlines()

        _logstr = 'System dictionary size: ' + str(len(full_dictionary))
        self._log('debug', _logstr)

        # Whittle dictionary down to sane options
        dictionary = []
        min_length = self.PASSPHRASE_WORD_LENGTH[0]
        max_length = self.PASSPHRASE_WORD_LENGTH[1]

        for word in full_dictionary:
            if min_length <= len(word) <= max_length and word.isalpha():
                dictionary.append(word.lower())

        dictionary = tuple(dictionary)

        _logstr = 'Effective dictionary size: ' + str(len(dictionary))
        self._log('debug', _logstr)

        return dictionary

    def generate_passphrase(self, dictionary):
        """
        """

        words = []
        for x in range(0, self.PASSPHRASE_NUM_WORDS):
            word = random.SystemRandom().choice(dictionary)
            words.append(word)

        passphrase = '-'.join(words)

        _logstr = 'Generated passphrase: ' + passphrase
        self._log('debug', _logstr)

        return passphrase

    def generate_ssh_keys(self, passphrase):
        """
        """

        def generate_key(keydir, passphrase, bits, keytype, comment):
            keyfile = keydir + '/id_' + keytype
            # Check if the key already exists so we don't overwrite it
            if os.path.isfile(keyfile):
                _logstr = 'SSH key \"' + keyfile + '\" exists, aborting.'
                self._log('info', _logstr)
                return False

            keygen = (
                'ssh-keygen',
                '-t', keytype,
                '-b', bits,
                '-N', passphrase,
                '-C', comment,
                '-f', keyfile,
            )

            self._log('info', 'Generating ' + keytype + ' SSH key...')

            exit_code = self._shell(keygen)

            if exit_code == 0:
                _logstr = 'SSH key \"' + keyfile + '\" successfully created!'
                self._log('info', _logstr)
                return True
            else:
                _logstr = 'SSH key \"' + keyfile + '\" was not created.'
                self._log('error', _logstr)
                return False

        # Create the directory if it doesn't exist
        keydir = os.path.join(self.HOME, self.SSH_KEY_DIR)
        self._mkdir(keydir)

        # Create a standard comment for each key
        comment = self.USER + "@" + self.HOSTNAME

        # Keep track of whether keys are generated
        sshkey_created = False

        # Generate SSH keys
        for (keytype, generate) in self.SSH_KEY_TYPES.iteritems():
            if generate:
                result = generate_key(keydir,
                                      passphrase,
                                      self.SSH_RSA_BITS,
                                      keytype,
                                      comment)
                sshkey_created = sshkey_created or result

        return sshkey_created

    def get_sysinfo(self):
        """
        """

        platform = system()
        self._log('debug', 'Platform: ' + platform)

        if platform == 'Darwin':
            sysinfo = self.get_sysinfo_darwin()
        elif platform == 'Linux':
            sysinfo = self.get_sysinfo_linux()
        else:
            return None

        if sysinfo is not None:
            _logstr = 'Detected ' + sysinfo[0] + ' ' + sysinfo[1]
            self._log('debug', _logstr)
            return sysinfo[0], sysinfo[1]
        else:
            self._log('critical', 'Operating System not supported.')
            return None

    def get_sysinfo_linux(self):
        """
        """

        # Function for searching *-release files
        def search_release_file(filename):
            self._log('debug', 'Searching release file: ' + filename)
            if os.path.isfile(filename):
                sysinfo = self._read(filename)
                if sysinfo is None:
                    return None
            else:
                return None

            regex = re.compile("(\d{2}|Fedora)", re.MULTILINE)
            match = re.findall(regex, sysinfo)

            self._log('debug', 'Regex search produced: ' + ' '.join(match))

            if len(match) >= 2:
                return match[0], match[1]
            else:
                return None

        for filename in glob.glob('/etc/*-release'):
            sysinfo = search_release_file(filename)
            if sysinfo is not None:
                return sysinfo[0], sysinfo[1]
        else:
            return None

    def get_sysinfo_darwin(self):
        """
        """

        try:
            sysinfo = subprocess.check_output(['sw_vers']).split()
        except OSError:
            return None

        self._log('debug', 'sw_vers returned: ' + ' '.join(sysinfo))

        # Extra confirmation OS is Mac
        opsys = "Mac" if "Mac" in sysinfo else None

        # Search sw_vers results for macOS version (e.g. 10.X.X)
        regex = re.compile("\d+\.\d+[\.\d+]?")
        re_result = filter(lambda x: re.search(regex, x), sysinfo)
        osver = re_result[0] if len(re_result) > 0 else None

        if opsys is not None and osver is not None:
            return opsys, osver
        else:
            return None

    def homebrew_install(self):
        """
        """

        #
        # Check if Homebrew is already installed
        #
        cmd = ('brew', 'update')
        if self._shell(cmd) == 0:
            # Upon success, report Homebrew installed
            self._log('info', 'Brew updated successfully.')
            return None
        else:
            # Upon failure, try re-installing
            _logstr = 'Brew update failed, attempting install.'
            self._log('info', _logstr)

        #
        # Homebrew install
        #

        # Download Homebrew install script
        brew_install = self._download('Homebrew install script',
                                      self.HOMEBREW_URL)
        if brew_install is False:
            return False

        try:
            # Pass Homebrew install script to Ruby to execute
            cmd = ('ruby', '-e', brew_install)
            p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
            p.communicate(self.passwd + "\n")
        except OSError:
            self._log('critical', 'Failed to run Homebrew script.')
            return False

        return True if p.returncode == 0 else False

    def puppet_create_env(self):
        """
        """

        #
        # Set Puppet modulepath
        #
        puppet_confdir = ('puppet', 'config', 'print', 'confdir')
        paths = subprocess.check_output(puppet_confdir).split(':')

        for path in paths:
            if self.USER in path:
                modulepath = path
                mod_install_args = ()
                break
        else:
            modulepath = self.HB_CONFDIR
            mod_install_args = ('--modulepath', modulepath)

        #
        # Install Puppet modules
        #
        puppet_mod_install = ('puppet', 'module', 'install')
        for module in self.PUPPET_MODULES:
            cmd = puppet_mod_install + (module) + mod_install_args
            if self._shell(cmd) != 0:
                _logstr = 'Error installing Puppet module: ' + module
                self._log('warning', _logstr)
            else:
                _logstr = 'Installed Puppet module: ' + module
                self._log('info', _logstr)

        #
        # Install HomeBox module
        #
        filename = self.PUPPET_HB_BRANCH + '.zip'
        local_file = modulepath + '/' + filename
        remote_file = self.PUPPET_HB_MANIFEST_URL + '/' + filename

        self._log('debug', 'Local file: ' + local_file)
        self._log('debug', 'Remote file: ' + remote_file)

        # Download zip file of HomeBox module
        hb_zip = self._download('HomeBox zip file', remote_file)
        if hb_zip is False:
            return False
        self._write(local_file, hb_zip, True)

        # Extract zip file into config directory
        self._unzip(local_file, modulepath)

        # Remove original zip file
        self._rmfile(local_file)

    def puppet_install(self, opsys):
        """
        """

        def gem_install(opsys):
            self._log('info', 'Installing Puppet for Linux as a Ruby gem.')

            #
            # Install RVM GPG keys
            # See https://rvm.io/rvm/install
            #
            self._log('info', 'Importing GPG key.')
            gpg = ('gpg',
                   '--keyserver',
                   'hkp://keys.gnupg.net',
                   '--recv-keys',
                   '409B6B1796C275462A1703113804BB82D39DC0E3',
                   '7D2BAF1CF37B13E2069D6956105BD0E739499BDB')

            if self._shell(gpg) != 0:
                self._log('critical', 'RVM GPG keys failed to import.')
                return False

            #
            # Install RVM dependency (system Ruby)
            #
            self._log('info', 'Installing system Ruby.')
            yum = 'dnf' if opsys == 'Fedora' else 'yum'
            pkg_install = (yum, 'install', 'ruby', '-qy')

            try:
                p = subprocess.Popen(pkg_install,
                                     stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE)
                p.communicate(self.passwd + "\n")
            except OSError:
                self._log('critical', 'Failed to installed system Ruby.')
                return False

            #
            # Install RVM
            #
            self._log('info', 'Installing RVM.')
            rvm_install = self._download('RVM script', 'https://get.rvm.io')
            if rvm_install is False:
                self._log('critical', 'Failed to download RVM script.')
                return False

            try:
                # Pass RVM install script to Bash to execute
                p = subprocess.Popen(('bash'), stdin=subprocess.PIPE)
                p.communicate(rvm_install)
            except OSError:
                self._log('critical', 'Failed to run RVM script.')
                return False
            if p.returncode != 0:
                self._log('critical', 'RVM failed to install.')
                return False

            self._log('info', 'Installed RVM successfully.')

            #
            # Install Ruby
            #
            self._log('info', 'Installing RVM Ruby.')
            rvm = os.path.join(self.HOME, '.rvm/bin/rvm')
            self._log('debug', 'rvm path is: \"' + rvm + '\"')

            ruby_install = (rvm, 'install', 'ruby')

            if self._shell(ruby_install) != 0:
                self._log('critical', 'RVM Ruby failed to install.')
                return False

            self._log('info', 'Installed RVM Ruby successfully.')

            #
            # Install Puppet
            #
            self._log('info', 'Installing Puppet.')

            # Get latest version of Ruby
            rubies = []
            ruby_dirs = os.path.join(self.HOME, '.rvm/rubies')
            for ruby_dir in glob.glob(ruby_dirs + '/ruby-*'):
                rubies.append(ruby_dir)
            rubies.sort(reverse=True)
            ruby_version = rubies[0]

            # Set path to gem binary
            gem = os.path.join(ruby_version + '/bin/gem')
            self._log('debug', 'gem path is: \"' + gem + '\"')

            puppet_install = (gem, 'install', 'puppet')
            return True if self._shell(puppet_install) == 0 else False

        def mac_install():
            self._log('info', 'Installing Puppet for Mac.')
            cmd = ('brew', 'cask', 'install', 'puppet-agent')
            return True if self._shell(cmd) == 0 else False

        #
        # Test if Puppet is present
        #
        if self._shell(('puppet', '--version')) == 0:
            self._log('debug', 'Puppet check exited with "0".')
            return None

        #
        # Method of installing Puppet per OS
        #
        if opsys == 'Mac':
            self._log('info', 'Installing Puppet with Homebrew.')
            return mac_install()
        elif opsys == 'Fedora' or opsys == 'CentOS':
            self._log('info', 'Installing Puppet as a Ruby gem.')
            return gem_install(opsys)
        else:
            self._log('critical', opsys + ' is not supported!')
            return False

    def save_passphrase(self, passphrase):
        """
        """

        passfile = os.path.join(self.HOME, self.SSH_KEY_DIR, 'passphrase')
        self._write(passfile, passphrase)

        try:
            os.chmod(passfile, 0o400)
        except OSError:
            _logstr = 'Unable to change permissions on passphrase file.'
            self._log('warning', _logstr)

        return passfile

    def _download(self, name, source):
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

    def _log(self, lvl, msg):
        """Logging wrapper function."""
        level = logging.getLevelName(lvl.upper())
        self.logger.log(level, msg)

    def _log_to_console(self, log_level, log_format):
        """Adds a console handler to the logger."""
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(log_level)
        ch.setFormatter(log_format)
        self.logger.addHandler(ch)

    def _log_to_file(self, log_level, log_format):
        """Adds a file handler to the logger."""
        logfile = 'bootstrap-' + time.strftime('%b%d-%H%M') + '.log'
        fh = logging.FileHandler(logfile)
        fh.setLevel(log_level)
        fh.setFormatter(log_format)
        self.logger.addHandler(fh)

    def _log_to_null(self, log_level, log_format):
        """Adds a null handler to the logger."""
        nh = logging.NullHandler()
        nh.setLevel(log_level)
        nh.setFormatter(log_format)
        self.logger.addHandler(nh)

    def _mkdir(self, path, mode=0755):
        """Directory creation wrapper function."""
        try:
            os.makedirs(path, mode)
            self._log('info', 'Created directory: ' + path)
        except OSError as e:
            _logstr = 'Directory \"' + path + '\" exists, aborting.'
            self._log('info', _logstr)
            if e.errno != errno.EEXIST:
                raise

    def _read(self, filename):
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

    def _rmfile(self, path):
        """File removal wrapper function."""
        try:
            os.remove(path)
            self._log('info', 'Deleted file: ' + path)
        except IOError:
            _logstr = 'Error deleting file \"' + path + '\"'
            self._log('warning', _logstr)

    def _shell(self, cmd):
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

    def _unzip(self, filename, filepath):
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

    def _write(self, filename, stream, binary=False):
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

    def _print_section(title):
        width = len(title) + 2
        print('')
        print('=' * width)
        print(title)
        print('-' * width)
        print('')

    # Set available arguments
    parser = argparse.ArgumentParser(description='Boostraps Mac or \
                                     Fedora systems.')
    group = parser.add_mutually_exclusive_group()

    group.add_argument('-q', '--quiet', action='store_true',
                       help='disables console output')
    group.add_argument('-v', '--verbose', action='store_true',
                       help='enables console debugging')
    parser.add_argument('-l', '--log', action='store_true',
                        help='enables debug logging to file')
    parser.add_argument('-s', '--setup', action='store_true',
                        help='execute advanced setup (see README)')
    args = parser.parse_args()

    # Parse arguments
    log_to_file = True if args.log else False

    if args.quiet:
        bsh = Bootstrap(log_file=log_to_file)
        sys.stdout = open(os.devnull, 'w')
    elif args.verbose:
        bsh = Bootstrap(debug=True,
                        log_console=True,
                        log_file=log_to_file)
    else:
        bsh = Bootstrap()

    # Test system for support
    _print_section('Probing for OS')
    sysinfo = bsh.get_sysinfo()
    if sysinfo is None:
        sys.exit('Operating System not supported.')
    else:
        opsys = sysinfo[0]
        osver = sysinfo[1]
        print('Found: ' + opsys + ' ' + osver)

    # Generate SSH keys using diceware passphrase
    _print_section('Generating SSH Keys')
    dictionary = bsh.create_dictionary()
    passphrase = bsh.generate_passphrase(dictionary)
    sshkey_created = bsh.generate_ssh_keys(passphrase)

    # Save and secure passphrase for user
    if sshkey_created:
        _print_section('Saving & Securing SSH Passphrase')
        passfile = bsh.save_passphrase(passphrase)
        if passfile:
            print('Your passphrase was saved to: ' + passfile + "\n")
        else:
            print('Unable to save passphrase to file.')
    else:
        print('No SSH keys created.')

    # Install Homebrew for MacOS
    if opsys == "Mac":
        _print_section('Installing Xcode and Homebrew')
        result = bsh.homebrew_install()
        if result is None:
            print('Homebrew appears to be installed already.')
        elif result is True:
            print('Homebrew successfully installed.')
        else:
            sys.exit('Homebrew failed to install.')

    # Install Puppet Agent
    _print_section('Installing Puppet')
    result = bsh.puppet_install(opsys)
    if result is None:
        print('Puppet appears to be installed already.')
    elif result is True:
        print('Puppet successfully installed.')
    else:
        sys.exit('Encountered an error installing Puppet.')

    # Create Puppet environment
    _print_section('Building Puppet Environment')
    result = bsh.puppet_create_env()
    if result is True:
        print('Puppet environment successfully bootstrapped.')
    else:
        sys.exit('Puppet environment bootstrap failed.')