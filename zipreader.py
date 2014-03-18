import cStringIO
import zipfile

class ZipReader(object):
    def __init__(self, archive_name):
        archive=zipfile.ZipFile(archive_name, "r")
        self.files={}
        for name in archive.infolist():
            self.files[name.filename]=cStringIO.StringIO(archive.read(name))
