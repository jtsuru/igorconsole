import os
from subprocess import run

from natsort import natsorted

filepath = os.path.abspath(__file__)
dirpath = os.path.dirname(filepath)
os.chdir(dirpath)
run(["python", "setup.py", "bdist_wheel"])
run("echo y | pip uninstall igorconsole", shell=True)
os.chdir(dirpath + "/dist")
latest = natsorted(os.listdir())[-1]
run(["pip", "install", latest])