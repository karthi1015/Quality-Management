# -*- coding: utf-8 -*-
import clr
clr.AddReference("RevitAPI")

from Autodesk.Revit.DB import FilteredElementCollector as Fec
from Autodesk.Revit.DB import BuiltInCategory as Bic
from Autodesk.Revit.DB import BuiltInParameter as Bip
from Autodesk.Revit.DB import Transaction, Document
import Autodesk
import re
from rpw.ui.forms import (FlexForm, Label, ComboBox, Button)
from pyrevit import revit, DB
from rpw import doc

__context__ = 'selection'
__doc__ = 'Changes wall top or base constraint across multiple levels. ' \
          'HOW TO USE: '   \
          'Select walls and run script. Easy, right?.'
__title__ = 'Walls Mass Level Change'

class Element_info:
    def __init__(self, id, old, new, elem):
        self.id = id
        self.old = old
        self.new = new
        self.elem = elem


regex_lvl = re.compile(r'_[A-Z]{4}')

# get selected element
selection = revit.get_selection()
selected_elements = selection.elements
levels = Fec(doc).OfCategory(Bic.OST_Levels).WhereElementIsNotElementType().ToElements()

# ui
components = [Label('Top or bottom constraint:'),
               ComboBox("combobox", {"Abhängigkeit oben":Bip.WALL_HEIGHT_TYPE, "Abhängigkeit unten":Bip.WALL_BASE_CONSTRAINT}),
               Label('Move to level:'),
               ComboBox("combobox1", {"OKFF":"_OKFF", "OKRF":"_OKRF", "UKRD":"_UKRD"}),
               Button('Select')]
form = FlexForm('Title', components)
form.show()

values = form.values
ui_0 = values["combobox"]
ui_1 = values["combobox1"]
constraint = ui_0

change_log = []
for el in selected_elements:
    lvl_id = el.get_Parameter(constraint).AsElementId()
    lvl_name = Document.GetElement(doc, lvl_id).Name
    lvl_name_new = regex_lvl.sub(ui_1, lvl_name)
    element_info = Element_info("none", lvl_name, lvl_name_new, el)
    for lvl in levels:
        if lvl.Name == lvl_name_new:
            element_info.id = lvl.Id
    change_log.append(element_info)

# entering a transaction to modify the revit model database -------------------
# start transaction
tx = Transaction(doc, "Mass change level of selection")
tx.Start()

for change in change_log:
    change.elem.get_Parameter(constraint).Set(change.id)

# end transaction
tx.Commit()

print("paramater changed: " + str(constraint))
print("new suffix: " + str(ui_1))

for i in change_log:
    print("Wall with ID: " + str(i.id.ToString()) + " was on level: " + str(i.old) + ", is now on level: " + str(i.new))
