# -*- coding: utf-8 -*-
import clr
clr.AddReference("RevitAPI")
clr.AddReference("System")
from System.Collections.Generic import List
from Autodesk.Revit.DB import FilteredElementCollector as Fec
from Autodesk.Revit.DB import ElementMulticategoryFilter, Document
from Autodesk.Revit.DB import BuiltInCategory as Bic
from Autodesk.Revit.DB import BuiltInParameter as Bip
from Autodesk.Revit.DB import Transaction, FillPattern, FillPatternElement
from Autodesk.Revit.DB import OverrideGraphicSettings, View, ElementId
import Autodesk
from pyrevit import revit, DB, script
from rpw import doc

# mouse hover-over text
__doc__ = 'Visualizes the level properties of Walls, Floors,' \
          ' Structural Columns and Structural Framing.'

class StructuralElement:
    # class containing information about the elements of includet categories
    def __init__(self, id, lvl_bott, lvl_top):
        self.id = id
        self.lvl_bott = lvl_bott
        self.lvl_top = lvl_top


class WarningElement:
    # class of elements that are suspicious but not necessairily incorred.
    # for example "SO_" on OKFF on any Subsurface level
    def __init__(self, id, name, lvl):
        self.id = id
        self.name = name
        self.lvl = lvl


def GetElemProps(elem_lst):
    # this function takes all elements in the categories list and creates an object of the
    # StructuralElement class and appends it to the elem_info list.
    for elem in elem_lst:
            try:
                id = elem.Id
                if elem.Category.Name == "Wände":
                    if elem.get_Parameter(Bip.WALL_STRUCTURAL_SIGNIFICANT).AsInteger() == 1:
                        if not (elem.Name.startswith("AW-FA_") or elem.Name.startswith("IW-FA_")):
                            element_ids.append(id)
                            if not elem.get_Parameter(Bip.WALL_TOP_IS_ATTACHED).AsInteger() == 1:
                                lvl_bott_id = elem.get_Parameter(Bip.WALL_BASE_CONSTRAINT).AsElementId()
                                try:
                                    lvl_top_id = elem.get_Parameter(Bip.WALL_HEIGHT_TYPE).AsElementId()
                                    lvl_top = CnvrtToName(lvl_top_id)
                                except:
                                    # catch top constraint "manual"
                                    lvl_top = ""
                                # create and append objects
                                elem_info.append(StructuralElement(id, CnvrtToName(lvl_bott_id), lvl_top))
                            else:
                                elem_info.append(StructuralElement(id, "", ""))
                elif elem.Category.Name == "Geschossdecken":
                    if elem.get_Parameter(Bip.FLOOR_PARAM_IS_STRUCTURAL).AsInteger() == 1:
                        if elem.Name.startswith("GD_"):
                            lvl_bott_id = elem.get_Parameter(Bip.LEVEL_PARAM).AsElementId()
                            lvl_bott = CnvrtToName(lvl_bott_id)
                            lvl = CnvrtToName(lvl_bott_id)
                            # modify data for easy matching
                            lvl_top = "UKRD"
                            if "OKFF" in lvl_bott and lvl_bott.startswith("-"):
                                # modify data for easy matching
                                lvl_bott = "OKRF"
                                # create and append objects
                                elem_info.append(StructuralElement(id, lvl_bott, lvl_top))
                                element_ids.append(id)
                                elem_wrngs.append(WarningElement(id, elem.Name, lvl))
                            else:
                                elem_info.append(StructuralElement(id, lvl_bott, lvl_top))
                                element_ids.append(id)
                        elif elem.Name.startswith("SO_"):
                            lvl_bott_id = elem.get_Parameter(Bip.LEVEL_PARAM).AsElementId()
                            lvl_bott = CnvrtToName(lvl_bott_id)
                            lvl = CnvrtToName(lvl_bott_id)
                            if "OKFF" in lvl_bott:
                                # modify data for easy matching
                                lvl_bott = "OKRF"
                                lvl_top = "UKRD"
                                # create and append objects
                                elem_info.append(StructuralElement(id, lvl_bott, lvl_top))
                                element_ids.append(id)
                                # append warning
                                elem_wrngs.append(WarningElement(id, elem.Name, lvl))
                            elif "OKRF" in lvl_bott:
                                # modify data for easy matching
                                lvl_top = "UKRD"
                                # create and append objects
                                elem_info.append(StructuralElement(id, lvl_bott, lvl_top))
                                element_ids.append(id)
                                # append warning
                                elem_wrngs.append(WarningElement(id, elem.Name, lvl))
                        elif elem.Name.startswith("GD-BA_") or elem.Name.startswith("SO-BA_"):
                            lvl_bott_id = elem.get_Parameter(Bip.LEVEL_PARAM).AsElementId()
                            element_ids.append(id)
                            if "OKFF" in CnvrtToName(lvl_bott_id):
                                # modify data for easy matching
                                lvl_bott = "OKRF"
                                lvl_top = "UKRD"
                                # create and append objects
                                elem_info.append(StructuralElement(id, lvl_bott, lvl_top))
                        elif elem.Name.startswith("BA_"):
                            # modify data for easy matching
                            lvl_bott = ""
                            lvl_top = ""
                            # create and append objects
                            elem_info.append(StructuralElement(id, lvl_bott, lvl_top))
                            element_ids.append(id)
                elif elem.Category.Name == "Tragwerksstützen":
                    element_ids.append(id)
                    if not elem.get_Parameter(Bip.COLUMN_TOP_ATTACHED_PARAM).AsInteger() == 1:
                        lvl_bott_id = elem.get_Parameter(Bip.FAMILY_BASE_LEVEL_PARAM).AsElementId()
                        lvl_top_id = elem.get_Parameter(Bip.FAMILY_TOP_LEVEL_PARAM).AsElementId()
                        # create and append objects
                        elem_info.append(StructuralElement(id, CnvrtToName(lvl_bott_id), CnvrtToName(lvl_top_id)))
                    else:
                        elem_info.append(StructuralElement(id, "", ""))
                elif elem.Category.Name == "Skelettbau":
                    lvl_bott_id = elem.get_Parameter(Bip.INSTANCE_REFERENCE_LEVEL_PARAM).AsElementId()
                    # modify data for easy matching
                    lvl_top_id = "UKRD"
                    # create and append objects
                    elem_info.append(StructuralElement(id, CnvrtToName(lvl_bott_id), lvl_top_id))
                    element_ids.append(id)
                else:
                    pass
            except:
                pass


def CnvrtToName(id):
    # Convert level ID to level Name
    lvl_name = Document.GetElement(doc, id).Name
    return lvl_name



# get all fill patterns
fill_patterns = Fec(doc).OfClass(FillPatternElement).WhereElementIsNotElementType().ToElements()
# get id of solid fill
solid_fill = fill_patterns[0].Id

# set colors
color_true = Autodesk.Revit.DB.Color(0,133,68)
color_true2 = Autodesk.Revit.DB.Color(0,100,68)
color_false = Autodesk.Revit.DB.Color(164,26,7)
color_false2 = Autodesk.Revit.DB.Color(100,26,7)

# create graphical overrides
ogs_true = OverrideGraphicSettings().SetProjectionFillColor(color_true)
ogs_true.SetProjectionFillPatternId(solid_fill)
ogs_true.SetSurfaceTransparency(10)
ogs_true.SetProjectionLineColor(color_true2)

ogs_false = OverrideGraphicSettings().SetProjectionFillColor(color_false)
ogs_false.SetProjectionFillPatternId(solid_fill)
ogs_false.SetSurfaceTransparency(0)
ogs_false.SetProjectionLineColor(color_false2)

# connect to revit model elements via FilteredElementCollector
# collect all the elements of categories
categories = [Bic.OST_Walls, Bic.OST_Floors, Bic.OST_StructuralColumns, Bic.OST_StructuralFraming]
col_bic = List[Bic](categories)
struct_elems = Fec(doc).WherePasses(ElementMulticategoryFilter(col_bic)).WhereElementIsNotElementType().ToElements()

# prepare lists
elem_info = []
element_ids = []
elem_wrngs = []

# process elements
GetElemProps(struct_elems)

# entering a transaction to modify the revit model database
# start transaction
tx = Transaction(doc, "check structural element levels")
tx.Start()

# isolate all elements of category
col1 = List[ElementId](element_ids)
doc.ActiveView.IsolateElementsTemporary(col1)

# set graphical overrides
for elem in elem_info:
        if ("OKRF" in str(elem.lvl_bott)) and ("UKRD" in str(elem.lvl_top)):
            doc.ActiveView.SetElementOverrides((elem.id), ogs_true)
        else:
            doc.ActiveView.SetElementOverrides((elem.id), ogs_false)

# commit the changes to the revit model database
# end transaction
tx.Commit()

# print suspicious elemnts with clickable ids
output = script.get_output()
for el in elem_wrngs:
    print("Note: " + str(el.name) + " with ID: " + output.linkify(el.id) + " is hosted on: " + str(el.lvl))
