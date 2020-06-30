import abacusSoftware.constants as constants
import urllib.request

URL_VERSION = "https://raw.githubusercontent.com/Tausand-dev/AbacusSoftware/master/lastStableVersion.md"
TARGET_URL = "https://www.tausand.com/downloads/"

def versionstr(version):
    if "=" in version:
        version = version.split("=")[-1].replace('"', "").replace("'", "")
    version = version.split(".")
    return [int(v) for v in version]

def checkUpdate():
    try:
        with urllib.request.urlopen(URL_VERSION) as response:
           html = response.read().decode()
           url_version = versionstr(html)
    except Exception as e:
        url_version = [0]

    current_version = versionstr(constants.__version__)
    n = min(len(url_version), len(current_version))
    
    for i in range(n):
        if url_version[i] > current_version[i]:
            return ".".join([str(v) for v in url_version])
        elif url_version[i] < current_version[i]: #corrected on v1.4.0 (2020-06-29)
            return None  #if current_version is greater than url_version, do not update

    return None
