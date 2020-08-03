import clr
clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import FilteredElementCollector as Fec
from Autodesk.Revit.DB import Transaction
from Autodesk.Revit.DB import OverrideGraphicSettings
from Autodesk.Revit.DB import View
from Autodesk.Revit.DB import TemporaryViewMode

import Autodesk


# reference the current open revit model to work with:
doc = __revit__.ActiveUIDocument.Document
view = doc.ActiveView


# connect to revit model elements via FilteredElementCollector
elements = filter(None, Fec(doc, doc.ActiveView.Id).ToElements())

ogs = OverrideGraphicSettings().SetSurfaceTransparency(0)


# entering a transaction to modify the revit model database
# start transaction
tx = Transaction(doc, "clear graphic overrides")
tx.Start()

doc.ActiveView.DisableTemporaryViewMode(TemporaryViewMode.TemporaryHideIsolate)

for element in elements:

    doc.ActiveView.SetElementOverrides((element.Id), ogs)

# commit the changes to the revit model database
# end transaction
tx.Commit()
#print("successfully reset graphic overrides in view")
