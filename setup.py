#!/usr/bin/env python

#
#  setup.py
#  
#  Copyright The GRS Modulator Contributors.
#  
#  This file is part of GRS Modulator.
#
#  GRS Modulator is free software; you can redistribute it
#  and/or modify it under the terms of the GNU General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#  
#  GRS Modulator is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public
#  License along with GRS Modulator; if not, see <http://www.gnu.org/licenses/>.
#  
#

import setuptools
import os

#from sphinx.setup_command import BuildDoc

# Make sure we are running on posix (Linux, Unix, MAC OSX)
if os.name != 'posix':
    sys.exit("Sorry, Windows is not supported yet!")

exec(open('grs_modulator/version.py').read())

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name                            = "grs_modulator",
    version                         = __version__,
    author                          = "Carlos Augusto Porto Freitas",
    author_email                    = "carlos.portof@hotmail.com",
    maintainer                      = "Carlos Augusto Porto Freitas",
    maintainer_email                = "carlos.portof@hotmail.com",
    url                             = "https://github.com/spacelab-ufsc/grs-modulator",
    license                         = "GPLv3",
    description                     = "GRS Modulator",
    long_description                = long_description,
    long_description_content_type   = "text/markdown",
    platforms                       = ["Linux"],
    classifiers                     = [
        "Development Status :: 1 - Planning",
        "Environment :: Console",
        "Intended Audience :: Education",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Telecommunications Industry",
        "Intended Audience :: Science/Research"
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Natural Language :: English",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Topic :: Communications :: Ham Radio",
        "Topic :: Education",
        "Topic :: Scientific/Engineering",
        ],
    download_url                    = "https://github.com/spacelab-ufsc/grs-modulator/releases",
    packages                        = setuptools.find_packages(),
    install_requires                = ['numpy','scipy','pyzmq','pyadi-iio'],
    entry_points                    = {
        'console_scripts': [
            'grs-modulator = grs_modulator.__main__:main'
            ]
        },
)
