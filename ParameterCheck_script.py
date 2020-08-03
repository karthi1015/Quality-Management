# -*- coding: utf-8 -*-
import clr
clr.AddReference("RevitAPI")
clr.AddReference("System")
from System.Collections.Generic import List
from Autodesk.Revit.DB import FilteredElementCollector as Fec
from Autodesk.Revit.DB import BuiltInCategory as Bic
from Autodesk.Revit.DB import Transaction,  FillPattern, FillPatternElement
from Autodesk.Revit.DB import OverrideGraphicSettings, View, ElementId
from Autodesk.Revit.DB import Category, Subelement, Document
import Autodesk
import re
import sys

from collections import namedtuple

from pyrevit import revit, DB
from pyrevit import forms
from pyrevit import script
from pyrevit import coreutils
from pyrevit.coreutils import pyutils


__context__ = 'selection'
__doc__ = 'Visualizes parameter values of elements of the same category. ' \
          'HOW TO USE: '   \
          'Select one element that has the desired parameter value, ' \
          'the run this script and select the parameter from the pop-up-window. '
__title__ = 'Parameter Check'

# reference the current open revit model to work with:
doc = __revit__.ActiveUIDocument.Document

# get selected element
selection = revit.get_selection()
selected_elements = selection.elements
selected_element = selected_elements[0]

# split element name after first "_"
selected_element_name = selected_element.Name
name_split = selected_element_name.split("_")
prefix = name_split[0]

# get element category
element_cat = selected_element.Category.Id
element_cat_name = selected_element.Category.Name

# set up tuple to acces an elements parameter by .name
ParamDef = namedtuple('ParamDef', ['name', 'type'])

# get all fill patterns
fill_patterns = Fec(doc).OfClass(FillPatternElement).WhereElementIsNotElementType().ToElements()

# get id of solid fill
solid_fill = fill_patterns[0].Id

# set colors
color_true = Autodesk.Revit.DB.Color(177,199,56)
color_true2 = Autodesk.Revit.DB.Color(126,150,56)

color_false = Autodesk.Revit.DB.Color(200,0,0)
color_false2 = Autodesk.Revit.DB.Color(128,0,0)

color_none = Autodesk.Revit.DB.Color(128,128,128)
color_none2 = Autodesk.Revit.DB.Color(50,50,50)

# create graphical overrides
ogs_true = OverrideGraphicSettings().SetProjectionFillColor(color_true)
ogs_true.SetProjectionFillPatternId(solid_fill)
ogs_true.SetSurfaceTransparency(10)
ogs_true.SetProjectionLineColor(color_true2)

ogs_false = OverrideGraphicSettings().SetProjectionFillColor(color_false)
ogs_false.SetProjectionFillPatternId(solid_fill)
ogs_false.SetSurfaceTransparency(0)
ogs_false.SetProjectionLineColor(color_false2)

ogs_none = OverrideGraphicSettings().SetProjectionFillColor(color_none)
ogs_none.SetProjectionFillPatternId(solid_fill)
ogs_none.SetSurfaceTransparency(40)
ogs_none.SetProjectionLineColor(color_none2)

# set up regex to compare levels "OKFF" "OKRD" etc.
regex_lvl = re.compile('[A-Z]{4}')


# setting up paramter values for comparison
def process_storage_type(param_check):
    #determine parameter storage type
    try:
        if param_check.StorageType == DB.StorageType.Double:
            param = param_check.AsDouble()
        elif param_check.StorageType == DB.StorageType.Integer:
            param = param_check.AsInteger()
        elif param_check.StorageType == DB.StorageType.String:
            param = param_check.AsString()
        elif param_check.StorageType == DB.StorageType.ElementId:
            param_id = param_check.AsElementId()
            param_name = Document.GetElement(doc, param_id).Name
            level_loc = regex_lvl.findall(param_name)
            param = level_loc[0]
        else:
            print("Cannot read Parameter, sorry :(")
        return param
    except:
        pass


# get all parameters from selected element to display them in clickable pop-up
def process_options(element_list):
    # find all relevant parameters

    param_sets = []

    for el in element_list:
        shared_params = set()
        # find element parameters
        for param in el.ParametersMap:
            pdef = param.Definition
            shared_params.add(ParamDef(pdef.Name, pdef.ParameterType))

        param_sets.append(shared_params)

    # make a list of options from discovered parameters
    if param_sets:
        all_shared_params = param_sets[0]
        for param_set in param_sets[1:]:
            all_shared_params = all_shared_params.intersection(param_set)

        return {'{} <{}>'.format(x.name, x.type): x
                for x in all_shared_params}


# main -----------------------------------------------------------------------
# ask user to select an option
options = process_options(selection.elements)

if options:
    selected_switch = \
        forms.CommandSwitchWindow.show(sorted(options),
                                       message='Sum values of parameter:')

    if selected_switch:
        selected_option = options[selected_switch]


        # connect to revit model elements via FilteredElementCollector
        # collect all the elements of selected elements category
        elements = Fec(doc).OfCategoryId(element_cat).WhereElementIsNotElementType().ToElements()

        # get selected parametervalue of selcted element
        sel_el_param_val = process_storage_type(selected_element.LookupParameter(selected_option.name))

        # output lists
        element_ids = []
        elements_true = []
        elements_false = []
        elements_none = []

        # main check ----------------------------------------
        for element in elements:

            # collect element ids
            element_id = element.Id
            element_ids.append(element_id)

            # get element name
            element_name = element.Name

            # as long as these categories do not have a naming convention, all elements will be treated equally
            if not ("Türen" in str(element_cat_name) or "Fenster" in str(element_cat_name) or "Geländer" in str(element_cat_name)):

                # elements not of the above categories are split into groups according to their prefix (f.e: "AW_" and everyting else)
                if element_name.startswith(prefix):
                    other_el_param_val = process_storage_type(element.LookupParameter(selected_option.name))
                    if other_el_param_val == sel_el_param_val:
                        elements_true.append(element)
                    else:
                        elements_false.append(element)
                else:
                    elements_none.append(element)

            # elements of the obove categories are treated equally
            else:
                other_el_param_val = process_storage_type(element.LookupParameter(selected_option.name))
                if other_el_param_val == sel_el_param_val:
                    elements_true.append(element)
                else:
                    elements_false.append(element)


        # create a collection from all element ids
        col1 = List[ElementId](element_ids)

        # entering a transaction to modify the revit model database
        # start transaction
        tx = Transaction(doc, "check type against parameter value")
        tx.Start()

        # isolate all elements of category
        doc.ActiveView.IsolateElementsTemporary(col1)

        # set graphical overrides
        for element in elements_true:
            doc.ActiveView.SetElementOverrides((element.Id), ogs_true)

        for element in elements_false:
            doc.ActiveView.SetElementOverrides((element.Id), ogs_false)

        for element in elements_none:
            doc.ActiveView.SetElementOverrides((element.Id), ogs_none)

        # commit the changes to the revit model database
        # end transaction
        tx.Commit()


# done.
