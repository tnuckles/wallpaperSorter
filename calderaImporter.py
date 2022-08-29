#!usr/bin/env python

from datetime import datetime
import glob
from wallpaperSorterVariables import batchFoldersDir

today = datetime.today()

def calderaBatchImporter():
    checkForBatchFolders()
    return 

def checkForBatchFolders():
    batchFoldersGlob = glob.glob(batchFoldersDir + '/Batch *')
    if len(batchFoldersGlob) > 0:
        batchSelector(batchFoldersGlob)
    else:
        print('| No batches to batch.')
        return
    
def batchSelector(listOfBatches):
    listOptionCounter = 1
    otBatchList = []
    lateBatchList = []
    todayBatchList = []
    futureBatchList = []
    for batch in listOfBatches:
        if batch.endswith('OT'):
            otBatchList.append(batch)
        elif batch.endswith('Late'):
            lateBatchList.append(batch)
        elif batch.endswith('Today'):
            todayBatchList.append(batch)
        else:
            futureBatchList.append(batch)
    
    listOptionCounter = printBatchList('OT', otBatchList, listOptionCounter)
    otListStop = listOptionCounter-1
    listOptionCounter = printBatchList('Late', lateBatchList, listOptionCounter)
    lateListStop = listOptionCounter-1
    listOptionCounter = printBatchList('Today', todayBatchList, listOptionCounter)
    todayListStop = listOptionCounter-1
    listOptionCounter = printBatchList('Future', futureBatchList, listOptionCounter)
    futureListStop = listOptionCounter-1

    print('\n| Which batch would you like to import into caldera?')
    command = int(input('| Command > '))
    if command <= otListStop:
        print('\n| Selected', otBatchList[command-1], 'for print.')
    elif otListStop < command <= lateListStop:
        print('late')
    elif lateListStop < command <= todayListStop:
        print('today')
    elif todayListStop < command <= futureListStop:
        print('future')

    return batchSelector(listOfBatches)

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
