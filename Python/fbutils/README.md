# HMDC Python Logging Wrapper

Instead of re-implementing logging for every module, you can import the wrapper module that takes care of a majority of the process, making the process easier.

## Example Usage

    def __init__(self, logger=None, debug_level=None, log_to_console=False, log_to_file=False):

      if logger is None:
        self.hmdclog = self._set_logger(debug_level, log_to_console, log_to_file)
      else:
        self.hmdclog = logger

    def _set_logger(self, debug_level, log_to_console, log_to_file):

      if debug_level is None:
        hmdclog = hmdclogger.HMDCLogger(example_name, self.conf_settings['debug_level'])
        hmdclog.log_to_file(self.conf_settings['log_file'])
      else:
        hmdclog = hmdclogger.HMDCLogger(example_name, debug_level)

        if log_to_console is False and log_to_file is False:
          raise Exception("You must set a console or file logging handler.")

        if log_to_console:
          hmdclog.log_to_console()
        if log_to_file:
          hmdclog.log_to_file(self.conf_settings['log_file'])

      return hmdclog

* This example module takes in variables for the debug level, and booleans for logging to console and logging to a file (they are ''not'' mutually exclusive).
* The optional debugging parameters are superseded by settings from a conf file (of which the process of import/parsing is not detailed here).
* An existing instance of HMDCLogger can be passed via `logger` parameter if this class is being imported. It will supersede conf file settings and/or any debugging variables passed to the class.
* A new instance of HMDCLogger is created with an identifier and the debug level. A list of debug levels is available at [[https://docs.python.org/2/library/logging.html#logging-levels | docs.python.org]].
* Calling `log_to_console()` or `log_to_file()` enables that respective logging.
* When enabling file logging, please note the first argument does ''not'' take a trailing slash.

You can log messages as follows:
* `self.hmdclog.log('info', "Informational logging message.")`
* `self.hmdclog.log('debug', "A debugging statement.")`
* `self.hmdclog.log('warning', "Non-critical information.")`
* `self.hmdclog.log('error', "A problem has occurred.")`
* `self.hmdclog.log('critical', "A serious issue arose.")`

## Calling HMDCLogger

There are additional optional parameters when creating an instance of HMDCLogger:
* `name` (required)
* `debug_level` (required)
* `log_format` (optional) - Please note, the Python logger is not flexible in some areas; the attribute `funcName` will not work because this picks up the wrapper function and not the actual module function adding the log. This is resolved by hardcoding the attribute by querying the Python stack. A complete list of attributes is available at [[https://docs.python.org/2/library/logging.html#logrecord-attributes | docs.python.org]]. ''The default is really good, so I don't suggest modifying this unless you really need to.''
* `date_format` (optional) - The date format is completely customizable.