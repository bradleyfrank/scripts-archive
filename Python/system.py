#!/usr/bin/env python3

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
              _sysinfo = self._read(filename)
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