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
from Autodesk.Revit.DB import DisplayUnitType, UnitUtils
import Autodesk
import colorsys
from collections import namedtuple
from pyrevit import revit, DB, script
from rpw import doc
import re

# mouse hover-over text
__doc__ = 'Visualizes the level properties of Walls, Floors,' \
          ' Structural Columns and Structural Framing.'

# regex to get everything after "_"
# regex_lvl = re.compile("_.*")

class StructuralElement:
    # class containing information about the elements of includet categories
    def __init__(self, id, offset, info):
        self.id = id
        self.offset = offset
        self.info = info


class WarningElement:
    # class of elements that are suspicious but not necessairily incorred.
    # for example "SO_" on OKFF on any Subsurface level
    def __init__(self, id, name, text):
        self.id = id
        self.name = name
        self.text = text


class LevelInfo:
    def __init__(self, id, name, elevation):
        self.id = id
        self.name = name
        self.elevation = elevation


def CnvrtToName(id):
    # Convert level ID to level Name
    lvl_name = Document.GetElement(doc, id).Name
    return lvl_name


def ToFloat(double):
    converted = UnitUtils.ConvertFromInternalUnits(double, DisplayUnitType.DUT_METERS)
    return converted


def GetLvlOKRF(lvl_name):
    lvl_name_new = lvl_name.replace("OKFF", "OKRF")
    for level in level_info:
        if lvl_name_new == level.name:
            new_lvl = level
    return new_lvl


def GetLvlDist(lvl_id):
    # print("------------")
    lvl_name = CnvrtToName(lvl_id)
    if ("OKRF" in lvl_name) and ("OKFF" in lvl_name):
        # print([0, lvl_name])
        lvl_name_new = re.sub("_.*", "_UKRD", lvl_name)
        # print(["new bottom level: ", lvl_name_new])
    elif "OKRF" in lvl_name:
        # print([1, lvl_name])
        lvl_name_new = lvl_name.replace("OKRF", "UKRD")
        # print(["new bottom level: ", lvl_name_new])
    elif "OKFF" in lvl_name:
        # print([2, lvl_name])
        lvl_okrf = GetLvlOKRF(lvl_name)
        lvl_id = lvl_okrf.id
        lvl_name_new = lvl_name.replace("OKFF", "UKRD")
        # print(["new bottom level: ", lvl_name_new])
    current_lvl = Document.GetElement(doc, lvl_id)
    # print(["new top level: ", current_lvl.Name])
    current_lvl_elev_double = current_lvl.get_Parameter(Bip.LEVEL_ELEV).AsDouble()
    current_lvl_elev = ToFloat(current_lvl_elev_double)
    for level in level_info:
        if lvl_name_new == level.name:
            # print(current_lvl_elev)
            # print(level.elevation)
            dist = current_lvl_elev - level.elevation
    # print(dist)
    return dist


def GetElemProps(elem_lst):
    # this function takes all elements in the categories list and creates an object of the
    # StructuralElement class and appends it to the elem_info list.
    for elem in elem_lst:
            try:
                id = elem.Id
                name = elem.Name
                if elem.Category.Name == "Geschossdecken":
                    if elem.get_Parameter(Bip.FLOOR_PARAM_IS_STRUCTURAL).AsInteger() == 1:
                        element_ids.append(id)
                        offset_raw = elem.get_Parameter(Bip.FLOOR_HEIGHTABOVELEVEL_PARAM).AsDouble()
                        # print([1, offset_raw])
                        offset = ToFloat(offset_raw)
                        lvl_bott_id = elem.get_Parameter(Bip.LEVEL_PARAM).AsElementId()
                        thickness = ToFloat(elem.get_Parameter(Bip.FLOOR_ATTR_THICKNESS_PARAM).AsDouble())
                        type_id = elem.FloorType.Id
                        # print([2, type_id])
                        elem_type = Document.GetElement(doc, type_id)
                        compound_struc = elem_type.GetCompoundStructure()
                        structure_idx = compound_struc.StructuralMaterialIndex
                        # print(structure_idx)
                        if structure_idx != -1:
                            structure_width_double = compound_struc.GetLayerWidth(structure_idx)
                            structure_width = ToFloat(structure_width_double)
                            lvl_dist = GetLvlDist(lvl_bott_id)
                            difference = round((lvl_dist - structure_width), 3)
                            # print(structure_width)
                            # print(difference)
                            # print(id)
                            if difference != 0:
                                text_note = " Structural layer width differs from level distance."
                                elem_wrngs.append(WarningElement(id, name, text_note))
                        if name.startswith("GD_"):
                            # we are assuming from the previous steps that the floor
                            # is hosted correctly.
                            offset_calc = offset
                            info = str(offset_calc)
                        elif name.startswith("GD-BA_"):
                            # we are assuming from the previous steps that the floors
                            # is hosted correctly.
                            # we are assuming that the floors compound structure
                            # fits with OKFF and OKRF levels
                            offset_calc = offset
                            info = str(offset_calc)
                        elem_info.append(StructuralElement(id, offset_calc, info))
                elif elem.Category.Name == "Skelettbau":
                    element_ids.append(id)
                    offset_raw = elem.get_Parameter(Bip.Z_OFFSET_VALUE).AsDouble()
                    offset = ToFloat(offset_raw)
                    info = str(offset)
                    elev_0 = elem.get_Parameter(Bip.STRUCTURAL_BEAM_END0_ELEVATION).AsDouble()
                    elev_1 = elem.get_Parameter(Bip.STRUCTURAL_BEAM_END1_ELEVATION).AsDouble()
                    if  elev_0 != 0 or elev_1 != 0:
                        text_note = " has Start- or Endebenenversatz." \
                        " Only allowed on slanted framing. Use z-Versatzwert."
                        elem_wrngs.append(WarningElement(id, name, text_note))
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
    elevation_double = level.get_Parameter(Bip.LEVEL_ELEV).AsDouble()
    elevation = ToFloat(elevation_double)
    level_info.append(LevelInfo(id, level.Name, elevation))

# get all fill patterns
fill_patterns = Fec(doc).OfClass(FillPatternElement).WhereElementIsNotElementType().ToElements()
# get id of solid fill
solid_fill = fill_patterns[0].Id

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
    colors_hsv.append((i, 0.5, 0.9))
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
tx = Transaction(doc, "check floor and framing level offsets")
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

        # Document.GetElement(doc, elem.id).get_Parameter(Bip.ALL_MODEL_MARK).Set(elem.info + " / " + str(elem.id))

    except:
        pass

# commit the changes to the revit model database
# end transaction
tx.Commit()

output = script.get_output()
for el in elem_wrngs:
    print("Note: " + str(el.name) + " with ID: " + output.linkify(el.id) + el.text)
