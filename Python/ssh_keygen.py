#!/usr/bin/env python

import getpass
import os
import random
import socket

class SSHkeygen:
    """
    Class variables:
        HOME (string): path to user's home directory
        FQDN (string): client fully qualified domain name
        HOSTNAME (string): client hostname (i.e. without ".local")
        PASSPHRASE_NUM_WORDS (int): number of words to use in a passphrase
        PASSPHRASE_WORD_LENGTH (tuple): format is (minimum, maximum)
        SSH_KEY_DIR (string): directory (relative to HOME) to save SSH keys
        SSH_KEY_TYPES (tuple): which SSH key types to generate
        SSH_RSA_BITS (string): SSH key length
        SOURCE_DICTIONARY (string): location of valid system dictionary file
        USER (string): username
    """
  
    HOME = os.path.expanduser('~')
    USER = getpass.getuser()
    PASSPHRASE_NUM_WORDS = 5
    PASSPHRASE_WORD_LENGTH = (3, 8)
    SSH_KEY_DIR = '.ssh'
    SSH_KEY_TYPES = {'dsa': False,
                     'rsa': True,
                     'ecdsa': False,
                     'ed25519': True}
    SOURCE_DICTIONARY = '/usr/share/dict/words'

    def __init__(self):
        # Get hostname
        self.FQDN = socket.getfqdn()
        _fqdn = self.FQDN.split('.')

        if len(_fqdn) == 1:
            self.HOSTNAME = _fqdn[0]
        elif _fqdn[1] == 'local':
            self.HOSTNAME = _fqdn[0]
        else:
            self.HOSTNAME = self.FQDN

    def create_dictionary(self):
        # Read in full system dictionary
        with open(self.SOURCE_DICTIONARY, 'r') as fp:
            words = fp.read()
        full_dictionary = words.splitlines()

        # Whittle dictionary down to sane options
        dictionary = []
        min_length = self.PASSPHRASE_WORD_LENGTH[0]
        max_length = self.PASSPHRASE_WORD_LENGTH[1]

        for word in full_dictionary:
            if min_length <= len(word) <= max_length and word.isalpha():
                dictionary.append(word.lower())

        return tuple(dictionary)

    def generate_passphrase(self, dictionary):
        words = []
        for x in range(0, self.PASSPHRASE_NUM_WORDS):
            word = random.SystemRandom().choice(dictionary)
            words.append(word)

        return '-'.join(words)

    def generate_ssh_keys(self, passphrase):

        def generate_key(keydir, passphrase, keytype, comment):
            keyfile = keydir + '/id_' + keytype

            # Check if the key already exists so we don't overwrite it
            if os.path.isfile(keyfile):
                return False

            keygen = (
                'ssh-keygen',
                '-t', keytype,
                '-b', '4096',
                '-N', passphrase,
                '-C', comment,
                '-f', keyfile,
            )

            return True if self._shell(keygen) == 0 else False

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
                result = generate_key(keydir, passphrase, keytype, comment)
                sshkey_created = sshkey_created or result

        return sshkey_created

    def save_passphrase(self, passphrase):
        """
        """

        passfile = os.path.join(self.HOME, self.SSH_KEY_DIR, 'passphrase')
        self._write(passfile, passphrase)

        try:
            os.chmod(passfile, 0o400)
        except OSError:
            pass

        return passfile

if __name__ == '__main__':
    ssh = SSHkeygen()
    # Generate SSH keys using diceware passphrase
    dictionary = ssh.create_dictionary()
    passphrase = ssh.generate_passphrase(dictionary)
    sshkey_created = ssh.generate_ssh_keys(passphrase)

    # Save and secure passphrase for user
    if sshkey_created:
        passfile = ssh.save_passphrase(passphrase)
        if passfile:
            print('Your passphrase was saved to: ' + passfile + "\n")
        else:
            print('Unable to save passphrase to file.')
    else:
        print('No SSH keys created.')