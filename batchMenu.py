#!usr/bin/env python

import wallpaperSorterVariables as gv

def getBatchID(): # returns batch ID and increments batchCounter by 1
    currentID = gv.globalBatchCounter['batchCounter']
    gv.globalBatchCounter['batchCounter'] += 1
    return currentID

def confirmBatchMenu(material, length): # Menu to Confirm Batch Details. Calls batchDetailsMenu if user says it's incorrect.
    menuOptions = (
        (1, 'Yes'),
        (2, 'No'),
    )
    validOptions = populateValidOptions(menuOptions)
    print('\n| Confirm: Batch', length, 'feet of', material, 'PDFs?')
    printMenuOptions(menuOptions)
    command = menuOptions[(getInput(validOptions)-1)]
    if command == menuOptions[1]:
        return batchDetailsMenu()
    else:
        return

def includeOTs():
    menuOptions = (
        (1, 'Yes'),
        (2, 'No'),
    )
    validOptions = populateValidOptions(menuOptions)
    print('\n| Include Order Troubles?')
    printMenuOptions(menuOptions)
    command = menuOptions[(getInput(validOptions)-1)]
    if command == menuOptions[0]:
        return True
    else:
        return False

def populateValidOptions(menuOptions): # Gathers valid options from menus (like batchDetailsMenu) and ensures they are valid
    validOptions = []
    for option in menuOptions:
        validOptions.append(option[0])
    return validOptions

def getInput(validOptionsList): # Prompts user for input and validates it against valid options. Should be reusable for all types of menus that match the batchDetailsMenu style.
    command = input('\n| Command > ')
    try:
        command = int(command)
    except ValueError:
        print('\n| Please enter a valid number')
        return getInput(validOptionsList)
    while command not in validOptionsList:
        print('\n| Not a valid choice.')
        return getInput(validOptionsList)
    return command

def getBatchLength(material): # prompts the user for a batch length. Verifies that it is a whole number, rounds it down to the nearest integer, ensures that it's greater than the minimum length and smaller than the max length for a given material type.
    if material == 'Smooth':
        maxLength = 145
    elif material == 'Woven':
        maxLength = 95
    batchLength = input('| Please enter a batch length in feet > ')
    try:
        batchLength = int(batchLength)
        batchLength = round(batchLength)
    except ValueError:
        print('| Please enter a whole number.')
        return getBatchLength(material)
    if batchLength < 4:
        print('| Length is too small for ' +  material + '. Please enter a greater length.')
        return getBatchLength(material)
    elif batchLength > maxLength:
        print('| Length is too great for ' +  material + '. Please enter a smaller length.')
        return getBatchLength(material)
    else:
        return batchLength * 12

def printMenuOptions(listOfMenuOptions): #takes a list of menu items and prints them out neatly. See below for format.
    # (1, Smooth)
    # (int for valid option, displayed menu option)
    # Will display like: (1) Smooth
    for option in listOfMenuOptions:
        print('|  (' + str(option[0]) + ')', option[1],)

def batchDetailsMenu(): # Menu to get the main details of a new batch. Returns a dictionary containing the material, material length, and minimum length. Calls populateValidOptions to properly display valid menu options. Calls getInput to get and verify user input. Calls getBatchLength to ask the user for a batch length if a default one is not chosen.
    menuOptions = (
        (1, 'Smooth, 150 Feet', 'Smooth', gv.dirLookupDict['MaterialLength']['Smooth'], True),
        (2, 'Woven, 100 Feet', 'Woven', gv.dirLookupDict['MaterialLength']['Woven'], True),
        (3, 'Smooth, 150 Feet, Disregard Minimum Length', 'Smooth', gv.dirLookupDict['MaterialLength']['Smooth'], False),
        (4, 'Woven, 100 Feet, Disregard Minimum Length', 'Woven', gv.dirLookupDict['MaterialLength']['Woven'], False),
        (5, 'Smooth, Custom Length, Disregard Minimum Length', 'Smooth', 0, False),
        (6, 'Woven, Custom Length, Disregard Minimum Length', 'Woven', 0, False),
        (7, 'Quit and return to Main Menu', 'Smooth', 0, True)
    )
    validOptions = populateValidOptions(menuOptions)

    print('| Please enter a batch type: ')
    printMenuOptions(menuOptions)
    
    command = menuOptions[(getInput(validOptions)-1)]
    
    if command[1].startswith('Quit'):
        print('\n| Returning to Main Menu')
        return
   
    batchDetails = {
        'material':command[2],
        'materialLength':command[3] * 12,
        'minLength':command[4]
    }
    if batchDetails['materialLength'] == 0:
        batchDetails['materialLength'] = getBatchLength(batchDetails['material'])
    return batchDetails