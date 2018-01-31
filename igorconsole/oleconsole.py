
"""Objective Igor COM-connection wrapper classes.

Todo:
    * Make table classes
"""
import configparser
import datetime
import itertools
import json
import logging
import os
import pkgutil
import re
import sys
import tempfile
import time
import warnings

from abc import ABC, abstractclassmethod
from collections import abc as c_abc


import numpy as np

logger = logging.getLogger(__name__)

import pythoncom
from pythoncom import com_error
import win32com.client

from . import comutils
from . import oleconsts as csts
from . import utils

CODEPAGE = 0
dtypedict = {
    0x02: np.float32,
    0x01 | 0x02: np.complex64,
    0x04: np.float64,
    0x01 | 0x04: np.complex128,
    0x08: np.int8,
    0x10: np.int16,
    0x20: np.int32,
    0x48: np.uint8,
    0x50: np.uint16,
    0x60: np.uint32,
    0x00: str
}
dtypedict.update({v:k for k, v in dtypedict.items()})
config = configparser.ConfigParser()
PATH, _ = os.path.split(__file__)
config.read(PATH + "/config.ini")
APPEND_SWITCH = int(config["Wave"]["append_switch_length1"])
COMMAND_MAXLEN = int(config["Command"]["max_length"])
del config, _
HOME_DIR = os.path.expanduser("~")

def object_type(obj):
    if not isinstance(obj, win32com.client.CDispatch):
        return type(obj)
    if not hasattr(obj, "_username_"):
        raise TypeError()
    if obj._username_ != "<unknown>":
        return obj._username_
    if hasattr(obj, "Wave"):
        return "DataFolder"
    if hasattr(obj, "GetScaling"):
        return "Wave"
    if hasattr(obj, "Execute"):
        return "Application"
    if hasattr(obj, "DataFolderExists"):
        return "DataFolders"
    elif hasattr(obj, "WaveExists"):
        return "Waves"
    elif hasattr(obj, "VariableExists"):
        return "Variables"
    elif hasattr(obj, "DataType"):
        return "Variable"
    raise TypeError()



class IgorApp:
    "Managing connection to igor and sending message."

    def __init__(self):
        self.reference = None
        self._version = None

    @classmethod
    def run(cls, visible=True):
        """Run a new igor instance and connect.
        Params:
            visible (bool): set if show igor  window or not.
        Returns:
            IgorApp: igor control instance.
        Exceptions:
            com_error: When the com is not added to the registory.
        """
        result = IgorApp()
        com = win32com.client.Dispatch("IgorPro.Application")
        com.Visible = visible
        result.reference = com
        if 7.0 <= result.version < 7.07:
            # to prevent crashing
            time.sleep(5)
        result.write_history('* Started from igorconsole.\n')

        return result

    @classmethod
    def connect(cls, visible=True):
        """Connect to an existing igor instance.
        Params:
            visible (bool): set if show igor window or not.
        Returns:
            IgorApp: igor control instance.
        Exceptions:
            com_error: When igor instance was not found,
                or when the com is not added to the registory.
        """
        result = IgorApp()
        com = win32com.client.GetActiveObject("IgorPro.Application")
        com.Visible = visible
        result.reference = com
        if 7.0 <= result.version < 7.07:
            # to prevent crashing
            time.sleep(5)
        result.write_history('* Connected from igorconsole.\n')

        return result

    @classmethod
    def start(cls, visible=True):
        """Connecting to the igor instance if exists, else make a new instance.
        Params:
            visible (bool): set if show igor  window or not.
        Returns:
            IgorApp: igor control instance.
        Exceptions:
            com_error: When the com is not added to the registory.
        """
        try:
            return cls.connect(visible=visible)
        except com_error:
            return cls.run(visible=visible)

    def show(self):
        """Make igor window visible."""
        self.reference.Visible = True

    def hide(self):
        """Make igor window invisible."""
        self.reference.Visible = False

    """
    Igor API wrapper methods
    """
    @property
    def get_application(self):
        """Reference to the com instance"""
        return self.reference.Application()

    def execute(self, command, logged=False):
        """Execute igor raw command.
        Args:
            command (str): command. The limit length is 400 chrs.
            logged (bool): if enabled, the command is logged in the igor history.
        Returns:
            histories (list of str): Output of the igor in the history area.
            results (list of str): Any strs created by sprintf.
        """
        errcode, errmsg, history, result = self.reference.Execute2(not logged, False, command)
        if errcode:
            raise RuntimeError("Igor execute error " + str(errcode) + ": " + errmsg)

        history = history.split("\r")
        result = result.split("\r")

        return ([i.strip() for i in history][:-1], [i.strip() for i in result])

    def get_value(self, *values, logged=False):
        """Get a value evaluated in igor.
        Params:
            values (str): igor command.
            logged (bool): leave a command in the history area.
        Returns:
            int, float, or str: Evaluated value.
        Examples:
            import igorconsole; import numpy as np
            igor = igorconsole.start()
            igor.get_value("1+1") -> 2.0
            igor.get_value("4 * sin(pi/2)") -> 4.0

            igor.root.linear = np.arange(100) # make a new int wave at root:linear
            igor.get_value("linear[3]") -> 3.0 # get as a float
            igor.root.linear[3] -> 3 # check
        """
        def convert(val):
            try:
                return int(val[0])
            except ValueError:
                pass
            try:
                return float(val[0])
            except ValueError:
                return result[0]

        returnvalue = []
        for value in values:
            try:
                history, result = self.execute('fprintf 0, \"%.16f\" {0}'.format(value))
            except:
                history, result = self.execute('fprintf 0, ' + value)
            else:
                returnvalue.append(convert(result))

        if len(returnvalue) == 1:
            return returnvalue[0]
        else:
            return tuple(returnvalue)

    @property
    def fullpath(self):
        "Path of the igor program."
        return self.reference.FullName

    @property
    def name(self):
        """Name of the instance
        Returns:
            str: 'Igor Pro'
        """
        return self.reference.Name

    @property
    def is_visible(self):
        return self.reference.Visible

    def status1(self, int_):
        return self.reference.Status1(int_)

    @property
    def version(self):
        """Version of the igor
        Returns:
            float: version
        """
        if self._version is None:
            self._version = self.status1(csts.Status.IgorVersion)
        return self._version

    @property
    def is_procedure_running(self):
        "Returns True if a user procedure is running."
        return bool(self.status1(csts.Status.RunningProcedure))

    @property
    def is_que_empty(self):
        return bool(self.status1(csts.Status.OperationQueueIsEmpty))

    @property
    def is_pause_for_user(self):
        return bool(self.status1(csts.Status.PauseForUser))

    @property
    def is_experiment_modified(self):
        return bool(self.status1(csts.Status.ExperimentModified))

    @property
    def is_experiment_never_saved(self):
        return bool(self.status1(csts.Status.ExperimentNeverSaved))

    @property
    def is_procedures_compiled(self):
        return bool(self.status1(csts.Status.ProceduresCompiled))

    def write_history(self, text, norm_newline_chr=True):
        """Send text to the history.
        Params:
            text (str): texts to send.
        """
        if norm_newline_chr:
            text = text.replace("\r\n", "\n").replace("\r", "\n")\
                   .replace("\n", "\r\n")
        self.reference.SendToHistory(CODEPAGE, text)
    
    def print(self, *objects, sep=" ", end="\n"):
        write = self.write_history
        firstline = True
        for item in objects:
            if firstline:
                firstline = False
            else:
                write(sep)
            write(str(item))
        write(end)


    def new_experiment(self, only_when_saved=True):
        """ Create a new experiment file.
        Params:
            only_when_saved (bool): check current experiment file is saved.
                No alert/dialog will be appeared when disabled.
        """
        if only_when_saved and self.is_experiment_modified:
            warnings.warn("This file is not saved."
                          + "Please make 'True' only_when_saved flag.")
            return None
        self.reference.NewExperiment(0)

    def new_experiment_wo_save(self):
        """ Create a new experiment file.
        No alert/dialog will be appeared even if the current experiment file has not benn saved.
        """
        self.new_experiment(only_when_saved=False)


    def load_experiment(self, filepath, loadtype=csts.LoadType.Open):
        self.reference.LoadExperiment(0, loadtype, "", filepath)

    def load_experiment_as_newfile(self, filepath):
        self.load_experiment(filepath, loadtype=csts.LoadType.Stationery)

    def merge_experiment(self, filepath):
        self.load_experiment(filepath, loadtype=csts.LoadType.Merge)

    def _save(self, filepath, savetype=csts.SaveType.Save,
              filetype=csts.ExpFileType.Default, symbolicpathname=""):
        self.reference.SaveExperiment(0, savetype, filetype,
                                         symbolicpathname, filepath)

    def save(self, filepath="", filetype=csts.ExpFileType.Default):
        "Save and overwrite the current experiment file."
        self._save(filepath, savetype=csts.SaveType.Save, filetype=filetype)

    def save_as(self, filepath, filetype=csts.ExpFileType.Default,
                symbolicpathname="", overwrite=False):
        """Save the current project as a new experiment file.
        Params:
            filepath (str): save destimation.
            filetype (int): experiment file type.
                -1: Devault
                 0: Unpacked
                 1: Packed

        """
        if (not overwrite) and os.path.exists(filepath):
            raise FileExistsError
        self._save(filepath, savetype=csts.SaveType.SaveAs,
                   filetype=filetype, symbolicpathname=symbolicpathname)

    def save_copy(self, filepath, filetype=csts.ExpFileType.Default,
                  symbolicpathname="", overwrite=False):
        if (not overwrite) and os.path.exists(filepath):
            raise FileExistsError
        self._save(filepath, savetype=csts.SaveType.SaveCopy,
                   filetype=filetype, symbolicpathname=symbolicpathname)

    def open_file(self, filepath, filekind="procedure",
                  readonly=False, invisible=False, symbolicpathname=""):
        readonly = csts.OpenFile.ReadOnly if readonly else 0b00
        invisible = csts.OpenFile.Invisible if invisible else 0b00
        opentype = readonly | invisible

        if filekind.lower() == "notebook":
            filekind = csts.FileKind.Notebook
        elif filekind.lower() == "procedure":
            filekind = csts.FileKind.Procedure
        elif filekind.lower() == "help":
            filekind = csts.FileKind.Help

        self.reference.OpenFile(opentype, filekind, symbolicpathname, filepath)

    def quit(self, only_when_saved=True):
        if only_when_saved and self.is_experiment_modified:
            warnings.warn("This file is not saved."
                          + "Please make 'True' only_when_saved flag.")
            return None
        if self.version < 7.0:
            self.reference.Quit()
        else:
            wmi = win32com.client.GetObject("winmgmts:")
            number_of_igor_instance = lambda: len([item for item in wmi.InstancesOf("Win32_Process")
                if item.Properties_("Name").Value == "Igor.exe"])
            initial_instance_num = number_of_igor_instance()
            self.reference.Quit()
            while number_of_igor_instance() >= initial_instance_num > 0:
                time.sleep(0)


    def quite_wo_save(self):
        self.quit(only_when_saved=False)

    @property
    def data(self):
        return Folder("root:", self)

    root = data

    @property
    def cwd(self):
        cwd_path = self.execute("fprintf 0, getdatafolder(1)")[1][0]
        return Folder(cwd_path, self)

    def window_names(self, wintype):
        return self.execute(r'fprintf 0, winlist("*", ";", "win:'
                            + str(wintype) + r'")')[1][0].split(";")[:-1]

    @property
    def graphs(self):
        return [Graph(item, self) for item in self.window_names(csts.WindowType.Graph)]

    @property
    def tables(self):
        return [Table(item, self) for item  in self.window_names(csts.WindowType.Table)]

    @property
    def layouts(self):
        return [Layout(item, self) for item in  self.window_names(csts.WindowType.Layout)]

    @property
    def panels(self):
        return [Panel(item, self) for item in self.window_names(csts.WindowType.Panel)]
    def display(self, ywaves, xwave=None, *,
                winname=None, title=None, yaxis=None, xaxis=None,
                frame=None, hide=False, host=None, win_location=None,
                unit=None, win_behavior=0, category_plot=False,
                inset_frame=None, vertical=False, overwrite=False):
        """ Make a graph on igor. Call Display command in igor
        Params:
            ywaves (Wave, or list, tuple of Waves): wave(s) of y-axis data.
            xwave (Wave, optional): wave of x-axis data.
            winname (str, optional): unique name to identify the graph. (/N flag.)
            title (str, optional): non-unique title of the graph, to show on igor pro.
            yaxis (str, optional): specify the y-axis. See also the note section.
            xaxis (str, optional): specify the x-axis. See also the note section.
            frame (tuple of numerics, optional): the position of frame. (/FG=(left, top, right, bottom) flag.)
            hide (bool, optional): hides the graph window. Default false. (/HIDE flag.)
            host (Window, optional): specify the window to make a graph. (/HOST flag.)
            win_location (tuple of numerics, optional): the position of graph window. (/W flag.)
            unit (str, optional): "cm" or "inch" as a potision of win_location.
            win_behavior (int, optional): set the behavior when you try to close the window.
                See also the Note section. (/K flag.)
            category_plot (bool, optional): make a category plot in igor pro 6.37 or later. (/NCAT flag.)
            inset_frame (tuple, optional): (/PG flag.)
            vertical (optional): defualt false. (/VERT flag.)
            overwrite (bool optional): overwrite the graph if winname is duplicated. defualt false.

        Note:
            - How to specify the x- and y-axis
                left axis (default): "L" or ("L", None)
                right axis: "R" or ("R", None)
                bottom axis (default): "B" or ("B", None)
                top axis: "T" or (T, None)
                the second right axis named y2: ("R", "y2")
            - How to set win_behavior
                0: show dialog
                1: close the graph without any dialog
                2: you cannot close the window
                3: hides the window
        """
        def yaxis_to_tuple(axis):
            if isinstance(axis, tuple):
                return axis
            if isinstance(axis, str):
                if axis.lower() == "l":
                    return ("l", None)
                elif axis.lower() == "r":
                    return ("r", None)
                else:
                    return ("l", axis)

        def xaxis_to_tuple(axis):
            if isinstance(axis, tuple):
                return axis
            if isinstance(axis, str):
                if axis.lower() == "b":
                    return ("b", None)
                elif axis.lower() == "t":
                    return ("t", None)
                else:
                    return ("b", axis)


        command = ""
        if winname is None:
            winname = datetime.datetime.now().strftime("icg_%Y%m%d%H%M%S%f")

        winname_is_already_exists = bool(self.get_value('WinType("{0}")'.format(winname)))
        if overwrite:
            command += "DoWindow/K {};".format(winname)
        elif winname_is_already_exists:
            raise RuntimeError("Graph already exists")
        command += "Display"
        if xaxis is not None:
            command += "/{0}={1}".format(*xaxis_to_tuple(xaxis))
        if frame is not None:
            command += "/FG=({0}, {1}, {2}, {3})".format(*frame)
        command += "/HIDE={0}".format(int(hide))
        if host is not None:
            command += "/HOST={0}".format(host.name)
        if unit is not None:
            if unit.lower() == "inch":
                command += "/I"
            if unit.lower() == "cm":
                command += "/M"
        command += "/K={}".format(win_behavior)
        if yaxis is not None:
            command += "/{0}={1}".format(*yaxis_to_tuple(yaxis))
        command += "/N={}".format(winname)
        if self.version > 6.36 and category_plot:
            command += "/NCAT"
        if inset_frame is not None:
            command += "/PG=({0}, {1}, {2}, {3})".format(*inset_frame)
        if vertical:
            command += "/VERT"
        if win_location is not None:
            command += "/W=({0}, {1}, {2}, {3})".format(*win_location)

        command += " "
        if isinstance(ywaves, Wave):
            ywaves = [ywaves]
        for i, ywave in enumerate(ywaves):
            if i != 0:
                command += ", "
            command += ywave.quoted_path
        if xwave is not None:
            command += " vs {}".format(xwave.quoted_path)
        if title is not None:
            command += ' as "{}"'.format(title)
        # Since the graph name cannot be duplicated with the name of the wave
        # in the current directory, an empty folder is firstlly created and
        # the graph will be created in the folder.
        commands = command.split(";")
        with TempFolder(self):
            while commands:
                oneline = ""
                while commands and len(oneline) < 300:
                    oneline += commands.pop() +";"
                self.execute(oneline)
        return Graph(winname, self)

    def _newpath(self, path: str):
        path = path.replace("\\", ":").replace("/", ":") + ":"
        path = path.replace("::", ":")
        self.execute('NewPath/O/C igorconsole_path "{}"'.format(path))

    def append_to_waves(self, waves, vals):
        wave_paths = np.array([w.quoted_path for w in waves])
        shapes = [w.shape for w in waves]
        lengths = [0 if not s else s[0] for s in shapes]
        length_set = set(lengths)
        lengths = np.array(lengths)
        commands = []
        apd = commands.append
        command_oneline = "" #command, whose length is limited to 400 chrs.
        # send command: InsertPoints {length},1,wave1,wave2,wave3,...;
        # if it is too long,
        # InsertPoints {length},1,wave1,wave2;
        # InsertPoints {length},1,wave3,wave4...;
        for l_set in length_set:
            #select waves whose {length} are the same. 
            waves_to_append = wave_paths[lengths == l_set]
            str_insert_points = "InsertPoints {},1".format(l_set)
            command_buff = str_insert_points
            for wave_path in waves_to_append:
                toappend = "," + wave_path
                logger.debug("lset: {}".format(l_set))
                logger.debug("command_oneline: {}".format(command_oneline))
                logger.debug("command_buff: {}".format(command_buff))
                logger.debug("toappend: {}".format(toappend))
                if len(command_oneline + command_buff + toappend) < COMMAND_MAXLEN:
                    #On the first cycle, when the previous command is
                    #{previous command;}
                    #length of:
                    #{previous command;} InsertPoints{length},1,wave1
                    # is shorter than 400
                    #{previous command;} + InsertPoints{length},1,wave1
                    #
                    #On the second cycle
                    #{previouscommand;InsertPoints{length},1,wave1} + ,wave2
                    logger.debug("route:1")
                    command_buff += toappend
                elif len(command_buff + toappend) < COMMAND_MAXLEN:
                    #When: {previous command;} InsertPoints{length},1,wave1
                    #exceeds the limit length.
                    #send previous command to the list.
                    logger.debug("route:2")
                    if not command_oneline:
                        pass
                    elif command_oneline.endswith(";"):
                        apd(command_oneline)
                    else:
                        apd(command_oneline + ";")
                    command_oneline = command_buff + toappend + ";"
                    command_buff = str_insert_points
                else:
                    #when len(command_buff + toappend) >= 400, but assuming
                    #len(toappend) < 400
                    #when len(toappend) >= 400 or (actually >= 1000)
                    #an exception raised.
                    logger.debug("route:3")
                    if not command_oneline:
                        pass
                    elif command_oneline.endswith(";"):
                        apd(command_oneline)
                        command_oneline = ""
                    else:
                        apd(command_oneline + ";")
                        command_oneline = ""
                    if command_buff.endswith(",1"):
                        apd(command_buff + toappend + ";")
                        command_buff = str_insert_points
                    else:
                        apd(command_buff + ";")
                        command_buff = str_insert_points + toappend
            if command_buff.endswith(",1"):
                command_buff = ""#本当は不必要
            else:
                command_oneline += command_buff
                command_buff = ""#本当は不必要
            if command_oneline and not command_oneline.endswith(";"):
                command_oneline += ";"
        if not command_oneline.endswith(",1;"):
            apd(command_oneline)
        for command in commands:
            logger.debug("command {0}: {1}".format(len(command), command))
            self.execute(command)
        for wv, v in zip(waves, vals):
            wv[-1] = v

    def wave(self, path:str):
        return Wave(path, self)

    def folder(self, path:str):
        return Folder(path, self)

    def variable(self, path:str):
        return Variable(path, self)


class IgorObjectBase(ABC):
    def _path(self, relative=False, quoted=False):
        return self.reference.Path(relative, quoted)

    @property
    def path(self):
        return self._path(relative=False, quoted=False)

    @property
    def quoted_path(self):
        return self._path(relative=False, quoted=True)

    @property
    def name(self):
        return self.reference.Name

    @property
    def parent(self):
        return Folder(self.reference.ParentDataFolder, self.app, input_check=False)

    @property
    def _parent_path(self):
        path = self.path
        return path[0 : path.rfind(":", 0, -1)+1]


# 代入演算子オーバーロードの影響でクラス内に代入できなので注意。
#attributeを増やすにはsetattrメソッドを使うこと。
class Folder(IgorObjectBase):
    def __init__(self, reference, app, *, input_check=True):
        set_ = lambda i, p: self.setattr(i, p)
        set_("app", app)
        if isinstance(reference, str):
            reference = app.reference.DataFolder(reference)
        elif (not input_check) or object_type(reference) == "DataFolder":
            pass
        else:
            raise TypeError("reference is not a DataFolder")
        set_("reference", reference)

    @property
    def is_inuse(self):
        return self.reference.InUse

    @property
    def _data_folders_ref(self):
        return self.app.reference.DataFolders(self.path)

    def __repr__(self):
        return "<igorconsole.Folder at: {}>".format(self.path)

    def __str__(self):
        return "Igor Folder: {}".format(self.path)

    def setattr(self, item, val):
        object.__setattr__(self, item, val)

    def __getattr__(self, key):
        if key in dir(self):
            raise AttributeError()
        if key in self:
            return self.__getitem__(key)
        raise AttributeError()

    def __setattr__(self, item, val):
        if item in self.subfolders:
            raise KeyError(item + " is already exists as a folder.")
        if item in dir(self):
            raise warnings.warn(item
                                + " will be screened by the class atribute. "
                                + "Use dictionary expression (folder[key]) to acccess.",
                                UserWarning)
        self.__setitem__(item, val)

    def __getitem__(self, key):
        temp = self.subfolders
        if key in temp:
            return temp[key]

        temp = self.variables
        if key in temp:
            return temp[key]

        temp = self.waves
        if key in temp:#バグのせいで遅い。
            return temp[key]

        if not isinstance(key, str):
            raise TypeError("key should be a string.")
        raise KeyError("Object {} not found.".format(key))

    def from_dict(self, dict_like, overwrite=False):
        waves = self.waves
        variables = self.variables
        for key, value in dict_like.items():
            if isinstance(value, str) or (not hasattr(value, "__len__")):
                variables.add(str(key), value, overwrite=overwrite)
            elif hasattr(value, "__iter__") and hasattr(value, "__getitem__"):
                waves.add(str(key), value, overwrite=overwrite)

    def __setitem__(self, key, val):
        if isinstance(val, str) or (not hasattr(val, "__len__")):
            self.make_variable(key, val)
        elif isinstance(val, Wave):
            self.app.execute("Duplicate/O {0} {1}'{2}'")\
            .format(val.quoted_path, self.quoted_path, key)
        elif isinstance(val, dict) or isinstance(val, c_abc.Mapping):
            self.make_folder(key, overwrite=True)
            f = self.subfolders[key]
            f.from_dict(val)
        elif str(val.__class__) == "<class 'pandas.core.frame.DataFrame'>":
            import pandas as pd
            if isinstance(val, pd.DataFrame):
                self.make_folder(key, overwrite=True)
                f = self.subfolders[key]
                for column in val.columns:
                    f[str(column)] = val[column]
        elif hasattr(val, "__iter__") and hasattr(val, "__getitem__"):
            self.make_wave(key, val)
        else:
            raise ValueError()

    def __contains__(self, name):
        ref = self.reference
        result = self._data_folders_ref.DataFolderExists(name)\
                 or ref.WaveExists(name)\
                 or ref.VariableExists(name)
        return result

    @property
    def subfolders(self):
        return FolderCollection(self.reference.SubDataFolders, self.app)

    @property
    def waves(self):
        return WaveCollection(self.reference.Waves, self.app, self)

    @property
    def variables(self):
        return VariableCollection(self.reference.Variables, self.app)


    def make_folder(self, name, overwrite=False):
        return self.subfolders.add(name, overwrite)

    def make_wave(self, name, array_like=None, shape=None, overwrite=True, dtype=None):
        return self.waves.add(name, array_like, shape=shape, overwrite=overwrite, dtype=dtype)

    def make_variable(self, name, value, overwrite=True):
        return self.variables.add(name, value, overwrite=overwrite)

    def show(self, print_=True):
        result = []
        result.append("Subfolders:")

        for i, folder in enumerate(self.subfolders.keys()):
            result.append("  subfolders {0}: {1}".format(i, folder))

        result.append("Waves:")
        for i, wave in enumerate(self.waves.keys()):
            result.append("  waves {0}: {1}".format(i, wave))

        result.append("Variables:")
        for i, val in enumerate(self.variables.keys()):
            result.append("  variables {0}: {1}".format(i, val))

        if print_:
            print("\n".join(result))
        else:
            return "\n".join(result)

    def chdir(self):
        self.app.execute("cd {}".format(self.quoted_path), logged=False)

    def delete_folder(self, target):
        self._data_folders_ref.Remove(target)

    def delete(self):
        set_ = lambda i, p: self.setattr(i, p)
        parent = self.parent
        name = self.path.split(":")[-2]

        set_("reference", None)
        parent.delete_folder(name)
    
    f = subfolders

    w = waves

    v = variables

class TempFolder(Folder):
    def __init__(self, app, name=None):
        super().__init__(None, app, input_check=False)
        if name is None:
            #ここで作ったnameは被らないと信じる。
            name = datetime.datetime.now().strftime("__ictmp_%Y%m%d%H%M%S%f")
        self.setattr("_tmpfname", name)

    def __enter__(self):
        self.setattr("current_dir", self.app.cwd)
        #このメソッドはFolders.add内で使用しているので、一次フォルダ作成にはAPIを直接呼ぶこと。
        overwrite = True
        newf = self.app.reference.DataFolders("root:").Add(self._tmpfname, overwrite)
        super().setattr("reference", newf)
        super().chdir()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.current_dir.chdir()
        super().delete()

class Variable(IgorObjectBase):
    def __init__(self, reference, app, *, input_check=True):
        self.app = app
        if isinstance(reference, str):
            path = reference.replace("'", "")
            parent = ":".join(path.split(":")[:-1]) + ":"
            self.reference = app.reference.DataFolder(parent).Variable(path)
        elif (not input_check) or object_type(reference) == "Variable":
            self.reference = reference
        else:
            raise TypeError("reference is not a variable")


    @property
    def dtype(self):
        return dtypedict[self.reference.DataType]

    @property
    def value(self):
        dtype = self.dtype
        if dtype == np.complex128:
            return complex(*self.reference.GetNumericValue())
        if dtype == np.float64:
            return self.reference.GetNumericValue()[0]
        if dtype == str:
            return self.reference.GetStringValue(CODEPAGE)

    #def delete(self):
    #    parent = self.parent
    #    name = self.path.split(":")[-2]
    #    parent.variables.remove(name)
    #    set_("reference", None)
    #    parent.delete_folder(name)

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return str(self)

    def __eq__(self, obj):
        if isinstance(obj, Variable):
            return self.value == obj.value
        else:
            return self.value == obj

    def __complex__(self):
        return complex(self.value)

    def __float__(self):
        return float(self.value)

    # numeric operations
    def __add__(self, obj):
        if isinstance(obj, Variable):
            return self.value + obj.value
        else:
            return self.value + obj

    def __sub__(self, obj):
        if isinstance(obj, Variable):
            return self.value - obj.value
        else:
            return self.value - obj

    def __mul__(self, obj):
        if isinstance(obj, Variable):
            return self.value * obj.value
        else:
            return self.value * obj

    def __truediv__(self, obj):
        if isinstance(obj, Variable):
            return self.value / obj.value
        else:
            return self.value / obj

    def __floordiv__(self, obj):
        if isinstance(obj, Variable):
            return self.value // obj.value
        else:
            return self.value // obj

    def __mod__(self, obj):
        if isinstance(obj, Variable):
            return self.value % obj.value
        else:
            return self.value % obj

    def __divmod__(self, obj):
        return self // obj, self % obj

    def __pow__(self, obj):
        if isinstance(obj, Variable):
            return self.value ** obj.value
        else:
            return self.value ** obj

    #rite side operation
    def __radd__(self, obj):
        if isinstance(obj, Variable):
            return obj.value + self.value
        else:
            return obj + self.value

    def __rsub__(self, obj):
        if isinstance(obj, Variable):
            return obj.value - self.value
        else:
            return obj - self.value

    def __rmul__(self, obj):
        if isinstance(obj, Variable):
            return obj.value * self.value
        else:
            return obj * self.value

    def __rtruediv__(self, obj):
        if isinstance(obj, Variable):
            return obj.value / self.value
        else:
            return obj / self.value

    def __rfloordiv__(self, obj):
        if isinstance(obj, Variable):
            return obj.value // self.value
        else:
            return obj // self.value

    def __rmod__(self, obj):
        if isinstance(obj, Variable):
            return obj.value % self.value
        else:
            return obj % self.value

    def __rpow__(self, obj):
        if isinstance(obj, Variable):
            return obj.value ** self.value
        else:
            return obj ** self.value

class Lock(Variable):
    def __init__(self, app, *, timeout=60):
        super().__init__(None, app, input_check=False)
        self.__name = "ic__lock__"
        self.timeout = timeout

    def __enter__(self):
        overwrite = False
        current_time = time.monotonic
        init_time = current_time()
        while current_time() - init_time < self.timeout:
            try:
                newv = self.app.reference.DataFolder("root:")\
                       .Variables.Add(self.__name, dtypedict[np.float64], overwrite)
                break
            except com_error as e:
                err_msg = e.args[2][2]
                if err_msg == "name already exists as a variable (IVariables::Add)":
                    from random import uniform
                    time.sleep(uniform(1e-3, 20e-3))
                    logger.debug(e)
                else:
                    raise
        else:
            raise TimeoutError()
        self.reference = newv

    def __exit__(self, exc_type, exc_value, traceback):
        self.app.reference.DataFolder("root:")\
              .Variables.Remove(self.__name)


class Wave(IgorObjectBase):
    def __init__(self, reference, app, *, input_check=True):
        self.app = app
        self._length = None
        if isinstance(reference, str):
            path = reference.replace("'", "")
            parent = ":".join(path.split(":")[:-1]) + ":"
            self.reference = app.reference.DataFolder(parent).Wave(path)
        elif (not input_check) or object_type(reference) == "Wave":
            self.reference = reference
        else:
            raise TypeError("reference is not a Wave")

    @property
    def is_inuse(self):
        return self.reference.InUse

    @staticmethod
    def _unit_to_int(dimension):
        d = dimension
        dmatch = lambda exp: re.match(exp, dimension, re.IGNORECASE)
        if utils.isint(d):
            d = int(d)
        elif dmatch("rows?"):
            d = 0
        elif dmatch("columns?"):
            d = 1
        elif dmatch("layers?"):
            d = 2
        elif dmatch("chunks?"):
            d = 3
        elif d == "data":
            d = -1
        return d

    def get_unit(self, dimension=csts.WaveDimension.Data):
        dimension = Wave._unit_to_int(dimension)
        return self.reference.Units(dimension, CODEPAGE)

    def set_unit(self, unit, dimension=csts.WaveDimension.Data):
        dimension = Wave._unit_to_int(dimension)
        self.reference.SetUnits(dimension, CODEPAGE, unit)

    def get_scaling(self, dimension):
        dimension = Wave._unit_to_int(dimension)
        #the returned value order is different from the igor mannual.
        grad, init = self.reference.GetScaling(dimension)
        return init, grad

    def set_scaling(self, init, grad, dimension, type=0):
        if type == 0:
            self.reference.SetScaling(dimension, grad, init)

    def position(self, index):
        #vectorized
        index = np.asarray(index)
        dim = self.ndim
        grad = np.empty(dim)
        init = np.empty(dim)
        for i in range(dim):
            init[i], grad[i] = self.get_scaling(i)
        result = grad * index + init
        if index.ndim == 0:
            return result[0]
        else:
            return result

    @property
    def position_array(self):
        shape = self.shape
        ndim = len(shape)
        if ndim == 0:
            return np.array([])
        size = utils.prod(shape)
        index = np.stack(np.unravel_index(np.arange(size), shape), axis=1)
        result = self.position(index)
        if ndim == 1:
            result = result.reshape(*shape)
        else:
            result = result.reshape(*shape, ndim)
        return result

    parray = position_array

    def index(self, *position, return_type=round):
        def one_d(dimension, value):
            init, grad = self.get_scaling(dimension)
            return (value-init) / grad

        if len(position) == 1:
            return return_type(one_d(0, position[0]))
        else:
            return tuple(return_type(one_d(d, position))
                         for d, position in enumerate(position))

    @property
    def dtype(self):
        return dtypedict[self.reference.GetDimensions()[0]]

    @property
    def array(self):
        dtype = self.dtype
        if issubclass(dtype, np.complexfloating):
            return utils.from_igor_complex_wave_order(self._array(), dtype=dtype)
        else:
            return np.array(self._array(), dtype=dtype)

    @array.setter
    def array(self, obj):
        self.parent.make_wave(self.name, obj)

    def _array(self):
        return self.reference.GetNumericWaveData(dtypedict[self.dtype])

    def append(self, obj):
        length = self._length
        if (length is not None) and length > APPEND_SWITCH:
            self._append2(obj)
        else:
            self._append1(obj)

    def _append1(self, obj):
        obj = utils.to_list(obj)
        new_array = list(self._array())
        new_array += obj
        self._length = len(new_array)
        f = self.parent
        f.make_wave(self.name, new_array) 

    def _append2(self, obj):
        obj = utils.to_list(obj)
        length = len(self)
        command = "InsertPoints {0},{1},{2}"\
                  .format(length, len(obj), self.quoted_path)
        self.app.execute(command)
        for i, val in enumerate(obj):
            self.reference.SetNumericWavePointValue(length + i, val) 

    def to_Series(self, index="position"):
        import pandas as pd
        index = index.lower()
        if index == "position":
            indice = self.parray
        elif index == "points":
            indice = None
        else:
            indice = None
        return pd.Series(self.array.flatten(), index=indice)


    def resize(self, *shape):
        # 5.9 ms
        new_array = self.array
        new_array.reshape(*shape)
        f = self.parent
        f.make_wave(self.name, new_array)

    @property
    def ndim(self):
        # 75.8 us
        return len(self.shape)

    @property
    def shape(self):
        result = tuple(i for i in self.reference.GetDimensions()[1:] if i != 0)
        self._length = 0 if not result else result[0]
        return result

    @property
    def size(self):
        return utils.prod(self.shape)

    def __len__(self):
        shape = self.shape
        if shape:
            return shape[0]
        else:
            return 0

    def __getitem__(self, key):
        return self.array[key]

    def __setitem__(self, key, value):
        shape = self.shape
        length = shape[0] if shape else 0
        ndim = len(shape)
        if utils.isint(key) and ndim == 1 and utils.isreal(value):
            if key >= length:
                raise IndexError("Wave index out of range")
            elif key < -length:
                raise IndexError("Wave index out of range")
            else:
                self.reference.SetNumericWavePointValue(key%length, value)
        else:
            wv = self.array
            wv[key] = value
            self._length = len(wv)
            if issubclass(wv.dtype.type, np.complexfloating):
                wv = utils.to_igor_complex_wave_order(wv)
            array_dtype = wv.dtype.type
            variant_array = comutils.to_variant_array(wv)
            self.reference.SetNumericWaveData(dtypedict[array_dtype], variant_array)

    def __lt__(self, other):
        if isinstance(other, Wave):
            return self.array < other.array
        else:
            return self.array < other

    def __le__(self, other):
        if isinstance(other, Wave):
            return self.array <= other.array
        else:
            return self.array <= other

    def __eq__(self, other):
        if isinstance(other, Wave):
            return self.array == other.array
        else:
            return self.array == other

    def __gt__(self, other):
        if isinstance(other, Wave):
            return self.array > other.array
        else:
            return self.array > other

    def __ge__(self, other):
        if isinstance(other, Wave):
            return self.array >= other.array
        else:
            return self.array >= other

    def __add__(self, dest):
        if isinstance(dest, Wave):
            sv = self.array
            sv += dest.array
            return sv
        else:
            sv = self.array
            sv += dest
            return sv

    def __radd__(self, dest):
        return self.__add__(dest)

    def __mul__(self, dest):
        if isinstance(dest, Wave):
            sv = self.array
            sv *= dest.array
            return sv
        else:
            sv = self.array
            sv *= dest
            return sv

    def __rmul__(self, dest):
        return self.__mul__(dest)

    def __sub__(self, dest):
        return self.__add__(dest * -1)

    def __truediv__(self, dest):
        if isinstance(dest, Wave):
            sv = self.array
            sv /= dest.array
            return sv
        else:
            sv = self.array
            sv /= dest
            return sv

    def __rtruediv__(self, dest):
        return dest / self.array

    def __getattr__(self, key):
        if hasattr(np.ndarray, key):
            return self.array.__getattribute__(key)
        else:
            raise AttributeError()


class IgorObjectCollectionBase(ABC, c_abc.Mapping):
    def __init__(self, reference, app):
        self.reference = reference
        self.app = app

    def __getattr__(self, item):
        return self.__getitem__(item)

    def __len__(self):
        return self.reference.Count

    def __iter__(self):
        return (self[i] for i in range(len(self)))

    def __reversed__(self):
        return (self[i] for i in range(len(self)-1, -1, -1))

    def get(self, key):
        if utils.isint(key) and 0 <= key < len(self):
            return self[int(key)]
        if isinstance(key, str) and key in self:
            return self[key]
        return None

    @abstractclassmethod
    def copy(self):
        pass

    @abstractclassmethod
    def add(self, name, overwrite=False):
        pass

    #@property
    #def names(self):
    #    return (ref.Name for ref in self.reference)

    def keys(self):
        return {item.Name for item in self.reference}

    def items(self):
        return {(key, self[key]) for key in self.keys()}


    def values(self):
        return [self[key] for key in self.keys()]


class FolderCollection(IgorObjectCollectionBase):
    def __getitem__(self, key):
        """
        get folders by numeric index or by the folder name.
        """
        key = key if isinstance(key, str) else int(key)
        return Folder(self.reference(key), self.app, input_check=False)

    def __contains__(self, name):
        return self.reference.DataFolderExists(name)

    def add(self, name, overwrite=False):
        with TempFolder(self.app):
            return Folder(self.reference.Add(name, overwrite), self.app, input_check=False)

    def copy(self):
        return FolderCollection(self.reference, self.app)


class WaveCollection(IgorObjectCollectionBase):
    def __init__(self, reference, app, parent=None):
        super().__init__(reference, app)
        #相互参照を作らないように注意
        self.parent = parent

    def __getitem__(self, key):
        """
        get waves by numeric index or by the folder name.
        """
        key = key if isinstance(key, str) else int(key)
        return Wave(self.reference(key), self.app, input_check=False)

    def __contains__(self, name):
        #self.reference.WaveExists(name) has bug, and always returns False. (igor 6.37, igor 7.06)
        if self.parent is not None:
            return self.parent.reference.WaveExists(name)
        return name in self.names

    def add(self, name, array_like=None, *,
            shape=None, overwrite=True, dtype=None,
            keep_info=False):
        return self.add_numeric(name, array_like,
                                shape=shape, overwrite=overwrite,
                                dtype=dtype, keep_info=keep_info)

    def add_numeric(self, name, array_like=None, *,
                    shape=None, overwrite=True, dtype=None,
                    keep_info=True):
        if (array_like is None) and (shape is not None):
            dtype = np.float if dtype is None else dtype
            array_like = np.zeros(shape)
        elif array_like is None:
            array_like = []
        array = np.asarray(array_like) if dtype is None else np.asarray(array_like, dtype=dtype)
        dtype = dtypedict[array.dtype.type]
        shape = np.zeros(4, dtype=int)
        ashape = array.shape
        shape[:len(ashape)] = ashape
        shape = shape.tolist()
        if keep_info and (name in self):
            oldwave = self[name]
            scales = [oldwave.get_scaling(i) for i in range(-1, 4)]
            units = [oldwave.get_unit(i) for i in range(-1, 4)]
            _set_info = True
        else:
            _set_info = False

        wv = self.reference.Add(name, dtype, *shape, overwrite)
        if issubclass(array.dtype.type, np.complexfloating):
            array = utils.to_igor_complex_wave_order(array)
        array_dtype = array.dtype.type
        variant_array = comutils.to_variant_array(array)
        wv.SetNumericWaveData(dtypedict[array_dtype], variant_array)
        result = Wave(wv, self.app, input_check=False)
        if _set_info:
            for i, scale, unit in zip(range(-1, 4), scales, units):
                result.set_scaling(*scale, i)
                result.set_unit(unit, i)
        return result

    def copy(self):
        return WaveCollection(self.reference, self.app, self.parent)

    #def _to_dict(self, parray=False):
    #    result = {wave.name: wave.array for wave in self}
    #    if parray:
    #        p_dict = {wave.name + "_pos": wave.parray for wave in self}
    #        result.update(p_dict)
    #    return result

    def _to_Series_dict(self, index="position"):
        return {name: wave.to_Series(index=index) for name, wave,
                in zip(self.keys(), self.values())}

    def to_DataFrame(self, index="position", **kwargs):
        import pandas as pd
        if "axis" not in kwargs:
            kwargs["axis"] = 1
        sdict = self._to_Series_dict(index=index)
        if "keys" not in kwargs:
            kwargs["keys"] = sdict.keys()
        return pd.concat(sdict.values(), **kwargs)


class VariableCollection(IgorObjectCollectionBase):
    def __getitem__(self, key):
        """
        get variables by numeric index or by the folder name.
        """
        key = key if isinstance(key, str) else int(key)
        return Variable(self.reference(key), self.app, input_check=False)

    def __contains__(self, name):
        return self.reference.VariableExists(name)

    def add(self, name, value, overwrite=False):
        if isinstance(value, Variable):
            self.add(name, value.value, overwrite=overwrite)
        elif isinstance(value, str):
            return self._add_string(name, value, overwrite=overwrite)
        else:
            return self._add_numeric(name, value, overwrite=overwrite)

    def _add_numeric(self, name, value, overwrite=True):
        if utils.isreal(value):
            dtype = dtypedict[np.float64]
        elif utils.iscomplex(value):
            dtype = dtypedict[np.complex128]
        else:
            raise ValueError()
        v = self.reference.Add(name, dtype, overwrite)
        v.SetNumericValue(value.real, value.imag)
        return Variable(v, self.app, input_check=False)

    def _add_string(self, name, value, overwrite=True):
        dtype = dtypedict[str]
        v = self.reference.Add(name, dtype, overwrite)
        v.SetStringValue(CODEPAGE, value)
        return Variable(v, self.app, input_check=False)

    def copy(self):
        return WaveCollection(self.reference, self.app)


class Window:
    def __init__(self, name, app):
        self.name = name
        self.app = app

    def __repr__(self):
        return "<igorconsole.Window({0}, IgorApp)>".format(self.name)

    def to_front(self):
        self.app.execute('DoWindow/F ' + self.name)

    def to_back(self):
        self.app.execute('DoWindow/B ' + self.name)

    def kill(self):
        self.app.execute('DoWindow/K ' + self.name)
        del self.name
        del self.app


class Graph(Window):
    def __init__(self, name, app):
        super().__init__(name, app)

    def __repr__(self):
        return "<igorconsole.Graph named {0}>".format(self.name)

    def trace_names(self, normal=True, contour=True, hidden=False):
        flags = 0
        if normal:
            flags += 0b1
        if contour:
            flags += 0b10
        if not hidden:
            flags += 0b100
        listname = self.app.execute('fprintf 0, tracenamelist("{0}", ";", {1})'\
                   .format(self.name, flags))[1][0].split(";")[:-1]
        return listname

    def traces(self, normal=True, contour=True, hidden=False):
        def to_fullpath(trace_name):
            command = 'fprintf 0, GetWavesDataFolder(TraceNameToWaveRef("{0}", "{1}"), 2)'\
                      .format(self.name, trace_name)
            return self.app.execute(command)[1][0]
        names = self.trace_names(normal, contour, hidden)
        return (Wave(to_fullpath(name), self.app) for name in names)

    #def remove_trace(self, waves):
    #    if isinstance(waves, Wave) or isinstance(waves, str):
    #        waves = (waves)
    #    wave_names = (wv if isinstance(wv, str) else wv.path for wv in waves)

    def append(self, ywave, xwave=None, position="lb"):
        position = "/" + "/".join(position)

        ywave = ywave.quoted_path if isinstance(ywave, Wave) else str(ywave)
        command = "appendtograph/w={0}{1} {2}".format(self.name, position, ywave)
        if xwave is not None:
            xwave = xwave.path if isinstance(xwave, Wave) else str(xwave)
            command += " vs {0}".format(xwave)
        self.app.execute(command)

    def modify_by_commands(self, commands):
        commands = [commands] if isinstance(commands, str) else commands
        com = []
        apd = com.append
        for command in commands:
            apd("ModifyGraph/W={0} {1};".format(self.name, command))
        while com:
            oneline = ""
            while com and len(oneline) < 300:
                oneline += com.pop()
            self.app.execute(oneline)

    def modify(self, command_dict=None, **kwargs):
        command_dict = {} if command_dict is None else command_dict
        command_dict.update(kwargs)
        commands = []
        for key, val in command_dict.items():
            val = int(val) if utils.isbool(val) else val
            val = '"{0}"'.format(val) if isinstance(val, str) else val
            commands.append("{0}={1}".format(key, val))
        self.modify_by_commands(commands)

    def modify_w(self, command_dict=None, **kwargs):
        command_dict = {} if command_dict is None else command_dict
        command_dict.update(kwargs)
        for key, val in command_dict.items():
            try:
                self.modify({key: val})
            except RuntimeError as e:
                warnings.warn("Not executed: {0}={1[key]}".format(key, kwargs), UserWarning)

    def modify_s(self, command_dict=None, **kwargs):
        command_dict = {} if command_dict is None else command_dict
        command_dict.update(kwargs)
        for key, val in command_dict.items():
            try:
                self.modify({key: val})
            except RuntimeError:
                pass

    def style(self, style:str):
        if os.path.exists("{0}/igorconsole/styles/{1}.json".format(HOME_DIR, style)):
            fpath = "{0}/igorconsole/styles/{1}.json".format(HOME_DIR, style)
        elif os.path.exists("{0}/styles/{1}.json".format(PATH,style)):
            fpath = "{0}/styles/{1}.json".format(PATH,style)
        else:
            raise ValueError("Cannot find the style file.")
        with open(fpath, "rt") as f:
            style = json.load(f)
        self.modify_s(style)

    def map_color(self, style:str, init_trace_num=None,
                  last_trace_num=None, *args, **kwargs):
        trace_names = self.trace_names()[init_trace_num:last_trace_num]
        length = len(trace_names)
        from . import colorfuncs
        grad_func = colorfuncs.gradation[style]
        trace_colors = {}
        for i, trace in enumerate(trace_names):
            color = tuple(grad_func(i/(length-1), *args, **kwargs))
            trace_colors["rgb({})".format(trace)] = color
        self.modify(trace_colors)

    def setaxis(self, axis_name, num1=None, num2=None, silent_error=False):
        if num1 is None:
            num1 = "*"
        if num2 is None:
            num2 = "*"

        command = []
        command.append("setaxis")
        command.append("/w={0} ".format(self.name))
        if silent_error:
            command.append("/z ")
        command.append("{0} {1}, {2}".format(axis_name, num1, num2))
        self.app.execute("".join(command))

    def autoaxis(self, axis_name, mode="normal", from_zero=False,
                 limit="datalimit", reverse=False, silent_error=False):
        mode_dict = {"no": 0, "normal": 1, "subset":2}
        from_zero_dict = {"normal": 0, "from": 1, "symmeetric": 2, "if_unipoler": 3}
        limit_dict = {"datalimit": 0, "auto": 1, "inset": 2}

        if isinstance(mode, str):
            mode = mode_dict[mode]
        if isinstance(from_zero, str):
            from_zero = from_zero_dict[from_zero]
        if isinstance(limit, str):
            limit = limit_dict[limit]

        mode = int(mode)
        from_zero = int(from_zero)
        limit = int(limit)

        command = []
        command.append("setaxis")
        command.append("/w={0}".format(self.name))
        command.append("/a={0}".format(mode))
        command.append("/e={0}".format(from_zero))
        command.append("/n={0}".format(limit))
        if reverse:
            command.append("/r")
        if silent_error:
            command.append("/z")
        self.app.execute("".join(command))

    def setlabel(self, axis_name, string, silent_error=False):
        command = []
        command.append("label")
        command.append("/w={0}".format(self.name))
        if silent_error:
            command.append("/z")
        command.append(axis_name)
        command.append(string)
        self.app.execute("".join(command))

    def save_image(self, filename, filetype="pdf",
                   color="cmyk", size=None, sizeunit="cm",
                   embed_fonts=False, overwrite=False,
                   resolution="4x", preview=False, transparent=False):
        command = []
        apd = command.append
        apd("savepict")
        if overwrite:
            apd("/o")

        t = filetype
        if t == "windowsmetafile" or t == "wmf":
            t = 8
        elif t == "enhanced metafile" or t == "metafile" or t == "emf":
            t = -2
        elif t == "bitmap" or t == "bmp":
            t = -4
        elif t == "eps":
            t = -3
        elif t == "pdf":
            t = -8
        elif t == "png":
            t = -5
        elif t == "jpg" or t == "jpeg":
            t = -6
        elif t == "tiff":
            t = -7
        else:
            t = -8
        apd("/e={0}".format(t))

        cmyk_able = (-3, -8, -7)
        transparent_able = (-5,)
        reso_able = (-4, -5, -6)
        font_embed_able = [-3, -8]

        if color == "rgb":
            pass
        elif color == "cmyk" and t in cmyk_able:
            apd("/c=2")
        else:
            apd("/c=0")

        if (not embed_fonts) or (t not in font_embed_able):
            pass
        if embed_fonts == "all":
            apd("/ef=2")
        else:
            apd("/ef=1")

        if t in transparent_able and transparent:
            apd("/tran=1")

        if t == -3 and not preview:
            apd("/s")

        r = resolution
        ress = (72, 75, 96, 100, 120, 150, 200, 300, 400, 500, 600, 750, 800,
                1000, 1200, 1500, 2000, 2400, 2500, 3000, 2500, 3600, 4000, 4500, 4800)
        if t in reso_able:
            if r == "1x" or r == "screen":
                apd("/b=72")
            elif r == "2x":
                apd("/b=144")
            elif r == "4x":
                apd("/b=288")
            elif r == "5x":
                apd("/b=360")
            elif r == "8x":
                apd("/b=576")
            elif utils.isint(r) and (r in ress):
                apd("/b={0}".format(r))
            else:
                raise RuntimeError()

        if size is not None:
            if sizeunit == "cm":
                apd("/m")
            elif sizeunit == "inch" or sizeunit == "inches":
                apd("/i")

            apd("/w=(0, 0, {0[0]}, {0[1]})".format(size))

        apd("/win={0}".format(self.name))
        folder = os.path.dirname(filename)
        file_ = os.path.basename(filename)
        self.app._newpath(folder)
        apd("/P=igorconsole_path")
        apd(' as "{0}"'.format(file_))
        return self.app.execute("".join(command))

    def get_image_binary(self, filetype="pdf",
                         color="cmyk", size=None, sizeunit="cm",
                         embed_fonts=False, overwrite=False,
                         resolution="4x", preview=False, transparent=False):
        with tempfile.TemporaryDirectory() as tmpd:
            path = tmpd + "\\tmpfile"
            self.save_image(path, filetype=filetype,
                            color=color, size=size, sizeunit=sizeunit,
                            embed_fonts=embed_fonts, overwrite=overwrite,
                            resolution=resolution, preview=preview,
                            transparent=transparent)

            with open(path, "rb") as tmpf:
                result = tmpf.read()
        return result

    def get_image(self, filetype="png",
                  color="rgb", size=None, sizeunit="cm",
                  embed_fonts=False, overwrite=False,
                  resolution="4x", preview=False, transparent=False):
        from PIL import Image
        with tempfile.TemporaryDirectory() as tmpd:
            path = tmpd + "\\tmpfile"
            self.save_image(path, filetype=filetype,
                            color=color, size=size, sizeunit=sizeunit,
                            embed_fonts=embed_fonts, overwrite=overwrite,
                            resolution=resolution, preview=preview,
                            transparent=transparent)

            img = np.asarray(Image.open(path))
            return Image.fromarray(img)

    def show_image(self, filetype="png",
                   color="rgb", size=None, sizeunit="cm",
                   embed_fonts=False, overwrite=False,
                   resolution="4x", preview=False, transparent=False):

        img = self.get_image(filetype=filetype,
                             color=color, size=size, sizeunit=sizeunit,
                             embed_fonts=embed_fonts, overwrite=overwrite,
                             resolution=resolution, preview=preview,
                             transparent=transparent)
        from matplotlib import pyplot
        pyplot.imshow(img)
        pyplot.gca().spines["left"].set_visible(False)
        pyplot.gca().spines["bottom"].set_visible(False)
        pyplot.gca().spines["right"].set_visible(False)
        pyplot.gca().spines["top"].set_visible(False)
        pyplot.show()


class Table(Window):
    def _raw_info_str(self, num):
        command = 'fprintf 0,TableInfo("{0}",{1})'.format(self.name, num)
        return self.app.execute(command)[1][0]

    def _raw_info_list(self, num):
        return self._raw_info_str(num).split(";")[:-1]

    def _raw_info_dict(self, num):
        return {item.split(":", 1)[0]: item.split(":", 1)[1]
                for item in self._raw_info_list(num)}

    def _column_name(self, num):
        return self._raw_info_dict(num)["COLUMNNAME"]

    @property
    def column_num(self):
        return int(self._raw_info_dict(-2)["COLUMNS"]) - 1

    @property
    def row_num(self):
        return int(self._raw_info_dict(-2)["ROWS"])

    @property
    def _column_names(self):
        return [self._column_name(i) for i in range(self.column_num)]

    def _int_to_column_index(self, key: int):
        length = self.column_num
        if -length <= key < length:
            return int(key)%length
        else:
            raise IndexError("key {} out of bounds.".format(key))

    def _str_to_column_index(self, key: str):
        key = str(key)
        cnames = self._column_names
        if "." not in key:
            cnames = [cn.rsplit(".")[0] for cn in cnames]
        unique_cnames = utils.to_unique_key(cnames)
        if key in unique_cnames:
            return unique_cnames.index(key)
        if key in cnames:
            return cnames.index(key)

    def _slice_to_column_index(self, key):
        length = self.column_num
        start = 0 if key.start is None else max(-length, key.start)%length
        stop = length if key.stop is None else min(key.stop, length)
        stop = stop+length if stop < 0 else stop
        step = 1 if key.step is None else key.step
        return iter(range(start, stop, step))

    def _to_column_index(self, key):
        if utils.isint(key):
            return self._int_to_column_index(key)
        elif utils.isstr(key):
            #access by column name
            return self._str_to_column_index(key)
        elif isinstance(key, slice):
            #access by slice
            return self._slice_to_column_index(key)
        elif hasattr(key, "__iter__")\
             and hasattr(key, "__len__")\
             and len(key) == self.column_num\
             and all(utils.isbool(item) for item in key):
             #access by bool index
            return (i for i, filt in enumerate(key) if filt)
        elif hasattr(key, "__iter__"):
            #access by fancy index. str list is acceptable
            return iter(key)
        else:
            raise TypeError("Key must be a str or integer.")

    def _unique_key(self):
        return utils.to_unique_key(self._column_names)

    def _column_wave(self, key):
        key = self._to_column_index(key)
        if isinstance(key, int):
            return Wave(self._raw_info_dict(key)["WAVE"], self.app)
        else:
            return [Wave(self._raw_info_dict(item)["WAVE"], self.app)
                    for item in key]

    def __contains__(self, obj):
        if utils.isstr(obj):
            if obj in self.keys():
                return True
            if obj in self._column_names:
                return True
            return False
        elif isinstance(obj, Wave):
            for wv in self.waves:
                if obj.is_(wv):
                    return True
            return False

    def __len__(self):
        #return len(self.keys())
        # -> optimaized
        return len(self._column_names)

    def keys(self):
        return self._unique_key()

    def values(self):
        return self.waves

    def items(self):
        keys = self.keys()
        values = self.values()
        return [(k, v) for k, v in zip(keys, values)]

    @property
    def _column_waves(self):
        return [self._column_wave(i) for i in range(self.column_num)]

    @property
    def _waves_paths(self):
        return set(self._raw_info_dict(i)["WAVE"] for i in range(self.column_num))

    @property
    def waves(self):
        return [Wave(path, self.app) for path in self._wave_paths()]

    def wave_at(self, column):
        return self._column_wave(column)

    def append(self, wave, *, return_key=True):
        command = "AppendToTable/W={0} {1}".format(self.name, wave.quoted_path)
        self.app.execute(command)
        if return_key:
            return self.keys()[-1]

    def _to_Series_dict(self, index="position"):
        return {name: wave.to_Series(index=index) for name, wave,
                in zip(self._column_names, self._column_waves)}

    def to_DataFrame(self, index="position", **kwargs):
        import pandas as pd
        if "axis" not in kwargs:
            kwargs["axis"] = 1
        sdict = self._to_Series_dict(index=index)
        if "keys" not in kwargs:
            kwargs["keys"] = sdict.keys()
        return pd.concat(sdict.values(), **kwargs)


class NoteBook(Window):
    #not implemented yet
    pass


class Layout(Window):
    #not implemented yet
    pass


class Panel(Window):
    #not implemented yet
    pass
