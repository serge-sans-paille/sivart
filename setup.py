from setuptools import setup
from sivart import __version__, __doc__

setup(name='sivart',
      version=__version__,
      description=__doc__,
      author='Serge Guelton',
      author_email='serge.guelton@telecom-bretagne.eu',
      url='https://github.com/serge-sans-paille/sivart',
      py_modules=['sivart'],
      classifiers=['Development Status :: 4 - Beta',
                   'Environment :: Console',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: BSD License',
                   'Natural Language :: English',
                   'Programming Language :: Python :: 2',
                   'Programming Language :: Python :: 3',
                   'Topic :: Software Development :: Testing'],
      license="BSD 3-Clause",
      install_requires=['python-vagrant', 'argparse', 'pyyaml']
      )
