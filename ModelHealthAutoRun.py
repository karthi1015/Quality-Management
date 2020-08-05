# -*- coding: utf-8 -*-
import clr
clr.AddReference("RevitAPI")
from pyrevit import HOST_APP
import Autodesk.Revit.DB as DB
from Autodesk.Revit.DB import FilteredElementCollector as Fec
from Autodesk.Revit.DB import BuiltInCategory as Bic
from Autodesk.Revit.DB import Document, ElementId, LinePatternElement
from Autodesk.Revit.DB import ElementQuickFilter, ElementFilter, ElementMulticategoryFilter
import re
import csv
import os
from System.Collections.Generic import List
from datetime import date

# general data ---------------------------------------------------------------
today = date.today()


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


def Naming_Match(cat_elem_list):
    # check interior cat_elems
    # return a list with index 0 = number of match and index 1 = number of nomatch
    cat_match_list = []
    cat_nomatch_list = []
    for cat_elem in cat_elems_list:
        # ask every door for its type name
        cat_elem_type = cat_elem.Name
        amount_of_mats = len(regex_cat_elem_mat.findall(cat_elem_type))
        cat_elem_total = len(regex_cat_elem_total.findall(cat_elem_type))
        cat_elem_total_postfix = len(regex_cat_elem_total_postfix.findall(cat_elem_type))
        # check multi material cat_elems:
        if cat_elem_type.count("__") == 1 and amount_of_mats > 1 and cat_elem_total == 1:
            # check for not free text at the end
            if len(filter(None, re.split(regex_cat_elem_total, cat_elem_type))) == 1:
                cat_match_list.append(cat_elem)
            # check for correct free text at the end
        elif cat_elem_total_postfix == 1:
                cat_match_list.append(cat_elem)
            else:
                cat_match_list.append(cat_elem)
        # ckeck single material cat_elems with no total thickness
        elif cat_elem_type.count("__") == 0 and amount_of_mats == 1 and cat_elem_total == 0:
            cat_match_list.append(cat_elem)
        else:
            cat_nomatch_list.append(cat_elem)
    return [len(cat_match_list), len(cat_nomatch_list)]


# __models__ is set to a list of model file paths------------------------------
# __models__ = ['C:\model1.rvt']
for model in __models__:
    uidoc = HOST_APP.uiapp.OpenAndActivateDocument(model)
    doc = uidoc.Document

    # do something here with the document
    doc_name_list = str(doc.Title)
    # .rsplit("_", 1)
    doc_name = doc_name_list.replace("_ZENTRALMODELL", "")

    # Warnings -----------------------------------------------------------------
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

    # all model elements ------------------------------------------------------
    categories = doc.Settings.Categories
    model_cats = []
    for category in categories:
        if str(category.CategoryType) == "Model":
            model_cats.append(category.Id)

    nr_of_elems = 0
    for i in model_cats:
        cat_elems = Fec(doc).OfCategoryId(i).WhereElementIsNotElementType().ToElements()
        nr_of_elems += len(cat_elems)

    # Naming Conventions ------------------------------------------------------

    # regex to get material and thickness
    regex_mat = re.compile('_[A-ZÄÖÜ]+\ [0-9]?[,]?[0-9]')
    # regex to get total thickness
    regex_total = re.compile('__\d+,?\d?\d?')
    # regex to get total thickness and suffix
    regex_total_postfix = re.compile('__\d+,?\d?\d?_')

    # Walls naming -------------------------------------------------------
    # connect to revit model elements via FilteredElementCollector
    # collect all the elements
    elements = Fec(doc).OfCategory(Bic.OST_Walls).WhereElementIsNotElementType().ToElements()

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


    elements_info = []

    for element in elements:
        element_id = element.Id
        element_type_name = element.Name
        element_aw_fa = element_type_name.startswith("AW-FA_")
        element_iw_fa = element_type_name.startswith("IW-FA_")
        element_aw = element_type_name.startswith("AW_")
        element_iw = element_type_name.startswith("IW_")
        element_info = Element_info(element_aw_fa, element_iw_fa, True, element_aw, element_iw, False, element_type_name, element_id)
        elements_info.append(element_info)

    elements_aw_iw = []

    for element in elements_info:
        if element.aw or element.iw:
            elements_aw_iw.append(element)
        if element.aw_fa:
            element.none = False
            element.match = True
        if element.iw_fa:
            element.none = False
            element.match = True

    for el in process_elements(elements_aw_iw):
        el.match = True
        el.none = False

    # count elements with correct and incorrect naming
    nr_of_name_walls_correct = 0
    nr_of_name_walls_incorrect = 0

    for element in elements_info:
        if element.match and (element.aw or element.aw_fa):
            nr_of_name_walls_correct += 1
        if element.match and (element.iw or element.iw_fa):
            nr_of_name_walls_correct += 1
        if element.none:
            nr_of_name_walls_incorrect += 1


    # Structural Columns naming ------------------------------------------
    # connect to revit model elements via FilteredElementCollector
    # collect all the structural columns
    strct_clms = Fec(doc).OfCategory(Bic.OST_StructuralColumns).WhereElementIsNotElementType().ToElements()

    # make all lists to store structural columns in the process
    strct_clms_check = []
    strct_clms_none_final = 0

    # regex for rectangular columns
    regex_rect = re.compile('_[A-ZÄÖÜ]+\ [0-9]?[,]?[0-9]+x[0-9]?[,]?[0-9]+')
    # regex for cylindrical columns
    regex_cyl = re.compile('_[A-ZÄÖÜ]+\ d[0-9]?[,]?[0-9]+')

    # first rough seperation
    for strct_clm in strct_clms:
        # ask every structural columns for its type name
        strct_clm_type = strct_clm.Name
        # seperate AST_ from IST_ from -none-
        if strct_clm_type.startswith("AST_") or strct_clm_type.startswith("IST_"):
            strct_clms_check.append(strct_clm)
        else:
            strct_clms_none_final += 1

    nr_of_name_clms_correct = 0
    nr_of_name_clms_incorrect = 0

    # check exterior structural columns
    for strct_clm in strct_clms_check:
        # ask every structural columns for its type name
        strct_clm_type = strct_clm.Name
        amount_of_mats_rect = len(regex_rect.findall(strct_clm_type))
        amount_of_mats_cyl = len(regex_cyl.findall(strct_clm_type))
        # check naming with regex:
        if strct_clm_type.count("__") == 0 and (amount_of_mats_rect == 1 or amount_of_mats_cyl == 1):
            nr_of_name_clms_correct += 1
        else:
            nr_of_name_clms_incorrect += 1

    # Roofs Floors naming ------------------------------------------------------
    def Name_Floors_Roofs(bic_ost_category, prfx_cvr, prfx_strct, prfx_comb):
        # connect to revit model elements via FilteredElementCollector
        # collect all the roofs
        cat_elems = Fec(doc).OfCategory(bic_ost_category).WhereElementIsNotElementType().ToElements()
        # make all lists to store cat_elems in the process
        cat_elems_check = []
        cat_elems_none_final = 0
        # first rough seperation
        for cat_elem in cat_elems:
            # ask every door for its type name
            cat_elem_type = cat_elem.Name
            # seperate AW_ from IW_ from AW-FA_ from IW-FA_ from -none-
            if cat_elem_type.startswith(prfx_cvr)\
            or cat_elem_type.startswith(prfx_strct)\
            or cat_elem_type.startswith(prfx_comb):
                cat_elems_check.append(cat_elem)
            else:
                cat_elems_none_final += 1
        return [Naming_Match(cat_elems_check)[0], cat_elems_none_final + Naming_Match(cat_elems_check)[1]]


    nr_of_name_roofs_correct = Name_Floors_Roofs(Bic.OST_Roofs, "DA_", "D_", "D-DA_")[0]
    nr_of_name_roofs_incorrect = Name_Floors_Roofs(Bic.OST_Roofs, "DA_", "D_", "D-DA_")[1]
    nr_of_name_floors_correct = Name_Floors_Roofs(Bic.OST_Floors, "BA_", "GD_", "GD-BA_")[0]
    nr_of_name_floors_incorrect = Name_Floors_Roofs(Bic.OST_Floors, "BA_", "GD_", "GD-BA_")[1]

    # Ceiling names ----------------------------------------------------------
    # connect to revit model elements via FilteredElementCollector
    # collect all the ceilings
    ceilings = Fec(doc).OfCategory(Bic.OST_Ceilings).WhereElementIsNotElementType().ToElements()

    # make all lists to store ceilings in the process
    ceilings_check = []
    ceilings_none_final = 0

    # first rough seperation
    for ceiling in ceilings:
        # ask every ceiling for its type name
        ceiling_type = ceiling.Name
        # seperate AD_ from DB_ from -none-
        if ceiling_type.startswith("AD_") or ceiling_type.startswith("DB_"):
            ceilings_check.append(ceiling)
        else:
            ceilings_none_final += 1

    nr_of_name_ceilings_correct = Naming_Match(ceilings_check)[0]
    nr_of_name_ceilings_incorrect = Naming_Match(ceilings_check)[1]\
                                    + ceilings_none_final


    # data lists --------------------------------------------------------------
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
    headers.append("WallName correct")
    data.append(nr_of_name_walls_correct)
    headers.append("WallName incorrect")
    data.append(nr_of_name_walls_incorrect)
    headers.append("ColumNname correct")
    data.append(nr_of_name_clms_correct)
    headers.append("ColumnName incorrect")
    data.append(nr_of_name_clms_incorrect)
    headers.append("RoofName correct")
    data.append(nr_of_name_roofs_correct)
    headers.append("RoofName incorrect")
    data.append(nr_of_name_roofs_incorrect)
    headers.append("FloorName correct")
    data.append(nr_of_name_floors_correct)
    headers.append("FloorName incorrect")
    data.append(nr_of_name_floors_incorrect)
    headers.append("CeilingName correct")
    data.append(nr_of_name_ceilings_correct)
    headers.append("CeilingName incorrect")
    data.append(nr_of_name_ceilings_incorrect)

    # regular Bic counting
    bics_count = [Bic.OST_Views, Bic.OST_Sheets, Bic.OST_Rooms, Bic.OST_Areas, Bic.OST_RvtLinks, Bic.OST_Materials,\
                    Bic.OST_IOSDetailGroups, Bic.OST_IOSModelGroups, Bic.OST_DesignOptionSets, Bic.OST_DesignOptions,\
                    Bic.OST_RasterImages, Bic.OST_Levels, Bic.OST_Grids, Bic.OST_GenericModel, Bic.OST_FillPatterns,\
                    Bic.OST_Revisions]
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
    # write modeldata
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

    # write column configuration file for power bi
    with open("F:/910_EDV/910_REVIT/Model Health Monitor/Columns.csv", 'wb') as file2:
        wr = csv.writer(file2, dialect="excel", delimiter=";")
        for header in headers:
            wr.writerow([header])



# open console
# run:
# pyrevit run "C:\Users\yschindel\github\Quality-Management\ModelHealthAutoRun.py" --revit=2019 "F:\910_EDV\910_REVIT\Model Health Monitor\ListOfModelsToProcess_2019.txt"
