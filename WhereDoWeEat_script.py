# -*- coding: utf-8 -*-
import random
from rpw.ui.forms import SelectFromList
import csv
from rpw.ui.forms import (FlexForm, Label, ComboBox, Button)
from rpw.ui.forms import CommandLink, TaskDialog
import os


class Eat:

    def __init__(self, name, style, price, veggie, distance, portion, maps):
        self.name = name
        self.style = style
        self.price = price
        self.veggie = veggie
        self.distance = distance
        self.portion = portion
        self.maps = maps


def pick_my_eat(filtered_list):
    max_number = len(filtered_list)
    random_number = random.randint(0,max_number-1)

    return filtered_list[random_number]


eats = []

with open("F:/910_EDV/910_REVIT/11_pyRevit/PickMyEat.csv", 'r') as file:
    reader = csv.reader(file, delimiter=";")
    header = next(reader)
    for row in reader:
        eats.append(Eat(row[0], row[1], row[2], row[3], row[4], row[5], row[6]))

names = []
styles = []
veggie = []
portion = []

for i in eats:
    names.append(i.name)
    styles.append(i.style)
    veggie.append(i.veggie)
    portion.append(i.portion)

styles_set = set(styles)
veggie_set = set(veggie)
portion_set = set(portion)

names_dict = dict(zip(names, names))
styles_dict = dict(zip(styles_set, styles_set))
price_dict = {"low" :1, "mid" :2, "high" :3}
veggie_dict = dict(zip(veggie_set, veggie_set))
distance_dict = {"walk" :1, "long walk" :2, "bike" :3}
portion_dict = dict(zip(portion_set, portion_set))

styles_dict["all"] = "all"
veggie_dict["all"] = "all"
portion_dict["all"] = "all"

run_again = True

while run_again == True:
    # ui
    components = [Label('style:'),
                   ComboBox("combobox", styles_dict),
                   Label('Max. price:'),
                   ComboBox("combobox1", price_dict),
                   Label('veggie:'),
                   ComboBox("combobox2", veggie_dict),
                   Label('Max. distance:'),
                   ComboBox("combobox3", distance_dict),
                   Label('portion:'),
                   ComboBox("combobox4", portion_dict),
                   Button('Select')]
    form = FlexForm('Title', components)
    form.show()

    values = form.values

    ui_0 = values["combobox"]
    ui_1 = values["combobox1"]
    ui_2 = values["combobox2"]
    ui_3 = values["combobox3"]
    ui_4 = values["combobox4"]

    if str(ui_0) == "all":
        for i in eats:
            i.style = "all"

    if str(ui_2) == "all":
        for i in eats:
            i.veggie = "all"

    if str(ui_4) == "all":
        for i in eats:
            i.portion = "all"

    eats_filtered = []

    for i in eats:
        if str(ui_0) == str(i.style) and int(i.price) <= ui_1 and str(ui_2) == str(i.veggie) and int(i.distance) <= ui_3 and str(ui_4) == str(i.portion):
            eats_filtered.append(i)


    pick = pick_my_eat(eats_filtered)
    # print(pick.name, pick.price, pick.distance, pick.maps)


    commands = [CommandLink('Yes, guide me Odin!', return_value = False),
                CommandLink('No, Ragnarok awaits me there.', return_value = True)]

    dialog = TaskDialog('Today you shall dine at: ',
                    title_prefix = False,
                    content = pick.name,
                    commands = commands,
                    # buttons=['Cancel', 'OK', 'RETRY'],
                    # footer='It has a footer',
                    # verification_text='Add Verification Checkbox',
                    # expanded_content='Add Expanded Content',
                    show_close = True)
    # dialog.show()

    run_again = dialog.show()



if run_again == False:
    direction_map = "start \"\" " + pick.maps
    os.system(direction_map)
