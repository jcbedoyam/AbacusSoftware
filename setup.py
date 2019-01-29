import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "abacusSoftware",
    version = "1.2.5",
    author = "Juan Barbosa",
    author_email = "js.barbosa10@uniandes.edu.co",
    description = ("Abacus Software is a suite of tools build to ensure your experience with Tausand's coincidence counters becomes simplified."),
    license = "GPL",
    keywords = "example documentation tutorial",
    url = "https://github.com/Tausand-dev/ReimaginedQuantum",
    packages=['abacusSoftware'],
    install_requires = ['pyAbacus', 'pyserial', 'numpy', 'pyqtgraph', 'PyQt5', 'qdarkstyle'],
    long_description = "",#read('README'),
    classifiers = [
        "Development Status :: 1 - Planning",
        "Topic :: Utilities",
        "License :: OSI Approved :: GNU General Public License (GPL)",
    ],
)
