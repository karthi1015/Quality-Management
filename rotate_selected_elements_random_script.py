# -*- coding: utf-8 -*-
import clr
clr.AddReference("RevitAPI")
clr.AddReference("System")
import math
import random
from Autodesk.Revit.DB import Transaction, Location, Line, XYZ
from Autodesk.Revit.DB import ElementTransformUtils
from pyrevit import revit, DB

__context__ = 'selection'
__doc__ = 'Randomly rotates selected elements.'

# reference the current open revit model to work with:
doc = __revit__.ActiveUIDocument.Document

# get selected element
selection = revit.get_selection()
elements = selection.elements

degrees_to_rotate = 45.0
# Convert the user input from degrees to radians.
converted_value = float(degrees_to_rotate) * (math.pi / 180.0)


# entering a transaction to modify the revit model database
# start transaction
tx = Transaction(doc, "check type against parameter value")
tx.Start()

for element in elements:
    origin = element.Location.Point
    line_z = Line.CreateBound(origin, XYZ(origin.X, origin.Y, origin.Z + 1))
    ElementTransformUtils.RotateElement(doc, element.Id, line_z, random.uniform(0, (math.pi * 2)))

# commit the changes to the revit model database
# end transaction
tx.Commit()
