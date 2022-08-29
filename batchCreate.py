#!usr/bin/env python

import glob
from math import floor
import wallpaperSorterVariables as gv
import getPdfData as getPdf
import pdf_splitter as pdfSplitter
from add_macos_tag import apply_tag as applyTag
from shutil import move, copy, Error
from os import mkdir, remove, rmdir, walk, listdir
from PyPDF2 import utils

def getPdfGlob(dueDate, material, fullOrSamp): # Takes a "due date" (OT, Late, Today, Future), a material type, and full or sample, then returns a glob list 
    dueDateLookup = {
        'OT':'1 - OT/',
        'Late':'2 - Late/',
        'Today':'3 - Today/',
        'Future':'4 - Future/',
        'all':'*/',
    }
    material = gv.dirLookupDict[material]
    if fullOrSamp.lower() == 'full':
        fullOrSamp = 'Full/**/*.pdf'
    elif fullOrSamp.lower() == 'sample':
        fullOrSamp = 'Sample/*.pdf'
    else:
        fullOrSamp = '**/*.pdf'
    
    return glob.glob(gv.sortingDir + dueDateLookup[dueDate] + material + fullOrSamp, recursive=True)

def createBatch(currentBatchDict, availablePdfs): # gathers PDFs for the new batch
    includeOTs = currentBatchDict['batchDetails']['includeOTs']
    
    # iterates through avialable PDFs and calls the batch loop control to add them to the current batch list
    if includeOTs == True: #checks whether or not the batch should contain order trouble PDFs
        currentBatchDict = batchLoopController('OT','full',currentBatchDict, availablePdfs)
    if (includeOTs == True) and (currentBatchDict['batchDetails']['length'] < (currentBatchDict['batchDetails']['materialLength'] - 9.6)): #if the batch should include OTs and there's at least room for one sample, check for samples
        currentBatchDict = batchLoopController('OT','sample',currentBatchDict, availablePdfs)
    if currentBatchDict['batchDetails']['length'] < currentBatchDict['batchDetails']['materialLength'] - 96: #if there's at least room for 8' panel, check for more full orders. Otherwise, move onto samples
        currentBatchDict = batchLoopController('Late','full',currentBatchDict, availablePdfs)
    if currentBatchDict['batchDetails']['length'] < (currentBatchDict['batchDetails']['materialLength'] - 9.6): #if there's at least room for one sample, check for samples
        currentBatchDict = batchLoopController('Late','sample',currentBatchDict, availablePdfs)
    if currentBatchDict['batchDetails']['length'] < currentBatchDict['batchDetails']['materialLength'] - 96: #if there's at least room for 8' panel, check for more full orders. Otherwise, move onto samples
        currentBatchDict = batchLoopController('Today','full',currentBatchDict, availablePdfs)
    if currentBatchDict['batchDetails']['length'] < (currentBatchDict['batchDetails']['materialLength'] - 9.6): #if there's at least room for one sample, check for samples
        currentBatchDict = batchLoopController('Today','sample',currentBatchDict, availablePdfs)
    if currentBatchDict['batchDetails']['length'] < currentBatchDict['batchDetails']['materialLength'] - 96: #if there's at least room for 8' panel, check for more full orders. Otherwise, move onto samples
        currentBatchDict = batchLoopController('Future','full',currentBatchDict, availablePdfs)
    if currentBatchDict['batchDetails']['length'] < (currentBatchDict['batchDetails']['materialLength'] - 9.6): #if there's at least room for one sample, check for samples
        currentBatchDict = batchLoopController('Future','sample',currentBatchDict, availablePdfs)

    currentBatchDict['batchDetails']['priority'] = setBatchPriority(currentBatchDict)
    addColorGuides(currentBatchDict)
    
    return currentBatchDict

def createBatchFolderAndMovePdfs(currentBatchDict): # Creates a new batch folder and moves the pdfs over.
    # variables from currentBatchDict for the new batch directory
    batchID = currentBatchDict['batchDetails']['ID']
    batchPriority = currentBatchDict['batchDetails']['priority']
    batchMaterial = currentBatchDict['batchDetails']['material']
    batchLength = currentBatchDict['batchDetails']['length']
    materialLength = currentBatchDict['batchDetails']['materialLength']
    tag = 'Hotfolder'
    
    # new batch directory name and path assembly
    batchDirectory = gv.batchFoldersDir + 'Batch #' + str(batchID) + ' ' + batchMaterial + ' L' + str(batchLength) + ' P-' + str(batchPriority)

    # make new batch directory and the Full and Sample hotfolders
    mkdir(batchDirectory)
    makeBatchDirectories(batchDirectory)
    
    # print new batch confirmation
    print('\n| New Batch:', str(batchID))
    print('| Material:', batchMaterial)
    print('| Length:', batchLength)

    # List of batch lists to iterate through and move pdfs
    listOfBatchLists = (
        currentBatchDict['OT']['full']['batchList'],
        currentBatchDict['OT']['sample']['batchList'],
        currentBatchDict['Late']['full']['batchList'],
        currentBatchDict['Late']['sample']['batchList'],
        currentBatchDict['Today']['full']['batchList'],
        currentBatchDict['Today']['sample']['batchList'],
        currentBatchDict['Future']['full']['batchList'],
        currentBatchDict['Future']['sample']['batchList'],
    )

    # small mechanism for iterating through the proper directories inside a batch folder
    batchPriorityCounter = 0
    batchPriorityDict = {
        1: batchDirectory + '/1 - OT/Full',
        2: batchDirectory + '/1 - OT/Samples',
        3: batchDirectory + '/2 - Late/Full',
        4: batchDirectory + '/2 - Late/Samples',
        5: batchDirectory + '/3 - Today/Full',
        6: batchDirectory + '/3 - Today/Samples',
        7: batchDirectory + '/4 - Future/Full',
        8: batchDirectory + '/4 - Future/Samples',
    }

    # begin moving PDFs in the currentBatchDict to the new directory folders
    for batchList in listOfBatchLists:
        batchPriorityCounter += 1
        if len(batchList) > 0:
            for printPdf in batchList:
                if '999999999-header' not in printPdf:
                    tryToMovePDF(printPdf, batchPriorityDict[batchPriorityCounter], getPdf.friendlyName(printPdf))
                    continue
                copy(printPdf, batchPriorityDict[batchPriorityCounter]) #this should copy over the header very last
    batchPriorityCounter = 0

    # after moving items, iterate through full orders and split any that are >2 repeat.
    for printPdf in glob.glob(batchDirectory + '/*.pdf'):
        if getPdf.repeat(printPdf) > 2:
            try:
                pdfSplitter.cropMultiPanelPDFs(printPdf, batchDirectory + '/Full')
            except utils.PdfReadError:
                print('| Couldn\'t split file. In case it\'s needed, a copy of the original file is in "#Past Orders/Original Files"')
                print('| PDF:', getPdf.friendlyName(printPdf))
                tag = 'Manual'

    # Check if a color guide or roll stickers needs to be added, then add them.
    if currentBatchDict['batchDetails']['colorGuides']['uniqueFilename'] != '':
        copy(currentBatchDict['batchDetails']['colorGuides']['default'], batchDirectory + currentBatchDict['batchDetails']['colorGuides']['uniqueFilename'])
    if currentBatchDict['batchDetails']['rollStickers']['uniqueFilename'] != '':
        copy(currentBatchDict['batchDetails']['rollStickers']['default'], batchDirectory + currentBatchDict['batchDetails']['rollStickers']['uniqueFilename'])

    # apply the manual or hotfolder tag
    applyTag(tag, batchDirectory)
    removeEmptyDirectories(batchDirectory)

    return

def addColorGuides(currentBatchDict): # check if the total length can fit color guides or roll stickers, and add them appropriately
    batchMaterial = currentBatchDict['batchDetails']['material']
    batchLength = currentBatchDict['batchDetails']['length']
    materialLength = currentBatchDict['batchDetails']['materialLength']


    if batchLength <= materialLength - 8:
        utilityQty = floor((materialLength - batchLength)/9.5)
        if utilityQty == 0:
            utilityQty = 1
            currentBatchDict['batchDetails']['colorGuides']['uniqueFilename'] = '/5 - Utility/999999999-1-(' + str(gv.today) + ')-Stnd-' + gv.substrate[batchMaterial] + '-Samp-Rp 2-Qty ' + str(utilityQty*2) + '-Color Chart-L' + str(utilityQty * 9.5) + '-W25-H9.pdf'
            batchLength += (utilityQty * 9.5)
        elif utilityQty <= 11:
            currentBatchDict['batchDetails']['colorGuides']['uniqueFilename'] = '/5 - Utility/999999999-1-(' + str(gv.today) + ')-Stnd-' + gv.substrate[batchMaterial] + '-Samp-Rp 2-Qty ' + str(utilityQty*2) + '-Color Chart-L' + str(utilityQty * 9.5) + '-W25-H9.pdf'
            batchLength += (utilityQty * 9.5)
        elif utilityQty > 11:
            stickerRollQty = 2
            utilityQty = utilityQty - stickerRollQty
            currentBatchDict['batchDetails']['colorGuides']['uniqueFilename'] = '/5 - Utility/999999999-1-(' + str(gv.today) + ')-Stnd-' + gv.substrate[batchMaterial] + '-Samp-Rp 2-Qty ' + str(utilityQty*2) + '-Color Chart-L' + str(utilityQty * 9.5) + '-W25-H9.pdf'
            currentBatchDict['batchDetails']['rollStickers']['uniqueFilename'] = '/5 - Utility/999999999-1-(' + str(gv.today) + ')-Stnd-' + gv.substrate[batchMaterial] + '-Samp-Rp 2-Qty ' + str(stickerRollQty*2) + '-Roll Stickers-L19-W25-H9.pdf'
            batchLength += (utilityQty * 9.5)
            batchLength += 19

    currentBatchDict['batchDetails']['length'] = batchLength
    
    return currentBatchDict

def makeBatchDirectories(batchDirectory): # makes all the proper batch directories for the batch folder to keep it organized
    batchListDict = (
        batchDirectory + '/1 - OT',
        batchDirectory + '/2 - Late',
        batchDirectory + '/3 - Today',
        batchDirectory + '/4 - Future',
        batchDirectory + '/5 - Utility'
    )
    batchListDict2 = (
        batchListDict[0] + '/Full',
        batchListDict[0] + '/Samples',
        batchListDict[1] + '/Full',
        batchListDict[1] + '/Samples',
        batchListDict[2] + '/Full',
        batchListDict[2] + '/Samples',
        batchListDict[3] + '/Full',
        batchListDict[3] + '/Samples',
    )

    for batchList in batchListDict:
        mkdir(batchList)
    
    for batchList in batchListDict2:
        mkdir(batchList)

def removeEmptyDirectories(batchDirectory): # once a batch folder has been made, walks through the batch folder and removes any empty directories.
    dirToWalk = list(walk(batchDirectory))
    for path, _, _ in dirToWalk[::-1]:
        if len(listdir(path)) == 0:
            rmdir(path)
    return

def setBatchPriority(currentBatchDict): # iterates over each batch list and sets the apropriate priority
    otFull = currentBatchDict['OT']['full']['batchList']
    otSamp = currentBatchDict['OT']['sample']['batchList']
    lateFull = currentBatchDict['Late']['full']['batchList']
    lateSamp = currentBatchDict['Late']['sample']['batchList']
    todayFull = currentBatchDict['Today']['full']['batchList']
    todaySamp = currentBatchDict['Today']['sample']['batchList']
    futureFull = currentBatchDict['Future']['full']['batchList']
    futureSamp = currentBatchDict['Future']['sample']['batchList']

    
    if (len(otFull) > 0) or (len(otSamp) > 0):
        return 'OT'
    elif (len(lateFull) > 0) or (len(lateSamp) > 0):
        return 'Late'
    elif (len(todayFull) > 0) or (len(todaySamp) > 0):
        return 'Today'
    elif (len(futureFull) > 0) or (len(futureSamp) > 0):
        return 'Future'

def tryToMovePDF(printPDF, BatchDir, friendlyPdfName): # function that tries to move a PDF. If it can't move, it will try to copy then remove the original. If it can't do that, it will error out gracefully.
    try:
        move(printPDF, BatchDir)
        return
    except Error:
        if getPdf.size == 'Full':
            copy(printPDF, BatchDir)
        try:
            remove(printPDF)
            return
        except OSError:
            print('|> Moved PDF to batch folder, but couldn\'t remove the original file. Please remove the original file.')
            print('|> PDF:', friendlyPdfName)
            print('|> Path:', printPDF)
            return
    except FileNotFoundError:
        print('|> Couldn\'t move PDF. Please check to make sure it exists.')
        print('|> PDF:', friendlyPdfName)
        print('|> Path:', printPDF)
        return

def batchLoopController(dueDate, fullOrSamp, currentBatchDict, availablePdfs): # single function to control calling the proper batch loop based on order size
    if fullOrSamp.lower() == 'full':
        currentBatchDict[dueDate][fullOrSamp] = batchLoopFull(currentBatchDict['batchDetails'], currentBatchDict[dueDate][fullOrSamp], availablePdfs[dueDate][fullOrSamp]['batchList'])
        currentBatchDict['batchDetails']['length'] += currentBatchDict[dueDate][fullOrSamp]['batchLength']
        if len(currentBatchDict[dueDate][fullOrSamp]['batchList']) > 0:
            currentBatchDict[dueDate][fullOrSamp]['batchList'].append(currentBatchDict[dueDate][fullOrSamp]['header'])
            currentBatchDict['batchDetails']['length'] += 1.75
    else:
        currentBatchDict[dueDate][fullOrSamp] = batchLoopSample(currentBatchDict['batchDetails'], currentBatchDict[dueDate][fullOrSamp], availablePdfs[dueDate][fullOrSamp]['batchList'])
        currentBatchDict['batchDetails']['length'] += currentBatchDict[dueDate][fullOrSamp]['batchLength']
        if len(currentBatchDict[dueDate][fullOrSamp]['batchList']) > 0:
            currentBatchDict[dueDate][fullOrSamp]['batchList'].append(currentBatchDict[dueDate][fullOrSamp]['header'])
            currentBatchDict['batchDetails']['length'] += 1.75
    return currentBatchDict

def checkForOtherSamplesOfSameOrder(orderNumber, sortedList, samplesAllowed, samplesAdded): # when adding samples to a batch, checks for and counts other samples in the same order, ensures they will all fit in the batch.
    samplesInOrder = 0

    for printPdf in sortedList:
        if orderNumber in printPdf:
            samplesInOrder +=1
    
    if samplesAdded + samplesInOrder > samplesAllowed:
        return False
    
    return True

def batchLoopSample(batchDetailsDict, batchDateDict, availablePdfs): # loop for adding samples to a batch and calculating length
    # assign variables for ease of use
    currentLength = batchDetailsDict['length']
    maxLength = batchDetailsDict['materialLength']
    sortedList = availablePdfs
    batchList = []
    
    # Get the number of samples we can fit in the remaining length.
    # Because samples are a fixed size, we calculate the number of samples that can fixed rather than the remaining percentage
    # take the availalbe length, subtract the current length, divide by 9.55 (the length of a sample, plus a bit more), round down, then multiply by two because we can fit two samples side by side.
    samplesAllowed = (floor((maxLength - currentLength)/9.55))*2
    samplesAdded = 0

    # main sample loop
    for printPdf in sortedList:
        roomForOrder = checkForOtherSamplesOfSameOrder(getPdf.orderNumber(printPdf), sortedList, samplesAllowed, samplesAdded)
        if not roomForOrder:
            continue
        else:
            batchList.append(printPdf)
            samplesAdded += 1
            if samplesAdded == samplesAllowed:
                break

    # calculate length to add to the current batch. Take the number of samples and divide it by two, rounded down, for the number of full rows. Then take the number of samples mod 2 to see if there's a single sample row. Add the two together, then multiply by 9.5 for length.
    lengthToAdd = (floor(samplesAdded/2) + (samplesAdded%2))*9.5

    batchDateDict['batchList'] = batchList
    batchDateDict['batchLength'] = lengthToAdd
    return batchDateDict

def batchLoopFull(batchDetailsDict, batchDateDict, availablePdfs): # loop for adding full pdfs to a batch and calculating length
    currentLength = batchDetailsDict['length']
    maxLength = batchDetailsDict['materialLength']
    sortedList = availablePdfs
    batchList = []
    
    #while (currentLength < (maxLength-24)):
    currentLength = 0
    findOdd = False
    oddMatchHeight = 0
    for printPdf in sortedList: # begins to iterate over the sorted list
        if currentLength > (maxLength-39): # if the remianing length is ever less than 39", break the loop. No full panels are shorter than 40", so this will save some time
            break
        pdfLength = getPdf.length(printPdf)
        pdfOddOrEven = getPdf.oddOrEven(printPdf)
        pdfHeight = getPdf.height(printPdf)
        if (findOdd == False): 
            if currentLength + pdfLength > maxLength * .93: # if the current item in the iteration will put the batch over the max length, skip it.
                continue
            else:
                currentLength += pdfLength # add the length of the item to the length of the batch
                batchList.append(printPdf) # add the path of the item to the batch list
                if pdfOddOrEven == 1: # if the item added was odd, set flags to search for an odd item with matching height
                    findOdd = True
                    oddMatchHeight = pdfHeight
        elif (findOdd == True): # if the current iteration needs to find an odd item
            if pdfOddOrEven == 1: # if the current item in the iteration is odd
                if oddMatchHeight == pdfHeight: # if the current item also matches the height of the last added item
                    if (currentLength + (pdfLength - (pdfHeight + .5))) > maxLength * .93: # if adding the current odd item will make the current length greather than the max length, skip it.
                        continue
                    else:
                        currentLength += (pdfLength - (pdfHeight + .5)) # if the last item and current item match heights, are both odd, and won't make the batch too long, add the length of the new item to the current length but remove the height of one row.  This is because two matching odd panels will fit together on a single row
                        batchList.append(printPdf) # add the path of the item to the batch list
                        findOdd = False
                else:
                    if currentLength + pdfLength > maxLength * .93: # if the current item in the iteration will put the batch over the max length, skip it.
                        continue
                    else:
                        currentLength += pdfLength # because we feed the loop sorted items, the very next item in the list should match. If it doesn't, it means there are no matching items and the current PDF should be added to the order and the length added normally.
                        batchList.append(printPdf)
                        oddMatchHeight = pdfHeight

    batchDateDict['batchList'] = batchList
    batchDateDict['batchLength'] = currentLength
    return batchDateDict