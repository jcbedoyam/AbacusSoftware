from cx_Freeze import setup, Executable
import sys

# Dependencies are automatically detected, but it might need
# fine tuning.
buildOptions = dict(packages = ['numpy.core._methods', 'numpy.lib.format'], excludes = [], include_files = '/home/juan/.anaconda3/lib/libmkl_avx.so')

base = 'Win32GUI' if sys.platform=='win32' else None

executables = [
    Executable('main.py', base=base, targetName = 'Quantum', icon="GUI/icon.ico")
]

setup(name='Quantum',
      version = '2.0',
      description = 'Quantum Physics',
      author = 'Juan Barbosa',
      author_email = 'js.barbosa10@uniandes.edu.co',
      options = dict(build_exe = buildOptions),
      executables = executables)
