#!usr/bin/env python

import os, shutil, math, datetime, glob
from PyPDF2 import utils
from datetime import  datetime
from batchCreation import getListOfPdfs
from batchCreationDueDateOld import getPdfGlob


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
            'length':0,
            'materialLength':0,
            'careAboutMinimumLength':True,
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

''' Function Definitions '''

### Main Controller and Functions ###

def buildABatch(): # Begins the batch building process
    print('\n| Welcome to Build-A-Batch!\n')
    
    # Prompts user for batch information and confirms their selection
    batchDetails = batchDetailsMenu()
    confirmBatchMenu(batchDetails['material'],int(batchDetails['materialLength']/12))
    
    # Resets currentBatchDict, then adds the details from the previous section
    resetCurrentBatchDict()
    currentBatchDict['batchDetails']['ID'] = getBatchID()
    currentBatchDict['batchDetails']['material'] = batchDetails['material']
    currentBatchDict['batchDetails']['materialLength'] = batchDetails['materialLength']
    currentBatchDict['batchDetails']['careAboutMinimumLength'] = batchDetails['minimumLength']

    #checks for orders that need to be printed
    '''
    Are there [OT] orders?
    How many [OT] orders are there?
    How many are sample orders?
        How long are they?
        Will the samples take up more than 20% of the total batch length?
            If they will take up less than 30%, add them all to the batch
            Otherwise, only add in enough to take up 20% of the batch.
        Recalculate batch length
    How many are full orders?
        Sort them by length. 
        How long will they be?
            By default, full orders should comprise 80% of the order (unless overriden by the sample logic above)
            If the total length of [OT] orders is less than the remaining length, add them all in.
            Otherwise, add in enough OT orders to meet, but not exceed, the remaining length.
        Recalculate batch length.
    
    Add in reverse order - OT should be added last, then Late, then Today, then Future.
    '''

    otFullGlob = getPdfGlob('Late', currentBatchDict['batchDetails']['material'], 'full')
    otSampleGlob= getPdfGlob('Late', currentBatchDict['batchDetails']['material'], 'Sample')
    totalOtFullCount = len(otFullGlob)
    totalOtSampleCount = len(otSampleGlob)
    totalOtSampleLength = ((math.floor(totalOtSampleCount / 2) + (totalOtSampleCount % 2)) * 9.5)
    totalOtFullLength = calculateFullLength(otFullGlob)
    if (totalOtFullCount + totalOtSampleCount) > 0:
        print('| Full OT Orders:', str(totalOtFullCount))
        print('| Sample OT Orders:', str(totalOtSampleCount))
        print('| Sample OT Length:', str(totalOtSampleLength/12))
    print(currentBatchDict)
    print(totalOtFullLength)

def calculateFullLength(globOfPdfs): # Takes a list of paths to pdfs, calls sortPdfsByLength to srot them by length, then calculates their full length.
    sortedList = sortPdfs(globOfPdfs)
    totalPdfsLength = 0
    findOdd = False
    oddMatchHeight = 0
    for printPdf in sortedList:
        pdfLength = getPdf.length(printPdf)
        pdfOddOrEven = getPdf.oddOrEven(printPdf)
        pdfHeight = getPdf.height(printPdf)
        if (findOdd == False):
            totalPdfsLength += pdfLength
            if pdfOddOrEven == 1:
                findOdd = True
                oddMatchHeight = pdfHeight
        elif (findOdd == True):
            if pdfOddOrEven == 1:
                if oddMatchHeight == pdfHeight:
                    totalPdfsLength += (pdfLength - (pdfHeight + .5))
                    findOdd = False
                else:
                    totalPdfsLength += pdfLength
                    oddMatchHeight = pdfHeight
    return totalPdfsLength
    
def sortPdfs(pdfList):
    sortedByOdd = sortPdfsByOdd(pdfList)
    sortedByHeight = sortPdfsByHeight(sortedByOdd)
    sortedByLength = sortPdfsByLength(sortedByHeight)
    pdfList = combineMultiplePdfLists(sortedByLength)
    return pdfList

def sortPdfsByOdd(pdfList): # Takes a list of pathstopdfs and returns a dict of lists sorted by odd and even quantities, respectively.
    sortedPdfs = {
        'evenPdfs':[],
        'oddPdfs':[],
    }
    for printPdf in pdfList:
        pdfOdd = getPdf.oddOrEven(printPdf)
        if pdfOdd == 1:
            sortedPdfs['oddPdfs'].append(printPdf)
        else:
            sortedPdfs['evenPdfs'].append(printPdf)
    return sortedPdfs

def sortPdfsByHeight(pdfDict):# takes a dict of lists of pathstopdfs and sorts them by height, from greatest to least.
    sortedList = {
        '146.25':[],
        '136.25':[],
        '124.25':[],
        '112.25':[],
        '100.25':[],
        '88.25':[],
        '76.25':[],
        '64.25':[],
        '52.25':[],
        '40.25':[],
    }
    for listToSort in pdfDict:
        for printPdf in pdfDict[listToSort]:
            pdfHeight = str(getPdf.height(printPdf))
            sortedList[pdfHeight].append(printPdf)
        pdfDict[listToSort] = sortedList
        sortedList = {
            '146.25':[],
            '136.25':[],
            '124.25':[],
            '112.25':[],
            '100.25':[],
            '88.25':[],
            '76.25':[],
            '64.25':[],
            '52.25':[],
            '40.25':[],
        }
    return pdfDict

def sortPdfsByLength(pdfDict): # takes a list of pathstopdfs and sorts them by length, from greatest to least.
    # Original sort code is at the bottom.
    listToSort = []
    sortedList = []
    for oddList in pdfDict:
        for heightList in pdfDict[oddList]:
            for printPdf in pdfDict[oddList][heightList]:
                pdfLength = getPdf.length(printPdf)
                listToSort.append((pdfLength, printPdf))
            listToSort.sort(reverse=True, key=lambda pdf: pdf[0])
            pdfList = listToSort
            listToSort = []
            for printPdf in pdfList:
                sortedList.append(printPdf[1])
            pdfDict[oddList][heightList] = sortedList
            sortedList = []
    return pdfDict
        
def combineMultiplePdfLists(pdfDict):
    sortedList = []
    for oddList in pdfDict:
        for heightList in pdfDict[oddList]:
            for printPdf in pdfDict[oddList][heightList]:
                sortedList.append(printPdf)
    return sortedList

def resetCurrentBatchDict(): # sets currentBatchDict to default/empty values.
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

    return

# Menu Functions

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
        (1, 'Smooth, 150 Feet', 'Smooth', 145, True),
        (2, 'Woven, 100 Feet', 'Woven', 95, True),
        (3, 'Smooth, 150 Feet, Disregard Minimum Length', 'Smooth', 145, False),
        (4, 'Woven, 100 Feet, Disregard Minimum Length', 'Woven', 95, False),
        (5, 'Smooth, Custom Length, Disregard Minimum Length', 'Smooth', 0, False),
        (6, 'Woven, Custom Length, Disregard Minimum Length', 'Woven', 0, False),
    )
    validOptions = populateValidOptions(menuOptions)

    print('| Please enter a batch type: ')
    printMenuOptions(menuOptions)
    
    command = menuOptions[(getInput(validOptions)-1)]
    batchDetails = {
        'material':command[2],
        'materialLength':command[3] * 12,
        'minimumLength':command[4]
    }
    if batchDetails['materialLength'] == 0:
        batchDetails['materialLength'] = getBatchLength(batchDetails['material'])
    return batchDetails

### Batch Building Functions ###

def getPdfGlob(dueDate, material, fullOrSamp): # Takes a "due date" (OT, Late, Today, Future), a material type, and full or sample, then returns a glob list 
    dueDateLookup = {
        'OT':'1 - OT Orders/',
        'Late':'2 - Late/',
        'Today':'3 - Today/',
        'Future':'4 - Future/',
    }
    material = gv.dirLookupDict[material]
    if fullOrSamp.lower() == 'full':
        fullOrSamp = 'Full/**/*.pdf'
    else:
        fullOrSamp = 'Sample/*.pdf'
    
    return glob.glob(gv.sortingDir + dueDateLookup[dueDate] + material + fullOrSamp, recursive=True)

''' Leaving the following because it's the original sort code
# def sortPdfsByLength(pdfList): # takes a list of pathstopdfs and sorts them by length, from greatest to least.
#     listToSort = []
#     sortedList = []
#     for print_pdf in pdfList:
#         pdf_length = getPdf.length(print_pdf)
#         listToSort.append((pdf_length, print_pdf))
#     listToSort.sort(reverse=True, key=lambda pdf: pdf[0])
#     pdfList = listToSort
#     for print_pdf in pdfList:
#         sortedList.append(print_pdf[1])
#     pdfList = sortedList
#     return pdfList
'''

buildABatch()