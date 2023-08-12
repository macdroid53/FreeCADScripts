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
import FreeCAD
#from FreeCAD import App
import FreeCADGui
#from FreeCADGui import Gui
from FreeCAD import Base, Rotation, Vector
import Part
import Sketcher
#from Sketcher import ActiveSketch
import DraftVecUtils

from draftgeoutils.general import geomType


from draftgeoutils.edges import findMidpoint
from draftgeoutils.intersections import findIntersection
from draftgeoutils.arcs import arcFrom2Pts

from PySide2 import QtGui, QtCore, QtWidgets
'''
import PySide
from PySide import QtGui ,QtCore
from PySide.QtGui import QComboBox
from PySide.QtGui import QMessageBox
from PySide.QtGui import QTableWidget, QApplication
from PySide.QtGui import *
from PySide.QtCore import *
'''
from ArcSlotAtPoint_ui import ArcSlotAtPoint_Dlg

def semicircleFrom2Pts(firstPt, lastPt, normal = Vector(0, 0 ,1)):
    """Build a semicircle between 2 points, ccw around the normal vector."""
    center = (firstPt + lastPt)/2
    radiusVector = firstPt - center
    rot = Rotation(normal, 90)
    intermediatePt = center + rot.multVec(radiusVector)
    #newArc = Part.Edge(Part.Arc(firstPt, intermediatePt, lastPt))
    newArc = Part.Arc(firstPt, intermediatePt, lastPt)
    return newArc

def arcFromCenter2Pts(firstPt,lastPt, center, ccw = True, normal = Vector(0, 0, 1)):
    """ Build a ccw arc from firstPt to LastPt around center. The normal direction
    argument for the plane containing the arc is unused unless firstPt, lastPt and center are collinear
    and therefore do not themselves define the plane"""
    r1 = firstPt - center
    r2 = lastPt - center
    rad1 = r1.Length
    rad2 = r2.Length
    if rad1 < 1e-7 or rad2 <1e-7:  #zero radius arc
        return None
        # (PREC = 4 = same as Part Module),  Is it possible?
    if round(rad1-rad2, 4) != 0:
        return None
    if round(r1.cross(r2).Length, 4) == 0:  #semicircle case
        if ccw:
            return semicircleFrom2Pts(firstPt, lastPt, normal)
        else:
            return semicircleFrom2Pts(firstPt, lastPt, -normal)
    else:  #arc case
        if ccw:
            rot = Rotation(r1, r2) # rotates r1 into r2
        else:
            rot = Rotation(r2, r1)
        identity = Rotation(0,0,0,1)
        rothalf = rot.slerp(identity, 0.5) #rotate by half the angle
        intermediatePt = center + rothalf.multVec(r1)
        #newArc = Part.Edge(Part.Arc(firstPt, intermediatePt, lastPt))
        newArc = Part.Arc(firstPt, intermediatePt, lastPt)
        return newArc

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
   

def getpoint(edit_mode):
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
        if sel_cnt != 1 or sel_nam.find('Vertex') != 0:
            msg="Select only one point/vertex!"
            diag = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning, 'Error MessageBox', msg)
            diag.setWindowModality(QtCore.Qt.ApplicationModal)
            diag.exec_()
            return
        else:
            vert_selected = True

    Act_Doc = FreeCAD.ActiveDocument
    #DocName=FreeCADGui.ActiveDocument.Document.Name
    SkeName=FreeCADGui.ActiveDocument.getInEdit().Object
    CurDoc=Act_Doc.getObject(SkeName.Name)
    #SelEx=FreeCADGui.Selection.getSelectionEx()[0].SubElementNames
    #print('Selected edges in container: ', SelEx) #print the names of the selected edges
    #FreeCAD.Console.PrintMessage("Hello World!\n")
    if len(selected) < 1: # assume rectangle to be created at origin
        cenvec = FreeCAD.Vector(0,0,0) # global origin
        Vert_ID, Pos_ID = (-1,1) # RootPoint
        #pass
    else:
        # when we get here we know there is one vertex selected
        #for sel in FreeCADGui.Selection.getSelectionEx():
            '''if DEBUG:
                print('---------------------------------------')
                print('Container type: ', sel.Object) #prints the ???
                print('Container object: ', sel.ObjectName) #prints the name of the container that contains the selected edges
                print('Container user label: ', sel.Object.Label)
            SelNams = sel.SubElementNames
            if DEBUG:
                print('Selected edges in container: ', SelNams) #print the names of the selected edges
            Elem=SelNams[0]'''
            #Number = re.findall(r'\d+',Elem)[0] # Number becomes the float of the first numbers (0..9) found in the string Elem
            Number = re.findall(r'\d+',sel_nam)[0] # Number becomes the float of the first numbers (0..9) found in the string Elem
            Index = int(Number)-1 # convert to integer and decrease by one. Lists start numbering with 0, the edge-numbers start with 1
            Vert_ID, Pos_ID = SkeName.getGeoVertexIndex(Index)
            ''' '''
            verts = []
            selected_thing = SkeName.Geometry[Vert_ID]
            print('TypeID: ' + selected_thing.TypeId)
            if selected_thing.TypeId == 'Part::GeomPoint':
                gpnt=SkeName.Geometry[Vert_ID]
                #verts.append(FreeCAD.Vector(gpnt.X,gpnt.Y,gpnt.Z))
                cenvec=FreeCAD.Vector(gpnt.X,gpnt.Y,gpnt.Z)
            elif selected_thing.TypeId == 'Part::GeomLineSegment':
                if Pos_ID == 1:
                    cenvec=selected_thing.StartPoint
                else:
                    cenvec=selected_thing.EndPoint
            elif selected_thing.TypeId == 'Part::GeomCircle':
                print("Pos_ID: " + str(Pos_ID))
                if Pos_ID == 3:
                    cenvec=selected_thing.Center
            elif selected_thing.TypeId == 'Part::GeomArcOfCircle':
                print("Pos_ID: " + str(Pos_ID))
                if Pos_ID == 3:
                    cenvec=selected_thing.Center

    axis = FreeCAD.Vector(0, 0, 1)
    axis_rev = FreeCAD.Vector(0, 0, -1)

    #vert_selected = False
    get_dims_dlg = ArcSlotAtPoint_Dlg(vert_selected)
    get_dims_dlg.exec_()
    if get_dims_dlg.result == 'OK':
        slot_radius, slot_width, slot_ang, constrain_to_sel = get_dims_dlg.get_slot_data()
    else:
        return

    #Create main arcs
    #slot_radius = 40
    #slot_width = 10.0
    slot_outer = slot_radius + slot_width/2
    slot_inner = slot_radius - slot_width/2
    #outer arc
    #arc0=CurDoc.addGeometry(Part.ArcOfCircle(Part.Circle(cenvec,axis,slot_outer),0.205017,1.282238),False)
    arc0=CurDoc.addGeometry(Part.ArcOfCircle(Part.Circle(cenvec,axis,slot_outer),0.0,0.79),False)
    arc0_outercenvec=CurDoc.Geometry[arc0].Center
    arc0_outerendvec=CurDoc.Geometry[arc0].EndPoint
    arc0_outerstrtvec=CurDoc.Geometry[arc0].StartPoint
    #inner arc
    #arc1=CurDoc.addGeometry(Part.ArcOfCircle(Part.Circle(cenvec,axis,slot_inner),0.205017,1.282238),False)
    arc1=CurDoc.addGeometry(Part.ArcOfCircle(Part.Circle(cenvec,axis,slot_inner),0.0,0.79),False)
    arc1_innercenvec=CurDoc.Geometry[arc1].Center
    arc1_innerendvec=CurDoc.Geometry[arc1].EndPoint
    arc1_innerstrtvec=CurDoc.Geometry[arc1].StartPoint

    # constrain inner and outer radii
    CurDoc.addConstraint(Sketcher.Constraint('Radius',arc0,slot_outer))
    CurDoc.addConstraint(Sketcher.Constraint('Radius',arc1,slot_inner))

    # first end arc
    # Create a line between ends of inner and outer arc
    endarc0_line = Part.LineSegment(arc0_outerendvec, arc1_innerendvec).toShape()
    # Find center of this line to be center of end arc
    endarc0_cen = findMidpoint(endarc0_line)
    # create the end arc
    endarc0_geo = arcFromCenter2Pts(arc0_outerendvec, arc1_innerendvec, endarc0_cen)
    endarc0 = CurDoc.addGeometry(endarc0_geo)

    # second end arc
    # Create a line between ends of inner and outer arc
    endarc1_line = Part.LineSegment(arc0_outerstrtvec, arc1_innerstrtvec).toShape()
    endarc1_cen = findMidpoint(endarc1_line)
    #endarc=arcFromCenter2Pts(arc0_outerstrtvec, arc1_innerstrtvec, endarc_cen, False)
    endarc1_geo=arcFromCenter2Pts(arc1_innerstrtvec, arc0_outerstrtvec, endarc1_cen)
    endarc1 = CurDoc.addGeometry(endarc1_geo)

    #empty list for constraints
    constraint_list = []
    # set tangents on arcs
    # endarc0
    #CurDoc.addConstraint(Sketcher.Constraint('Tangent',arc0,2,endarc0,1))
    constraint_list.append(Sketcher.Constraint('Tangent',arc0,2,endarc0,1))
    #CurDoc.addConstraint(Sketcher.Constraint('Tangent',arc1,2,endarc0,2))
    constraint_list.append(Sketcher.Constraint('Tangent',arc1,2,endarc0,2))
    # endarc1
    #CurDoc.addConstraint(Sketcher.Constraint('Tangent',arc0,1,endarc1,2))
    constraint_list.append(Sketcher.Constraint('Tangent',arc0,1,endarc1,2))
    #CurDoc.addConstraint(Sketcher.Constraint('Tangent',arc1,1,endarc1,1))
    constraint_list.append(Sketcher.Constraint('Tangent',arc1,1,endarc1,1))

    # first constructon line for angle
    cl0_geo = Part.LineSegment(endarc0_cen, arc0_outercenvec)
    cl0 = CurDoc.addGeometry(cl0_geo, True)

    # second constructon line for angle
    cl1_geo = Part.LineSegment(endarc1_cen, arc0_outercenvec)
    cl1 = CurDoc.addGeometry(cl1_geo, True)

    # constrain the end points of the consruction lines
    # use 2 for 3rd & 5th argument because arc0_outercenvec was given as 2nd argument above
    #CurDoc.addConstraint(Sketcher.Constraint('Coincident',cl0,2,cl1,2))
    constraint_list.append(Sketcher.Constraint('Coincident',cl0,2,cl1,2))
    # constrain the centers of the main arcs to the construction line
    #CurDoc.addConstraint(Sketcher.Constraint('Coincident',arc0,3,cl0,2))
    constraint_list.append(Sketcher.Constraint('Coincident',arc0,3,cl0,2))
    #CurDoc.addConstraint(Sketcher.Constraint('Coincident',arc1,3,cl0,2))
    constraint_list.append(Sketcher.Constraint('Coincident',arc1,3,cl0,2))

    # constrain end arcs to construction lines
    #CurDoc.addConstraint(Sketcher.Constraint('Coincident',endarc0,3,cl1,1))
    constraint_list.append(Sketcher.Constraint('Coincident',endarc0,3,cl1,1))

    #CurDoc.addConstraint(Sketcher.Constraint('Coincident',endarc1,3,cl0,1))
    constraint_list.append(Sketcher.Constraint('Coincident',endarc1,3,cl0,1))

    # constrain angle of slot
    #--------------Realized these lines are redundant
    #slot_ang_const = CurDoc.addConstraint(Sketcher.Constraint('Angle',cl0,2,cl1,2,math.radians(slot_ang)))
    #CurDoc.setDatum(slot_ang_const,math.radians(slot_ang))
    #--------------Switched to below
    constraint_list.append(Sketcher.Constraint('Angle',cl0,2,cl1,2,math.radians(slot_ang)))

    #constrain to selected point
    if constrain_to_sel:
        #CurDoc.addConstraint(Sketcher.Constraint('Coincident',cl0,2,Vert_ID,Pos_ID))
        constraint_list.append(Sketcher.Constraint('Coincident',cl0,2,Vert_ID,Pos_ID))

    CurDoc.addConstraint(constraint_list)

    CurDoc.recompute()

    #FreeCAD.Console.PrintMessage("PPDBG1\n")
    #FreeCAD.Console.PrintMessage("PPDBG2\n")
    #FreeCAD.Console.PrintMessage("PPDBG3\n")
    #FreeCAD.Console.PrintMessage("PPDBG4\n")
    #FreeCAD.Console.PrintMessage("PPDBG4.1\n")
    #FreeCAD.Console.PrintMessage("PPDBG5\n")
    #FreeCAD.Console.PrintMessage("PPDBG7\n")
    #FreeCAD.Console.PrintMessage("PPDBG6\n")
    #FreeCAD.Console.PrintMessage("PPDBG7.1\n")
    #FreeCAD.Console.PrintMessage("PPDBG8\n")

    FreeCAD.ActiveDocument.recompute()
    FreeCADGui.Selection.clearSelection()

sketch_edit_mode = conf_mode()
if sketch_edit_mode:
    getpoint(sketch_edit_mode)
