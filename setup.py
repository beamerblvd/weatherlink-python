import os
from setuptools import setup, find_packages
import sys

from weatherlink import __version__

packages = find_packages(exclude=['tests', 'tests.*'])

install_requirements = [
	'requests==2.9.1'
]

test_requirements = [

]

if sys.argv[-1] == 'info':
	print 'WeatherLink-Python Setup Information'
	print
	print 'Packages found: %s' % packages
	print 'Install requirements: %s' % install_requirements
	sys.exit()

if sys.argv[-1] == 'tag':
	os.system('git tag -a {version} -m "Released version {version}."'.format(version=__version__))
	os.system('git push --tags')
	sys.exit()


setup(
	name='weatherlink',
	version=__version__,
	description=('A Python library for dealing with Davis(R) WeatherLink(R) database files, '
				 'web service downloads, and console downloads'),
	author='Nick Williams',
	url='https://github.com/beamerblvd/weatherlink-python',
	packages=packages,
	install_requires=install_requirements,
	tests_require=test_requirements,
)
