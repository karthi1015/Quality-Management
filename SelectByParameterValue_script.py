# -*- coding: utf-8 -*-
import clr
clr.AddReference("RevitAPI")
clr.AddReference("System")
from System.Collections.Generic import List
from Autodesk.Revit.DB import FilteredElementCollector as Fec
from Autodesk.Revit.DB import BuiltInCategory as Bic
from Autodesk.Revit.DB import ElementId
from Autodesk.Revit.DB import Category, Document
from Autodesk.Revit.UI import Selection
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
__doc__ = 'Selects elements with the same value in specified instance parameter.'



# reference the current open revit model to work with:
doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument

# get selected element
selection = revit.get_selection()
selected_elements = selection.elements
selected_element = selected_elements[0]

# get element category
element_cat = selected_element.Category.Id

# set up tuple to acces an elements parameter by .name
ParamDef = namedtuple('ParamDef', ['name', 'type'])


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

        # main check ----------------------------------------
        for element in elements:

            # collect element ids
            element_id = element.Id

            other_el_param_val = process_storage_type(element.LookupParameter(selected_option.name))
            if other_el_param_val == sel_el_param_val:
                element_ids.append(element_id)
            else:
                pass


        # create a collection from all element ids
        col1 = List[ElementId](element_ids)
        # select elements
        uidoc.Selection.SetElementIds(col1)
