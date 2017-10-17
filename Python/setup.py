import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "AbacusSoftware",
    version = "1.0.2",
    author = "Juan Barbosa",
    author_email = "js.barbosa10@uniandes.edu.co",
    description = ('Build to simplify usage of Tausands tools.'),
    license = "GPL",
    keywords = "example documentation tutorial",
    url = "https://github.com/Tausand-dev/ReimaginedQuantum",
    packages=['abacusSoftware'],
    install_requires=['numpy', 'matplotlib', 'pyserial', 'importlib'],
    long_description=read('README'),
    classifiers=[
        "Development Status :: 1 - Planning",
        "Topic :: Utilities",
        "License :: OSI Approved :: GNU General Public License (GPL)",
    ],
)

# from distutils.core import setup, Extension
#
# setup(name = 'reimaginedQuantum',
#        version = '1.0',
#        description = 'Reimagined Quantum attemp',
#        packages = ['reimaginedQuantum'])
