#!usr/bin/env python

import glob
from os import remove
from shutil import move
from os.path import exists
from datetime import datetime
from time import sleep as wait
from getPdfData import friendlyName
from batchCreate import tryToMovePDF
from batchMenu import populateValidOptions, printMenuOptions
from wallpaperSorterVariables import batchFoldersDir, hotfoldersDir


today = datetime.today()

def calderaBatchImporter(): # main function for this module. First calls checkForBatchFolders
    checkForBatchFolders()
    return 

def checkForBatchFolders(): # checks for batch folders to import. If there are none, shorts the module. Otherwise, continues
    batchFoldersGlob = glob.glob(batchFoldersDir + '/Batch *')
    if len(batchFoldersGlob) > 0:
        batchToImport = batchSelector(batchFoldersGlob) # accepts a list of batches, then returns a single, user-selected batch
        importToCaldera(batchToImport) # begins to import the user-selected batch. Accepts a batch as a file path.
        return calderaBatchImporter()
    else:
        print('| No batches to import.')
        return
    
def batchSelector(listOfBatches): #takes a list of batches. Sorts them by priority, sorts priorities by order number, then prints them like a menu. Accepts input from user to indicate a batch for importing. Returns batch name as a file path
    listOptionCounter = 1
    otBatchList = []
    lateBatchList = []
    todayBatchList = []
    futureBatchList = []

    # iterates through list of batches to sort by priority
    for batch in listOfBatches:
        if batch.endswith('OT'):
            otBatchList.append(batch)
        elif batch.endswith('Late'):
            lateBatchList.append(batch)
        elif batch.endswith('Today'):
            todayBatchList.append(batch)
        else:
            futureBatchList.append(batch)

    # calls sortBatchesByID on each batchList to sort by ID from least to greatest
    otBatchList = sortBatchesByID(otBatchList)
    lateBatchList = sortBatchesByID(lateBatchList)
    todayBatchList = sortBatchesByID(todayBatchList)
    futureBatchList = sortBatchesByID(futureBatchList)
    
    # Calls printBatchList on each list to print it nicely for the user. Returns the number of the last item in the list
    listOptionCounter = printBatchList('OT', otBatchList, listOptionCounter)
    otListStop = listOptionCounter-1 
    listOptionCounter = printBatchList('Late', lateBatchList, listOptionCounter)
    lateListStop = listOptionCounter-1
    listOptionCounter = printBatchList('Today', todayBatchList, listOptionCounter)
    todayListStop = listOptionCounter-1
    listOptionCounter = printBatchList('Future', futureBatchList, listOptionCounter)
    futureListStop = listOptionCounter-1

    # populates menu for batch selecting. When the user provides a number, we do interval comparison to see which list it should be from. After decided, we subtract one from the user's input to align it to the list, then subtract the length of the previous list to make the user's input align properly with a python list.
    # Then return the batch
    print('\n| Which batch would you like to import into caldera?')
    command = int(input('| Command > '))
    if command <= otListStop:
        command -= 1
        batch = otBatchList[command]
        print('\n| Selected', batch.split('/')[-1], 'for print.')
        return batch
    elif otListStop < command <= lateListStop:
        command -= (1 + otListStop)
        batch = lateBatchList[command]
        print('\n| Selected', batch.split('/')[-1], 'for print.')
        return batch
    elif lateListStop < command <= todayListStop:
        command -= (1 + lateListStop)
        batch = todayBatchList[command]
        print('\n| Selected', batch.split('/')[-1], 'for print.')
        return batch
    elif todayListStop < command <= futureListStop:
        command -= (1 + todayListStop)
        batch = futureBatchList[command]
        print('\n| Selected', batch.split('/')[-1], 'for print.')
        return batch

def importToCaldera(batch): # takes a batch as a file path and loops through its contents in reverse order. Moves each print pdf to a specified printer's hotfolder based on material type.

    print('| Caldera Online.')
    print('|', batch)
    
    printerToUse = getPrinter()

    move(batch, hotfoldersDir + printerToUse + '/z_Currently Importing/')
    wait(2.5)
    
    # Creates variables for the batch
    batch = batch.split('/')[-1] 
    batchMaterial = batch.split(' ')[2]
    receivingHotfolder = hotfoldersDir + printerToUse + batchMaterial + '/'
    batch = hotfoldersDir + printerToUse + 'z_Currently Importing/' + batch + '/'
    
    batchLists = (
        (glob.glob(batch + '4 - Future/Samples/*.pdf', recursive=True)),
        (glob.glob(batch + '4 - Future/Full/*.pdf', recursive=True)),
        (glob.glob(batch + '3 - Today/Samples/*.pdf', recursive=True)),
        (glob.glob(batch + '3 - Today/Full/*.pdf', recursive=True)),
        (glob.glob(batch + '2 - Late/Samples/*.pdf', recursive=True)),
        (glob.glob(batch + '2 - Late/Full/*.pdf', recursive=True)),
        (glob.glob(batch + '1 - OT/Samples/*.pdf', recursive=True)),
        (glob.glob(batch + '1 - OT/Full/*.pdf', recursive=True)),
    )

    for pdfList in batchLists:
        moveToHotfolder(pdfList, receivingHotfolder)

    print('\n| Moved', batch.split('/')[-2], 'into', receivingHotfolder.split('/')[6].split(' ')[1], batchMaterial, 'HotFolder')
    return

def getPrinter():
    menuOptions = (
        (1, 'Ichi'),
        (2, 'Ni'),
        (3, 'San'),
    )

    validOptions = populateValidOptions(menuOptions)
    print('| Please select a printer to use: ')
    printMenuOptions(menuOptions)

    command = menuOptions[(getInput(validOptions)-1)][1]

    printerLookup = {
        'Ichi':'1 Ichi/',
        'Ni':'2 Ni/',
        'San':'3 San/',
    }

    return printerLookup[command]

def moveToHotfolder(pdfList, receivingHotfolder):
    for printPdf in pdfList:
        if '999999999-header' not in printPdf:
            print('| Moving', friendlyName(printPdf))
            tryToMovePDF(printPdf, receivingHotfolder, friendlyName(printPdf))
            wait(2)
            continue
    for headerPdf in pdfList:
        if '99999999-header' in headerPdf:
            if exists(receivingHotfolder + headerPdf.split('/')[-1]):
                remove(headerPdf)
            else:
                move(headerPdf, receivingHotfolder)
            wait(2)
    return

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

def printBatchList(listName, batchList, optionCounter):
    if len(batchList) == 0:
        return optionCounter
    print('\n| Available', listName, 'batches:')
    for batch in batchList:
        printBatchOption(batch, optionCounter)
        optionCounter += 1
    return optionCounter

def printBatchOption(batch, optionCounter):
    batchName = batch.split('/')[-1]
    print('|  (' + str(optionCounter) + ')', batchName)

def sortBatchesByID(batchList): # takes a list of pathsToBatches and sorts them by batch ID, from least to greatest.
    listToSort = []
    sortedList = []
    for batch in batchList:
        batchID = batch.split('/')[-1].split(' ')[1].split('#')[1]
        listToSort.append((batchID, batch))
    listToSort.sort(reverse=False, key=lambda batchDir: batchDir[0])
    newBatchList = listToSort
    listToSort = []
    for printPdf in newBatchList:
        sortedList.append(printPdf[1])
    batchList = sortedList
    sortedList = []
    return batchList

# def mainMenu():
#     menuOptions = (
#         (1, 'Sort Orders', sortDownloadedOrders),
#         (2, 'Batch Orders', batchCreationController),
#         (3, 'Caldera Batch Importer', calderaBatchImporter),
#         (4, 'Download Orders from Google Drive', transferFilesFromDrive),
#         (5, 'Update Sorting Based on Due Dates', moveForDueDates),
#         ('Q', 'Quit'),
#     )

#     validOptions = populateValidOptions(menuOptions)

#     print ('| Please enter an option: ')
#     printMenuOptions(menuOptions)

#     command = menuOptions[(getInput(validOptions)-1)]

#     if command[0] == 'Q':
#         print('\n| Job\'s done!')
#         return False

#     return command[2]()

# def populateValidOptions(menuOptions): # Gathers valid options from menus (like batchDetailsMenu) and ensures they are valid
#     validOptions = []
#     for option in menuOptions:
#         validOptions.append(option[0])
#     return validOptions

# def printMenuOptions(listOfMenuOptions): #takes a list of menu items and prints them out neatly. See below for format.
#     # (1, Smooth)
#     # (int for valid option, displayed menu option)
#     # Will display like: (1) Smooth
#     for option in listOfMenuOptions:
#         print('|  (' + str(option[0]) + ')', option[1],)

# def getInput(validOptionsList): # Prompts user for input and validates it against valid options. Should be reusable for all types of menus that match the batchDetailsMenu style.
#     command = input('\n| Command > ')
#     try:
#         command = int(command)
#     except ValueError:
#         print('\n| Please enter a valid number')
#         return getInput(validOptionsList)
#     while command not in validOptionsList:
#         print('\n| Not a valid choice.')
#         return getInput(validOptionsList)
#     return command

# def main():
#     while True:
#         mainMenu()
#     return

# try:
#     startupChecks()
# except:
#     pass

# main()
