#!usr/bin/env python

import glob
import wallpaperSorterVariables as gv
import getPdfData as getPdf
import pdf_splitter as pdfSplitter
from add_macos_tag import apply_tag as applyTag
from shutil import move, copy, Error
from os import mkdir, remove
from PyPDF2 import utils


def getPdfGlob(dueDate, material, fullOrSamp): # Takes a "due date" (OT, Late, Today, Future), a material type, and full or sample, then returns a glob list 
    dueDateLookup = {
        'OT':'1 - OT Orders/',
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

#def createBatch(includeOTs, batchDict, availablePdfs): #batch creation process
def createBatch(currentBatchDict, availablePdfs):
    includeOTs = currentBatchDict['batchDetails']['includeOTs']
    
    #checks whether or not the batch should contain order trouble PDFs
    if includeOTs == True:
        currentBatchDict = batchLoopController('Today','full',currentBatchDict, availablePdfs)
        #if currentBatchDict['batchDetails']['length'] > (currentBatchDict['batchDetails']['materialLength'] - 9.6):
    if currentBatchDict['batchDetails']['length'] < currentBatchDict['batchDetails']['materialLength'] - 96:
        currentBatchDict = batchLoopController('Late','full',currentBatchDict, availablePdfs)
    if currentBatchDict['batchDetails']['length'] < currentBatchDict['batchDetails']['materialLength'] - 96:
        currentBatchDict = batchLoopController('Today','full',currentBatchDict, availablePdfs)
    if currentBatchDict['batchDetails']['length'] < currentBatchDict['batchDetails']['materialLength'] - 96:
        currentBatchDict = batchLoopController('Future','full',currentBatchDict, availablePdfs)
    return currentBatchDict

def createBatchFolderAndMovePdfs(currentBatchDict):
    # variables from currentBatchDict for the new batch directory
    batchID = currentBatchDict['batchDetails']['ID']
    batchMaterial = currentBatchDict['batchDetails']['material']
    batchPriority = currentBatchDict['batchDetails']['priority']
    batchLength = currentBatchDict['batchDetails']['length']
    tag = 'Hotfolder'
    
    # new batch directory name and path assembly
    batchDirectory = gv.batchFoldersDir + 'Batch #' + str(batchID) + ' ' + batchMaterial + ' L' + str(batchLength) + ' P' + str(batchPriority)
    batchDirectoryFull = batchDirectory + '/Full'
    batchDirectorySamp = batchDirectory + '/Samples'


    # make new batch directory and the Full and Sample hotfolders
    mkdir(batchDirectory)
    mkdir(batchDirectoryFull)
    mkdir(batchDirectorySamp)
    
    # print new batch confirmation
    print('\n| New Batch:', str(batchID))
    print('| Material', batchMaterial)
    print('| Length:', batchLength)

    # begin moving PDFs in the currentBatchDict to the new directory folders
    for printPdf in currentBatchDict['Late']['full']['batchList']:
        if getPdf.size(printPdf) == 'Full':
            tryToMovePDF(printPdf, batchDirectoryFull, getPdf.friendlyName(printPdf))
        else:
            tryToMovePDF(printPdf, batchDirectorySamp, getPdf.friendlyName(printPdf))
    
    # after moving items, iterate through full orders and split any that are >2 repeat.
    for printPdf in glob.glob(batchDirectoryFull + '/*.pdf'):
        if getPdf.repeat(printPdf) > 2:
            try:
                pdfSplitter.cropMultiPanelPDFs(printPdf, batchDirectory + '/Full')
            except utils.PdfReadError:
                print('| Couldn\'t split file. In case it\'s needed, a copy of the original file is in "#Past Orders/Original Files"')
                print('| PDF:', getPdf.friendlyName(printPdf))
                tag = 'Manual'
    
    # apply the manual or hotfolder tag
    applyTag(tag, batchDirectory)
    return

def tryToMovePDF(printPDF, BatchDir, friendlyPdfName):
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

def batchLoopController(dueDate, fullOrSamp, currentBatchDict, availablePdfs):
    if fullOrSamp.lower() == 'full':
        currentBatchDict[dueDate][fullOrSamp] = batchFullLoop(currentBatchDict['batchDetails'], currentBatchDict[dueDate][fullOrSamp], availablePdfs[dueDate][fullOrSamp]['batchList'])
        currentBatchDict['batchDetails']['length'] += currentBatchDict[dueDate][fullOrSamp]['batchLength']
    return currentBatchDict

def batchFullLoop(batchDetailsDict, batchDateDict, availablePdfs):
    currentLength = batchDetailsDict['length']
    maxLength = batchDetailsDict['materialLength']
    sortedList = availablePdfs
    batchList = []
    
    #while (currentLength < (maxLength-24)):
    currentLength = 0
    findOdd = False
    oddMatchHeight = 0
    for printPdf in sortedList:
        if currentLength > (maxLength-24):
            break
        pdfLength = getPdf.length(printPdf)
        pdfOddOrEven = getPdf.oddOrEven(printPdf)
        pdfHeight = getPdf.height(printPdf)
        if (findOdd == False):
            if currentLength + pdfLength > maxLength:
                continue
            else:
                currentLength += pdfLength
                batchList.append(printPdf)
                if pdfOddOrEven == 1:
                    findOdd = True
                    oddMatchHeight = pdfHeight
        elif (findOdd == True):
            if pdfOddOrEven == 1:
                if oddMatchHeight == pdfHeight:
                    if (currentLength + (pdfLength - (pdfHeight + .5))) > maxLength:
                        continue
                    else:
                        currentLength += (pdfLength - (pdfHeight + .5))
                        batchList.append(printPdf)
                        findOdd = False
                else:
                    if currentLength + pdfLength > maxLength:
                        continue
                    else:
                        currentLength += pdfLength
                        batchList.append(printPdf)
                        oddMatchHeight = pdfHeight

    batchDateDict['batchList'] = batchList
    batchDateDict['batchLength'] = currentLength
    return batchDateDict

    '''
    ### Write Main Batching Loop Here ###
    '''

    return