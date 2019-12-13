# Standard Library
import os
import traceback

# Project
from wsn.parsers.cr6 import CR6Parser
from wsn.upload import ImportCommand, upload2pg, upload2ch


CONFIG = {
    'eton2': [upload2pg],
    'finseflux': [upload2ch],
    'mobileflux': [upload2ch],
}


class Command(ImportCommand):

    EXTENSION = '.dat'
    PARSER = CR6Parser
    SAFETY_TIME = 5 * 60 # 5 minutes

    def _handle_file(self, filepath, metadata, fields, rows):
        dirpath, filename = os.path.split(filepath)
        dirname = os.path.basename(dirpath)

        # Upload
        for upload_to in CONFIG.get(dirname, [upload2pg]):
            try:
                upload_to(dirname, metadata, fields, rows)
            except Exception:
                self.stderr.write(f"{filepath} ERROR")
                traceback.print_exc(file=self.stderr)
                return

        # Archive file
        self.stdout.write(f"{filepath} file uploaded")
        self.archive(filepath)
        self.stdout.write(f"{filepath} file archived")
