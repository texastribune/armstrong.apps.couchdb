from setuptools import setup

setup(
    name='armstrong.apps.couchdb',
    version='0.1',
    description='Provides a few generic views for wrapping calls to CouchDB',
    author='Texas Tribune',
    author_email='tech@texastribune.org',
    url='http://github.com/texastribune/armstrong.apps.couchdb/',
    packages=[
        'armstrong',
        'armstrong.apps',
        'armstrong.apps.couchdb',
    ],

    install_requires=[
        'setuptools',
    ],

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
)
