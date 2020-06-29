import os

from setuptools import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name="abacusSoftware",
    version="1.4.0",
    author="Juan Barbosa",
    author_email="js.barbosa10@uniandes.edu.co",
    maintainer="David Guzman",
    maintainer_email="da.guzman@outlook.com",
    description=(
        "Abacus Software is a suite of tools build to ensure your experience with Tausand's coincidence counters becomes simplified."),
    license="GPL",
    keywords="example documentation tutorial",
    url="https://github.com/Tausand-dev/AbacusSoftware",
    packages=['abacusSoftware'],
    install_requires=['pyAbacus>=1.1', 'pyserial', 'numpy', 'pyqtgraph', 'PyQt5', 'qdarkstyle'],
    long_description="",
    entry_points={
        'console_scripts': [
            'abacusSoftware = abacusSoftware.main:run',
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Topic :: Utilities",
        "License :: OSI Approved :: GNU General Public License (GPL)",
    ],
)
