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
import re
import math
import itertools
import FreeCAD, FreeCADGui
import Part
import Sketcher
from RoundedRect_ui import RoundedRect_Dlg

from PySide2 import QtGui, QtCore, QtWidgets


def conf_mode():
    '''
    Implication here is that the selection object is an open sketch and the selected items are SubElements in the sketch object
    So, the actual selected edges must be extracted from the selection
    Not sure what other things can be in edit mode...
    But below checks to see if the active document has an open sketch
    '''
    mode=True
    if FreeCADGui.ActiveDocument.getInEdit() is not None and FreeCADGui.ActiveDocument.getInEdit().Object.TypeId == 'Sketcher::SketchObject':
        if DEBUG:
            print('Container type: ', FreeCADGui.ActiveDocument.getInEdit().Object.TypeId)
            print('Container object: ', FreeCADGui.ActiveDocument.getInEdit().Object.Name) #prints the name of the container that contains the selected edges
        pass
    else:
        msg="Must be in sketch edit!"
        diag = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning, 'Error', msg)
        diag.setWindowModality(QtCore.Qt.ApplicationModal)
        diag.exec_()
        mode=False
    return mode
    
def deactivate_all_constraints(act_ske):
    for index, constraint in enumerate(act_ske.Constraints):
        if constraint.IsActive:
            act_ske.toggleActive(index)

def activate_all_constraints(act_ske):
    for index, constraint in enumerate(act_ske.Constraints):
        if not constraint.IsActive:
            act_ske.toggleActive(index)

def delete_named_constraints(act_ske, name):
    for index, constraint in enumerate(act_ske.Constraints):
        if constraint.Name == name:
            act_ske.delConstraint(index)
            return


def make_rect(edit_mode):
    DocSke= FreeCADGui.ActiveDocument.getInEdit().Object

    vert_selected = False # set default value
    selected=FreeCADGui.Selection.getSelectionEx()
    if len(selected) < 1: # assume rectangle to be created at origin
        pass
    else:
        try:
            SelEx=FreeCADGui.Selection.getSelectionEx()[0].SubElementNames
        except:
            msg="Must select one point/vertex!"
            diag = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning, 'Error MessageBox', msg)
            diag.setWindowModality(QtCore.Qt.ApplicationModal)
            diag.exec_()
            return
        sel_cnt = len(SelEx)
        sel_nam=selected[0].SubElementNames[0]
        if not any(re.findall(r'Vertex|RootPoint', sel_nam, re.IGNORECASE)):
        #if sel_cnt != 1 or sel_nam.find('Vertex') != 0:
            msg="Select only one point/vertex!"
            diag = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning, 'Error MessageBox', msg)
            diag.setWindowModality(QtCore.Qt.ApplicationModal)
            diag.exec_()
            return
        else:
            vert_selected = True
    '''else:
        diag = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Critical,"Error Message","Must be in sketch edit mode!" )
        #diag.setWindowFlags(PySide.QtCore.Qt.WindowStaysOnTopHint)
        diag.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        diag.exec_()
        return
    '''
    get_dims_dlg = RoundedRect_Dlg(vert_selected)
    get_dims_dlg.exec_()
    # Note: get_dims_dlg checks all side lengths greater than 2X corner_radius
    if get_dims_dlg.result == 'OK':
        overall_Y, overall_X, corner_radius, constrain_to_sel = get_dims_dlg.get_slot_data()
        #FreeCAD.Console.PrintMessage("overall hei: " + format(overall_Y, 'f') + "\n")
    else:
        return
    #set up the values to center the vectors
    corner_dia = 2*corner_radius
    half_Y = (overall_Y-corner_dia)/2
    half_X = (overall_X-corner_dia)/2
    rot_vec = FreeCAD.Vector(0,0,1)

    # empty list for new geometry
    geom_list = []

    if constrain_to_sel:
        # if constrain to selected point is true
        # need to keep the selected point from moving
        # when we constrain the rectangle to it later
        if any(re.findall(r'RootPoint', sel_nam, re.IGNORECASE)):
            Vert_ID, Pos_ID = (-1,1) # RootPoint
            sel_vec = FreeCAD.Vector(0,0,0)
        else:
            Number = re.findall(r'\d+',sel_nam)[0] # Number becomes the float of the first numbers (0..9) found in the string sel_name
            '''
            The above Python construct re.findall(r'\d+',sel_nam) returns a list with all numeric chars from sel_nam
            so, sel_nam='abc5def6' returns ['5','6'] or sel_nam='abc55def66'returns ['55','66']
            adding the index [0], it returns the first character found, i.e. '5'
            Note: [0-9] is not always equivalent to \d. In python3, [0-9] matches only 0123456789 characters,
            while \d matches [0-9] and other digit characters, for example Eastern Arabic numerals
            '''
            Index = int(Number)-1 # convert to integer and decrease by one. Lists start numbering with 0, the edge-numbers start with 1
            Vert_ID, Pos_ID = DocSke.getGeoVertexIndex(Index)
            selected_thing = DocSke.Geometry[Vert_ID]
            if selected_thing.TypeId == 'Part::GeomPoint':
                gpnt=DocSke.Geometry[Vert_ID]
                sel_vec=FreeCAD.Vector(gpnt.X,gpnt.Y,gpnt.Z)
            elif selected_thing.TypeId == 'Part::GeomLineSegment':
                if Pos_ID == 1:
                    sel_vec=selected_thing.StartPoint
                else:
                    sel_vec=selected_thing.EndPoint

        deactivate_all_constraints(DocSke)
    # create named constriants on the selected vertex if constrain_to_sel is ture
    if constrain_to_sel:
        lock_x_constraint = Sketcher.Constraint('DistanceX',Vert_ID,Pos_ID, sel_vec.x)
        lock_x_constraint.Name='RRLockx'
        lock_x = DocSke.addConstraint(lock_x_constraint)
        lock_y_constraint = Sketcher.Constraint('DistanceY',Vert_ID,Pos_ID, sel_vec.y)
        lock_y_constraint.Name='RRLocky'
        lock_y = DocSke.addConstraint(lock_y_constraint)
        named_lock_list = [lock_x_constraint.Name, lock_y_constraint.Name]
        pass

    # right side
    start_vec = FreeCAD.Vector(half_X+corner_radius, half_Y, 0)
    end_vec = FreeCAD.Vector(half_X+corner_radius, -half_Y, 0)
    line_seg = Part.LineSegment(start_vec, end_vec)
    geom_list.append(line_seg)
    #L0=DocSke.addGeometry(line_seg, False)

    # lower right arc
    arccen_vec = FreeCAD.Vector(half_X, -half_Y,0)
    circ_geom = Part.Circle(arccen_vec, rot_vec, corner_radius)
    start_ang = math.radians(-90) #radians = -1.570796 degrees = 90
    end_ang = 0.0
    arc_seg = Part.ArcOfCircle(circ_geom,start_ang,end_ang)
    geom_list.append(arc_seg)
    #L1=DocSke.addGeometry(arc_seg, False)

    # bottom side
    start_vec = FreeCAD.Vector(half_X,-(half_Y+corner_radius), 0)
    end_vec = FreeCAD.Vector(-(half_X),-(half_Y+corner_radius), 0)
    line_seg = Part.LineSegment(start_vec, end_vec)
    geom_list.append(line_seg)
    #L2=DocSke.addGeometry(line_seg, False)

    # lower left arc
    arccen_vec = FreeCAD.Vector(-half_X,-half_Y,0)
    circ_geom = Part.Circle(arccen_vec, rot_vec, corner_radius)
    start_ang = math.radians(-180)
    end_ang = math.radians(-90)
    arc_seg = Part.ArcOfCircle(circ_geom,start_ang,end_ang)
    geom_list.append(arc_seg)

    # left side
    start_vec = FreeCAD.Vector(-(half_X+corner_radius),-half_Y,0)
    end_vec = FreeCAD.Vector(-(half_X+corner_radius),half_Y,0)
    line_seg = Part.LineSegment(start_vec, end_vec)
    geom_list.append(line_seg)

    # upper left arc
    arccen_vec = FreeCAD.Vector(-half_X,half_Y,0)
    circ_geom = Part.Circle(arccen_vec, rot_vec, corner_radius)
    start_ang = math.radians(90)
    end_ang = math.radians(180)
    arc_seg = Part.ArcOfCircle(circ_geom,start_ang,end_ang)
    geom_list.append(arc_seg)

    # top side
    start_vec = FreeCAD.Vector(-half_X,half_Y+corner_radius,0)
    end_vec = FreeCAD.Vector(half_X,half_Y+corner_radius,0)
    line_seg = Part.LineSegment(start_vec, end_vec)
    geom_list.append(line_seg)

    # upper right arc
    arccen_vec = FreeCAD.Vector(half_X,half_Y,0)
    circ_geom = Part.Circle(arccen_vec, rot_vec, corner_radius)
    start_ang = 0.0
    end_ang = math.radians(90)
    arc_seg = Part.ArcOfCircle(circ_geom,start_ang,end_ang)
    geom_list.append(arc_seg)

    L0, L1, L2, L3, L4, L5, L6, L7 = DocSke.addGeometry(geom_list, False)

    constraints_list = []
    #set vertical length and equal
    constraints_list.append(Sketcher.Constraint('DistanceY',L0,2,L0,1,overall_Y-2*corner_radius))
    constraints_list.append(Sketcher.Constraint('Vertical',L0))
    constraints_list.append(Sketcher.Constraint('Vertical',L4))
    constraints_list.append(Sketcher.Constraint('Equal',L0,L4))

    #set horizontal length and equal
    constraints_list.append(Sketcher.Constraint('DistanceX',L6,1,L6,2,overall_X-2*corner_radius))
    constraints_list.append(Sketcher.Constraint('Equal',L6,L2))
    constraints_list.append(Sketcher.Constraint('Horizontal',L6))
    constraints_list.append(Sketcher.Constraint('Horizontal',L2))

    # set arc tangents
    constraints_list.append(Sketcher.Constraint('Tangent',L0,2,L1,2))
    constraints_list.append(Sketcher.Constraint('Tangent',L1,1,L2,1))
    constraints_list.append(Sketcher.Constraint('Tangent',L2,2,L3,2))
    constraints_list.append(Sketcher.Constraint('Tangent',L3,1,L4,1))
    constraints_list.append(Sketcher.Constraint('Tangent',L4,2,L5,2))
    constraints_list.append(Sketcher.Constraint('Tangent',L5,1,L6,1))
    constraints_list.append(Sketcher.Constraint('Tangent',L6,2,L7,2))
    constraints_list.append(Sketcher.Constraint('Tangent',L0,1,L7,1))

    # make two corner radius equal, because of other constraints, other corners will follow
    constraints_list.append(Sketcher.Constraint('Equal',L1,L7))

    # set the corner radius
    constraints_list.append(Sketcher.Constraint('Radius',L7,corner_radius))

    # add constraints
    DocSke.addConstraint(constraints_list)

    # constrain whole structure to selected vertex if constrain_sel is true
    if constrain_to_sel:
        # add symmetry constraint to rectangle
        DocSke.addConstraint(Sketcher.Constraint('Symmetric',L3,3,L7,3,Vert_ID,Pos_ID)) 
        # Remove named lock constraints
        for name in named_lock_list:
            delete_named_constraints(DocSke, name)
    
    activate_all_constraints(DocSke)

    #DocSke.touch()
    FreeCAD.ActiveDocument.recompute()
    FreeCADGui.Selection.clearSelection()





sketch_edit_mode = conf_mode()
#sketch_edit_mode = True
if sketch_edit_mode:
    make_rect(sketch_edit_mode)
