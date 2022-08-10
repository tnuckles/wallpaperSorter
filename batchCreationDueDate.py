#!usr/bin/env python

import os, shutil, math, datetime, glob
from PyPDF2 import utils
from datetime import  datetime
from batchCreation import getListOfPdfs


import wallpaperSorterVariables as gv
import getPdfData as getPdf
import pdf_splitter
import add_macos_tag as set_tag

today = datetime.today()

### Global Variables

currentBatchDict = {
        'batchDetails': {
            'ID':'',
            'material':'',
            'priority':0,
            'length':0
        },
        'OT':{
            'full':{
                'batchLength':0,
                'batchList':[],
            },
            'sample':{
                'batchLength':0,
                'batchList':[],
            },
        },
        'Late':{
            'full':{
                'batchLength':0,
                'batchList':[],
            },
            'sample':{
                'batchLength':0,
                'batchList':[],
            },
        },
        'Today':{
            'full':{
                'batchLength':0,
                'batchList':[],
            },
            'sample':{
                'batchLength':0,
                'batchList':[],
            },
        },
        'Future':{
            'full':{
                'batchLength':0,
                'batchList':[],
            },
            'sample':{
                'batchLength':0,
                'batchList':[],
            },
        },
    }

### Function Definitions

def getBatchID():
    currentID = gv.globalBatchCounter['batchCounter']
    gv.globalBatchCounter['batchCounter'] += 1
    return currentID

def confirmBatch(material, length):
    options = 1,2
    print('\n| Confirm: Batch', length, 'feet of', material, 'PDFs?')
    print('| 1. Yes')
    print('| 2. No')
    try:
        command = int(input('\n| Command > '))
    except ValueError:
        print('\n| Please enter a number, not text.')
        return confirmBatch(material, length)
    while int(command) not in options:
        print('\n| Not a valid choice.')
        return confirmBatch(material, length)
    if command == 1:
        return True
    elif command == 2:
        return False

def populateValidOptions(menuOptions):
    validOptions = []
    for option in menuOptions:
        validOptions.append(option[0])
    return validOptions

def getInput(validOptionsList):
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

def getBatchLength(material):
    if material == 'Smooth':
        maxLength = 145
    elif material == 'Woven':
        maxLength = 95
    batchLength = input('| Please enter a batch length > ')
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
        return batchLength

def mainMenu():
    menuOptions = (
        (1, 'Smooth, 150 Feet', 'Smooth', 145, True),
        (2, 'Woven, 100 Feet', 'Woven', 95, True),
        (3, 'Smooth, 150 Feet, Disregard Minimum Length', 'Smooth', 145, False),
        (4, 'Woven, 100 Feet, Disregard Minimum Length', 'Woven', 95, False),
        (5, 'Smooth, Custom Length, Disregard Minimum Length', 'Smooth', 0, False),
        (6, 'Woven, Custom Length, Disregard Minimum Length', 'Woven', 0, False),
    )
    validOptions = populateValidOptions(menuOptions)

    print('| Please enter a batch type: ')
    for option in menuOptions:
        print('|  (' + str(option[0]) + ')', option[1],)
    
    command = menuOptions[(getInput(validOptions)-1)]
    batchDetails = {
        'material':command[2],
        'materialLength':command[3]
    }
    if batchDetails['materialLength'] == 0:
        batchDetails['materialLength'] = getBatchLength(batchDetails['material'])
    return batchDetails

def buildABatch():
    print('\n| Welcome to Build-A-Batch!\n')
    batchDetails = mainMenu()
    print(batchDetails)
buildABatch()