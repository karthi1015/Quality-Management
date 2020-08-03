# -*- coding: utf-8 -*-
import clr
clr.AddReference("RevitAPI")
# Import DocumentManager
clr.AddReference('RevitServices')
import RevitServices
from RevitServices.Persistence import DocumentManager

from System.Collections.Generic import List
from Autodesk.Revit.DB import FilteredElementCollector as Fec
from Autodesk.Revit.DB import BuiltInCategory as Bic
from Autodesk.Revit.DB import Transaction, Document, FailureMessage, ElementId, FillPatternElement, OverrideGraphicSettings
from Autodesk.Revit.UI import Selection

import Autodesk
from rpw import doc

# get all fill patterns
fill_patterns = Fec(doc).OfClass(FillPatternElement).WhereElementIsNotElementType().ToElements()

# get id of solid fill
solid_fill = fill_patterns[0].Id

# set colors
color_true = Autodesk.Revit.DB.Color(243,220,86)
color_true2 = Autodesk.Revit.DB.Color(238,130,11)

color_none = Autodesk.Revit.DB.Color(200,200,200)
color_none2 = Autodesk.Revit.DB.Color(123,123,123)

# create graphical overrides
ogs_true = OverrideGraphicSettings().SetProjectionFillColor(color_true)
ogs_true.SetProjectionFillPatternId(solid_fill)
ogs_true.SetSurfaceTransparency(0)
ogs_true.SetProjectionLineColor(color_true2)

ogs_none = OverrideGraphicSettings().SetProjectionFillColor(color_none)
ogs_none.SetProjectionFillPatternId(solid_fill)
ogs_none.SetSurfaceTransparency(40)
ogs_none.SetProjectionLineColor(color_none2)

# get all warnings
warnings = Document.GetWarnings(doc)

#  flatten list function
def list_flatten(elem_list):
    for i in elem_list:
        if type(i) == list:
            list_flatten(i)
        else:
            fail = i
    return fail


# elements with warnings
failing_elems_ids = []

for warning in warnings:
    failing_elem = warning.GetFailingElements()
    failing_elems_ids.append(failing_elem)

# fatten data structure and get ids of elements
fail_ids = []

for i in failing_elems_ids:
    fail_ids.append(list_flatten(i).ToString())

# get all elements in view
elements_in_view = Fec(doc, doc.ActiveView.Id).WhereElementIsNotElementType().ToElements()

# get ids of elements in view
ids_in_view = []

for i in elements_in_view:
    ids_in_view.append(str(i.Id))

# reduce warning ids by intersection with ids of visible elements
warning_ids_view = set(ids_in_view).intersection(set(fail_ids))

# get all elements that have warnings
has_warning = []

for i in elements_in_view:
    for id in warning_ids_view:
        if id == str(i.Id):
            has_warning.append(i)



# entering a transaction to modify the revit model database -------------------
# start transaction
tx = Transaction(doc, "Highlight Warnings")
tx.Start()

# set graphical overrides
for element in elements_in_view:
    doc.ActiveView.SetElementOverrides((element.Id), ogs_none)

for element in has_warning:
    doc.ActiveView.SetElementOverrides((element.Id), ogs_true)

# end transaction
tx.Commit()
