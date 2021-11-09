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

from pathlib import Path
import FreeCAD
import FreeCADGui
from PySide2 import QtGui, QtCore, QtWidgets

def noselerror():
    msg="Must select at least one object with faces!"
    diag = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning, 'Error MessageBox', msg)
    diag.setWindowModality(QtCore.Qt.ApplicationModal)
    diag.exec_()
    return

def fetch_path_param():
    """Fetch the path to the symbol directory
    From FreeCAD user parameters
    Returns the path or empty string"""
    # 
    param_grp=FreeCAD.ParamGet("User parameter:BaseApp/Preferences/General/customsymbols")
    fetched_path=param_grp.GetString("symdir")
    if len(fetched_path) > 0:
        return fetched_path
    else:
        return ""

def file_select(start_dir):
    """Present a dialog to allow the user to select the desired symbol."""
    try:
        FreeCAD.Console.PrintMessage(start_dir+"\n")
        OpenName = QtWidgets.QFileDialog.getOpenFileName(None,"Read a file txt",start_dir,"*.svg")
        FreeCAD.Console.PrintMessage("Read "+OpenName[0]+"\n")
        if len(OpenName[0]) > 0:
            return OpenName[0]
        else:
            FreeCAD.Console.PrintMessage("No file specified!\n")
            return ''
    except Exception:
        FreeCAD.Console.PrintMessage('Exception occured while selecting symbol file!')
        return ''

def insert_symbol(symbol_file, td_page):
    """Insert the selected symbol into the active TechDraw Page"""
    f = open(symbol_file,'r')
    svg = f.read()
    f.close()
    newsym = FreeCAD.activeDocument().addObject('TechDraw::DrawViewSymbol','Symbol')
    newsym.Symbol = svg
    sym_label = Path(symbol_file).stem
    newsym.Label=sym_label
    td_page.addView(newsym)
    FreeCAD.ActiveDocument.recompute()
    FreeCAD.Console.PrintMessage("Active page: "+td_page.Name+"\n")

def version019():
    """FreeCAD 0.19 version of confirming the selected target is a TechDraw Page"""
    selected=FreeCADGui.Selection.getSelectionEx()
    if len(selected) < 1: # assume rectangle to be created at origin
        noselerror()
    else:
        asel=selected[0]
    if repr(asel.Object) == '<DrawPage object>':
        path = fetch_path_param()
        active_page = asel.Object
        selected_file = file_select(path)
        if selected_file != '':
            insert_symbol(selected_file, active_page)
    else:
        FreeCAD.Console.PrintMessage("TechDraw page must be selected in the tree!\n")

def version020():
    """FreeCAD 0.20 version of confirming the selected target is a TechDraw Page
    The TechDrawView object and getPage method were added in 0.20"""
    #if str(FreeCADGui.ActiveDocument.ActiveView) == '<TechDrawView object>':
    if repr(FreeCADGui.ActiveDocument.ActiveView) == '<TechDrawView object>':
        path = fetch_path_param()
        active_page = FreeCADGui.ActiveDocument.ActiveView.getPage()
        FreeCAD.Console.PrintMessage("Active page: "+active_page.Name+"\n")
        selected_file = file_select(path)
        if selected_file != '':
            insert_symbol(selected_file, active_page)
    else:
        FreeCAD.Console.PrintMessage("Active page must be a TechDraw page!\n")

major, minor, dot =  FreeCAD.Version()[0:3]
if int(minor) >= 20:
    version020()
else:
    version019()
