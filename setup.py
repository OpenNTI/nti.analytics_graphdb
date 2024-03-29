import codecs
from setuptools import setup, find_packages

VERSION = '0.0.0'

entry_points = {
	'z3c.autoinclude.plugin': [
		'target = nti.analytics_graphdb',
	],
	'console_scripts': [
		"nti_analytics_graphdb_view_events = nti.analytics_graphdb.scripts.view_events:main",
	]
}

setup(
	name='nti.analytics_graphdb',
	version=VERSION,
	author='Josh Zuech',
	author_email='josh.zuech@nextthought.com',
	description="NTI Analytics GraphDB",
	long_description=codecs.open('README.rst', encoding='utf-8').read(),
	license='Proprietary',
	keywords='pyramid preference',
	classifiers=[
		'Intended Audience :: Developers',
		'Natural Language :: English',
		'License :: OSI Approved :: Apache Software License.7',
		'Programming Language :: Python :: 2.7',
		'Programming Language :: Python :: 3',
		'Programming Language :: Python :: 3.3',
	],
	packages=find_packages('src'),
	package_dir={'': 'src'},
	namespace_packages=['nti'],
	install_requires=[
		'setuptools',
		'nti.analytics',
		'nti.graphdb'
	],
	entry_points=entry_points
)
