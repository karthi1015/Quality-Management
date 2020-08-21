# -*- coding: utf-8 -*-
import clr
clr.AddReference("RevitAPI")
clr.AddReference("System")
from System.Collections.Generic import List
from Autodesk.Revit.DB import FilteredElementCollector as Fec
from Autodesk.Revit.DB import BuiltInCategory as Bic
from Autodesk.Revit.DB import Transaction
from Autodesk.Revit.DB import FillPattern
from Autodesk.Revit.DB import FillPatternElement
from Autodesk.Revit.DB import OverrideGraphicSettings
from Autodesk.Revit.DB import View
from Autodesk.Revit.DB import ElementId
import Autodesk
import re

# reference the current open revit model to work with:
doc = __revit__.ActiveUIDocument.Document

# get all fill patterns
fill_patterns = Fec(doc).OfClass(FillPatternElement).WhereElementIsNotElementType().ToElements()


# get id of solid fill
solid_fill = fill_patterns[0].Id

# set colors
color_gd = Autodesk.Revit.DB.Color(177,199,56)
color_gd2 = Autodesk.Revit.DB.Color(126,150,56)

color_ba = Autodesk.Revit.DB.Color(3,147,188)
color_ba2 = Autodesk.Revit.DB.Color(0,64,128)

color_gd_ba = Autodesk.Revit.DB.Color(3,100,188)
color_gd_ba2 = Autodesk.Revit.DB.Color(0,25,128)

color_none = Autodesk.Revit.DB.Color(200,0,0)
color_none2 = Autodesk.Revit.DB.Color(128,0,0)

# create graphical overrides
# try is here to deal with the api change from 2019 to 2020
# when rvt 2019 is completely deprecated with SMP, delete try statement
# and use only except part as main operation
try:
    ogs_gd = OverrideGraphicSettings().SetProjectionFillColor(color_gd)
    ogs_gd.SetProjectionFillPatternId(solid_fill)
except:
    ogs_gd = OverrideGraphicSettings().SetSurfaceForegroundPatternColor(color_gd)
    ogs_gd.SetSurfaceForegroundPatternId(solid_fill)
ogs_gd.SetSurfaceTransparency(10)
ogs_gd.SetProjectionLineColor(color_gd2)

try:
    ogs_ba = OverrideGraphicSettings().SetProjectionFillColor(color_ba)
    ogs_ba.SetProjectionFillPatternId(solid_fill)
except:
    ogs_ba = OverrideGraphicSettings().SetSurfaceForegroundPatternColor(color_ba)
    ogs_ba.SetSurfaceForegroundPatternId(solid_fill)
ogs_ba.SetSurfaceTransparency(10)
ogs_ba.SetProjectionLineColor(color_ba2)

try:
    ogs_gd_ba = OverrideGraphicSettings().SetProjectionFillColor(color_gd_ba)
    ogs_gd_ba.SetProjectionFillPatternId(solid_fill)
except:
    ogs_gd_ba = OverrideGraphicSettings().SetSurfaceForegroundPatternColor(color_gd_ba)
    ogs_gd_ba.SetSurfaceForegroundPatternId(solid_fill)
ogs_gd_ba.SetSurfaceTransparency(10)
ogs_gd_ba.SetProjectionLineColor(color_gd_ba2)

try:
    ogs_none = OverrideGraphicSettings().SetProjectionFillColor(color_none)
    ogs_none.SetProjectionFillPatternId(solid_fill)
except:
    ogs_none = OverrideGraphicSettings().SetSurfaceForegroundPatternColor(color_none)
    ogs_none.SetSurfaceForegroundPatternId(solid_fill)
ogs_none.SetSurfaceTransparency(0)
ogs_none.SetProjectionLineColor(color_none2)

# connect to revit model elements via FilteredElementCollector
# collect all the floors
elements = Fec(doc).OfCategory(Bic.OST_Floors).WhereElementIsNotElementType().ToElements()

# regex to get material and thickness (_STB 25,5)
regex_mat = re.compile('_[A-ZÄÖÜ]+\ [0-9]?[,]?[0-9]')
# regex to get total thickness (__52,5)
regex_total = re.compile('__\d+,?\d?\d?')
regex_total_postfix = re.compile('__\d+,?\d?\d?_')

# create class to contain all info about element
class Element_info:
    def __init__(self, none, gd, gdba, so, soba, ba, match, type_name, id):
        self.none = none
        self.gd = gd
        self.gdba = gdba
        self.so = so
        self.soba = soba
        self.ba = ba
        self.match = match
        self.type_name = type_name
        self.id = id


# has to run over lists: aw and iw
def process_elements(element_list):
    match_list = []
    # check exterior elements
    for el in element_list:
        # ask every element for its type name
        el_type = el.type_name
        amount_of_mats = len(regex_mat.findall(el_type))
        el_total = len(regex_total.findall(el_type))
        el_total_postfix = len(regex_total_postfix.findall(el_type))
        # check multi material elements:
        if el_type.count("__") == 1 and amount_of_mats > 1 and el_total == 1:
        # check for not free text at the end
            if len(filter(None, re.split(regex_total, el_type))) == 1:
                match_list.append(el)
        # check for correct free text at the end
            elif el_total_postfix == 1:
                match_list.append(el)
        # ckeck single material elements with no total thickness
        elif el_type.count("__") == 0 and amount_of_mats == 1 and el_total == 0 and el.gdba == False and el.soba == False:
            match_list.append(el)
    return match_list

element_ids = []
elements_info = []

for element in elements:
    # gather information and create objects of Element_info class
    element_id = element.Id
    element_ids.append(element_id)
    element_type_name = element.Name
    element_gd = False
    element_gdba = False
    element_so = False
    element_soba = False
    element_ba = False
    if element_type_name.startswith("GD_"):
        element_gd = True
    elif element_type_name.startswith("GD-BA_"):
        element_gdba = True
    elif element_type_name.startswith("SO_"):
        element_so = True
    elif element_type_name.startswith("SO-BA_"):
        element_soba = True
    elif element_type_name.startswith("BA_"):
        element_ba = True
    element_info = Element_info(True, element_gd, element_gdba, element_so, element_soba, element_ba, False, element_type_name, element_id)
    elements_info.append(element_info)

elements_aw_iw = []

for element in elements_info:
    if element.gd or element.gdba or element.so or element.soba or element.ba:
        elements_aw_iw.append(element)

for el in process_elements(elements_aw_iw):
    el.match = True
    el.none = False

col1 = List[ElementId](element_ids)


# entering a transaction to modify the revit model database -------------------
# start transaction
tx = Transaction(doc, "check type names of elements")
tx.Start()

doc.ActiveView.IsolateElementsTemporary(col1)

# set graphical overrides
for element in elements_info:
    if element.match and (element.gd or element.so):
        doc.ActiveView.SetElementOverrides((element.id), ogs_gd)
    elif element.match and (element.gdba or element.soba):
        doc.ActiveView.SetElementOverrides((element.id), ogs_gd_ba)
    elif element.match and element.ba:
        doc.ActiveView.SetElementOverrides((element.id), ogs_ba)
    if element.none:
        doc.ActiveView.SetElementOverrides((element.id), ogs_none)


# commit the changes to the revit model database
# end transaction
tx.Commit()
