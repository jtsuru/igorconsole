
class Window:
    def __init__(self, name, app):
        self.name = name
        self.app = app

    def __repr__(self):
        return f"<automation.igorconsole.Window({self.name}, IgorApp)>"
    
    def to_front(self):
        self.app.execute('dowindow/f ' + self.name)
    
    def to_back(self):
        self.app.execute('dowindow/b ' + self.name)
    
    def kill(self):
        self.app.execute('dowindow/k ' + self.name)
        del self.name
        del self.app

class Graph(Window):
    def __init__(self, name, app):
        super().__init__(name, app)
    
    def __repr__(self):
        return f"<automation.igorconsole.Graph named self.name>"

    def traces(self, normal=True, contour=True, hidden=False):
        flags = 0
        if normal:
            flags += 0b1
        if contour:
            flags += 0b10
        if not hidden:
            flags += 0b100
        return self.app.execute(f'fprintf 0, tracenamelist("", ";", {flags})')[1][0].split(";")[:-1]

    
    def append(self, ywave, xwave=None, position="lb"):
        position = "/" + "/".join(position)

        ywave = ywave.path if isinstance(ywave, Wave) else str(ywave)
        command = f"appendtograph/w={self.name}{position} {ywave}"
        if xwave:
            xwave = xwave.path if isinstance(xwave, Wave) else str(xwave)
            command += f"vs {xwave}"
        self.app.execute(command)
    
    def modify_by_commands(self, commands):
        commands = [commands] if isinstance(commands, str) else commands
        com = ""
        for command in commands:
            com += f"modifygraph/w={self.name} {command};"
        self.app.execute(com)
    
    def modify(self, **kwargs):
        commands = []
        for key in kwargs:
            val = int(kwargs[key]) if isinstance(kwargs[key], bool) else kwargs[key]
            val = f'"{val}"' if isinstance(val, str) else val
            if "_" in key:
                k = key.split("_")
                commands.append(f"{k[0]}({k[1]})={val}")
            else:
                commands.append(f"{key}={val}")
        self.modify_by_commands(commands)

    
    def modify_w(self, **kwargs):
        for key in kwargs:
            try:
                self.modify(**{key:kwargs[key]})
            except RuntimeError as e:
                warnings.warn(f"Not executed: {key}={kwargs[key]}", UserWarning)

    def modify_s(self, **kwargs):
        for key in kwargs:
            try:
                self.modify(**{key:kwargs[key]})
            except RuntimeError:
                pass
    
    def setaxis(self, axis_name, num1=None, num2=None, silent_error=False):
        if num1 is None:
            num1 = "*"
        if num2 is None:
            num2 = "*"

        command = []
        command.append("setaxis")
        command.append(f"/w={self.name} ")
        if silent_error:
            command.append("/z ")
        command.append(f"{axis_name} {num1} {num2}")
        self.app.execute("".join(command))
    
    def autoaxis(self, axis_name, mode="normal", from_zero=False, limit="datalimit", reverse=False, silent_error=False):
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
        command.append(f"/w={self.name}")
        command.append(f"/a={mode}")
        command.append(f"/e={from_zero}")
        command.append(f"/n={limit}")
        if reverse:
            command.append("/r")
        if silent_error:
            command.append("/z")
        self.app.execute("".join(command))

    def setlabel(self, axis_name, string, silent_error=False):
        command = []
        command.append("label")
        command.append(f"/w={self.name}")
        if silent_error:
            command.append("/z")
        command.append(f" {axis_name}")
        command.append(f" {string}")
        self.app.execute("".join(command))



if __name__ == "__main__":
    import math
    import numpy as np
    #from igorconsole import IgorApp
    #起動 or 接続
    igor = IgorApp().start()

    # wave、変数の作成、初期化
    igor.data.wavex = []
    igor.data.wavey = []
    igor.data.time_ = []
    igor.data.val = 0.01 #変数

    time_ = igor.data.time_
    xw = igor.data.wavex
    yw = igor.data.wavey
    val = igor.data.val

    igor.plot(x=xw, y=yw)
    #要素に個別代入
    import datetime
    delta = datetime.datetime.now()
    for i in range(5000):
        xw.append(val * i * math.cos(i * val), speed=10)
        yw.append(val * i * math.sin(i * val), speed=10)
        now = datetime.datetime.now()
        time_.append((now-delta).total_seconds(), speed=10)
        delta = now



    
    #ベクトル演算も可
    igor.data.wavez = xw + 2 * yw
    igor.plot(y=igor.data.wavez)
    #全てのigor組み込みのコマンド、自作マクロを実行可能。
    igor.execute("displayMultiFileAnalyzer()")

class Table(Window):
    pass

class NoteBook(Window):
    pass

class Layout(Window):
    pass
