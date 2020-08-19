# -*- coding: utf-8 -*-
import clr
clr.AddReference("RevitAPI")
clr.AddReference("System")
from System.Collections.Generic import List
from Autodesk.Revit.DB import FilteredElementCollector as Fec
from Autodesk.Revit.DB import BuiltInCategory as Bic
from Autodesk.Revit.DB import ElementMulticategoryFilter
from Autodesk.Revit.DB import Transaction, ElementId

__doc__ = 'Isolate Structural Elements'

# reference the current open revit model to work with:
doc = __revit__.ActiveUIDocument.Document

# connect to revit model elements via FilteredElementCollector
# collect all the elements of selected elements category
categories1 = [Bic.OST_Walls, Bic.OST_Floors]
categories2 = [Bic.OST_StructuralColumns, Bic.OST_StructuralFraming]
col_bic1 = List[Bic](categories1)
col_bic2 = List[Bic](categories2)
struct_elems1 = Fec(doc).WherePasses(ElementMulticategoryFilter(col_bic1)).WhereElementIsNotElementType().ToElements()
struct_elems2 = Fec(doc).WherePasses(ElementMulticategoryFilter(col_bic2)).WhereElementIsNotElementType().ToElements()

element_ids = []

# test walls and floors for structural property and append true elemets to list
for elem in struct_elems1:
    if not (elem.Name.startswith("AW-FA_") or elem.Name.startswith("IW-FA_")):
        try:
            id = elem.Id
            if elem.LookupParameter("Tragwerk").AsInteger() == 1:
                element_ids.append(id)
        except:
            pass

# test columns and framing for structural property and append true elemets to list
for elem in struct_elems2:
    try:
        id = elem.Id
        element_ids.append(id)
    except:
        pass

# create a collection from all element ids
col1 = List[ElementId](element_ids)

# entering a transaction to modify the revit model database
# start transaction
tx = Transaction(doc, "check structural elements")
tx.Start()

# isolate all elements of category
doc.ActiveView.IsolateElementsTemporary(col1)

# commit the changes to the revit model database
# end transaction
tx.Commit()
