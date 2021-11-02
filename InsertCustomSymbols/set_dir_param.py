#!/usr/bin/env python
# -*- coding: utf-8 -*-
DEBUG = False
if DEBUG:
    import ptvsd
    print("Waiting for debugger attach")
    # 5678 is the default attach port in the VS Code debug configurations
    #ptvsd.enable_attach(address=('localhost', 5678), redirect_output=True)
    ptvsd.enable_attach(address=('localhost', 5678))
    ptvsd.wait_for_attach()

import os 
import FreeCAD
import FreeCADGui
import TechDraw
from PySide2 import QtGui, QtCore, QtWidgets

def setParam(param_val):
    """Set/create customsymbols group and the symdir parameter with the value specified in param_val"""
    param_grp=FreeCAD.ParamGet("User parameter:BaseApp/Preferences/General/customsymbols")
    param_grp.SetString("symdir", param_val)

# Allow the user to select the symbol directory.
sel_dir = str(QtWidgets.QFileDialog.getExistingDirectory(None, "Select Directory"))
setParam(sel_dir)
pass