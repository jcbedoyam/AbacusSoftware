import abacusSoftware.constants as constants
import urllib.request

URL_VERSION = "https://raw.githubusercontent.com/Tausand-dev/AbacusSoftware/master/Software/constants.py"
TARGET_URL = "https://sourceforge.net/projects/quantum-temp/"

def versionstr(version):
    if "=" in version:
        version = version.split("=")[-1].replace('"', "").replace("'", "")
    version = version.split(".")
    return [int(v) for v in version]

def checkUpdate():
    try:
        with urllib.request.urlopen(URL_VERSION) as response:
           html = response.read().decode().split("\n")
           for line in html:
               if "__version__" in line:
                   url_version = versionstr(line)
                   break
    except Exception as e:
        url_version = 0

    current_version = versionstr(constants.__version__)
    n = min(len(url_version), len(current_version))

    for i in range(n):
        if url_version[i] > current_version[i]:
            return ".".join([str(v) for v in url_version])

    return None
