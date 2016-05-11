import os
from setuptools import setup, find_packages
import sys

from weatherlink import __version__

packages = find_packages(exclude=['tests', 'tests.*'])

install_requirements = [
	'six>=1.10.0',
	'enum34>=1.1.5',
	'pytz>=2016.4',
	'requests==2.9.1',
	'mysql_connector_python>=2.0.4',
]

dependency_links = [
	'https://cdn.mysql.com/Downloads/Connector-Python/mysql-connector-python-2.0.4.zip#egg=mysql_connector_python-2.0.4',
]

test_requirements = [
	'argparse==1.4.0',
	'coverage==4.0.3',
	'nose==1.3.7',
	'funcsigs==1.0.2',
	'mock==2.0.0',
	'nosexcover==1.0.10',
	'traceback2==1.4.0',
	'linecache2==1.0.0',
	'unittest2==1.1.0',
]

if sys.argv[-1] == 'info':
	print('WeatherLink-Python Setup Information')
	print()
	print('Packages found: %s' % packages)
	print('Install requirements: %s' % install_requirements)
	sys.exit()

if sys.argv[-1] == 'tag':
	os.system('git tag -a {version} -m "Released version {version}."'.format(version=__version__))
	os.system('git push --tags')
	sys.exit()


setup(
	name='weatherlink',
	version=__version__,
	description=(
		'A Python library for dealing with Davis(R) WeatherLink(R) database files, '
		'web service downloads, and console downloads'
	),
	author='Nick Williams',
	url='https://github.com/beamerblvd/weatherlink-python',
	packages=packages,
	install_requires=install_requirements,
	dependency_links=dependency_links,
	tests_require=test_requirements,
)
