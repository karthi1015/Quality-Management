# -*- coding: utf-8 -*-
import clr
clr.AddReference("RevitAPI")
clr.AddReference("System")
from System.Collections.Generic import List
from Autodesk.Revit.DB import FilteredElementCollector as Fec
from Autodesk.Revit.DB import BuiltInCategory as Bic
from Autodesk.Revit.DB import Transaction, FillPattern, FillPatternElement
from Autodesk.Revit.DB import OverrideGraphicSettings, View, ElementId
import Autodesk
from pyrevit import revit, DB

__doc__ = 'Visualizes the structural property of Walls, Floors,' \
          ' Structural Columns and Structural Framing.'

# reference the current open revit model to work with:
doc = __revit__.ActiveUIDocument.Document

# class containing information about the elements of includet categories
class StructuralElement:
    def __init__(self, id, structural):
        self.id = id
        self.structural = structural


# this function takes all walls and floors and creates an object of the
# StructuralElement class and appends it to the elem_info list.
def GetElemProps(elem_lst):
    for elem in elem_lst:
        if not (elem.Name.startswith("AW-FA_") or elem.Name.startswith("IW-FA_")):
            try:
                id = elem.Id
                structural = elem.LookupParameter("Tragwerk").AsInteger()
                elem_info.append(StructuralElement(id, structural))
                element_ids.append(id)
            except:
                pass


# this function takes all structural columns and structurals framings
# and creates an object of the
# StructuralElement class and appends it to the elem_info list.
def ElemCnvrt(elem_lst):
    for elem in elem_lst:
        id = elem.Id
        elem_info.append(StructuralElement(id, 1))
        element_ids.append(id)


# get all fill patterns
fill_patterns = Fec(doc).OfClass(FillPatternElement).WhereElementIsNotElementType().ToElements()
# get id of solid fill
solid_fill = fill_patterns[0].Id

# set colors
color_true = Autodesk.Revit.DB.Color(78,199,190)
color_true2 = Autodesk.Revit.DB.Color(0,77,71)
color_false = Autodesk.Revit.DB.Color(236,77,0)
color_false2 = Autodesk.Revit.DB.Color(153,51,0)

# create graphical overrides
try:
    ogs_true = OverrideGraphicSettings().SetProjectionFillColor(color_true)
    ogs_true.SetProjectionFillPatternId(solid_fill)
except:
    ogs_true = OverrideGraphicSettings().SetSurfaceForegroundPatternColor(color_true)
    ogs_true.SetSurfaceForegroundPatternId(solid_fill)
ogs_true.SetSurfaceTransparency(10)
ogs_true.SetProjectionLineColor(color_true2)

try:
    ogs_false = OverrideGraphicSettings().SetProjectionFillColor(color_false)
    ogs_false.SetProjectionFillPatternId(solid_fill)
except:
    ogs_false = OverrideGraphicSettings().SetSurfaceForegroundPatternColor(color_false)
    ogs_false.SetSurfaceForegroundPatternId(solid_fill)
ogs_false.SetSurfaceTransparency(0)
ogs_false.SetProjectionLineColor(color_false2)

# connect to revit model elements via FilteredElementCollector
# collect all the elements of selected elements category
walls = Fec(doc).OfCategory(Bic.OST_Walls).WhereElementIsNotElementType().ToElements()
floors = Fec(doc).OfCategory(Bic.OST_Floors).WhereElementIsNotElementType().ToElements()
columns = Fec(doc).OfCategory(Bic.OST_StructuralColumns).WhereElementIsNotElementType().ToElements()
framing = Fec(doc).OfCategory(Bic.OST_StructuralFraming).WhereElementIsNotElementType().ToElements()

# prepare lists
elem_info = []
element_ids = []

# process elements
GetElemProps(walls)
GetElemProps(floors)
ElemCnvrt(columns)
ElemCnvrt(framing)

# create a collection from all element ids
col1 = List[ElementId](element_ids)

# entering a transaction to modify the revit model database
# start transaction
tx = Transaction(doc, "check structural elements")
tx.Start()

# isolate all elements of category
doc.ActiveView.IsolateElementsTemporary(col1)

# set graphical overrides
for elem in elem_info:
    if elem.structural == 1:
        doc.ActiveView.SetElementOverrides((elem.id), ogs_true)
    if elem.structural == 0:
        doc.ActiveView.SetElementOverrides((elem.id), ogs_false)

# commit the changes to the revit model database
# end transaction
tx.Commit()
