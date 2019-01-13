import os
from setuptools import setup, find_packages
import sys

from weatherlink import __version__

packages = find_packages(exclude=['tests', 'tests.*'])

install_requirements = [
	'six>=1.10.0',
	'enum34>=1.1.5;python_version<"3.4"',
	'pytz>=2016.4',
	'requests>=2.9.1',
	'mysql_connector_python>=2.0.4',
]

dependency_links = [
	'https://cdn.mysql.com/Downloads/Connector-Python/mysql-connector-python-2.0.4.zip#egg=mysql_connector_python-2.0.4',
]

test_requirements = [
	'mock>=2.0.0',
	'pytest',
	'pytest-cov',
	'python-dateutil',
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
	setup_requires=['pytest-runner'],
	extras_require={
		'testing': test_requirements,
	},
)
