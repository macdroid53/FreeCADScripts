"""
RoundedRect_ui
This module provides the dialog to collect
required values to construct the rectangle with rounded corners
"""
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import FreeCAD

from PySide2 import QtGui, QtCore, QtWidgets

DEBUG = False
if DEBUG:
	import ptvsd
	print("Waiting for debugger attach")
	# 5678 is the default attach port in the VS Code debug configurations
	#ptvsd.enable_attach(address=('localhost', 5678), redirect_output=True)
	ptvsd.enable_attach(address=('localhost', 5678))
	ptvsd.wait_for_attach()

usr_canc = "canc"
userOK = "OK"

class RoundedRect_Dlg(QtWidgets.QDialog):
   """
   Display dialog to collect values for rounded rectangle
   """
   ap_style  = "font-size: 14px"

   def __init__(self, vert_selected):
      super(RoundedRect_Dlg, self).__init__()
      self.vert_selected = vert_selected
      self.usr_vals = []
      self.initUI()

   def initUI(self):

      self.result = usr_canc
      # create our window
      self.resize(400,300)
      self.setWindowTitle("Common Shapes")
      #self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
   
      but_hei = 30
      title_cont=QtWidgets.QFrame() #container info title widgets
      title_lay = QtWidgets.QHBoxLayout()
      title_cont.setLayout(title_lay)
      self.txt_win = QtWidgets.QLabel()
      self.txt_win.setWordWrap(False)
      self.txt_win.setText('Rounded Rectangle')
      self.txt_win.setStyleSheet(self.ap_style)
      self.txt_win.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
      title_lay.addWidget(self.txt_win)

      image01 = '/home/mac/SharedData/FC_common/RoundedRect.png'
      arcslot_pixmap = QtGui.QPixmap(image01)
      imgwid=QtWidgets.QLabel()
      imgwid.setPixmap(arcslot_pixmap.scaledToWidth(128))
      title_lay.addWidget(imgwid)
      
      self.info_cont=QtWidgets.QFrame(self) #container info entry widgets
      self.info_form=QtWidgets.QFormLayout(self) #form layout to go in frame
      self.info_cont.setLayout(self.info_form)

      #label & textbox for radius entry
      self.ovrhei_lbl = QtWidgets.QLabel(self)
      self.ovrhei_lbl.setText('Overall height')
      self.ovrhei_lbl.setToolTip('Enter overall height')
      self.ovrhei_txtbox=QtWidgets.QLineEdit(self)
      self.ovrhei_txtbox.setToolTip('Enter overall height')
      self.info_form.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.ovrhei_lbl)
      self.info_form.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.ovrhei_txtbox)

      #label & textbox slot width
      self.ovrwid_lbl = QtWidgets.QLabel(self)
      self.ovrwid_lbl.setText('Overall width')
      self.ovrwid_lbl.setToolTip('Enter overall width')
      self.ovrwid_txtbox=QtWidgets.QLineEdit()
      self.ovrwid_txtbox.setToolTip('Enter overall width')

      self.info_form.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.ovrwid_lbl)
      self.info_form.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.ovrwid_txtbox)
 

      #label & textbox for angle entry
      self.corrad_lbl = QtWidgets.QLabel()
      self.corrad_lbl.setText('Corner radius')
      self.corrad_lbl.setToolTip('Enter corner radius')
      self.corrad_txtbox=QtWidgets.QLineEdit()
      self.corrad_txtbox.setToolTip('Enter corner radius')
      self.info_form.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.corrad_lbl)
      self.info_form.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.corrad_txtbox)

      #checkbox for constrain
      self.constrain_chkbox = QtWidgets.QCheckBox()
      if not self.vert_selected:
         self.constrain_chkbox.setEnabled(False)
      self.constrain_chkbox.setText('Constrain to selected vertex')
      self.constrain_chkbox.setToolTip('Check to have resultant geometry constrained to selected vertex')
      self.info_form.setWidget(3, QtWidgets.QFormLayout.LabelRole, self.constrain_chkbox)

      btn_cont = QtWidgets.QFrame() # frame to contain buttons

      Btn_can = QtWidgets.QPushButton('Cancel', self)
      Btn_can.clicked.connect(self.onCancel)
      #Btn_can.setAutoDefault(True)
      #Btn_can.move(150, w_hei - but_hei * 1.5)

      # OK button
      Btn_ok = QtWidgets.QPushButton('OK', self)
      Btn_ok.clicked.connect(self.onOk)
      #Btn_ok.move(260, w_hei - but_hei * 1.5)
      # now make the window visible

      #vertical layout cancel, ok, label
      lay1 = QtWidgets.QHBoxLayout(self)
      lay1.addWidget(Btn_can)
      lay1.addWidget(Btn_ok)
      btn_cont.setLayout(lay1)

      lay = QtWidgets.QVBoxLayout(self)
      #lay=QtWidgets.QGridLayout(self)
      #lay.addWidget(sc_a)
      lay.addWidget(title_cont)
      lay.addWidget(self.info_cont)
      lay.addWidget(btn_cont)
      Btn_ok.setDefault(True)   
      self.setLayout(lay)
      self.show()

   def set_text(self, msg):
      self.txt_win.setText(msg)

   def onCancel(self):
      self.result = usr_canc
      self.close()

   def onOk(self):
      self.result = userOK
      try:
         ovrhei_val = float( self.ovrhei_txtbox.displayText() )
         ovrwid_val = float( self.ovrwid_txtbox.displayText() )
         corrad_val = float( self.corrad_txtbox.displayText() )
      except ValueError as ve:
         msg="Height, Width, and Radius must be numbers!"
         diag = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning, 'Error MessageBox', msg)
         diag.setWindowModality(QtCore.Qt.ApplicationModal)
         diag.exec_()
         return
      if ovrhei_val <= corrad_val*2 or ovrwid_val <= corrad_val*2:
         msg="Height and Width must be greater than 2X Radius!"
         diag = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning, 'Error MessageBox', msg)
         diag.setWindowModality(QtCore.Qt.ApplicationModal)
         diag.exec_()
         return

      constrain_sel = self.constrain_chkbox.isChecked()
      self.usr_vals = [ovrhei_val, ovrwid_val, corrad_val, constrain_sel]
      self.close()

   def get_slot_data(self):
      return self.usr_vals
