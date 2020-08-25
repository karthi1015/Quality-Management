# -*- coding: utf-8 -*-
import clr
clr.AddReference("RevitAPI")
clr.AddReference("System")
from Autodesk.Revit.DB import FilteredElementCollector as Fec
from Autodesk.Revit.DB import BuiltInCategory as Bic
from Autodesk.Revit.DB import BuiltInParameter as Bip
from Autodesk.Revit.DB import Transaction

tx = Transaction(doc, "check structural level offsets")
tx.Start()

rooms = Fec(doc).OfCategory(Bic.OST_Rooms).WhereElementIsNotElementType().ToElements()
areas = Fec(doc).OfCategory(Bic.OST_Areas).WhereElementIsNotElementType().ToElements()

for room in rooms:
    try:
        print(room.get_Parameter(Bip.ROOM_NAME).AsString())
        value0 = room.LookupParameter("Geschoss").AsString()
        room.LookupParameter("temp").Set(value0)
    except:
        print(room.Id)

for area in areas:
    id = area.get_Parameter(Bip.AREA_SCHEME_ID).AsElementId()
    if str(id) == "522977":
        try:
            print(area.get_Parameter(Bip.ROOM_NAME).AsString())
            value1 = area.LookupParameter("Geschoss").AsString()
            area.LookupParameter("temp").Set(value1)
        except:
            print(area.Id)

tx.Commit()
