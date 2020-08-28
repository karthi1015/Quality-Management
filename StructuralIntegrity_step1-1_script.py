# -*- coding: utf-8 -*-
import clr
clr.AddReference("RevitAPI")
clr.AddReference("System")
from System.Collections.Generic import List
from Autodesk.Revit.DB import FilteredElementCollector as Fec
from Autodesk.Revit.DB import BuiltInCategory as Bic
from Autodesk.Revit.DB import BuiltInParameter as Bip
from Autodesk.Revit.DB import ElementMulticategoryFilter
from Autodesk.Revit.DB import Transaction, ElementId, FillPatternElement
from Autodesk.Revit.DB import OverrideGraphicSettings, Document
import Autodesk
from pyrevit import script

__doc__ = 'Isolate Structural Elements'

class StructuralElement:
    # class containing information about the elements of includet categories
    def __init__(self, id, structure, attached, name):
        self.id = id
        self.structure = structure
        self.attached = attached
        self.name = name


# reference the current open revit model to work with:
doc = __revit__.ActiveUIDocument.Document

# get all fill patterns
fill_patterns = Fec(doc).OfClass(FillPatternElement).WhereElementIsNotElementType().ToElements()
# get id of solid fill
solid_fill = fill_patterns[0].Id

# set colors
color_true = Autodesk.Revit.DB.Color(78,199,190)
color_true2 = Autodesk.Revit.DB.Color(0,77,71)
color_false = Autodesk.Revit.DB.Color(236,77,0)
color_false2 = Autodesk.Revit.DB.Color(153,51,0)
color_att = Autodesk.Revit.DB.Color(236,77,0)
color_att2 = Autodesk.Revit.DB.Color(153,51,0)

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

try:
    ogs_att = OverrideGraphicSettings().SetProjectionFillColor(color_att)
    ogs_att.SetProjectionFillPatternId(solid_fill)
except:
    ogs_att = OverrideGraphicSettings().SetSurfaceForegroundPatternColor(color_att)
    ogs_att.SetSurfaceForegroundPatternId(solid_fill)
ogs_att.SetSurfaceTransparency(10)
ogs_att.SetProjectionLineColor(color_att2)

# connect to revit model elements via FilteredElementCollector
# collect all the elements of selected elements category
categories1 = [Bic.OST_Walls, Bic.OST_Floors]
categories2 = [Bic.OST_StructuralColumns, Bic.OST_StructuralFraming]
col_bic1 = List[Bic](categories1)
col_bic2 = List[Bic](categories2)
struct_elems1 = Fec(doc).WherePasses(ElementMulticategoryFilter(col_bic1)).WhereElementIsNotElementType().ToElements()
struct_elems2 = Fec(doc).WherePasses(ElementMulticategoryFilter(col_bic2)).WhereElementIsNotElementType().ToElements()

element_ids = []
elem_info = []

# test walls and floors for structural property and append true elemets to list
for elem in filter(None, struct_elems1):
    if not (elem.Name.startswith("AW-FA_") or elem.Name.startswith("IW-FA_")):
        try:
            if elem.LookupParameter("Tragwerk").AsInteger() == 1:
                id = elem.Id
                try:
                    element_ids.append(id)
                    name = elem.Name
                    attached = 0
                    if elem.Category.Name == "Wände":
                        type_id = elem.WallType.Id
                        # print([1, type_id])
                        attached += elem.get_Parameter(Bip.WALL_TOP_IS_ATTACHED).AsInteger()
                        attached += elem.get_Parameter(Bip.WALL_BOTTOM_IS_ATTACHED).AsInteger()
                        # print(attached)
                    elif elem.Category.Name == "Geschossdecken":
                        type_id = elem.FloorType.Id
                        # print([2, type_id])
                    elem_type = Document.GetElement(doc, type_id)
                    # print(elem_type)
                    structure = elem_type.GetCompoundStructure().StructuralMaterialIndex
                    # print(structure)
                    elem_info.append(StructuralElement(id, structure, attached, name))
                except:
                    pass
        except:
            pass

# test columns and framing for structural property and append true elemets to list
for elem in struct_elems2:
    try:
        id = elem.Id
        name = elem.Name
        element_ids.append(id)
        attached = 0
        if elem.Category.Name == "Tragwerksstützen":
            if elem.get_Parameter(Bip.COLUMN_TOP_ATTACHED_PARAM).AsInteger() == 1:
                attached += 1
            structure = 0
            elem_info.append(StructuralElement(id, structure, attached, name))
    except:
        pass

# create a collection from all element ids
col1 = List[ElementId](element_ids)

# entering a transaction to modify the revit model database
# start transaction
tx = Transaction(doc, "check structural elements")
tx.Start()

# isolate all elements of category
doc.ActiveView.IsolateElementsTemporary(col1)

output = script.get_output()
# set graphical overrides
for elem in elem_info:
    if elem.attached != 0:
        doc.ActiveView.SetElementOverrides((elem.id), ogs_att)
        print("NOTE: Transparent orange element " + str(elem.name) + " with ID: " + output.linkify(elem.id) + \
        " is attached. Will not be automatically checked.")
    elif elem.structure != -1:
        doc.ActiveView.SetElementOverrides((elem.id), ogs_true)
    elif elem.structure == -1:
        doc.ActiveView.SetElementOverrides((elem.id), ogs_false)
        print("WARNING: Solid orange element " + str(elem.name) + " with ID: " + output.linkify(elem.id) + \
        " has no structural layer. Correct type before proceeding to next step.")
print("---------------------------")
print("Make sure to scroll to top.")

# commit the changes to the revit model database
# end transaction
tx.Commit()
