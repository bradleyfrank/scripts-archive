"""
ADMIN_GROUP (dict): system defined groups with sudo privileges
"""

ADMIN_GROUP = {'Mac': 'admin',
               'Fedora': 'wheel'}

def is_admin(self, opsys):
    """
    """
    admin_grp = self.ADMIN_GROUP[opsys]
    self._log('debug', 'System admin group: ' + admin_grp)

    # Get admin GID
    try:
        admin_gid = grp.getgrnam(admin_grp)[2]
        self._log('debug', 'System admin gid: ' + str(admin_gid))
    except KeyError:
        self._log('warning', 'Group ' + admin_grp + 'not found.')
        return False

    # Get user's groups
    user_groups = os.getgroups()
    _ug = [str(x) for x in user_groups]
    self._log('debug', 'User belongs to: ' + ' '.join(_ug))
    return True if admin_gid in user_groups else False

    # Test command for sudo
    exit_code = self._shell(['sudo', '-n', 'date'])
    return True if exit_code == 1 else False