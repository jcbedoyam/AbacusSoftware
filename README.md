# AbacusSoftware

## Getting windows ready
### Anaconda:
#### Installing environment:
```
conda create -n abacusenv python=3.4.5
activate abacusenv
```
#### Dependencies
```
conda install -c anaconda pywin32
pip install pyserial pyqtgraph pyinstaller
conda install pyqt
```
### Fixing pyinstaller:
https://github.com/pyinstaller/pyinstaller/commit/082078e30aff8f5b8f9a547191066d8b0f1dbb7e

https://github.com/pyinstaller/pyinstaller/commit/59a233013cf6cdc46a67f0d98a995ca65ba7613a
