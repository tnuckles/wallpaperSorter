#!usr/bin/env python

import os
from datetime import date, datetime
from sqlitedict import SqliteDict

today = datetime.today()

def main():
    options = 1,2,3,4,5,6,0
    print('\n| Main Menu')
    print('| 1. Sort Orders')
    print('| 2. Download Orders from Google Drive')
    print('| 3. Batch Orders')
    print('| 4. Update Sorting Based on Due Dates')
    print('| 5. Quit')
    try:
        command = int(input('\n| Command > '))
    except ValueError:
        print('\n| Please enter a whole number, not text.')
        return main()
    while int(command) not in options:
        print('\n| Not a valid choice.')
        return main()
    if command == 1:
        findJSONs()
        reportDuplicatePDFs()
        splitMultiPagePDFs()
        # if os.path.expanduser('~').split('/')[-1] == 'Trevor':
        #     checkRepeatSize()
        sortPDFsByDetails()
        buildDBSadNoises()
        return main()
    elif command == 2:
        transferFilesFromDrive()
        return main()
    elif command == 3:
        batch.batchCreationController()
        return main()
    elif command == 4:
        moveForDueDates()
        return main()
    elif command == 5:
        print('\n| Goodbye!')
        pass
    elif command == 0:
        if os.path.expanduser('~').split('/')[-1] == 'Trevor':
            print('\n| The creator is among us.')
            print('| Prepping folders for test.')
            fullOrPartialRun = input('| Do you want to do a full run? > ')
            if fullOrPartialRun == 'y':
                shutil.rmtree(batch.gv.batchFoldersDir)
                os.mkdir(batch.gv.batchFoldersDir)
                shutil.rmtree(gv.downloadDir)
                shutil.copytree('/Users/Trevor/Desktop/Backup/Downloaded', gv.downloadDir)
                shutil.rmtree(gv.sortingDir)
                shutil.copytree('/Users/Trevor/Desktop/Backup/5 Sorted for Print', gv.sortingDir)
                findJSONs()   
                reportDuplicatePDFs()
                #splitMultiPagePDFs()
                #checkRepeatSize()
                sortPDFsByDetails()
            transferFromDrive = input('| Do you want to transfer files from drive?\n| This will copy the current directory to a test directory. > ')
            if transferFromDrive == 'y':
                shutil.rmtree('/Volumes/GoogleDrive/Shared drives/# Production/#LvD Test Fulfillment')
                shutil.copytree('/Volumes/GoogleDrive/Shared drives/# Production/#LvD Fulfillment', '/Volumes/GoogleDrive/Shared drives/# Production/#LvD Test Fulfillment')
                transferFilesFromDrive()
            return main()
    print('\n| Job\'s Done!')

mainMenuDict = {
    'validOptions':(1,2,3,4,5,0),
    'menuOptions':((1,'1. Sort Orders', sortOrders()),(2,'2. Download Orders from Google Drive', transferFilesFromDrive()),(3,'3. Batch Orders',batch.batchCreationController()),(4,'4. Update Sorting Based on Due Dates',moveForDueDates()),(5,'5. Quit', pass)),
    }

def menuFunction():
    printMenu()
    takeInput()
    validateInput()
    executeInput()

def printMenu():
    for 
