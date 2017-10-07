import os
import shutil
import fnmatch
from glob import glob
from zipfile import ZipFile, ZIP_DEFLATED


ZIPFILE = 'dist/AbacusSoftware/AbacusSoftware.zip'
IGNORE = ['_cffi_backend.pyd']

def get_files():
    matches = []
    for root, dirnames, filenames in os.walk('.'):
        root = root[1:]
        if len(root) > 0:
            root = root[1:]
        for filename in filenames:
            matches.append(os.path.join(root, filename))
    return matches

def makeFileList():
    oldwd = os.getcwd()
    os.chdir('dist/AbacusSoftware')
    files = get_files()
    os.chdir(oldwd)

    with open("fileList.py", "w") as filelist:
        filelist.write("filelist = [")
        for file_ in files:
            if not file_ in IGNORE:
                print("ADDING: %s"%file_)
                filelist.write("r'%s',\n"%file_)
        filelist.write("]")

def zipfile_():
    oldwd = os.getcwd()
    os.chdir('dist/AbacusSoftware')
    files = get_files()
    with ZipFile('AbacusSoftware.zip', 'w', compression=ZIP_DEFLATED) as zpf:
        for file_ in files:
            if not file_ in IGNORE:
                zpf.write(file_)
                print('Zipped: %s'%file_)

    os.chdir(oldwd)

os.system('pyinstaller mainGUI.spec')
makeFileList()
os.system('pyinstaller uninstaller.spec')
os.rename('dist/uninstaller.exe', 'dist/AbacusSoftware/uninstaller.exe')
zipfile_()
os.rename(ZIPFILE, 'AbacusSoftware.zip')
os.system('pyinstaller installer.spec')
os.rename('dist/AbacusInstaller.exe', 'AbacusInstaller.exe')
shutil.rmtree('build')
shutil.rmtree('dist')
shutil.rmtree('__pycache__')

os.rename('AbacusSoftware.zip', 'AbacusSoftware-win32-x86-1.0.01.zip')
