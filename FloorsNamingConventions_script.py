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
floors = Fec(doc).OfCategory(Bic.OST_Floors).WhereElementIsNotElementType().ToElements()


# make all lists to store floors in the process
floors_gd = []
floors_ba = []
floors_gd_ba = []

floors_gd_final = []
floors_ba_final = []
floors_gd_ba_final = []

floors_none_final = []

floor_ids = []


# regex to get material and thickness (_STB 25,5)
# _[A-ZÄÖÜ]+\ [0-9]?[,]?[0-9]
# regex to get total thickness (__52,5)
# __[0-9]?[0-9]+?[,]?[0-9]

regex_mat = re.compile('_[A-ZÄÖÜ]+\ [0-9]?[,]?[0-9]')
regex_total = re.compile('__\d+,?\d?\d?')
regex_total_postfix = re.compile('__\d+,?\d?\d?_')


# create main logic here..:

# first rough seperation
for floor in floors:
    floor_id = floor.Id
    floor_ids.append(floor_id)

    # ask every door for its type name
    floor_type = floor.Name

    # seperate AW_ from IW_ from AW-FA_ from IW-FA_ from -none-
    if floor_type.startswith("BA_"):
        floors_ba.append(floor)

    elif floor_type.startswith("GD_"):
        floors_gd.append(floor)

    elif floor_type.startswith("GD-BA_"):
        floors_gd_ba.append(floor)

    else:
        floors_none_final.append(floor)


# check structural floors
for floor in floors_gd:

    # ask every door for its type name
    floor_type = floor.Name
    amount_of_mats = len(regex_mat.findall(floor_type))
    floor_total = len(regex_total.findall(floor_type))
    floor_total_postfix = len(regex_total_postfix.findall(floor_type))

    # check multi material floors:
    if floor_type.count("__") == 1 and amount_of_mats > 1 and floor_total == 1:

    # check for not free text at the end
        if len(filter(None, re.split(regex_total, floor_type))) == 1:
            floors_gd_final.append(floor)

    # check for correct free text at the end
        elif floor_total_postfix == 1:
            floors_gd_final.append(floor)

        else:
            floors_none_final.append(floor)

    # ckeck single material floors with no total thickness
    elif floor_type.count("__") == 0 and amount_of_mats == 1 and floor_total == 0:
        floors_gd_final.append(floor)

    else:
        floors_none_final.append(floor)

# check interior floors
for floor in floors_ba:

    # ask every door for its type name
    floor_type = floor.Name
    amount_of_mats = len(regex_mat.findall(floor_type))
    floor_total = len(regex_total.findall(floor_type))
    floor_total_postfix = len(regex_total_postfix.findall(floor_type))

    #print("-"*15)
    #print(floor_type)
    #print(amount_of_mats)
    #print(floor_total)

    # check multi material floors:
    if floor_type.count("__") == 1 and amount_of_mats > 1 and floor_total == 1:

# check for not free text at the end
        if len(filter(None, re.split(regex_total, floor_type))) == 1:
            floors_ba_final.append(floor)

    # check for correct free text at the end
        elif floor_total_postfix == 1:
            floors_ba_final.append(floor)

        else:
            floors_none_final.append(floor)

    # ckeck single material floors with no total thickness
    elif floor_type.count("__") == 0 and amount_of_mats == 1 and floor_total == 0:
        floors_ba_final.append(floor)

    else:
        floors_none_final.append(floor)

# check combined floors
for floor in floors_gd_ba:

    # ask every door for its type name
    floor_type = floor.Name
    amount_of_mats = len(regex_mat.findall(floor_type))
    floor_total = len(regex_total.findall(floor_type))
    floor_total_postfix = len(regex_total_postfix.findall(floor_type))

    #print("-"*15)
    #print(floor_type)
    #print(amount_of_mats)
    #print(floor_total)

    # check multi material floors:
    if floor_type.count("__") == 1 and amount_of_mats > 1 and floor_total == 1:

# check for not free text at the end
        if len(filter(None, re.split(regex_total, floor_type))) == 1:
            floors_gd_ba_final.append(floor)

    # check for correct free text at the end
        elif floor_total_postfix == 1:
            floors_gd_ba_final.append(floor)

        else:
            floors_none_final.append(floor)

    # ckeck single material floors with no total thickness
    elif floor_type.count("__") == 0 and amount_of_mats == 1 and floor_total == 0:
        floors_gd_ba_final.append(floor)

    else:
        floors_none_final.append(floor)


# visualize incorrect floors
#print("Wrong naming:")
#for floor in floors_none_final:
#    print(floor.Name)


col1 = List[ElementId](floor_ids)

# entering a transaction to modify the revit model database
# start transaction
tx = Transaction(doc, "check type names of floors")
tx.Start()

doc.ActiveView.IsolateElementsTemporary(col1)

# set graphical overrides
for floor in floors_none_final:
    doc.ActiveView.SetElementOverrides((floor.Id), ogs_none)

for floor in floors_gd_final:
    doc.ActiveView.SetElementOverrides((floor.Id), ogs_gd)

for floor in floors_ba_final:
    doc.ActiveView.SetElementOverrides((floor.Id), ogs_ba)

for floor in floors_gd_ba_final:
    doc.ActiveView.SetElementOverrides((floor.Id), ogs_gd_ba)



# commit the changes to the revit model database
# end transaction
tx.Commit()
#print("successfully changed model")
