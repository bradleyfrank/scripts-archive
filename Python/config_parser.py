#
# Get the current working directory of this script.
#
# The join() call prepends the current working directory, but the
# documentation says that if some path is absolute, all other paths left
# of it are dropped. Therefore, getcwd() is dropped when dirname(__file__)
# returns an absolute path. The realpath call resolves symbolic links if
# any are found.
#
__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))

#
# Create a config parser instance and read in the config file, located
# in the same directory as this script.
#
conf = configparser.ConfigParser()
conf.read(os.path.join(__location__, 'prkeeper.conf'))

# Download settings
download_path = conf['downloads']['download_path']
status_file = conf['downloads']['status_file']

# Logging settings
logfile = conf['logging']['logfile']
log_to_console = conf['logging']['log_to_console']
log_to_file = conf['logging']['log_to_file']