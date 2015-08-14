import os
import sys


class Config(object):

    def __init__(self, cfg_file):
        self.hdf5_path = "."
        self.hdf5_lock_path = "/tmp"

        self.max_pts = 720

        self.log_file       = False
        self.log_file_name  = './pd.log'
        self.log_file_level = 1

        self.log_console       = False
        self.log_console_level = 1

        self.log_syslog         = False
        self.log_syslog_address = '/dev/log'
        self.log_syslog_level   = 1

        if cfg_file is not None:
            self.load(cfg_file)

    def load(self, fname):
        err_msg = ""

        if os.path.isfile(fname):
            fp = open(fname)

            for (i, line) in enumerate(fp):
                line = line.strip()
                if ("=" in line) and (not line.startswith("#")):
                    pos = line.find("=")

                    name = line[:pos].strip()
                    value = line[pos + 1:].strip()

                    if name not in self.__dict__.keys():
                        try:
                            self.__dict__[name] = eval(value)
                        except SyntaxError:
                            err_msg = "Syntax error on config file '%s'\nline %d: %s." % (fname, i, value)

                    else:
                        err_msg = "Unknown config key '%s'." % name
        else:
            err_msg = "Config file '%s' not found." % fname

        if err_msg != "":                   # pragma: no branch
            sys.stderr.write("\n%s\nCan't continue. Quitting...\n\n" % err_msg)
            quit()
