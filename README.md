# AbacusSoftware
Abacus Software is a suite of tools build to ensure your experience with Tausand's coincidence counters becomes simplified.

Written in Python3, pyAbacus relies on the following modules:

- pyqtgraph
- NumPy
- PyQt5
- pyserial


## Installation
`pyAbacus` can be installed using `pip` as: 
```
pip install abacusSoftware
```

Or from GitHub
```
pip install git+https://github.com/Tausand-dev/abacusSoftware.git
```

## Execute abacusSoftware
On a terminal or command prompt type
```
abacusSoftware
```

## For developers
### Creating a virtual environment
Run the following code to create a virtual environment called `.venv`
```
python -m venv .venv
```

#### Activate
- On Unix systems:
```
source .venv/bin/activate
```
- On Windows:
```
.venv\Scripts\activate
```

#### Deactivate
```
deactivate
```

### Installing packages
After the virtual environment has been activated, install required packages by using:
```
python -m pip install -r requirements.txt
```

### Freezing code
After activating the virtual environment
#### Windows
```
pyinstaller build.spec
```

After creating all the files and the `.exe`, build the installer with the Inno Wizard,
by double clicking `installer_builder.iss`

### MacOS
```
pyinstaller build_mac.spec
```

### Linux
```
pyinstaller build.spec
```

### Fixing pyinstaller:
https://github.com/pyinstaller/pyinstaller/commit/082078e30aff8f5b8f9a547191066d8b0f1dbb7e

https://github.com/pyinstaller/pyinstaller/commit/59a233013cf6cdc46a67f0d98a995ca65ba7613a
