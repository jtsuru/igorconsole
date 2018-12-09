import configparser
import os

CODEPAGE = 0
config = configparser.ConfigParser()
PATH, _ = os.path.split(__file__)
config.read(PATH + "/config.ini")
APPEND_SWITCH = int(config["Wave"]["append_switch_length1"])
COMMAND_MAXLEN = int(config["Command"]["max_length"])
del config, _
HOME_DIR = os.path.expanduser("~")

__all__ = ["CODEPAGE", "PATH", "HOME_DIR", "APPEND_SWITCH", "COMMAND_MAXLEN"]
