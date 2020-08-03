# -*- coding: utf-8 -*-
import clr
clr.AddReference("RevitAPI")
import Autodesk.Revit.DB as DB
from Autodesk.Revit.DB import FilteredElementCollector as Fec
from Autodesk.Revit.DB import BuiltInCategory as Bic
from Autodesk.Revit.DB import Document, ElementId, LinePatternElement
from Autodesk.Revit.DB import ElementQuickFilter, ElementFilter, ElementMulticategoryFilter
from rpw import doc
import csv
import os
from System.Collections.Generic import List
from datetime import date

# general data ---------------------------------------------------------------
today = date.today()
doc_name_list = str(doc.Title).rsplit("_", 1)
doc_name = doc_name_list[0].replace("_ZENTRALMODELL", "")

# functions ------------------------------------------------------------------
#  flatten list function
def list_flatten(elem_list):
    for i in elem_list:
        if type(i) == list:
            list_flatten(i)
        else:
            return i


# count all elements of certain BuiltInCategory -------------------------------
def Count_Bic(built_in_category):
    bic_name = str(built_in_category).replace("OST_", "")
    bic_elems = Fec(doc).OfCategory(built_in_category).WhereElementIsNotElementType().ToElements()
    return [len(bic_elems), bic_name]


# Warnings -------------------------------------------------------------------
# get all warnings
warning_elem = Document.GetWarnings(doc)

# elements with warnings
failing_elems_ids = []

for elem in warning_elem:
    failing_elem = elem.GetFailingElements()
    failing_elems_ids.append(failing_elem)

# fatten data structure and get ids of elements
warnings = []

for fail in failing_elems_ids:
    warnings.append(list_flatten(fail))

# all model elements ----------------------------------------------------------
categories = doc.Settings.Categories
model_cats = []
for category in categories:
    if str(category.CategoryType) == "Model":
        model_cats.append(category.Id)

nr_of_elems = 0
for i in model_cats:
    cat_elems = Fec(doc).OfCategoryId(i).WhereElementIsNotElementType().ToElements()
    nr_of_elems += len(cat_elems)




# data lists ------------------------------------------------------------------
#  headers
headers = []
# data = values
data = []

headers.append("Date")
data.append(str(today))
headers.append("Document name")
data.append(str(doc_name))
headers.append("Warnings")
data.append(len(warnings))
headers.append("Model elements")
data.append(nr_of_elems)

# regular Bic counting
bics_count = [Bic.OST_Views, Bic.OST_Sheets, Bic.OST_Rooms, Bic.OST_Areas, Bic.OST_RvtLinks, Bic.OST_Materials,\
                Bic.OST_IOSDetailGroups, Bic.OST_IOSModelGroups, Bic.OST_DesignOptionSets, Bic.OST_DesignOptions]
for bic in bics_count:
    headers.append(Count_Bic(bic)[1])
    data.append(Count_Bic(bic)[0])

# count linestyles
lines_cat = doc.Settings.Categories.get_Item(Bic.OST_Lines)
lines_subcat = lines_cat.SubCategories
nr_of_linestyles = 0
for i in lines_subcat:
    nr_of_linestyles += 1
headers.append("LineStyles")
data.append(nr_of_linestyles)

# count linestypes
linetypes = Fec(doc).OfClass(LinePatternElement)
nr_of_linetypes = 0
for i in linetypes:
    nr_of_linetypes += 1
headers.append("LineTypes")
data.append(nr_of_linetypes)

# write csv -------------------------------------------------------------------
folder = "F:/910_EDV/910_REVIT/Model Health Monitor/modeldata/" + str(doc_name)
try:
    os.mkdir(folder)
except OSError:
    pass

path = str(folder) + "/" + str(today) + ".csv"
with open(path, 'wb') as file:
    wr = csv.writer(file, dialect="excel", delimiter=";")
    wr.writerow(headers)
    wr.writerow(data)

print("txs for your help.")
