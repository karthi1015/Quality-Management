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
color_ad = Autodesk.Revit.DB.Color(177,199,56)
color_ad2 = Autodesk.Revit.DB.Color(126,150,56)

color_db = Autodesk.Revit.DB.Color(3,147,188)
color_db2 = Autodesk.Revit.DB.Color(0,64,128)

color_none = Autodesk.Revit.DB.Color(200,0,0)
color_none2 = Autodesk.Revit.DB.Color(128,0,0)

# create graphical overrides
ogs_ad = OverrideGraphicSettings().SetProjectionFillColor(color_ad)
ogs_ad.SetProjectionFillPatternId(solid_fill)
ogs_ad.SetSurfaceTransparency(10)
ogs_ad.SetProjectionLineColor(color_ad2)

ogs_db = OverrideGraphicSettings().SetProjectionFillColor(color_db)
ogs_db.SetProjectionFillPatternId(solid_fill)
ogs_db.SetSurfaceTransparency(10)
ogs_db.SetProjectionLineColor(color_db2)

ogs_none = OverrideGraphicSettings().SetProjectionFillColor(color_none)
ogs_none.SetProjectionFillPatternId(solid_fill)
ogs_none.SetSurfaceTransparency(0)
ogs_none.SetProjectionLineColor(color_none2)

# connect to revit model elements via FilteredElementCollector
# collect all the ceilings
ceilings = Fec(doc).OfCategory(Bic.OST_Ceilings).WhereElementIsNotElementType().ToElements()


# make all lists to store ceilings in the process
ceilings_ad = []
ceilings_db = []

ceilings_ad_final = []
ceilings_db_final = []

ceilings_none_final = []

ceiling_ids = []


# regex to get material and thickness (_STB 25,5)
# _[A-ZÄÖÜ]+\ [0-9]?[,]?[0-9]
# regex to get total thickness (__52,5)
# __[0-9]?[0-9]+?[,]?[0-9]

regex_mat = re.compile('_[A-ZÄÖÜ]+\ [0-9]?[,]?[0-9]')
regex_total = re.compile('__\d+,?\d?\d?')
regex_total_postfix = re.compile('__\d+,?\d?\d?_')


# create main logic here..:

# first rough seperation
for ceiling in ceilings:
    ceiling_id = ceiling.Id
    ceiling_ids.append(ceiling_id)

    # ask every ceiling for its type name
    ceiling_type = ceiling.Name

    # seperate AD_ from DB_ from -none-
    if ceiling_type.startswith("AD_"):
        ceilings_db.append(ceiling)

    elif ceiling_type.startswith("DB_"):
        ceilings_ad.append(ceiling)

    else:
        ceilings_none_final.append(ceiling)


# check suspended ceilings
for ceiling in ceilings_ad:

    # ask every ceiling for its type name
    ceiling_type = ceiling.Name
    amount_of_mats = len(regex_mat.findall(ceiling_type))
    ceiling_total = len(regex_total.findall(ceiling_type))
    ceiling_total_postfix = len(regex_total_postfix.findall(ceiling_type))

    # check multi material ceilings:
    if ceiling_type.count("__") == 1 and amount_of_mats > 1 and ceiling_total == 1:

    # check for not free text at the end
        if len(filter(None, re.split(regex_total, ceiling_type))) == 1:
            ceilings_ad_final.append(ceiling)

    # check for correct free text at the end
        elif ceiling_total_postfix == 1:
            ceilings_ad_final.append(ceiling)

        else:
            ceilings_none_final.append(ceiling)

    # ckeck single material ceilings with no total thickness
    elif ceiling_type.count("__") == 0 and amount_of_mats == 1 and ceiling_total == 0:
        ceilings_ad_final.append(ceiling)

    else:
        ceilings_none_final.append(ceiling)

# check cladding ceilings
for ceiling in ceilings_db:

    # ask every ceiling for its type name
    ceiling_type = ceiling.Name
    amount_of_mats = len(regex_mat.findall(ceiling_type))
    ceiling_total = len(regex_total.findall(ceiling_type))
    ceiling_total_postfix = len(regex_total_postfix.findall(ceiling_type))

    #print("-"*15)
    #print(ceiling_type)
    #print(amount_of_mats)
    #print(ceiling_total)

    # check multi material ceilings:
    if ceiling_type.count("__") == 1 and amount_of_mats > 1 and ceiling_total == 1:

# check for not free text at the end
        if len(filter(None, re.split(regex_total, ceiling_type))) == 1:
            ceilings_db_final.append(ceiling)

    # check for correct free text at the end
        elif ceiling_total_postfix == 1:
            ceilings_db_final.append(ceiling)

        else:
            ceilings_none_final.append(ceiling)

    # ckeck single material ceilings with no total thickness
    elif ceiling_type.count("__") == 0 and amount_of_mats == 1 and ceiling_total == 0:
        ceilings_db_final.append(ceiling)

    else:
        ceilings_none_final.append(ceiling)



col1 = List[ElementId](ceiling_ids)

# entering a transaction to modify the revit model database
# start transaction
tx = Transaction(doc, "check type names of ceilings")
tx.Start()

doc.ActiveView.IsolateElementsTemporary(col1)

# set graphical overrides
for ceiling in ceilings_none_final:
    doc.ActiveView.SetElementOverrides((ceiling.Id), ogs_none)

for ceiling in ceilings_ad_final:
    doc.ActiveView.SetElementOverrides((ceiling.Id), ogs_ad)

for ceiling in ceilings_db_final:
    doc.ActiveView.SetElementOverrides((ceiling.Id), ogs_db)



# commit the changes to the revit model datadbse
# end transaction
tx.Commit()
#print("successfully changed model")
