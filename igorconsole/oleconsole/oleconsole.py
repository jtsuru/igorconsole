
"""Objective Igor COM-connection wrapper classes.

Todo:
    * Make documents
"""
import itertools
import json
import logging
import operator as op
import os
import re
import sys
import tempfile
import time
import warnings
from abc import ABC, abstractmethod
from collections import abc as c_abc
from collections import deque

import numpy as np
import pythoncom
from pythoncom import com_error
import win32com.client

from igorconsole.oleconsole import comutils, utils
import igorconsole.oleconsole.oleconsts as csts
from igorconsole.abc.igorobjects import IgorObjectBase, IgorFolderBase, IgorVariableBase, IgorWaveBase, IgorObjectCollectionBase
from igorconsole.abc.igorobjectlike import NdArrayMethodMixin
from .consts import CODEPAGE, PATH, HOME_DIR, APPEND_SWITCH, COMMAND_MAXLEN
logger = logging.getLogger(__name__)

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
    def run(cls, visible=False):
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
        if visible:
            com.Visible = True
        result.reference = com
        if 7.0 <= result.version < 7.07:
            # to prevent crashing
            time.sleep(5)
        result.write_history('* Started from igorconsole.\n')

        return result

    @classmethod
    def connect(cls, visible=False):
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
        if visible:
            com.Visible = True
        result.reference = com
        if 7.0 <= result.version < 7.07:
            # to prevent crashing
            time.sleep(5)
        result.write_history('* Connected from igorconsole.\n')

        return result

    @classmethod
    def start(cls, visible=False):
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

    def execute_commands(self, commands, logged=False):
        """Execute many igor commands.
        Args:
            command (iterable): list of commands.
            logged (bool): if enabled, the command is logged in the igor history.
        """
        for merged_command in utils.merge_commands(commands):
            self.execute(merged_command, logged=logged)

    def async_execute(self, command):
        self.execute('Execute/P/Z/Q "{}"'.format(command))

    def get_value(self, *values, logged=False):
        """Get a value evaluated in igor.
        Params:
            values (str): igor command.
            logged (bool): leave a command in the history area.
        Returns:
            value (int, float, or str): Evaluated value.
        Examples:
            >>> import igorconsole
            >>> import numpy as np
            >>> igor = igorconsole.start()
            >>> igor.get_value("1+1")
            2.0
            >>> igor.get_value("4 * sin(pi/2)")
            4.0
            >>> igor.root.linear = np.arange(100)
            >>> igor.get_value("linear[3]")
            3.0
            >>> igor.root.linear[3]
            3
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
        """Path of the igor program."""
        return self.reference.FullName

    @property
    def name(self):
        """Name of the instance
        Returns:
            str: 'Igor Pro'
        Examples:
            >>> import igorconsole
            >>> igor = igorconsole.start()
            >>> igor.name
            'Igor Pro'    
        """
        return self.reference.Name

    @property
    def is_visible(self):
        """Return if igor application is visible or not.
        Returns:
            is_visible (bool): True if igor is shown, Valse if hidden.
        Examples:
            >>> import igorconsole
            >>> igor = igorconsole.start(visible=False)
            >>> igor.is_visible
            False
            >>> igor.show()
            >>> igor.is_visible
            True
        """
        return self.reference.Visible

    def status1(self, int_):
        """Wrapper of IgorApplication.Status1"""
        return self.reference.Status1(int_)

    @property
    def version(self):
        """Version of the igor
        Returns:
            version (float): version of igor pro.
        """
        if self._version is None:
            self._version = self.status1(csts.Status.IgorVersion)
        return self._version

    @property
    def is_procedure_running(self):
        """Returns True if a user procedure is running."""
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
    
    write = write_history
    
    def print(self, *objects, sep=" ", end="\n"):
        """Print strings on igor history.
        """
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
        """Load existing experiment file.
        Args:
            filepath (str): path to the experiment file.
            loadtype (int): Load type the experiment file.
                The default value is igorconsole.oleconsts.LoadType.Open
                igorconsole.oleconsts.LoadType.Open or 2: open file
                igorconsole.oleconsts.LoadType.Marge or 5: marge files.
                igorconsole.oleconsts.LoadType.Stationery or 4: open filea s a new file.
        Note:
            You can use IgorApp.load_experiment_as_newfile or IgorApp.merge_experiment instead.
        """
        self.reference.LoadExperiment(0, loadtype, "", filepath)

    def load_experiment_as_newfile(self, filepath):
        """Load existing experiment file as a new file..
        Args:
            filepath (str): path to the experiment file.
        """
        self.load_experiment(filepath, loadtype=csts.LoadType.Stationery)

    def merge_experiment(self, filepath):
        """Load existing experiment file and marge it.
        Args:
            filepath (str): path to the experiment file.
        """
        self.load_experiment(filepath, loadtype=csts.LoadType.Merge)

    def _save(self, filepath, savetype=csts.SaveType.Save,
              filetype=csts.ExpFileType.Default, symbolicpathname=""):
        self.reference.SaveExperiment(0, savetype, filetype,
                                         symbolicpathname, filepath)

    def save(self, filepath="", filetype=csts.ExpFileType.Default):
        """Save and overwrite the current experiment file."""
        self._save(filepath, savetype=csts.SaveType.Save, filetype=filetype)

    def save_as(self, filepath, filetype=csts.ExpFileType.Default,
                symbolicpathname="", overwrite=False):
        """Save the current project as a new experiment file.
        Params:
            filepath (str): save destination.
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
        """Save the current project as a copy.
        Params:
            filepath (str): save destination.
            filetype (int): experiment file type.
                -1: Devault
                 0: Unpacked
                 1: Packed
        """
        if (not overwrite) and os.path.exists(filepath):
            raise FileExistsError("A file already exists at the directed path..")
        self._save(filepath, savetype=csts.SaveType.SaveCopy,
                   filetype=filetype, symbolicpathname=symbolicpathname)

    def open_file(self, filepath, filekind="procedure",
                  readonly=False, invisible=False, symbolicpathname=""):
        """Open a file.
        Params:
            filepath (str): file path.
            filekind (str): "procedure", "notebook" or "help". 
                The default value is "procedure".
            readonly (bool): The default value is False.
                Make this value True when you want make the file in read-only mode.
        """
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
        """Close igor pro application.
            Args:
                only_when_saved (bool): The default value is True.
                    If this value is Ture, igor pro application will not be closed
                    when the expeirment file is updated after the last save.
        """
        if only_when_saved and self.is_experiment_modified:
            warnings.warn("This file is not saved."
                          + "Please make 'True' only_when_saved flag.")
            return None
        if self.version < 7.0:
            self.reference.Quit()
        else:
            #On igor 7, Quit finished immediately before the application finishes completely,
            #which causes the exception when you run igor again quicly.
            wmi = win32com.client.GetObject("winmgmts:")
            def number_of_igor_instance():
                return len([item for item in wmi.InstancesOf("Win32_Process") if item.Properties_("Name").Value == "Igor.exe"])
            initial_instance_num = number_of_igor_instance()
            self.reference.Quit()
            while number_of_igor_instance() >= initial_instance_num > 0:
                time.sleep(0)

    def quit_wo_save(self):
        """Close igor pro application without saving even the experiment file is updated."""
        self.quit(only_when_saved=False)

    @property
    def data(self):
        """Root directory of the data in igor pro."""
        return OLEIgorFolder("root:", self)

    root = data

    @property
    def cwd(self):
        """Current working directory set in Igor pro."""
        cwd_path = self.execute("fprintf 0, getdatafolder(1)")[1][0]
        cwd_path = cwd_path.replace("'", "")
        return OLEIgorFolder(cwd_path, self)

    def window_names(self, wintype):
        """List up the name of windows on Igor pro.
        Args:
            wintype (int): window type.
                Graph: 1
                Table: 2
                Layout: 4
                Panel: 64
        """
        return self.execute(r'fprintf 0, winlist("*", ";", "win:'
                            + str(wintype) + r'")')[1][0].split(";")[:-1]

    @property
    def graphs(self):
        """List up the graph windows."""
        return [Graph(item, self) for item in self.window_names(csts.WindowType.Graph)]

    @property
    def tables(self):
        """List up talbes."""
        return [Table(item, self) for item  in self.window_names(csts.WindowType.Table)]

    @property
    def layouts(self):
        """List up the layout windows."""
        return [Layout(item, self) for item in  self.window_names(csts.WindowType.Layout)]

    @property
    def panels(self):
        """List up panels."""
        return [Panel(item, self) for item in self.window_names(csts.WindowType.Panel)]

    def win_exists(self, name):
        return bool(self.get_value('WinType("{0}")'.format(name)))

    #bug: ywavesが多すぎるときに失敗。
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
            winname = utils.current_time("icg_")
        if overwrite:
            command += "DoWindow/K {};".format(winname)
        elif self.win_exists(winname):
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
        if isinstance(ywaves, OLEIgorWave):
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
                    oneline += commands.pop(0) +";"
                self.execute(oneline)
        return Graph(winname, self)

    def edit(self, waves, *, winname=None, title=None, hide=False, host=None,
             win_location=None, unit=None, win_behavior=0, overwrite=False):
        commands = []
        oneline = []
        apd = oneline.append

        if winname is None:
            winname = utils.current_time("ict_")
        if overwrite:
            commands.append("DoWindow/K {};".format(winname))
        elif self.win_exists(winname):
            raise RuntimeError("Table already exists")

        apd("Edit")
        if hide:
            apd("/HIDE=1")
        if host is not None:
            apd("/HOST={0}".format(host.name))
        if unit is not None:
            if unit.lower() == "inch":
                apd("/I")
            elif unit.lower() == "cm":
                apd("/M")
        apd("/K={}".format(win_behavior))
        if win_location is not None:
            apd("/W=({0}, {1}, {2}, {3})".format(*win_location))
        if title is not None:
            apd(' as "{}";'.format(title))
        commands.append("".join(oneline))
        for com in commands:
            self.execute(com)
        result = Table(winname, self)
        for w in waves:
            result.append(w, return_key=False)
        return result

    def _newpath(self, path: str):
        path = path.replace("\\", ":").replace("/", ":") + ":"
        path = path.replace("::", ":")
        self.execute('NewPath/O/C igorconsole_path "{}"'.format(path))

    def append_to_waves(self, waves, vals):
        """Append multiple values to multiple waves respectively.
        Args:
            waves (list of OLEIgorWave): waves to which values are appended.
            vals (list of scalar values): values to append. 
        """
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
        """quicly return a Wave specified by path.
        Args:
            path (str): full path to the wave.
        Returns:
            wave: specified wave.
        """
        return OLEIgorWave(path, self)

    def folder(self, path:str):
        """quicly return a Folder specified by path.
        Args:
            path (str): full path to the folder.
        Returns:
            folder: specified folder.
        """
        return OLEIgorFolder(path, self)

    def variable(self, path:str):
        """quicly return a Variable specified by path.
        Args:
            path (str): full path to the variable.
        Returns:
            variable: specified variable.
        """
        return OLEIgorVariable(path, self)


class OLEIgorObjectBase(IgorObjectBase):
    def _path(self, relative=False, quoted=False):
        return self.reference.Path(relative, quoted)

    @property
    def path(self):
        """Unquoted full path to the Igor object."""
        return self._path(relative=False, quoted=False)

    @property
    def quoted_path(self):
        """Quoted full path to the Igor object."""
        return self._path(relative=False, quoted=True)

    @property
    def name(self):
        """Name of the Igor object."""
        return self.reference.Name

    @property
    def parent(self):
        """Parent folder of the object"""
        return OLEIgorFolder(self.reference.ParentDataFolder, self.app, input_check=False)

    @property
    def _parent_path(self):
        path = self.path
        return path[0 : path.rfind(":", 0, -1)+1]


# 代入演算子オーバーロードの影響でクラス内に代入できなので注意。
#attributeを増やすにはsetattrメソッドを使うこと。
class OLEIgorFolder(OLEIgorObjectBase, IgorFolderBase):
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
        """True if the data in this folder is used in any graphs or tables."""
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
        raise AttributeError("{} is not in this folder.".format(key))

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
        if key in temp:#Slow because of the bug of igor pro.
            return temp[key]

        if not isinstance(key, str):
            raise TypeError("key should be a string.")
        raise KeyError("Object {} not found.".format(key))

    def __setitem__(self, key, val):
        if OLEIgorWaveCollection.addable(val):
            self.waves[key] = val
        elif OLEIgorVariableCollection.addable(val):
            self.variables[key] = val
        elif OLEIgorFolderCollection.addable(val):
            self.subfolders[key] = val
        else:
            raise ValueError("Cannot convert to igor object.")

    def __contains__(self, name):
        ref = self.reference
        result = self._data_folders_ref.DataFolderExists(name)\
                 or ref.WaveExists(name)\
                 or ref.VariableExists(name)
        return result

    @property
    def subfolders(self):
        """Collection of the subfolders in this folder."""
        return OLEIgorFolderCollection(self.reference.SubDataFolders, self.app)

    @property
    def waves(self):
        """Collection of the waves in this folder."""
        return OLEIgorWaveCollection(self.reference.Waves, self.app, self)

    @property
    def variables(self):
        """Collection of the variables in this folder."""
        return OLEIgorVariableCollection(self.reference.Variables, self.app)


    def make_folder(self, name, overwrite=False):
        """Make a new folder.
        Args:
            name (str): name of the folder.
            overwrite (bool): Overwrite existing folder if True.
                The default value is False.
        Returns:
            folder: Made folder.
        """
        return self.subfolders.add(name, overwrite)

    def make_wave(self, name, array_like=None, shape=None, overwrite=True, dtype=None):
        """Make a new wave.
        Args:
            name (str): name of the wave.
            array_like (array or list): Optional. Data for the made wave.
            shape (tuple): Optional. You can specify the shape of the wave when array_like is not specified.
            overwrite (bool): Overwrite existing wave if True.
                The default value is True.
            dtype (np.dtype): data type of the wave.
        Returns:
            wave: Made wave.
        """
        return self.waves.add(name, array_like, shape=shape, overwrite=overwrite, dtype=dtype)

    def make_variable(self, name, value, overwrite=True):
        """Make a new wave.
        Args:
            name (str): name of the wave.
            value (int, float or str): value of the variable.
            overwrite (bool): Overwrite existing variable if True.
                The default value is True.
        Returns:
            variable: Made variable.
        """
        return self.variables.add(name, value, overwrite=overwrite)

    def chdir(self):
        """Change current directory to this folder."""
        self.app.execute("cd {}".format(self.quoted_path), logged=False)

    def delete_folder(self, target):
        """Delete subfolder of this folder.
        Args:
            target (name): name of the subfolder.
        """
        self._data_folders_ref.Remove(target)

    def delete(self):
        """Delite this folder."""
        set_ = lambda i, p: self.setattr(i, p)
        parent = self.parent
        name = self.path.split(":")[-2]

        set_("reference", None)
        parent.delete_folder(name)
    
    def walk(self, limit_depth=float("inf"), shallower_limit=0, method="dfs"):
        """Walk around the subfolders, like os.walk.
        Args:
            limit_depth (int): limit of the depth of the subfolder.
                default value is infinit.
            shallower_limit (int): shallower limit of the scanning.
                defaut value is 0.
            methods (str): You can select "dfs" or "bfs".
                default values is "dfs". 
        Yields:
            OLEIgorFolder: Current scanning directory.
            OLEIgorFolderCollection: Subfolders of the directory.
            OLEIgorVariableCollection: variables of the directory.
            OLEIgorWaveCollection: waves of the directory.
        """
        def get_children(depth, subfolders):
            children = [(depth+1, folder) for folder in subfolders]
            if method == "dfs":
                return reversed(children)
            else:
                return children

        deq = deque([(0, self)])
        method = method.lower()
        if method == "dfs":
            pop = deq.pop
        elif method == "bfs":
            pop = deq.popleft
        else:
            raise ValueError("Invalid method. Method must be 'dfs' or 'bfs'.")
        while deq:
            depth, folder = pop()
            subfolders = folder.subfolders
            if depth >= shallower_limit:
                yield folder, subfolders, folder.variables, folder.waves
            if depth < limit_depth:
                deq.extend(get_children(depth, subfolders))
    
    def to_DataFrame(self):
        """Convert igor folder to pandas.DataFrame"""
        return utils.to_pd_DataFrame(self._igorconsole_to_igorfolder())

    def _igorconsole_to_igorfolder(self):
        folders = {}
        for f in self.subfolders:
            folders[f.name] = f._igorconsole_to_igorfolder()
        contents = {}
        for v in self.variables:
            contents[v.name] = v._igorconsole_to_igorvariable()
        for w in self.waves:
            contents[w.name] = w._igorconsole_to_igorwave()
        info = {
            "type": "IgorFolder",
            "subfolders": folders,
            "contents": contents
        }
        return info

    f = subfolders

    w = waves

    v = variables

class TempFolder(OLEIgorFolder):
    def __init__(self, app, name=None):
        super().__init__(None, app, input_check=False)
        if name is None:
            name = utils.current_time("__ictf_")
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

class OLEIgorVariable(OLEIgorObjectBase, IgorVariableBase):
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
        """Data type of the variable"""
        return utils.to_npdtype(self.reference.DataType)

    @property
    def value(self):
        """Value of the variable"""
        dtype = self.dtype
        if dtype == np.complex128:
            return complex(*self.reference.GetNumericValue())
        if dtype == np.float64:
            return self.reference.GetNumericValue()[0]
        if dtype == str:
            return self.reference.GetStringValue(CODEPAGE)

    def delete(self):
        """Currently not implemented."""
        raise NotImplementedError()

    def __repr__(self):
        return str(self)

    def _igorconsole_to_igorvariable(self):
        info = {
            "type": "IgorVariable",
            "value": self.value
        }
        return info

    def __iadd__(self, other):
        self.parent.waves[self.name] = self + other
        return self

    def __isub__(self, other):
        self.parent.waves[self.name] = self - other
        return self

    def __imul__(self, other):
        self.parent.waves[self.name] = self * other
        return self

    def __itruediv__(self, other):
        self.parent.waves[self.name] = self / other
        return self

    def __ifloordiv__(self, other):
        self.parent.waves[self.name] = self // other
        return self

    def __imod__(self, other):
        self.parent.waves[self.name] = self % other
        return self

    def __ipow__(self, other):
        self.parent.waves[self.name] = self ** other
        return self

class OLEIgorWave(OLEIgorObjectBase, IgorWaveBase):
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

    def delete(self):
        """Currently not implemented."""
        raise NotImplementedError()

    @property
    def is_inuse(self):
        """True if the wave is used in any graphs of tables."""
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
        dimension = type(self)._unit_to_int(dimension)
        return self.reference.Units(dimension, CODEPAGE)

    def set_unit(self, unit, dimension=csts.WaveDimension.Data):
        dimension = type(self)._unit_to_int(dimension)
        self.reference.SetUnits(dimension, CODEPAGE, unit)

    def get_scaling(self, dimension):
        dimension = type(self)._unit_to_int(dimension)
        #the returned value order is different from the igor mannual.
        grad, init = self.reference.GetScaling(dimension)
        return init, grad

    def set_scaling(self, init, grad, dimension, type=0):
        if type == 0:
            self.reference.SetScaling(dimension, grad, init)

    def position(self, index):
        """Calculate coordinates of position from the index of the wave.
        Args:
            index (array_like): index of the points of the wave.
        Returns:
            numpy.ndarray: coordinates of the index.
        """
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
        """Array of the waves.
        Corresponding to the x-axis values if one-dimentional array.
        """
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
        """Calculate position from the index.
        Args:
            x (float): coordinates of x-axis.
            y (float): coordinates of y-axis. Use this if the dimension of the array >= 2.
            z (float): coordinates of z-axis. Use this if the dimension of the array >= 3.
            t (float): coordinates of t-axis. Use this if the dimension of thie array == 4.
            return_type (function): A function used to make the index int.
                The default value is int.
        Returns:
            int or tuple: index
        """
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
        """dtype of this array."""
        return np.dtype(utils.to_npdtype(self.reference.GetDimensions()[0]))

    @property
    def array(self):
        dtype = self.dtype.type
        if issubclass(dtype, np.complexfloating):
            return utils.from_igor_complex_wave_order(self._array(), dtype=dtype)
        else:
            return np.array(self._array(), dtype=dtype)

    def toarray(self):
        """Convert wave to numpy.ndarray."""
        return self.array

    def _array(self):
        return self.reference.GetNumericWaveData(utils.to_igor_data_type(self.dtype))

    def append(self, obj, keepscalings=True, keepunits=True):
        """Append value(s) to the wave.
        Args:
            obj (scalar value or array_like of the scalar value): The value(s) to add.
            keepscalings (bool): keep scaling information of the wave after adding
                the value(s). The default values is True.
            keepsunits (bool): keep units information of the wave after adding
                the value(s). The default values is True.
        """
        length = self._length
        if (length is not None) and length > APPEND_SWITCH:
            self._append2(obj)
        else:
            self._append1(obj, keepscalings, keepunits)

    def _append1(self, obj, keepscalings, keepunits):
        scalings = [self.get_scaling(i) for i in range(-1, 4)] if keepscalings else None
        units = [self.get_unit(i) for i in range(-1, 4)] if keepunits else None
        array = self.array
        dtype = array.dtype
        obj = np.array(obj, dtype=dtype, ndmin=1)
        new_array = np.concatenate([array, obj])
        self.parent.waves.add(self.name, new_array, scalings=scalings, units=units, overwrite=True)
        self._length = len(new_array)

    def _append2(self, obj):
        obj = utils.to_list(obj)
        length = len(self)
        command = "InsertPoints {0},{1},{2}"\
                  .format(length, len(obj), self.quoted_path)
        self.app.execute(command)
        for i, val in enumerate(obj):
            self.reference.SetNumericWavePointValue(length + i, val) 

    def to_Series(self, index="position"):
        """"Convert igor wave to pandas.Series if the wave is one dimentional.
        Args:
            index (str): Specify the index of the Series. The default value is "position".
                The index of the Series become x-axis value if "position", or become integer
                index if "points".
        """
        import pandas as pd
        index = index.lower()
        if index == "position":
            indice = self.parray
        elif index == "points":
            indice = None
        else:
            indice = None
        return pd.Series(self.array.ravel(), index=indice)

    @property
    def ndim(self):
        """Emulate property of numpy.ndarray. See the corresponding document of numpy."""
        # 75.8 us
        return len(self.shape)

    @property
    def shape(self):
        """Emulate property of numpy.ndarray. See the corresponding document of numpy."""
        result = tuple(i for i in self.reference.GetDimensions()[1:] if i != 0)
        self._length = 0 if not result else result[0]
        return result

    @property
    def size(self):
        """Emulate property of numpy.ndarray. See the corresponding document of numpy."""
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
            nptype, _, variant_array = comutils.nptype_vttype_and_variant_array(wv)
            self.reference.SetNumericWaveData(utils.to_igor_data_type(nptype), variant_array)

    def __iadd__(self, other):
        self.parent.waves[self.name] = self + other
        return self

    def __isub__(self, other):
        self.parent.waves[self.name] = self - other
        return self

    def __imul__(self, other):
        self.parent.waves[self.name] = self * other
        return self

    def __imatmul__(self, other):
        self.parent.waves[self.name] = self.__matmul__(other)
        return self

    def __itruediv__(self, other):
        self.parent.waves[self.name] = self / other
        return self

    def __ifloordiv__(self, other):
        self.parent.waves[self.name] = self // other
        return self

    def __imod__(self, other):
        self.parent.waves[self.name] = self % other
        return self

    def __ipow__(self, other):
        self.parent.waves[self.name] = self ** other
        return self

    def is_(self, other):
        """Check this instance ferer the same wave object.
        See also is_equiv document.
        Args:
            other (object): other object to compare.
        """
        return self.path == other.path

    def is_equiv(self, other):
        """Check the wave is equivalent.
            This returns True if "The all values in data is the same value" and
            "The scalings are the same" and "The units are the same".
        Args:
            other (object): other object to compare.
        Note:
            Use np.all(wave1 == wave2) to compare the data value only.
            Use is_ method to check if self and ther refers the same pointer of the igor object.
        """
        if not hasattr(other, "_igorconsole_to_igorwave"):
            return False
        selfinfo = self._igorconsole_to_igorwave()
        otherinfo = other._igorconsole_to_igorwave()
        try:
            if selfinfo["scalings"] != otherinfo["scalings"]:
                return False
            if selfinfo["units"] != otherinfo["units"]:
                return False
            return np.all(selfinfo["array"] == otherinfo["array"])
        except KeyError:
            return False

    #inplace
    def fill(self, value):
        """Emulate property of numpy.ndarray. See the corresponding document of numpy."""
        info = self._igorconsole_to_igorwave()
        info["array"].fill(value)
        self.parent.waves[self.name] = info

    #inplace
    def itemset(self, *args):
        """Emulate property of numpy.ndarray. See the corresponding document of numpy."""
        info = self._igorconsole_to_igorwave()
        info["array"].itemset(*args)
        self.parent.waves[self.name] = info

    #inplace
    def partition(self, *args, **kwargs):
        """Emulate property of numpy.ndarray. See the corresponding document of numpy."""
        info = self._igorconsole_to_igorwave()
        info["array"].partition(*args, **kwargs)
        self.parent.waves[self.name] = info

    #inplace
    def put(self, *args, **kwargs):
        """Emulate property of numpy.ndarray. See the corresponding document of numpy."""
        info = self._igorconsole_to_igorwave()
        info["array"].put(*args, **kwargs)
        self.parent.waves[self.name] = info

    #inplace
    def resize(self, *args, **kwargs):
        """Emulate property of numpy.ndarray. See the corresponding document of numpy."""
        info = self._igorconsole_to_igorwave()
        info["array"].resize(*args, **kwargs)
        self.parent.waves[self.name] = info

    #inplace
    def setfield(self, *args, **kwargs):
        """Emulate property of numpy.ndarray. See the corresponding document of numpy."""
        info = self._igorconsole_to_igorwave()
        info["array"].setfield(*args, **kwargs)
        self.parent.waves[self.name] = info

    #inplace
    def sort(self, *args, **kwargs):
        """Emulate property of numpy.ndarray. See the corresponding document of numpy."""
        info = self._igorconsole_to_igorwave()
        info["array"].sort(*args, **kwargs)
        self.parent.waves[self.name] = info

    #inplace
    @NdArrayMethodMixin.imag.setter
    def imag(self, obj):
        """Emulate property of numpy.ndarray. See the corresponding document of numpy."""
        info = self._igorconsole_to_igorwave()
        info["array"].imag = obj
        self.parent.waves[self.name] = info

    #inplace
    @NdArrayMethodMixin.real.setter
    def real(self, obj):
        """Emulate property of numpy.ndarray. See the corresponding document of numpy."""
        info = self._igorconsole_to_igorwave()
        info["array"].real = obj
        self.parent.waves[self.name] = info

    #inplace
    @NdArrayMethodMixin.shape.setter
    def shape(self, obj):
        """Emulate property of numpy.ndarray. See the corresponding document of numpy."""
        info = self._igorconsole_to_igorwave()
        info["array"].shape = obj
        self.parent.waves[self.name] = info

    #inplace
    @NdArrayMethodMixin.strides.setter
    def stridesl(self, obj):
        """Emulate property of numpy.ndarray. See the corresponding document of numpy."""
        info = self._igorconsole_to_igorwave()
        info["array"].strides = obj
        self.parent.waves[self.name] = info

    def _igorconsole_to_igorwave(self):
        info = {
            "type": "IgorWave",
            "array": self.array,
            "scalings": tuple(self.get_scaling(i) for i in range(-1, 4)),
            "units": tuple(self.get_unit(i) for i in range(-1, 4))
        }
        return info


class OLEIgorObjectCollection(IgorObjectCollectionBase):
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
        """get values if the specified variable exists, else return None
        Args (str or int): This behaves like dict when key is name of the wave.
            This behaves like list when key is int.
        Returns:
            str, int or None: values of the variable.
        """
        if utils.isint(key) and 0 <= key < len(self):
            return self[int(key)]
        if isinstance(key, str) and key in self:
            return self[key]
        return None

    @abstractmethod
    def add(self, name, overwrite=False):
        pass

    @abstractmethod
    def addable(self, obj):
        pass

    def keys(self):
        return {item.Name for item in self.reference}

    def items(self):
        return [(key, self[key]) for key in self.keys()]


    def values(self):
        return [self[key] for key in self.keys()]


class OLEIgorFolderCollection(OLEIgorObjectCollection):
    def __getitem__(self, key):
        """get folders by numeric index or by the folder name."""
        key = key if isinstance(key, str) else int(key)
        return OLEIgorFolder(self.reference(key), self.app, input_check=False)

    def __contains__(self, name):
        return self.reference.DataFolderExists(name)
    
    def __delitem__(self, name):
        raise NotImplementedError()

    def add(self, name, overwrite=False):
        """Add subfolders.
        Args:
            name (str): name of the folder.
        Returns:
            OLEIgorFolder: made folder.
        """
        with TempFolder(self.app):
            return OLEIgorFolder(self.reference.Add(name, overwrite), self.app, input_check=False)
    
    @staticmethod
    def addable(obj):
        """Check the object can be add to this folder."""
        if hasattr(obj, "_igorconsole_to_igorfolder"):
            return True
        if str(obj.__class__) == "<class 'pandas.core.frame.DataFrame'>":
            return True
        if isinstance(obj, dict) and ("type" in obj) and (obj["type"] == "IgorFolder"):
            return True
        return False
    
    def __setitem__(self, key, val):
        if not utils.isstr(key):
            raise TypeError("folder name must be a string.")
        if not type(self).addable(val):
            raise TypeError("cannot convert to igor folder structure.")
        if str(val.__class__) == "<class 'pandas.core.frame.DataFrame'>":
            val = utils.from_pd_DataFrame(val)
        if hasattr(val, "_igorconsole_to_igorfolder"):
            val = val._igorconsole_to_igorfolder()
        if isinstance(val, dict) and ("type" in val) and (val["type"] == "IgorFolder"):
            self.add(key, overwrite=True)
            f = self[key]
            for name, item in val["subfolders"].items():
                f[name] = item
            for name, item in val["contents"].items():
                f[name] = item
            return
        raise ValueError("Convert to igor folder structure failed.")

class OLEIgorWaveCollection(OLEIgorObjectCollection):
    def __init__(self, reference, app, parent=None):
        super().__init__(reference, app)
        #相互参照を作らないように注意
        self.parent = parent

    def __getitem__(self, key):
        """
        get waves by numeric index or by the folder name.
        """
        key = key if isinstance(key, str) else int(key)
        return OLEIgorWave(self.reference(key), self.app, input_check=False)

    def __contains__(self, name):
        #self.reference.WaveExists(name) has bug, and always returns False. (igor 6.37, igor 7.06)
        if self.parent is not None:
            return self.parent.reference.WaveExists(name)
        return name in self.names

    def __delitem__(self, name):
        raise NotImplementedError()

    def add(self, name, array_like=None, *,
            shape=None, overwrite=True, dtype=None,
            scalings=None, units=None):
        return self.add_numeric(name, array_like,
                                shape=shape, overwrite=overwrite,
                                dtype=dtype, scalings=scalings, units=units)

    def add_numeric(self, name, array_like=None, *,
                    shape=None, overwrite=True, dtype=None,
                    scalings=None, units=None):
        if (array_like is None) and (shape is not None):
            dtype = np.float if dtype is None else dtype
            array_like = np.zeros(shape)
        elif array_like is None:
            array_like = []
        #convert to np.array once to determine dtype and shape.
        array = np.asarray(array_like) if dtype is None else np.asarray(array_like, dtype=dtype)
        dtype = utils.to_igor_data_type(array.dtype.type)
        shape = [0] * 4
        ashape = array.shape
        shape[:len(ashape)] = ashape
        wv = self.reference.Add(name, dtype, *shape, overwrite)
        if issubclass(array.dtype.type, np.complexfloating):
            array = utils.to_igor_complex_wave_order(array)
        nptype, _, variant_array = comutils.nptype_vttype_and_variant_array(array)
        wv.SetNumericWaveData(utils.to_igor_data_type(nptype), variant_array)
        result = OLEIgorWave(wv, self.app, input_check=False)
        if scalings is not None:
            for i, scaling in enumerate(scalings):
                dimension = i - 1
                init, grad = scaling
                if dimension == -1 and init == 0.0 and grad == 0.0:
                    continue
                if dimension != -1 and init == 0.0 and grad == 1.0:
                    continue
                result.set_scaling(init, grad, dimension)
        if units is not None:
            for i, unit in enumerate(units):
                dimension = i - 1
                if unit == "":
                    continue
                result.set_unit(unit, dimension)
        return result

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

    @staticmethod
    def addable(obj):
        """Check if the object can be add to this folder."""
        #if wave or convartable
        if hasattr(obj, "_igorconsole_to_igorwave"):
            return True
        if isinstance(obj, dict) and ("type" in obj) and (obj["type"] == "IgorWave"):
            return True
        #pandas.DataFrame
        if str(obj.__class__) == "<class 'pandas.core.frame.DataFrame'>":
            return False
        #if list or array
        elif not utils.isstr(obj) and hasattr(obj, "__iter__") and hasattr(obj, "__getitem__"):
            if isinstance(obj, (list, tuple, np.ndarray)):
                return True
            if str(obj.__class__) == "<class 'pandas.core.series.Series'>":
                return True
            if isinstance(obj, (dict, c_abc.Mapping)):
                return False
        return False
    
    def __setitem__(self, key, val):
        if not utils.isstr(key):
            raise TypeError("wave name must be a string.")
        if not type(self).addable(val):
            raise TypeError("This object cannot be converted to igor wave.")

        if hasattr(val, "_igorconsole_to_igorwave"):
            val = val._igorconsole_to_igorwave()
        if isinstance(val, dict) and ("type" in val) and (val["type"] == "IgorWave"):
            array = val["array"]
            scalings = val["scalings"] if "scalings" in val else None
            units = val["units"] if "units" in val else None
            #scalings and units are not implemented yet
            self.add(key, array, shape=array.shape, scalings=scalings, units=units, overwrite=True)
            return

        if hasattr(val, "__iter__") and hasattr(val, "__getitem__"):
            self.add(key, val, overwrite=True)


class OLEIgorVariableCollection(OLEIgorObjectCollection):
    def __getitem__(self, key):
        """
        get variables by numeric index or by the folder name.
        """
        key = key if isinstance(key, str) else int(key)
        return OLEIgorVariable(self.reference(key), self.app, input_check=False)

    def __contains__(self, name):
        return self.reference.VariableExists(name)

    def __delitem__(self, name):
        raise NotImplementedError()

    def add(self, name, value, overwrite=False):
        if isinstance(value, OLEIgorVariable):
            self.add(name, value.value, overwrite=overwrite)
        elif isinstance(value, str):
            return self._add_string(name, value, overwrite=overwrite)
        else:
            return self._add_numeric(name, value, overwrite=overwrite)

    def _add_numeric(self, name, value, overwrite=True):
        if utils.isreal(value):
            dtype = utils.to_igor_data_type(np.float64)
        elif utils.iscomplex(value):
            dtype = utils.to_igor_data_type(np.complex128)
        else:
            raise ValueError()
        v = self.reference.Add(name, dtype, overwrite)
        v.SetNumericValue(value.real, value.imag)
        return OLEIgorVariable(v, self.app, input_check=False)

    def _add_string(self, name, value, overwrite=True):
        dtype = utils.to_igor_data_type(str)
        v = self.reference.Add(name, dtype, overwrite)
        v.SetStringValue(CODEPAGE, value)
        return OLEIgorVariable(v, self.app, input_check=False)
    
    @staticmethod
    def addable(obj):
        """Check if the object can be add to this folder."""
        if hasattr(obj, "_igorconsole_to_igorvariable"):
            return True
        if isinstance(obj, dict) and ("type" in obj) and (obj["type"] == "IgorVariable"):
            return True
        if utils.isstr(obj) or utils.isreal(obj) or utils.iscomplex(obj):
            return True

    def __setitem__(self, key, val):
        if not utils.isstr(key):
            raise TypeError("name of the igor variable must be a string.")
        if not type(self).addable(val):
            raise TypeError("Cannot convert to igor variable.")
        if hasattr(val, "_igorconsole_to_igorvariable"):
            val = val._igorconsole_to_igorvariable()
        if isinstance(val, dict) and ("type" in val) and (val["type"] == "IgorVariable"):
            val = val["value"]
        self.add(key, val, overwrite=True)


class Window:
    def __init__(self, name, app):
        self.name = name
        self.app = app

    def __repr__(self):
        return "<igorconsole.Window({0}, IgorApp)>".format(self.name)

    def to_front(self):
        """Bring the window to front."""
        self.app.execute('DoWindow/F ' + self.name)

    def to_back(self):
        """Send the window to front."""
        self.app.execute('DoWindow/B ' + self.name)

    def kill(self):
        """Delete the window."""
        self.app.execute('DoWindow/K ' + self.name)
        del self.name
        del self.app


class Graph(Window):
    def __init__(self, name, app):
        super().__init__(name, app)

    def __repr__(self):
        return "<igorconsole.Graph named {0}>".format(self.name)

    def __contains__(self, key):
        if isinstance(key, str):
            return key in self.keys()
        elif isinstance(key, OLEIgorWave):
            for wave in self.values():
                if key.is_(wave):
                    return True
            return False
        else:
            raise TypeError("Must be a string or wave.")

    def __len__(self):
        return len(self.keys())

    def __iter__(self):
        return iter(self.keys())

    def __getitem__(self, key):
        if utils.isint(key):
            return self.trace_wave(int(key), True, True, True)
        elif isinstance(key, str) and (key in self):
            return OLEIgorWave(self._to_fullpath(key), self.app)
        elif isinstance(key, (np.ndarray, list, slice)):
            result = np.array(self.values())[key]
            return result.tolist()
        raise KeyError("Trace {} is not in this graph.".format(key))

    def keys(self):
        """Developping."""
        return self.traces(True, True, True)

    def values(self):
        """Developping."""
        return list(self.trace_waves(True, True, True))

    def items(self):
        """Developping."""
        return [(key, self.trace_wave(key, True, True, True))
                for key in self.keys()]

    def get(self, key, default=None):
        """Developping."""
        try:
            return self[key]
        except KeyError:
            return default

    def __eq__(self, other):
        raise NotImplementedError()

    def traces(self, normal=True, contour=True, hidden=False):
        """Developping."""
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

    def _to_fullpath(self, trace_name):
        command = 'fprintf 0, GetWavesDataFolder(TraceNameToWaveRef("{0}", "{1}"), 2)'\
                    .format(self.name, trace_name)
        return self.app.execute(command)[1][0]

    def trace_wave(self, trace, normal=True, contour=True, hidden=False):
        """Developping."""
        if utils.isint(trace):
            trace = self.traces(normal, contour, hidden)[int(trace)]
        return OLEIgorWave(self._to_fullpath(trace), self.app)

    def trace_waves(self, normal=True, contour=True, hidden=False):
        """Developping."""
        names = self.traces(normal, contour, hidden)
        return (OLEIgorWave(self._to_fullpath(name), self.app) for name in names)

    #def remove_trace(self, waves):
    #    if isinstance(waves, Wave) or isinstance(waves, str):
    #        waves = (waves)
    #    wave_names = (wv if isinstance(wv, str) else wv.path for wv in waves)

    def append(self, ywave, xwave=None, position="lb"):
        """Developping."""
        position = "/" + "/".join(position)

        ywave = ywave.quoted_path if isinstance(ywave, OLEIgorWave) else str(ywave)
        command = "appendtograph/w={0}{1} {2}".format(self.name, position, ywave)
        if xwave is not None:
            xwave = xwave.quoted_path if isinstance(xwave, OLEIgorWave) else str(xwave)
            command += " vs {0}".format(xwave)
        self.app.execute(command)

    def modify_by_commands(self, commands):
        """Developping."""
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
        """Developping."""
        command_dict = {} if command_dict is None else command_dict
        command_dict.update(kwargs)
        commands = []
        for key, val in command_dict.items():
            val = int(val) if utils.isbool(val) else val
            val = '"{0}"'.format(val) if isinstance(val, str) else val
            commands.append("{0}={1}".format(key, val))
        self.modify_by_commands(commands)

    def modify_w(self, command_dict=None, **kwargs):
        """Developping."""
        command_dict = {} if command_dict is None else command_dict
        command_dict.update(kwargs)
        for key, val in command_dict.items():
            try:
                self.modify({key: val})
            except RuntimeError:
                warnings.warn("Not executed: {0}={1[key]}".format(key, kwargs), UserWarning)

    def modify_s(self, command_dict=None, **kwargs):
        """Developping."""
        command_dict = {} if command_dict is None else command_dict
        command_dict.update(kwargs)
        for key, val in command_dict.items():
            try:
                self.modify({key: val})
            except RuntimeError:
                pass

    def style(self, style:str):
        """Developping."""
        if os.path.exists("{0}/igorconsole/styles/{1}.json".format(HOME_DIR, style)):
            fpath = "{0}/igorconsole/styles/{1}.json".format(HOME_DIR, style)
        elif os.path.exists("{0}/../styles/{1}.json".format(PATH,style)):
            fpath = "{0}/../styles/{1}.json".format(PATH,style)
        else:
            raise ValueError("Cannot find the style file.")
        with open(fpath, "rt") as f:
            style = json.load(f)
        self.modify_s(style)

    def map_color(self, style:str, traces=None, *args, **kwargs):
        """Developping."""
        traces = self.traces() if traces is None else traces
        length = len(traces)
        from igorconsole import colorfuncs
        grad_func = colorfuncs.gradation[style]
        trace_colors = {}
        for i, trace in enumerate(traces):
            color = tuple(grad_func(i/(length-1), *args, **kwargs))
            trace_colors["rgb({})".format(trace)] = color
        self.modify(trace_colors)

    def setaxis(self, axis_name, num1=None, num2=None, silent_error=False):
        """Developping."""
        if num1 is None:
            num1 = "*"
        if num2 is None:
            num2 = "*"

        command = []
        command.append("SetAxis")
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
        """Developping."""
        command = []
        command.append("label")
        command.append("/w={0}".format(self.name))
        if silent_error:
            command.append("/z")
        command.append(axis_name)
        command.append('"' + string + '"')
        self.app.execute(" ".join(command))

    def save_image(self, filename, filetype="pdf",
                   color="cmyk", size=None, sizeunit="cm",
                   embed_fonts=False, overwrite=False,
                   resolution="4x", preview=False, transparent=False):
        """Developping."""
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
        """Developping."""
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
        """Developping."""
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
                   resolution="4x", preview=False, transparent=False,
                   ax=None):
        """Developping."""
        img = self.get_image(filetype=filetype,
                             color=color, size=size, sizeunit=sizeunit,
                             embed_fonts=embed_fonts, overwrite=overwrite,
                             resolution=resolution, preview=preview,
                             transparent=transparent)
        from matplotlib import pyplot
        if ax is None:
            ax = pyplot.gca()
        ax.imshow(img)
        ax.set_axis_off()
        return ax

    def reorder(self, order, normal=True, contour=True, hidden=False):
        """Reorder waves.
        Args:
             order: [0,3,2,1] or ["tr0", "tr3", "tr2", "tr1"]
        """
        order_array = np.asarray(order)
        if issubclass(order_array.dtype.type, np.integer):
            traces = self.traces(normal, contour, hidden)
            order = [traces[i] for i in order]
        elif issubclass(order_array.dtype.type, np.str_):
            pass
        else:
            raise ValueError()

        revorder = reversed(order)
        trace = next(revorder)
        for item in reversed(order):
            anchor, trace = trace, item
            command = "ReorderTraces/W={0} {1},{{{2}}}".format(self.name, anchor, trace)
            self.app.execute(command)

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
            return OLEIgorWave(self._raw_info_dict(key)["WAVE"], self.app)
        else:
            return [OLEIgorWave(self._raw_info_dict(item)["WAVE"], self.app)
                    for item in key]

    def __contains__(self, obj):
        if utils.isstr(obj):
            if obj in self.keys():
                return True
            if obj in self._column_names:
                return True
            return False
        elif isinstance(obj, OLEIgorWave):
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
        return [OLEIgorWave(path, self.app) for path in self._wave_paths()]

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
