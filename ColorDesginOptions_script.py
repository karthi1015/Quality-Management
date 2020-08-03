# -*- coding: utf-8 -*-
import clr
clr.AddReference("RevitAPI")
clr.AddReference("System")
from System.Collections.Generic import List
from Autodesk.Revit.DB import FilteredElementCollector as Fec
from Autodesk.Revit.DB import BuiltInCategory as Bic
from Autodesk.Revit.DB import Transaction,  FillPattern, FillPatternElement
from Autodesk.Revit.DB import OverrideGraphicSettings, View, ElementId
from Autodesk.Revit.DB import Category, Subelement, Document
import Autodesk
import re
import sys
import colorsys
from collections import namedtuple

from pyrevit import revit, DB
from pyrevit import forms
from pyrevit import script
from pyrevit import coreutils
from pyrevit.coreutils import pyutils


__doc__ = 'Visualizes the distribution of Design Options. ' \

# reference the current open revit model to work with:
doc = __revit__.ActiveUIDocument.Document
view = doc.ActiveView

# get all fill patterns
fill_patterns = Fec(doc).OfClass(FillPatternElement).WhereElementIsNotElementType().ToElements()

# get id of solid fill
solid_fill = fill_patterns[0].Id

# main -----------------------------------------------------------------------

# connect to revit model elements via FilteredElementCollector
elements = filter(None, Fec(doc, doc.ActiveView.Id).ToElements())

element_do = []
for element in elements:
    element_do.append(element.LookupParameter("Entwurfsoption").AsString())

design_options = set(element_do)
# for i in design_options:
#     print(i)

colors_hsv = []
for i in [x * 0.01 for x in range(0, 100, (99 / (len(design_options)-1)))]:
    # print(i)
    colors_hsv.append((i, 0.7, 0.9))
# print(colors_hsv)

def hsv2rgb(h,s,v):
    return tuple(round(i * 255) for i in colorsys.hsv_to_rgb(h,s,v))

colors_rgb = []
for color in colors_hsv:
    colors_rgb.append(hsv2rgb(color[0], color[1], color[2]))
# print(colors_rgb)

do_color = dict(zip(design_options, colors_rgb))
# print(do_color)

# create graphical overrides
ogs = OverrideGraphicSettings().SetSurfaceForegroundPatternId(solid_fill)
ogs.SetCutForegroundPatternId(solid_fill)

# entering a transaction to modify the revit model database
# start transaction
tx = Transaction(doc, "Visualize Design Options")
tx.Start()

for element in elements:
    try:
        color = do_color.get(element.LookupParameter("Entwurfsoption").AsString())
        # print(color)
        color_revit = Autodesk.Revit.DB.Color(color[0], color[1], color[2])
        # print(color_revit)
        # ogs.SetProjectionLineColor(color_revit)
        ogs.SetSurfaceForegroundPatternColor(color_revit)
        ogs.SetCutForegroundPatternColor(color_revit)
        doc.ActiveView.SetElementOverrides((element.Id), ogs)
    except:
        pass


# commit the changes to the revit model database
# end transaction
tx.Commit()
# done.
