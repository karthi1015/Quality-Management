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
color_ast = Autodesk.Revit.DB.Color(177,199,56)
color_ast2 = Autodesk.Revit.DB.Color(126,150,56)

color_ist = Autodesk.Revit.DB.Color(3,147,188)
color_ist2 = Autodesk.Revit.DB.Color(0,64,128)

color_none = Autodesk.Revit.DB.Color(200,0,0)
color_none2 = Autodesk.Revit.DB.Color(128,0,0)

# create graphical overrides
ogs_ast = OverrideGraphicSettings().SetProjectionFillColor(color_ast)
ogs_ast.SetProjectionFillPatternId(solid_fill)
ogs_ast.SetSurfaceTransparency(10)
ogs_ast.SetProjectionLineColor(color_ast2)

ogs_ist = OverrideGraphicSettings().SetProjectionFillColor(color_ist)
ogs_ist.SetProjectionFillPatternId(solid_fill)
ogs_ist.SetSurfaceTransparency(10)
ogs_ist.SetProjectionLineColor(color_ist2)

ogs_none = OverrideGraphicSettings().SetProjectionFillColor(color_none)
ogs_none.SetProjectionFillPatternId(solid_fill)
ogs_none.SetSurfaceTransparency(0)
ogs_none.SetProjectionLineColor(color_none2)

# connect to revit model elements via FilteredElementCollector
# collect all the structural_columns
structural_columns = Fec(doc).OfCategory(Bic.OST_StructuralColumns).WhereElementIsNotElementType().ToElements()


# make all lists to store structural_columns in the process
structural_columns_ast = []
structural_columns_ist = []

structural_columns_ast_final = []
structural_columns_ist_final = []

structural_columns_none_final = []

structural_column_ids = []


# regex to get material and thickness (_STB 25,5)
# _[A-ZÄÖÜ]+\ [0-9]?[,]?[0-9]
# regex to get total thickness (__52,5)
# __[0-9]?[0-9]+?[,]?[0-9]

regex_rect = re.compile('_[A-ZÄÖÜ]+\ [0-9]?[,]?[0-9]+x[0-9]?[,]?[0-9]+')
regex_cyl = re.compile('_[A-ZÄÖÜ]+\ d[0-9]?[,]?[0-9]+')


# create main logic here..:

# first rough seperation
for structural_column in structural_columns:
    structural_column_id = structural_column.Id
    structural_column_ids.append(structural_column_id)

    # ask every structural_column for its type name
    structural_column_type = structural_column.Name

    # seperate AST_ from IST_ from -none-
    if structural_column_type.startswith("AST_"):
        structural_columns_ist.append(structural_column)

    elif structural_column_type.startswith("IST_"):
        structural_columns_ast.append(structural_column)

    else:
        structural_columns_none_final.append(structural_column)


# check exterior structural_columns
for structural_column in structural_columns_ast:

    # ask every structural_column for its type name
    structural_column_type = structural_column.Name
    amount_of_mats_rect = len(regex_rect.findall(structural_column_type))
    amount_of_mats_cyl = len(regex_cyl.findall(structural_column_type))

    # check naming with regex:
    if structural_column_type.count("__") == 0 and (amount_of_mats_rect == 1 or amount_of_mats_cyl == 1):
        structural_columns_ast_final.append(structural_column)

    else:
        structural_columns_none_final.append(structural_column)

# check interior structural_columns
for structural_column in structural_columns_ist:

    # ask every structural_column for its type name
    structural_column_type = structural_column.Name
    amount_of_mats_rect = len(regex_rect.findall(structural_column_type))
    amount_of_mats_cyl = len(regex_cyl.findall(structural_column_type))

    # check naming with regex:
    if structural_column_type.count("__") == 0 and (amount_of_mats_rect == 1 or amount_of_mats_cyl == 1):
        structural_columns_ist_final.append(structural_column)

    else:
        structural_columns_none_final.append(structural_column)



col1 = List[ElementId](structural_column_ids)

# entering a transaction to modify the revit model database
# start transaction
tx = Transaction(doc, "check type names of structural_columns")
tx.Start()

doc.ActiveView.IsolateElementsTemporary(col1)

# set graphical overrides
for structural_column in structural_columns_none_final:
    doc.ActiveView.SetElementOverrides((structural_column.Id), ogs_none)

for structural_column in structural_columns_ast_final:
    doc.ActiveView.SetElementOverrides((structural_column.Id), ogs_ast)

for structural_column in structural_columns_ist_final:
    doc.ActiveView.SetElementOverrides((structural_column.Id), ogs_ist)



# commit the changes to the revit model datastbse
# end transaction
tx.Commit()
#print("successfully changed model")
