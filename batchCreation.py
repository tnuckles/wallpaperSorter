#!usr/bin/env python

import os, shutil, math, datetime, time, json, glob, pikepdf
import zipfile as zf
from pathlib import Path
from datetime import date, timedelta, datetime

from PyPDF2 import PdfFileReader, PdfFileWriter, PdfFileMerger, utils
from io import StringIO
import subprocess

import wallpaperSorterVariables as gv
import getPdfData as getPdf

today = datetime.today()

def BatchOrdersMain():
    options = 1,2,3,4,5,6,0
    print('\n| Main Menu > Batch Orders')
    print('| 1. Batch Smooth Full')
    print('| 2. Batch Smooth Samples')
    print('| 3. Batch Woven Full')
    print('| 4. Batch Woven Samples')
    print('| 5. Batch the whole damn thing')
    print('| 0. Return to Main Menu.')
    try:
        command = int(input('\n| Command > '))
    except ValueError:
        print('\n| Please enter a number, not text.')
        return BatchOrdersMain()
    while int(command) not in options:
        print('\n| Not a valid choice.')
        return BatchOrdersMain()
    if command == 1:
        confirm = confirmBatch('Smooth', 'Full')
        if confirm == True:
            batchingController('Smooth', 'Full')
            return BatchOrdersMain()
        elif confirm == False:
            print('\n| Returning to Batch Orders.')
            return BatchOrdersMain()
    elif command == 2:
        confirm = confirmBatch('Smooth', 'Sample')
        if confirm == True:
            batchingController('Smooth', 'Sample')
            return BatchOrdersMain()
        elif confirm == False:
            print('\n| Returning to Batch Orders.')
            return BatchOrdersMain()
    elif command == 3:
        confirm = confirmBatch('Woven', 'Full')
        if confirm == True:
            batchingController('Woven', 'Full')
            return BatchOrdersMain()
        elif confirm == False:
            print('\n| Returning to Batch Orders.')
            return BatchOrdersMain()
    elif command == 4:
        confirm = confirmBatch('Woven', 'Sample')
        if confirm == True:
            batchingController('Woven', 'Sample')
            return BatchOrdersMain()
        elif confirm == False:
            print('\n| Returning to Batch Orders.')
            return BatchOrdersMain()
    elif command == 5:
        batchingController('Woven', 'Full')
        batchingController('Woven', 'Sample')
        batchingController('Smooth', 'Full')
        batchingController('Smooth', 'Sample')
    elif command == 0:
        print('| Returning to Main Menu.')
        return main()

def confirmBatch(material, orderSize):
    options = 1,2
    print('\n| Confirm: Batch', material, orderSize, 'PDFs?')
    print('| 1. Yes')
    print('| 2. No')
    try:
        command = int(input('| Command > '))
    except ValueError:
        print('\n| Please enter a number, not text.')
        return confirmBatch(material, orderSize)
    while int(command) not in options:
        print('\n| Not a valid choice.')
        return confirmBatch(material, orderSize)
    if command == 1:
        return True
    elif command == 2:
        return False

def batchingController(material, orderSize):
    print('\n| Starting', material, orderSize, 'Batching.')
    materialLength = gv.dirLookupDict['MaterialLength'][material]
    # materialLength = int(input('\n| Please input your starting material length in feet > '))
    # while materialLength != type(int):
    #     materialLength = int(input('\n| Please input your starting material length in feet > '))
    batchDir = dirBuilder(material, orderSize)
    findOrdersForPrintv3(batchDir, material, orderSize, (int(materialLength)))
    removeEmptyBatchFolders(True)
    # if orderSize == 'Full':
    #     findOrdersForPrintv3(BatchDir, material, orderSize, (int(materialLength)))
    #     removeEmptyBatchFolders(True)
    # else:
    #     findSampleOrdersForPrint(BatchDir, material, orderSize, (int(materialLength * 12)))
    print('\n| Finished Batching', material, orderSize, 'orders.')

def dirBuilder(material, orderSize):
    BatchDir = gv.batchFoldersDir + 'Batch #' + str(gv.globalBatchCounter['batchCounter']) + ' ' + today.strftime('%m-%d-%y') + ' ' + material + ' ' + orderSize + ' L0'
    gv.globalBatchCounter['batchCounter'] += 1
    #BatchDir = doesDirExist(material, orderSize)
    os.mkdir(BatchDir)
    print('| New Batch Folder: Batch #' + str(gv.globalBatchCounter['batchCounter']-1))
    print()
    return BatchDir

def findOrdersForPrintv3(batchDir, material, orderSize, materialLength):
    pdfMaterial = gv.dirLookupDict[material]
    pdfSize = gv.dirLookupDict[orderSize]
    
    listOfPdfsToBatch = {
        'OTOrders' : glob.iglob(gv.sortingDir + '1 - OT Orders/' + pdfMaterial + pdfSize + '**/*.pdf', recursive=True),
        'lateOrders' : glob.iglob(gv.sortingDir + '2 - Late/' + pdfMaterial + pdfSize + '**/*.pdf', recursive=True),
        'todayOrders' : glob.iglob(gv.sortingDir + '3 - Today/' + pdfMaterial + pdfSize + '**/*.pdf', recursive=True),
        'futureOrders' : glob.iglob(gv.sortingDir + '4 - Future/' + pdfMaterial + pdfSize + '**/*.pdf', recursive=True),
        }

    OTOrders = listOfPdfsToBatch['OTOrders']
    lateOrders = listOfPdfsToBatch['lateOrders']
    todayOrders = listOfPdfsToBatch['todayOrders']
    futureOrders = listOfPdfsToBatch['futureOrders']

    foldersToCheck2p = glob.glob(gv.sortingDir + '*/' + pdfMaterial + pdfSize + '**/*.pdf', recursive=True)
    curBatchDirLength = 0
    findOdd = False
    oddMatchHeight = 0
    loopCounter = 0
    while len(foldersToCheck2p) > 0:
        ### Come back to this later. For some reason, the folders to check variable doesn't update so python always evaluates it to more than 0 after it's initially created. I plugged in a loop counter to temporarily fix it.
        while (curBatchDirLength < (materialLength - (materialLength * 0.9))) and loopCounter < 1:
            for printPDF in OTOrders:
                curBatchDirLength, findOdd, oddMatchHeight = batchPdfCheck(printPDF, batchDir, curBatchDirLength, findOdd, oddMatchHeight, materialLength)
            for printPDF in lateOrders:
                curBatchDirLength, findOdd, oddMatchHeight = batchPdfCheck(printPDF, batchDir, curBatchDirLength, findOdd, oddMatchHeight, materialLength)
            for printPDF in todayOrders:
                curBatchDirLength, findOdd, oddMatchHeight = batchPdfCheck(printPDF, batchDir, curBatchDirLength, findOdd, oddMatchHeight, materialLength)
            for printPDF in futureOrders:
                curBatchDirLength, findOdd, oddMatchHeight = batchPdfCheck(printPDF, batchDir, curBatchDirLength, findOdd, oddMatchHeight, materialLength)
            loopCounter += 1
        else:
            newBatchName = batchDir.split('/')[6].split(' L')[0] + ' L' + str(curBatchDirLength)
            os.rename(batchDir, gv.batchFoldersDir + newBatchName)
            print('\n| Batch Finished.\n| Batch Folder: ', newBatchName, '\n| Length:', str(round(curBatchDirLength/12, 2)), 'feet (' + str(curBatchDirLength), 'inches)')
            curBatchDirLength = 0
            batchDir = dirBuilder(material, orderSize)
            #materialLength = input('| Please input your material length. > ')
            return findOrdersForPrintv3(batchDir, material, orderSize, int(materialLength))

def removeEmptyBatchFolders(safe):
    for BatchFolder in glob.iglob(gv.batchFoldersDir + '*'):
        BatchLength = float(BatchFolder.split('/')[-1].split(' ')[-1].split('L')[1])
        if safe == True:
            if os.path.isdir(BatchFolder) == False:
                continue
            elif (len(os.listdir(BatchFolder)) == 0) and (BatchLength == 0):
                os.rmdir(BatchFolder)
        else:
            if os.path.isdir(BatchFolder) == False:
                continue
            elif (len(os.listdir(BatchFolder)) == 0):
                os.rmdir(BatchFolder)

def batchPdfCheck(printPDF, batchDir, curBatchDirLength, findOdd, oddMatchHeight, materialLength):
    friendlyPdfName = getPdf.friendlyName(printPDF) 
    pdfLength = getPdf.length(printPDF)
    pdfOddOrEven = getPdf.oddOrEven(printPDF)
    pdfHeight = getPdf.height(printPDF)
    if (curBatchDirLength + pdfLength) > (materialLength * 1.02):
        print('| PDF will exceed material length.\n| PDF:', friendlyPdfName)
        print()
        return curBatchDirLength, findOdd, oddMatchHeight
    else:
        if (findOdd == False) and (pdfOddOrEven == 0):
            success = tryToMovePDF(printPDF, batchDir, friendlyPdfName)
            if success == True:
                checkRepeatDuringBatching(batchDir + '/' + printPDF.split('/')[-1], batchDir)
                curBatchDirLength += pdfLength
                findOdd = False
                oddMatchHeight = 0
                return curBatchDirLength, findOdd, oddMatchHeight
        elif (findOdd == False) and (pdfOddOrEven == 1):
            success = tryToMovePDF(printPDF, batchDir, friendlyPdfName)
            if success == True:
                checkRepeatDuringBatching(batchDir + '/' + printPDF.split('/')[-1], batchDir)
                curBatchDirLength += pdfLength
                findOdd = True
                oddMatchHeight = pdfHeight
                return curBatchDirLength, findOdd, oddMatchHeight
        elif (findOdd == True) and (pdfOddOrEven == 0):
            return curBatchDirLength, findOdd, oddMatchHeight
        elif (findOdd == True) and (pdfOddOrEven == 1):
            if oddMatchHeight != pdfHeight:
                return curBatchDirLength, findOdd, oddMatchHeight
            else:
                success = tryToMovePDF(printPDF, batchDir, friendlyPdfName)
                if success == True:
                    checkRepeatDuringBatching(batchDir + '/' + printPDF.split('/')[-1], batchDir)
                    curBatchDirLength += pdfLength
                    findOdd = False
                    oddMatchHeight = 0
                    return curBatchDirLength, findOdd, oddMatchHeight
    return curBatchDirLength, findOdd, oddMatchHeight

def tryToMovePDF(printPDF, BatchDir, friendlyPdfName):
    try:
        shutil.move(printPDF, BatchDir + '/')
        return True
    except shutil.Error:
        shutil.copy(printPDF, BatchDir)
        try:
            os.remove(printPDF)
            return True
        except OSError:
            print('|> Moved PDF to batch folder, but couldn\'t remove the original file. Please remove the original file.')
            print('|> PDF:', friendlyPdfName)
            print('|> Path:', printPDF)
            return False
    except FileNotFoundError:
        print('|> Couldn\'t move PDF. Please check to make sure it exists.')
        print('|> PDF:', friendlyPdfName)
        print('|> Path:', printPDF)
        return False

def checkRepeatDuringBatching(pdf, batchDir):
    printPDFFull = pdf.split('/')[-1].split('-')[7]
    printPDFrepeat = int(pdf.split('/')[-1].split('-')[8].split('Rp ')[1])
    if printPDFFull == 'Full':
        if printPDFrepeat % 2 == 1:
            try:
                shutil.move(pdf, gv.needsAttention)
                print('| File has an odd repeat and has been moved to 4 Needs Attention')
                print('| File:', pdf.split('/')[-1])
            except shutil.Error:
                shutil.copy(pdf, gv.needsAttention)
                try:
                    os.remove(pdf)
                except OSError:
                    print('|> Could not successfully remove file.')
                    print('|> File:', pdf)
                    return
            except FileNotFoundError:
                print('| Couldn\'t find the following file.')
                print('| File:', pdf)
                return
        elif printPDFrepeat == 2:
            return
        elif printPDFrepeat > 2:
            try:
                cropMultiPanelPDFs(pdf, batchDir)
            except utils.PdfReadError:
                print('| Couldn\'t crop the panels for the following pdf. Please check the batch folder')
                print('| PDF:', pdf.split('/')[-1])
                return

def cropMultiPanelPDFs(printPDFToSplit, batchDir):
    orderDict = {
        'fileName':printPDFToSplit.split('.pdf')[0],
        'orderNumber': getPdf.orderNumber(printPDFToSplit),
        'orderItem': getPdf.orderItem(printPDFToSplit),
        'orderDueDate': getPdf.dueDate(printPDFToSplit),
        'shipVia': getPdf.shipMethod(printPDFToSplit),
        'material': getPdf.material(printPDFToSplit),
        'orderSize': getPdf.size(printPDFToSplit),
        'repeat': getPdf.repeat(printPDFToSplit),
        'repeatPanels': int(getPdf.repeat(printPDFToSplit) / 2),
        'quantity': getPdf.quantity(printPDFToSplit),
        'oddOrEven': getPdf.oddOrEven(printPDFToSplit),
        'templateName': getPdf.templateName(printPDFToSplit),
        'orderLength': getPdf.length(printPDFToSplit),
        'orderWidth': getPdf.width(printPDFToSplit),
        'orderHeight': getPdf.height(printPDFToSplit),
        'multiPagePDFs' : [],
        'PDFPanelsToCombine' : [],
        }
    
    orderDict['CroppedPDFName'] = orderDict['fileName'].split(orderDict['templateName'])[0] + orderDict['templateName'] + ' Split' + orderDict['fileName'].split(orderDict['templateName'])[1] + '.pdf'

    #print('| Working file\n| ', printPDFToSplit)
    #for entry in orderDict:
    #    print('|    ', orderDict[entry])

    os.chdir(batchDir)
    for page in range(orderDict['repeatPanels']):
        writer = PdfFileWriter()
        inputPDF = open(printPDFToSplit,'rb')
        cropPDF = PdfFileReader(inputPDF)
        page = cropPDF.getPage(0)
        lowerLeftX = 0
        lowerLeftY = 0
        upperRightX = 1800
        upperRightY = cropPDF.getPage(0).cropBox.getUpperRight()[1]
        for cropCount in range(orderDict['repeatPanels']):
            page.trimBox.lowerLeft = (lowerLeftX, lowerLeftY)
            page.trimBox.upperRight = (upperRightX, upperRightY)
            page.bleedBox.lowerLeft = (lowerLeftX, lowerLeftY)
            page.bleedBox.upperRight = (upperRightX, upperRightY)
            page.cropBox.lowerLeft = (lowerLeftX, lowerLeftY)
            page.cropBox.upperRight = (upperRightX, upperRightY)
            writer.addPage(page)
            lowerLeftX += 1728
            upperRightX += 1728
            printPDFName = batchDir + '/' + orderDict['orderNumber'] + '-' + orderDict['orderItem'] + '-' + str(cropCount + 1) + '.pdf'
            if printPDFName in orderDict['multiPagePDFs']:
                continue
            else:
                orderDict['multiPagePDFs'].append(printPDFName)
            with open(printPDFName, "wb") as outputPDF:
                writer.write(outputPDF)
        inputPDF.close()

    for PDF in orderDict['multiPagePDFs']:
        writer = PdfFileWriter()
        try:
            printPDF = PdfFileReader(open(PDF, "rb"))
        except utils.PdfReadError:
            print('| Couldn\'t fix file. Skipping.\n| File:', PDF)
            continue
        numOfPages = printPDF.getNumPages()

        for pageNum in range(numOfPages):
            if (pageNum + 1) < numOfPages:
                continue
            else:
                writer.addPage(printPDF.getPage(pageNum))
        newNamePt1 = orderDict['fileName'].split(orderDict['templateName'])[0]
        newNamePt2 = orderDict['fileName'].split(orderDict['templateName'])[1]
        panelNum = orderDict['templateName'] + ' Panel ' + str(pageNum + 1)
        newName = newNamePt1 + panelNum + newNamePt2 + '.pdf'
        if newName in orderDict['PDFPanelsToCombine']:
            continue
        else:
            orderDict['PDFPanelsToCombine'].append(newName)

        with open(newName, 'wb') as outputPDF:
            writer.write(outputPDF)
    
    splitAndCombinedPDF = combineSplitPDFS(orderDict['PDFPanelsToCombine'], orderDict['CroppedPDFName'])

    for PDF in orderDict['multiPagePDFs']:
        os.remove(PDF)
    for PDF in orderDict['PDFPanelsToCombine']:
        os.remove(PDF)

    print('| File has been split apart, cropped, and recombined.\n| File:', splitAndCombinedPDF.split('/')[-1])

    if Path(gv.calderaDir + '# Past Orders/Original Files/').exists() == False:
        os.mkdir(gv.calderaDir + '# Past Orders/Original Files')
    
    storageDir = gv.calderaDir + '# Past Orders/Original Files/'
    
    try:
        shutil.move(printPDFToSplit, storageDir)
    except shutil.Error:
        shutil.copy(printPDFToSplit, storageDir)
        os.remove(printPDFToSplit)

def combineSplitPDFS(listOfPDFs, saveLocation):
    masterPDF = PdfFileMerger()

    templateName = getPdf.templateName(saveLocation)
    nameWithoutSplit = saveLocation.split(templateName)[0] + templateName.split(' Split')[0] + saveLocation.split(templateName)[1]
    saveLocation = nameWithoutSplit

    for PDFToMerge in listOfPDFs:
        masterPDF.append(PdfFileReader(PDFToMerge, 'rb'))
    masterPDF.write(saveLocation)

    return saveLocation

def decompress_pdf(temp_buffer):
    temp_buffer.seek(0)  # Make sure we're at the start of the file.

    process = subprocess.Popen(['pdftk.exe',
                                '-',  # Read from stdin.
                                'output',
                                '-',  # Write to stdout.
                                'uncompress'],
                                stdin=temp_buffer,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

    return StringIO(stdout)

    