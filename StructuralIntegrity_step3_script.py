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
from rpw.ui.forms import (FlexForm, Label, ComboBox, Button)
from rpw.ui.forms import CommandLink, TaskDialog, SelectFromList
from rpw import doc
import re

# mouse hover-over text
__doc__ = 'Visualizes the level offset properties of Walls, Floors,' \
          ' Structural Columns and Structural Framing.' \
          ' Every unique offset has a distict color.' \
          ' Walls with top or bottom attachement are colored transparent orange.'


class StructuralElement:
    # class containing information about the elements of includet categories
    def __init__(self, id, offset, attached):
        self.id = id
        self.offset = offset
        self.attached = attached


class WarningElement:
    # class of elements that are suspicious but not necessairily incorred.
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


def ToInt(double):
    convert = UnitUtils.ConvertFromInternalUnits(double, DisplayUnitType.DUT_METERS)
    converted = int(round(round(convert, 3) * 1000))
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
    current_lvl_elev = ToInt(current_lvl_elev_double)
    for level in level_info:
        if lvl_name_new == level.name:
            # print(current_lvl_elev)
            # print(level.elevation)
            dist = current_lvl_elev - level.elevation
    # print(dist)
    return dist


def GetElemProps0(elem_lst):
    # this function takes all elements in the categories list and creates an object of the
    # StructuralElement class and appends it to the elem_info list.
    for elem in elem_lst:
            try:
                id = elem.Id
                name = elem.Name
                attached = 0
                if elem.Category.Name == "Geschossdecken":
                    if elem.get_Parameter(Bip.FLOOR_PARAM_IS_STRUCTURAL).AsInteger() == 1:
                        element_ids.append(id)
                        offset_raw = elem.get_Parameter(Bip.FLOOR_HEIGHTABOVELEVEL_PARAM).AsDouble()
                        # print([1, offset_raw])
                        offset = ToInt(offset_raw)
                        if ui_select == 1:
                            lvl_bott_id = elem.get_Parameter(Bip.LEVEL_PARAM).AsElementId()
                            thickness = ToInt(elem.get_Parameter(Bip.FLOOR_ATTR_THICKNESS_PARAM).AsDouble())
                            type_id = elem.FloorType.Id
                            # print([2, type_id])
                            elem_type = Document.GetElement(doc, type_id)
                            compound_struc = elem_type.GetCompoundStructure()
                            structure_idx = compound_struc.StructuralMaterialIndex
                            # print(structure_idx)
                            if structure_idx != -1:
                                structure_width_double = compound_struc.GetLayerWidth(structure_idx)
                                structure_width = ToInt(structure_width_double)
                                lvl_dist = GetLvlDist(lvl_bott_id)
                                difference = lvl_dist - structure_width
                                # print(structure_width)
                                # print(difference)
                                # print(id)
                                if difference != 0:
                                    offset = offset + difference
                                    text_note = " Structural layer width differs from level distance."
                                    elem_wrngs.append(WarningElement(id, name, text_note))
                                # print(offset, "----------------------------")
                        elem_info.append(StructuralElement(id, offset, attached))
                elif elem.Category.Name == "Skelettbau":
                    element_ids.append(id)
                    offset_raw = elem.get_Parameter(Bip.Z_OFFSET_VALUE).AsDouble()
                    offset = ToInt(offset_raw)
                    elev_0 = ToInt(elem.get_Parameter(Bip.STRUCTURAL_BEAM_END0_ELEVATION).AsDouble())
                    elev_1 = ToInt(elem.get_Parameter(Bip.STRUCTURAL_BEAM_END1_ELEVATION).AsDouble())
                    if  ((elev_0 != 0) or (elev_1 != 0)):
                        attached = 1
                        text_note = " has Start- or Endebenenversatz." \
                        " Only allowed on slanted framing. Use z-Versatzwert."
                        elem_wrngs.append(WarningElement(id, name, text_note))
                    elif ui_select == 1:
                            elev_top = ToInt(elem.get_Parameter(Bip.STRUCTURAL_ELEVATION_AT_TOP).AsDouble())
                            elev_bott = ToInt(elem.get_Parameter(Bip.STRUCTURAL_ELEVATION_AT_BOTTOM).AsDouble())
                            height = elev_top - elev_bott
                            offset = offset - height
                    elem_info.append(StructuralElement(id, offset, attached))
                else:
                    pass
            except:
                pass


def GetElemProps1(elem_lst):
    for elem in elem_lst:
        try:
            id = elem.Id
            name = elem.Name
            attached = 0
            if elem.Category.Name == "Wände":
                attached += elem.get_Parameter(Bip.WALL_TOP_IS_ATTACHED).AsInteger()
                attached += elem.get_Parameter(Bip.WALL_BOTTOM_IS_ATTACHED).AsInteger()
                if elem.get_Parameter(Bip.WALL_STRUCTURAL_SIGNIFICANT).AsInteger() == 1:
                    element_ids.append(id)
                    offset_raw = elem.get_Parameter(wall_constraint).AsDouble()
                    offset = ToInt(offset_raw)
                    elem_info.append(StructuralElement(id, offset, attached))
            elif elem.Category.Name == "Tragwerksstützen":
                element_ids.append(id)
                offset_raw = elem.get_Parameter(column_constraint).AsDouble()
                offset = ToInt(offset_raw)
                elem_info.append(StructuralElement(id, offset, attached))
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
    elevation = ToInt(elevation_double)
    level_info.append(LevelInfo(id, level.Name, elevation))

# get all fill patterns
fill_patterns = Fec(doc).OfClass(FillPatternElement).WhereElementIsNotElementType().ToElements()
# get id of solid fill
solid_fill = fill_patterns[0].Id

# connect to revit model elements via FilteredElementCollector
# collect all the elements of categories
categories0 = [Bic.OST_Floors, Bic.OST_StructuralFraming]
categories1 = [Bic.OST_Walls, Bic.OST_StructuralColumns]
col_bic0 = List[Bic](categories0)
col_bic1 = List[Bic](categories1)
struct_elems0 = Fec(doc).WherePasses(ElementMulticategoryFilter(col_bic0)).WhereElementIsNotElementType().ToElements()
struct_elems1 = Fec(doc).WherePasses(ElementMulticategoryFilter(col_bic1)).WhereElementIsNotElementType().ToElements()

# prepare lists
elem_info = []
element_ids = []
elem_wrngs = []

# create ui an get input
choose_dict = {"Base constraint" :0, "Top constraint" :1}
components = [Label('Choose top or bottom constraint:'),
               ComboBox("combobox", choose_dict), Button('Select')]
form = FlexForm('Title', components)
form.show()
values = form.values
ui_select = values["combobox"]
if ui_select == 0:
    wall_constraint = Bip.WALL_BASE_OFFSET
    column_constraint = Bip.FAMILY_BASE_LEVEL_OFFSET_PARAM
if ui_select == 1:
    wall_constraint = Bip.WALL_TOP_OFFSET
    column_constraint = Bip.FAMILY_TOP_LEVEL_OFFSET_PARAM

# process elements
GetElemProps0(struct_elems0)
GetElemProps1(struct_elems1)

# create colors
color_att = Autodesk.Revit.DB.Color(236,77,0)
color_att2 = Autodesk.Revit.DB.Color(153,51,0)

# create overrides
try:
    ogs_att = OverrideGraphicSettings().SetProjectionFillColor(color_att)
    ogs_att.SetProjectionFillPatternId(solid_fill)
except:
    ogs_att = OverrideGraphicSettings().SetSurfaceForegroundPatternColor(color_att)
    ogs_att.SetSurfaceForegroundPatternId(solid_fill)
ogs_att.SetSurfaceTransparency(10)
ogs_att.SetProjectionLineColor(color_att2)

#get unique offsets
offsets = []
for elem in elem_info:
    offsets.append(elem.offset)
unique_offsets = set(offsets)

#get hsv color range
colors_hsv = []
for i in [x * 0.01 for x in range(0, 100, (99 / (len(unique_offsets)-1)))]:

    colors_hsv.append((i, 0.5, 0.9))

def hsv2rgb(h,s,v):
    # convert hsv to rgb
    return tuple(round(i * 255) for i in colorsys.hsv_to_rgb(h,s,v))


# create rgb colors
colors_rgb = []
for color in colors_hsv:
    colors_rgb.append(hsv2rgb(color[0], color[1], color[2]))

offset_color = dict(zip(unique_offsets, colors_rgb))

ogs = OverrideGraphicSettings().SetSurfaceForegroundPatternId(solid_fill)
ogs.SetCutForegroundPatternId(solid_fill)

# entering a transaction to modify the revit model database
# start transaction
tx = Transaction(doc, "check structural level offsets")
tx.Start()

# isolate all elements of categories
col1 = List[ElementId](element_ids)
doc.ActiveView.IsolateElementsTemporary(col1)

# set graphical overrides
for elem in elem_info:
    try:
        if elem.attached == 0:
            color = offset_color.get(elem.offset)
            color_revit = Autodesk.Revit.DB.Color(color[0], color[1], color[2])
            ogs.SetSurfaceForegroundPatternColor(color_revit)
            ogs.SetCutForegroundPatternColor(color_revit)
            doc.ActiveView.SetElementOverrides((elem.id), ogs)
        elif elem.attached != 0:
            doc.ActiveView.SetElementOverrides((elem.id), ogs_att)
            print("NOTE: Transparent orange element with ID: " + output.linkify(elem.id) + \
            " is attached. Will not be automatically checked.")
        # Document.GetElement(doc, elem.id).get_Parameter(Bip.ALL_MODEL_MARK).Set(str(elem.offset))
    except:
        pass

# commit the changes to the revit model database
# end transaction
tx.Commit()
#
output = script.get_output()
for el in elem_wrngs:
    print("Note: " + str(el.name) + " with ID: " + output.linkify(el.id) + el.text)
