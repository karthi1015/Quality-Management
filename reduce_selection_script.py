# -*- coding: utf-8 -*-
import clr
clr.AddReference("RevitAPI")
clr.AddReference("System")
from System.Collections.Generic import List
import math
import random
from Autodesk.Revit.DB import Transaction, ElementId
from Autodesk.Revit.UI import Selection
from rpw.ui.forms import TextInput
from pyrevit import revit, DB

__context__ = 'selection'
__doc__ = 'Reduces the current selection to specified percantage.'

# reference the current open revit model to work with:
uidoc = __revit__.ActiveUIDocument

# get selected elements
selection = revit.get_selection()
elements = selection.elements

all_elem_ids = []

for element in elements:
    all_elem_ids.append(element.Id)

value = TextInput('Percentage:', default="42",\
 description="Current selection will be reduced to percentage.")

num_of_items = int(len(all_elem_ids) * (float(value) / 100))

reduced_ids = [all_elem_ids[i] for i in random.sample(range(0, len(all_elem_ids)), num_of_items)]

col1 = List[ElementId](reduced_ids)

uidoc.Selection.SetElementIds(col1)
