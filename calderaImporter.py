#!usr/bin/env python

import glob
from shutil import move, rmtree
from datetime import datetime
from time import sleep as wait
from os import mkdir, walk, listdir, rmdir
from getPdfData import friendlyName
from batchCreate import tryToMovePDF
from batchMenu import populateValidOptions, printMenuOptions
from wallpaperSorterVariables import batchFoldersDir, hotfoldersDir, pastOrdersDir


today = datetime.today()

def calderaBatchImporter(): # main function for this module. First calls checkForBatchFolders
    checkForBatchFolders()
    return 

def checkForBatchFolders(): # checks for batch folders to import and export. If there are none, shorts the module. Otherwise, continues
    importBatchFoldersGlob = glob.glob(batchFoldersDir + '/Batch *')
    exportBatchFoldersGlob = glob.glob(hotfoldersDir + '/*/z_Currently Importing */*')
    if (len(importBatchFoldersGlob) > 0) or (len(exportBatchFoldersGlob) > 0):
        batchToImport = batchSelector(importBatchFoldersGlob) # accepts a list of batches, then returns a single, user-selected batch
        if batchToImport[1] == 'Export':
            exportFromCaldera(batchToImport[0])
        else:
            importToCaldera(batchToImport) # begins to import the user-selected batch. Accepts a batch as a file path.
        return calderaBatchImporter()
    else:
        print('| No batches to import or export.')
        return
    
def batchSelector(listOfBatches): #takes a list of batches. Sorts them by priority, sorts priorities by order number, then prints them like a menu. Accepts input from user to indicate a batch for importing. Returns batch name as a file path
    listOptionCounter = 1
    otBatchList = []
    lateBatchList = []
    todayBatchList = []
    futureBatchList = []
    batchesToExport = {
        'smooth':getBatchesToExport('Smooth'),
        'woven':getBatchesToExport('Woven'),
    }

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
    smoothExportList = sortBatchesByID(batchesToExport['smooth'])
    wovenExportList = sortBatchesByID(batchesToExport['woven'])
    
    # Calls printBatchList on each list to print it nicely for the user. Returns the number of the last item in the list
    listOptionCounter = printBatchList('OT', otBatchList, listOptionCounter)
    otListStop = listOptionCounter-1 
    listOptionCounter = printBatchList('Late', lateBatchList, listOptionCounter)
    lateListStop = listOptionCounter-1
    listOptionCounter = printBatchList('Today', todayBatchList, listOptionCounter)
    todayListStop = listOptionCounter-1
    listOptionCounter = printBatchList('Future', futureBatchList, listOptionCounter)
    futureListStop = listOptionCounter-1
    listOptionCounter = printBatchList('Smooth', smoothExportList, listOptionCounter, export=True)
    smoothExportCounter = listOptionCounter-1
    listOptionCounter = printBatchList('Woven', wovenExportList, listOptionCounter, export=True)
    wovenExportCounter = listOptionCounter-1

    # populates menu for batch selecting. When the user provides a number, we do interval comparison to see which list it should be from. After decided, we subtract one from the user's input to align it to the list, then subtract the length of the previous list to make the user's input align properly with a python list.
    # Then return the batch
    print('\n| Which batch would you like to move?')
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
    elif futureListStop < command <= smoothExportCounter:
        command -= (1 + futureListStop)
        batch = smoothExportList[command]
        print('\n| Selected', batch.split('/')[-1], 'for export.')
        return [batch, 'Export']
    elif smoothExportCounter < command <= wovenExportCounter:
        command -= (1 + smoothExportCounter)
        batch = wovenExportList[command]
        print('\n| Selected', batch.split('/')[-1], 'for export.')
        return [batch, 'Export']

def getBatchesToExport(material):
    pathToDir = hotfoldersDir + '*/z_Currently Importing ' + material + '/*'
    batchList = (glob.glob(pathToDir, recursive=True))
    # sortedList = []
    
    # for batch in batchList:
    #     sortedList.append(batch.split('/')[-1])

    return batchList

def exportFromCaldera(batch):
    batchMaterial = batch.split('/')[-1].split(' ')[2]
    printer = batch.split('/')[-3]
    pathToHotfolder = batch.split(printer)[0] + printer + '/' + batchMaterial + '/'
    sampleRemovalList = []

    utilityToExport = glob.glob(pathToHotfolder + '/999999999-1-(*.pdf')
    samplesToExport = glob.glob(pathToHotfolder + '/*-Samp-*.pdf')
    fullToExport = glob.glob(pathToHotfolder + '/*-Full-*.pdf')
    headersToExport = glob.glob(pathToHotfolder + '/*header*.pdf')
    
    for printPdf in samplesToExport:
        if '999999999' in printPdf:
            sampleRemovalList.append(printPdf)
    for printPdf in sampleRemovalList:
            samplesToExport.remove(printPdf)

    removeEmptyDirectories(batch)

    if len(samplesToExport) > 0:
        mkdir(batch + '/Samples/')
    if len(fullToExport) > 0:
        mkdir(batch + '/Full/')
    if len(headersToExport) > 0:
        mkdir(batch + '/Headers/')
    if len(utilityToExport) > 0:
        mkdir(batch + '/Utility/')

    for pdf in samplesToExport:
        move(pdf, batch + '/Samples/')
    for pdf in fullToExport:
        move(pdf, batch + '/Full/')
    for pdf in headersToExport:
        move(pdf, batch + '/Headers/')
    for printPdf in utilityToExport:
        move(printPdf, batch + '/Utility/')

    move(batch, pastOrdersDir)

    print('\n| Exported', batch.split('/')[-1])
    return

def removeEmptyDirectories(batchDirectory): # once a batch folder has been made, walks through the batch folder and removes any empty directories.
    try:
        rmtree(batchDirectory + '/1 - OT')
    except:
        pass
    try:
        rmtree(batchDirectory + '/2 - Late')
    except:
        pass
    try:
        rmtree(batchDirectory + '/3 - Today')
    except:
        pass
    try:
        rmtree(batchDirectory + '/4 - Future')
    except:
        pass
    try:
        rmtree(batchDirectory + '/5 - Utility')
    except:
        pass
    return

def importToCaldera(batch): # takes a batch as a file path and loops through its contents in reverse order. Moves each print pdf to a specified printer's hotfolder based on material type.
    print('| Caldera Online.')
    print('| Batch:', batch.split('/')[-1])

    # get printer to use    
    printerToUse = getPrinter(batch.split('/')[-1].split(' ')[2])

    # get material type for currently importing hotfolder
    batchMaterial = batch.split('/')[-1].split(' ')[2]
    
    # move batch to the correct currently importing hotfolder
    move(batch, hotfoldersDir + printerToUse + 'z_Currently Importing ' + batchMaterial + '/')
    wait(2.5)
    
    # Creates variables for the batch
    batch = batch.split('/')[-1] 
    receivingHotfolder = hotfoldersDir + printerToUse + batchMaterial + '/'
    batch = hotfoldersDir + printerToUse + 'z_Currently Importing ' + batchMaterial + '/' + batch + '/'
    
    #globs of ALL batch lists
    # allBatchLists = (
    #     sortSamplesForCutting((glob.glob(batch + '4 - Future/Samples/*.pdf', recursive=True))),
    #     (glob.glob(batch + '4 - Future/Full/*.pdf', recursive=True)),
    #     sortSamplesForCutting((glob.glob(batch + '3 - Today/Samples/*.pdf', recursive=True))),
    #     (glob.glob(batch + '3 - Today/Full/*.pdf', recursive=True)),
    #     sortSamplesForCutting((glob.glob(batch + '2 - Late/Samples/*.pdf', recursive=True))),
    #     (glob.glob(batch + '2 - Late/Full/*.pdf', recursive=True)),
    #     sortSamplesForCutting((glob.glob(batch + '1 - OT/Samples/*.pdf', recursive=True))),
    #     (glob.glob(batch + '1 - OT/Full/*.pdf', recursive=True)),
    #     (glob.glob(batch + '5 - Utility/*.pdf', recursive=True)),
    # )

    allBatchLists = (
        ((glob.glob(batch + '4 - Future/Samples/*.pdf', recursive=True))),
        (glob.glob(batch + '4 - Future/Full/*.pdf', recursive=True)),
        ((glob.glob(batch + '3 - Today/Samples/*.pdf', recursive=True))),
        (glob.glob(batch + '3 - Today/Full/*.pdf', recursive=True)),
        ((glob.glob(batch + '2 - Late/Samples/*.pdf', recursive=True))),
        (glob.glob(batch + '2 - Late/Full/*.pdf', recursive=True)),
        ((glob.glob(batch + '1 - OT/Samples/*.pdf', recursive=True))),
        (glob.glob(batch + '1 - OT/Full/*.pdf', recursive=True)),
        (glob.glob(batch + '5 - Utility/*.pdf', recursive=True)),
    )

    for pdfList in allBatchLists:
        try:
            moveToHotfolder(pdfList, receivingHotfolder)
        except TypeError:
            pass

    print('\n| Moved', batch.split('/')[-2], 'into', receivingHotfolder.split('/')[6].split(' ')[1], batchMaterial, 'HotFolder')
    return

def getPrinter(batchMaterial):
    menuOptions = printerCheck(batchMaterial)

    validOptions = populateValidOptions(menuOptions)
    print('| Please select a printer to use: ')
    printMenuOptions(menuOptions)

    command = menuOptions[(getInput(validOptions)-1)][1]

    if 'unavailable' in command:
        print('\n|', command.split(' ')[0], 'already has a batch in the', batchMaterial, 'hotfolder.\n| Please export the batch before using', command.split(' ')[0] + '.\n')
        return getPrinter(batchMaterial)

    printerLookup = {
        'Ichi':'1 Ichi/',
        'Ni':'2 Ni/',
        'San':'3 San/',
    }

    return printerLookup[command]

def printerCheck(batchMaterial):
    materialHotfolders = glob.glob(hotfoldersDir + '*/z_Currently Importing ' + batchMaterial + '/*')
    unavailablePrinters = []
    availablePrinters = ['1 Ichi', '2 Ni', '3 San']
    revisedPrinters = []

    for batch in materialHotfolders:
        unavailablePrinters.append(batch.split('/')[-3])
    
    for printer in availablePrinters:
        if printer in unavailablePrinters:
            revisedPrinters.append(printer.split(' ')[0] + ' ' + printer.split(' ')[1] + ' is unavailable for ' + batchMaterial)
        else:
            revisedPrinters.append(printer)

    availablePrinters = []

    for printer in revisedPrinters:
        availablePrinters.append((int(printer.split(' ')[0]), printer.split(printer.split(' ')[0] + ' ')[1]))
    
    return availablePrinters

def sortSamplesForCutting(pdfList): #takes a list of samples, then sorts them by by every-other. That way the samples print from top to bottom instead of right to left
    if len(pdfList) == 0:
        return
    
    counter = 0

    firstList = []
    secondList = []

    for printPdf in pdfList:
        if '999999999-header' in printPdf:
            pdfList.append(printPdf)
            pdfList.remove(printPdf)
            break

    for printPdf in pdfList:
        if counter % 2 == 0:
            firstList.append(printPdf)
            counter += 1
        else:
            secondList.append(printPdf)
            counter += 1
    
    counter = len(firstList) + len(secondList)

    sortedList = []

    firstListCounter = 0
    secondListCounter = 0
    for i in range(counter):
        if i % 2 == 0:
            sortedList.append(firstList[firstListCounter])
            firstListCounter += 1
        else:
            sortedList.append(secondList[secondListCounter])
            secondListCounter += 1

    return sortedList

def moveToHotfolder(pdfList, receivingHotfolder):
    for printPdf in pdfList:
        if '999999999-header' not in printPdf:
            print('| Moving', friendlyName(printPdf))
            tryToMovePDF(printPdf, receivingHotfolder, friendlyName(printPdf))
            wait(.5)
            continue
    for headerPdf in pdfList:
        if '99999999-header' in headerPdf:
            # if exists(receivingHotfolder + headerPdf.split('/')[-1]):
            #     remove(headerPdf)
            # else:
            move(headerPdf, receivingHotfolder)
            wait(.5)
            break
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

def printBatchList(listName, batchList, optionCounter, export=False):
    if len(batchList) == 0:
        return optionCounter
    if export==True:
        print('\n| Available', listName, 'batches to export:')
    else:
        print('\n| Available', listName, 'batches to import:')
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
