quantity_per_panel_dict = {}

quantity = 25
quantity_counter = 0
repeat = 6
repeat = int(repeat / 2)

while quantity_counter < quantity:
    for panel in range(repeat):
        panel_num = panel+1
        if panel_num in quantity_per_panel_dict:
            quantity_per_panel_dict[panel_num] += 1
            quantity_counter += 1
            if quantity_counter == quantity:
                break
            elif panel_num == repeat:
                panel = 0
        else:
            quantity_per_panel_dict[panel_num] = 1
            quantity_counter += 1
            if quantity_counter == quantity:
                break
            elif panel_num == repeat:
                panel = 0

print(quantity_per_panel_dict)