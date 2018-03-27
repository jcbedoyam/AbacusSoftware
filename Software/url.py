import constants
import urllib.request

URL_VERSION = "https://raw.githubusercontent.com/Tausand-dev/AbacusSoftware/master/Software/constants.py"
TARGET_URL = "https://sourceforge.net/projects/quantum-temp/"

def versionstr(version):
    return version.replace(".", "")

def checkUpdate():
    try:
        with urllib.request.urlopen(URL_VERSION) as response:
           html = response.read().decode().split("\n")
           for line in html:
               if "__version__" in line:
                   line = versionstr(line)
                   exec(line)
                   break
        url_version = int(__version__)
    except Exception as e:
        url_version = 0

    current_version = int(versionstr(constants.__version__))

    if url_version > current_version:
        return __version__
    else:
        return None
