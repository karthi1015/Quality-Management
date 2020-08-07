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
color_d = Autodesk.Revit.DB.Color(177,199,56)
color_d2 = Autodesk.Revit.DB.Color(126,150,56)

color_da = Autodesk.Revit.DB.Color(3,147,188)
color_da2 = Autodesk.Revit.DB.Color(0,64,128)

color_d_da = Autodesk.Revit.DB.Color(3,100,188)
color_d_da2 = Autodesk.Revit.DB.Color(0,25,128)

color_none = Autodesk.Revit.DB.Color(200,0,0)
color_none2 = Autodesk.Revit.DB.Color(128,0,0)

# create graphical overrides
# try is here to deal with the api change from 2019 to 2020
# when rvt 2019 is completely deprecated with SMP, delete try statement
# and use only except part as main operation
try:
    ogs_d = OverrideGraphicSettings().SetProjectionFillColor(color_d)
    ogs_d.SetProjectionFillPatternId(solid_fill)
except:
    ogs_d = OverrideGraphicSettings().SetSurfaceForegroundPatternColor(color_d)
    ogs_d.SetSurfaceForegroundPatternId(solid_fill)
ogs_d.SetSurfaceTransparency(10)
ogs_d.SetProjectionLineColor(color_d2)

try:
    ogs_da = OverrideGraphicSettings().SetProjectionFillColor(color_da)
    ogs_da.SetProjectionFillPatternId(solid_fill)
except:
    ogs_da = OverrideGraphicSettings().SetSurfaceForegroundPatternColor(color_da)
    ogs_da.SetSurfaceForegroundPatternId(solid_fill)
ogs_da.SetSurfaceTransparency(10)
ogs_da.SetProjectionLineColor(color_da2)

try:
    ogs_d_da = OverrideGraphicSettings().SetProjectionFillColor(color_d_da)
    ogs_d_da.SetProjectionFillPatternId(solid_fill)
except:
    ogs_d_da = OverrideGraphicSettings().SetSurfaceForegroundPatternColor(color_d_da)
    ogs_d_da.SetSurfaceForegroundPatternId(solid_fill)
ogs_d_da.SetSurfaceTransparency(10)
ogs_d_da.SetProjectionLineColor(color_d_da2)

try:
    ogs_none = OverrideGraphicSettings().SetProjectionFillColor(color_none)
    ogs_none.SetProjectionFillPatternId(solid_fill)
except:
    ogs_none = OverrideGraphicSettings().SetSurfaceForegroundPatternColor(color_none)
    ogs_none.SetSurfaceForegroundPatternId(solid_fill)
ogs_none.SetSurfaceTransparency(0)
ogs_none.SetProjectionLineColor(color_none2)

# connect to revit model elements via FilteredElementCollector
# collect all the roofs
roofs = Fec(doc).OfCategory(Bic.OST_Roofs).WhereElementIsNotElementType().ToElements()

# make all lists to store roofs in the process
roofs_d = []
roofs_da = []
roofs_d_da = []

roofs_d_final = []
roofs_da_final = []
roofs_d_da_final = []

roofs_none_final = []

roof_ids = []


# regex to get material and thickness (_STB 25,5)
# _[A-ZÄÖÜ]+\ [0-9]?[,]?[0-9]
# regex to get total thickness (__52,5)
# __[0-9]?[0-9]+?[,]?[0-9]

regex_mat = re.compile('_[A-ZÄÖÜ]+\ [0-9]?[,]?[0-9]')
regex_total = re.compile('__\d+,?\d?\d?')
regex_total_postfix = re.compile('__\d+,?\d?\d?_')


# create main logic here..:

# first rough seperation
for roof in roofs:
    roof_id = roof.Id
    roof_ids.append(roof_id)

    # ask every door for its type name
    roof_type = roof.Name

    # seperate AW_ from IW_ from AW-FA_ from IW-FA_ from -none-
    if roof_type.startswith("DA_"):
        roofs_da.append(roof)

    elif roof_type.startswith("D_"):
        roofs_d.append(roof)

    elif roof_type.startswith("D-DA_"):
        roofs_d_da.append(roof)

    else:
        roofs_none_final.append(roof)


# check structural roofs
for roof in roofs_d:

    # ask every roof for its type name
    roof_type = roof.Name
    amount_of_mats = len(regex_mat.findall(roof_type))
    roof_total = len(regex_total.findall(roof_type))
    roof_total_postfix = len(regex_total_postfix.findall(roof_type))

    # check multi material roofs:
    if roof_type.count("__") == 1 and amount_of_mats > 1 and roof_total == 1:

    # check for not free text at the end
        if len(filter(None, re.split(regex_total, roof_type))) == 1:
            roofs_d_final.append(roof)

    # check for correct free text at the end
        elif roof_total_postfix == 1:
            roofs_d_final.append(roof)

        else:
            roofs_none_final.append(roof)

    # ckeck single material roofs with no total thickness
    elif roof_type.count("__") == 0 and amount_of_mats == 1 and roof_total == 0:
        roofs_d_final.append(roof)

    else:
        roofs_none_final.append(roof)

# check interior roofs
for roof in roofs_da:

    # ask every door for its type name
    roof_type = roof.Name
    amount_of_mats = len(regex_mat.findall(roof_type))
    roof_total = len(regex_total.findall(roof_type))
    roof_total_postfix = len(regex_total_postfix.findall(roof_type))

    # check multi material roofs:
    if roof_type.count("__") == 1 and amount_of_mats > 1 and roof_total == 1:

# check for not free text at the end
        if len(filter(None, re.split(regex_total, roof_type))) == 1:
            roofs_da_final.append(roof)

    # check for correct free text at the end
        elif roof_total_postfix == 1:
            roofs_da_final.append(roof)

        else:
            roofs_none_final.append(roof)

    # ckeck single material roofs with no total thickness
    elif roof_type.count("__") == 0 and amount_of_mats == 1 and roof_total == 0:
        roofs_da_final.append(roof)

    else:
        roofs_none_final.append(roof)

# check combined roofs
for roof in roofs_d_da:

    # ask every door for its type name
    roof_type = roof.Name
    amount_of_mats = len(regex_mat.findall(roof_type))
    roof_total = len(regex_total.findall(roof_type))
    roof_total_postfix = len(regex_total_postfix.findall(roof_type))

    # check multi material roofs:
    if roof_type.count("__") == 1 and amount_of_mats > 1 and roof_total == 1:

# check for not free text at the end
        if len(filter(None, re.split(regex_total, roof_type))) == 1:
            roofs_d_da_final.append(roof)

    # check for correct free text at the end
        elif roof_total_postfix == 1:
            roofs_d_da_final.append(roof)

        else:
            roofs_none_final.append(roof)

    # ckeck single material roofs with no total thickness
    elif roof_type.count("__") == 0 and amount_of_mats == 1 and roof_total == 0:
        roofs_d_da_final.append(roof)

    else:
        roofs_none_final.append(roof)

col1 = List[ElementId](roof_ids)

# entering a transaction to modify the revit model datadase
# start transaction
tx = Transaction(doc, "check type names of roofs")
tx.Start()

doc.ActiveView.IsolateElementsTemporary(col1)

# set graphical overrides
for roof in roofs_none_final:
    doc.ActiveView.SetElementOverrides((roof.Id), ogs_none)

for roof in roofs_d_final:
    doc.ActiveView.SetElementOverrides((roof.Id), ogs_d)

for roof in roofs_da_final:
    doc.ActiveView.SetElementOverrides((roof.Id), ogs_da)

for roof in roofs_d_da_final:
    doc.ActiveView.SetElementOverrides((roof.Id), ogs_d_da)



# commit the changes to the revit model datadase
# end transaction
tx.Commit()
#print("successfully changed model")
