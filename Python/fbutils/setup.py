from distutils.core import setup

setup(author='Bradley Frank',
      author_email='bfrank@hmdc.harvard.edu',
      description='Wrapper for the logging module.',
      license='GPLv2',
      name='HMDCLogger',
      packages=['hmdclogger'],
      requires=['inspect','logging','os','sys'],
      url='https://github.com/hmdc/hmdc-logger',
      version='1.2',
)
