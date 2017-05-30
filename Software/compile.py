import os
import shutil
import fnmatch
from glob import glob
from zipfile import ZipFile


ZIPFILE = 'dist/Quantum/Quantum.zip'

def get_files():
    matches = []
    for root, dirnames, filenames in os.walk('.'):
        root = root[1:]
        if len(root) > 0:
            root = root[1:]
        for filename in filenames:
            matches.append(os.path.join(root, filename))
    return matches

def zipfile_():
    oldwd = os.getcwd()
    os.chdir('dist/Quantum')
    files = get_files()
    with ZipFile('Quantum.zip', 'w') as zpf:
        for file_ in files:
            zpf.write(file_)
            print('Zipped: %s'%file_)
    os.chdir(oldwd)

os.system('pyinstaller mainGUI.spec')
zipfile_()
os.rename(ZIPFILE, 'Quantum.zip')
os.system('pyinstaller installer.spec')
os.rename('dist/QuantumInstaller.exe', 'QuantumInstaller.exe')
shutil.rmtree('build')
shutil.rmtree('dist')
shutil.rmtree('__pycache__')
os.remove('Quantum.zip')
