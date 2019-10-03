#
# Puppet variables
#
PUPPET_URL_MAC = 'https://downloads.puppetlabs.com/mac/puppet'

def puppet_download(osver, urlbase, filename):
    """
    """

    logger = logging.getLogger('bootstrap')

    def download(urlbase, majv, minv, filename):
        url_suffix = 'x86_64/puppet-agent-latest.dmg'
        url_version = str(majv) + '.' + str(minv)
        url = urlbase + "/" + url_version + '/' + url_suffix

        http_code = urllib.urlopen(url).getcode()

        logger.info('Trying download with version ' + url_version)
        logger.debug('Puppet URL: ' + url)
        logger.info('Puppet returned: ' + str(http_code))

        if http_code is 200:
            logger.info('Downloading Puppet for Mac ' + url_version)
            localfile = urllib.urlretrieve(url, filename)
            return localfile
        else:
            if minv > 0:
                result = download(urlbase, majv, minv-1, filename)
                return False if not result else result[0]
            else:
                return False

    macos = re.match("(\d+)\.(\d+)", osver)
    majv = int(macos.groups()[0])
    minv = int(macos.groups()[1])

    result = download(urlbase, majv, minv, filename)
    return False if not result else result[0]


    if opsys == "Mac":
        puppet_download = puppet_download(osver,
                                          PUPPET_URL_MAC,
                                          os.path.join(HOME, 'puppet.dmg'))
        if puppet_download:
            puppet_install(opsys)
        else:
            logger.warning('Unable to download Puppet; exiting...')
            sys.exit('Unable to download Puppet.')
    elif opsys == 'Fedora':
            puppet_install(opsys)