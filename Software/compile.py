import os
from glob import glob
from zipfile import ZipFile
import shutil

def zipfile_():
    files = glob('dist/Quantum/*')
    with ZipFile('Quantum.zip', 'w') as zpf:
        for file_ in files:
            zpf.write(file_)
os.system('pyinstaller mainGUI.spec')
zipfile_()
os.system('pyinstaller installer.spec')
os.move('dist/QuantumInstaller.exe', 'QuantumInstaller.exe')
shutil.rmtree('/build')
shutil.rmtree('/dist')
os.remove('Quantum.zip')
