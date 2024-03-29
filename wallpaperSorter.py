#!usr/bin/env python

import glob
from datetime import datetime
from batchController import buildABatch
from calderaImporter import calderaBatchImporter
from downloadFromDrive import transferFilesFromDrive
from wallpaperSorterFunctions import moveForDueDates, unzipRenameSortPdfs, startupChecks
from wallpaperSorterVariables import sortingDir

today = datetime.today()

def mainMenu():
    menuOptions = (
        (1, 'Sort Orders', unzipRenameSortPdfs),
        (2, 'Batch Orders', buildABatch),
        (3, 'Caldera Batch Importer', calderaBatchImporter),
        (4, 'Download Orders from Google Drive', transferFilesFromDrive),
        (5, 'Update Sorting Based on Due Dates', moveForDueDates),
        (6, 'Quit'),
    )

    validOptions = populateValidOptions(menuOptions)

    print ('| Please enter an option: ')
    printMenuOptions(menuOptions)

    command = menuOptions[(getInput(validOptions)-1)]

    if command[1].startswith('Quit'):
        print('\n| Job\'s done!')
        return False
    elif command[1].startswith('Update Sorting'):
        return command[2](glob.glob(sortingDir + '**/*.pdf', recursive=True))
    else:
        return command[2]()

def populateValidOptions(menuOptions): # Gathers valid options from menus (like batchDetailsMenu) and ensures they are valid
    validOptions = []
    for option in menuOptions:
        validOptions.append(option[0])
    return validOptions

def printMenuOptions(listOfMenuOptions): #takes a list of menu items and prints them out neatly. See below for format.
    # (1, Smooth)
    # (int for valid option, displayed menu option)
    # Will display like: (1) Smooth
    for option in listOfMenuOptions:
        print('|  (' + str(option[0]) + ')', option[1],)

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

def main():
    run = True
    try:
        #print('no startup checks today')
        startupChecks()
    except:
        pass
    while run == True:
        run = mainMenu()
    return

main()
