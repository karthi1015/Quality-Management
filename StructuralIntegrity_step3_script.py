# -*- coding: utf-8 -*-
import clr
clr.AddReference("RevitAPI")
clr.AddReference("System")
from System.Collections.Generic import List
from Autodesk.Revit.DB import FilteredElementCollector as Fec
from Autodesk.Revit.DB import ElementMulticategoryFilter, Document
from Autodesk.Revit.DB import BuiltInCategory as Bic
from Autodesk.Revit.DB import BuiltInParameter as Bip
from Autodesk.Revit.DB import Transaction, FillPattern, FillPatternElement
from Autodesk.Revit.DB import OverrideGraphicSettings, View, ElementId
import Autodesk
import colorsys
from collections import namedtuple
from pyrevit import revit, DB, script
from rpw import doc

# mouse hover-over text
__doc__ = 'Visualizes the level properties of Walls, Floors,' \
          ' Structural Columns and Structural Framing.'

class StructuralElement:
    # class containing information about the elements of includet categories
    def __init__(self, id, offset, info):
        self.id = id
        self.offset = offset
        self.info = info


class WarningElement:
    # class of elements that are suspicious but not necessairily incorred.
    # for example "SO_" on OKFF on any Subsurface level
    def __init__(self, id, name):
        self.id = id
        self.name = name


class LevelInfo:
    def __init__(self, id, name, elevation):
        self.id = id
        self.name = name
        self.elevation = elevation


def CnvrtToName(id):
    # Convert level ID to level Name
    lvl_name = Document.GetElement(doc, id).Name
    return lvl_name


def ToInt(value_str):
    str_new = value_str.replace(",", "")
    # print([2, str_new])
    converted = int(str_new)
    # print([3, converted])
    return converted


def GetLvlDistUKRD(lvl_id):
    name = CnvrtToName(lvl_id)
    name.replace("UKRD", "OKRF")
    current_lvl = Document.GetElement(doc, lvl_id)
    current_lvl_elev = current_lvl.get_Parameter(Bip.LEVEL_ELEV).AsDouble()
    for level in level_info:
        if name == level.name:
            dist = level.elevation - current_lvl_elev
    return dist


def GetElemProps(elem_lst):
    # this function takes all elements in the categories list and creates an object of the
    # StructuralElement class and appends it to the elem_info list.
    for elem in elem_lst:
            try:
                id = elem.Id
                if elem.Category.Name == "Geschossdecken":
                    if elem.get_Parameter(Bip.FLOOR_PARAM_IS_STRUCTURAL).AsInteger() == 1:
                        element_ids.append(id)
                        offset_raw = elem.get_Parameter(Bip.FLOOR_HEIGHTABOVELEVEL_PARAM).AsValueString()
                        # print([1, offset_raw])
                        offset = ToInt(offset_raw)
                        lvl_bott_id = elem.get_Parameter(Bip.LEVEL_PARAM).AsElementId()
                        thickness = ToInt(elem.get_Parameter(Bip.FLOOR_ATTR_THICKNESS_PARAM).AsValueString())
                        if elem.Name.startswith("GD_"):
                            # we are assuming from the previous steps that the floors
                            # is hosted correctly.
                            offset_calc = offset
                            info = str(offset_calc)
                        elif elem.Name.startswith("GD-BA_"):
                            # we are assuming from the previous steps that the floors
                            # is hosted correctly.
                            # we are assuming that the floors compound structure
                            # fits with OKFF and OKRF levels
                            offset_calc = offset
                            info = str(offset_calc)
                        elem_info.append(StructuralElement(id, offset_calc, info))
                elif elem.Category.Name == "Skelettbau":
                    element_ids.append(id)
                    offset_raw = elem.get_Parameter(Bip.Z_OFFSET_VALUE).AsValueString()
                    offset = ToInt(offset_raw)
                    info = str(offset)
                    elev_0 = elem.get_Parameter(Bip.STRUCTURAL_BEAM_END0_ELEVATION).AsDouble()
                    elev_1 = elem.get_Parameter(Bip.STRUCTURAL_BEAM_END1_ELEVATION).AsDouble()
                    if  elev_0 != 0 or elev_1 != 0:
                        elem_wrngs.append(WarningElement(id, elem.Name))
                    elem_info.append(StructuralElement(id, offset, info))
                else:
                    pass
            except:
                pass

# collect levels and their names
levels = Fec(doc).OfCategory(Bic.OST_Levels).WhereElementIsNotElementType().ToElements()
level_info = []
for level in levels:
    id = level.Id
    name = level.Name
    elevation = level.get_Parameter(Bip.LEVEL_ELEV).AsDouble()
    level_info.append(LevelInfo(id, name, elevation))

# get all fill patterns
fill_patterns = Fec(doc).OfClass(FillPatternElement).WhereElementIsNotElementType().ToElements()
# get id of solid fill
solid_fill = fill_patterns[0].Id

# set colors
color_true = Autodesk.Revit.DB.Color(0,133,68)
color_true2 = Autodesk.Revit.DB.Color(0,100,68)
color_false = Autodesk.Revit.DB.Color(164,26,7)
color_false2 = Autodesk.Revit.DB.Color(100,26,7)

# create graphical overrides


# connect to revit model elements via FilteredElementCollector
# collect all the elements of categories
categories = [Bic.OST_Floors, Bic.OST_StructuralFraming]
col_bic = List[Bic](categories)
struct_elems = Fec(doc).WherePasses(ElementMulticategoryFilter(col_bic)).WhereElementIsNotElementType().ToElements()

# prepare lists
elem_info = []
element_ids = []
elem_wrngs = []

# process elements
GetElemProps(struct_elems)

offsets = []
for elem in elem_info:
    offsets.append(elem.offset)
unique_offsets = set(offsets)

colors_hsv = []
for i in [x * 0.01 for x in range(0, 100, (99 / (len(unique_offsets)-1)))]:
    # print(i)
    colors_hsv.append((i, 0.7, 0.9))
# print(colors_hsv)

def hsv2rgb(h,s,v):
    return tuple(round(i * 255) for i in colorsys.hsv_to_rgb(h,s,v))

colors_rgb = []
for color in colors_hsv:
    colors_rgb.append(hsv2rgb(color[0], color[1], color[2]))
# print(colors_rgb)

offset_color = dict(zip(unique_offsets, colors_rgb))
# print(do_color)

ogs = OverrideGraphicSettings().SetSurfaceForegroundPatternId(solid_fill)
ogs.SetCutForegroundPatternId(solid_fill)

# entering a transaction to modify the revit model database
# start transaction
tx = Transaction(doc, "check structural element levels")
tx.Start()

# isolate all elements of category
col1 = List[ElementId](element_ids)
doc.ActiveView.IsolateElementsTemporary(col1)

# set graphical overrides
for elem in elem_info:
    try:
        color = offset_color.get(elem.offset)
        # print(color)
        color_revit = Autodesk.Revit.DB.Color(color[0], color[1], color[2])
        # print(color_revit)
        # ogs.SetProjectionLineColor(color_revit)
        ogs.SetSurfaceForegroundPatternColor(color_revit)
        ogs.SetCutForegroundPatternColor(color_revit)
        doc.ActiveView.SetElementOverrides((elem.id), ogs)

        Document.GetElement(doc, elem.id).get_Parameter(Bip.ALL_MODEL_MARK).Set(elem.info + " / " + str(elem.id))

    except:
        pass

# commit the changes to the revit model database
# end transaction
tx.Commit()

output = script.get_output()
for el in elem_wrngs:
    print("Note: " + str(el.name) + " with ID: " + output.linkify(el.id) + " has Start- or Endebenenversatz." \
    " Only allowed on slanted framing. Use z-Versatzwert.")
