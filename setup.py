#!usr/bin/env python
from setuptools import setup

setup(
    name='wallpaperSorter',
    version='0.2.3',
    author='Trevor Nuckles',
    author_email='trevnuckles@gmail.com',
    entry_points={
        'console_scripts': [
            'wallpaperSorter=wallpaperSorter:main'
            ]
    }
)