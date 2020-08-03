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

# connect to revit model elements via FilteredElementCollector
# collect all the elements
elements = Fec(doc).OfCategory(Bic.OST_Walls).WhereElementIsNotElementType().ToElements()
# get all fill patterns
fill_patterns = Fec(doc).OfClass(FillPatternElement).WhereElementIsNotElementType().ToElements()
# get id of solid fill
solid_fill = fill_patterns[0].Id

# set colors
color_aw = Autodesk.Revit.DB.Color(177,199,56)
color_aw2 = Autodesk.Revit.DB.Color(126,150,56)

color_iw = Autodesk.Revit.DB.Color(3,147,188)
color_iw2 = Autodesk.Revit.DB.Color(0,64,128)

color_none = Autodesk.Revit.DB.Color(200,0,0)
color_none2 = Autodesk.Revit.DB.Color(128,0,0)

# create graphical overrides
ogs_aw = OverrideGraphicSettings().SetProjectionFillColor(color_aw)
ogs_aw.SetProjectionFillPatternId(solid_fill)
ogs_aw.SetSurfaceTransparency(10)
ogs_aw.SetProjectionLineColor(color_aw2)

ogs_iw = OverrideGraphicSettings().SetProjectionFillColor(color_iw)
ogs_iw.SetProjectionFillPatternId(solid_fill)
ogs_iw.SetSurfaceTransparency(10)
ogs_iw.SetProjectionLineColor(color_iw2)

ogs_none = OverrideGraphicSettings().SetProjectionFillColor(color_none)
ogs_none.SetProjectionFillPatternId(solid_fill)
ogs_none.SetSurfaceTransparency(0)
ogs_none.SetProjectionLineColor(color_none2)

# regex to get material and thickness (_STB 25,5)
regex_mat = re.compile('_[A-ZÄÖÜ]+\ [0-9]?[,]?[0-9]')
# regex to get total thickness (__52,5)
regex_total = re.compile('__\d+,?\d?\d?')
regex_total_postfix = re.compile('__\d+,?\d?\d?_')


# create class to contain all info about element
class Element_info:

    def __init__(self, aw_fa, iw_fa, none, aw, iw, match, type_name, id):

        self.aw_fa = aw_fa
        self.iw_fa = iw_fa
        self.none = none
        self.aw = aw
        self.iw = iw
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
        elif el_type.count("__") == 0 and amount_of_mats == 1 and el_total == 0:
            match_list.append(el)

    return match_list

element_ids = []
elements_info = []

for element in elements:
    element_id = element.Id
    element_ids.append(element_id)

    element_type_name = element.Name

    element_aw_fa = element_type_name.startswith("AW-FA_")
    element_iw_fa = element_type_name.startswith("IW-FA_")
    element_aw = element_type_name.startswith("AW_")
    element_iw = element_type_name.startswith("IW_")

    element_info = Element_info(element_aw_fa, element_iw_fa, True, element_aw, element_iw, False, element_type_name, element_id)
    elements_info.append(element_info)


for element in elements_info:

    elements_aw = []
    elements_iw = []

    if element.aw:
        elements_aw.append(element)

    if element.iw:
        elements_iw.append(element)

    if element.aw_fa:
        el.none = False

    if element.iw_fa:
        el.none = False

    for el in process_elements(elements_aw):
        el.match = True
        el.none = False

    for el in process_elements(elements_iw):
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
    if element.match and (element.aw or element.aw_fa):
        doc.ActiveView.SetElementOverrides((element.id), ogs_aw)
    if element.match and (element.iw or element.iw_fa):
        doc.ActiveView.SetElementOverrides((element.id), ogs_iw)
    if element.none:
        doc.ActiveView.SetElementOverrides((element.id), ogs_none)


# commit the changes to the revit model database
# end transaction
tx.Commit()
