import clr
clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import FilteredElementCollector as Fec
from Autodesk.Revit.DB import BuiltInCategory as Bic
from Autodesk.Revit.DB import Transaction

# TODO micro steps to get the script to work

# reference the current open revit model to work with:
doc = __revit__.ActiveUIDocument.Document

# parameter names to work with:
# these are just the parameter names
# not the actual parameters or their values
# Vorgang = "hinges_side_family"
# instance_hinges_side = "hinges_side_instance"

# connect to revit model elements via FilteredElementCollector
# collect all the doors
doors = Fec(doc).OfCategory(Bic.OST_Doors).WhereElementIsNotElementType().ToElements()

# entering a transaction to modify the revit model database
# start transaction
tx = Transaction(doc, "set door hinges side")
tx.Start()

# create main logic here..:
for door in doors:
	print(15*"-")
	print(door.Id)

	# ask every door for its type
	door_type = door.Symbol
	# get the preset door hinge side
	hinges_default_param = door_type.LookupParameter("Vorgang")

	if hinges_default_param:
		hinges_type_side = hinges_default_param.AsString()

		# replace default values with short L or R
		if hinges_type_side == "SINGLE_SWING_RIGHT":
			hinges_type_side_short = "R"
		elif hinges_type_side == "SINGLE_SWING_LEFT":
			hinges_type_side_short = "L"
		elif hinges_type_side == "DOUBLE_DOOR_SINGLE_SWING_RIGHT":
				hinges_type_side_short = "R/L"
		elif hinges_type_side == "DOUBLE_DOOR_SINGLE_SWING_LEFT":
				hinges_type_side_short = "L/R"
		else:
			hinges_type_side_short = ""
		print("door default side: ", hinges_type_side_short)


		# aks if door is mirrored or not
		is_mirrored = door.Mirrored

		# perform some logic to determine the actual hinge side
		if not is_mirrored:
			door.LookupParameter("12_Tuertyp_Tueranschlag nach DIN").Set(hinges_type_side_short)
			print("door is not mirrored")

		elif is_mirrored:
			print("door is mirrored")
			if hinges_type_side_short == "R":
				door.LookupParameter("12_Tuertyp_Tueranschlag nach DIN").Set("L")
				print("instance is L")
			elif hinges_type_side_short == "L":
				door.LookupParameter("12_Tuertyp_Tueranschlag nach DIN").Set("R")
				print("instance is R")
			elif hinges_type_side_short == "R/L":
				door.LookupParameter("12_Tuertyp_Tueranschlag nach DIN").Set("L/R")
				print("instance is L/R")
			elif hinges_type_side_short == "L/R":
				door.LookupParameter("12_Tuertyp_Tueranschlag nach DIN").Set("R/L")
				print("instance is R/L")


	else:
		print("parameter missing!")

# commit the changes to the revit model database
# end transaction
tx.Commit()
print("successfully changed model")
