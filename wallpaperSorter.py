#!usr/bin/env python

import zipfile as zf
import getPdfData as getPdf
import batchCreation as batch
import batchController as batchCtrl 
import wallpaperSorterVariables as gv
import os, shutil, math, datetime, time, json, glob, pikepdf

from pathlib import Path
from datetime import date, timedelta, datetime
from add_macos_tag import apply_tag as applyTag

today = date.today()
### Definitions

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
        sortPDFsByDetails()
        buildDBSadNoises()
        return main()
    elif command == 2:
        transferFilesFromDrive()
        return main()
    elif command == 3:
        if os.path.expanduser('~').split('/')[-1] == 'Trevor':
            batchCtrl.buildABatch()
        else:
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

def startupChecks():
    checkOrderDirectoryStructure()
    checkBatchCounter()
    moveForDueDates()

def checkBatchCounter():
    if gv.globalBatchCounter['batchCounter'] > 9000:
        gv.globalBatchCounter['batchCounter'] = 1

def buildSortedDirStructure(parentFolder):
    os.mkdir(parentFolder + 'Smooth/')
    os.mkdir(parentFolder + 'Smooth/Sample')
    os.mkdir(parentFolder + 'Smooth/Full/')
    os.mkdir(parentFolder + 'Smooth/Full/Repeat 2/')
    os.mkdir(parentFolder + 'Smooth/Full/Repeat 2/Even Panels/')
    os.mkdir(parentFolder + 'Smooth/Full/Repeat 2/Odd Panels/')
    os.mkdir(parentFolder + 'Smooth/Full/Repeat Non-2/')
    os.mkdir(parentFolder + 'Smooth/Full/Repeat Non-2/Even Panels/')
    os.mkdir(parentFolder + 'Smooth/Full/Repeat Non-2/Odd Panels/')
    os.mkdir(parentFolder + 'Woven/')
    os.mkdir(parentFolder + 'Woven/Sample')
    os.mkdir(parentFolder + 'Woven/Full/')
    os.mkdir(parentFolder + 'Woven/Full/Repeat 2/')
    os.mkdir(parentFolder + 'Woven/Full/Repeat 2/Even Panels/')
    os.mkdir(parentFolder + 'Woven/Full/Repeat 2/Odd Panels/')
    os.mkdir(parentFolder + 'Woven/Full/Repeat Non-2/')
    os.mkdir(parentFolder + 'Woven/Full/Repeat Non-2/Even Panels/')
    os.mkdir(parentFolder + 'Woven/Full/Repeat Non-2/Odd Panels/')
    return

def checkOrderDirectoryStructure():
    if Path(gv.calderaDir + '# Past Orders/Original Files/').exists() == False:
        try:
            os.mkdir(gv.calderaDir + '# Past Orders/Original Files')
        except:
            pass
    if Path(gv.sortingDir + '1 - Late and OT/').exists() == True:
        try:
            os.mkdir(gv.sortingDir + '1 - OT Orders/')
        except:
            pass
        buildSortedDirStructure(gv.sortingDir + '1 - OT Orders/')
        try:
            os.mkdir(gv.sortingDir + '2 - Late/')
        except:
            pass
        buildSortedDirStructure(gv.sortingDir + '2 - Late/')
    if Path(gv.sortingDir + '2 - Today/').exists() == True:
        try:
            os.mkdir(gv.sortingDir + '3 - Today/')
        except:
            pass
        buildSortedDirStructure(gv.sortingDir + '3 - Today/')
    if Path(gv.sortingDir + '3 - Future/').exists() == True:
        try:
            os.mkdir(gv.sortingDir + '4 - Future/')
        except:
            pass
        buildSortedDirStructure(gv.sortingDir + '4 - Future/')
    return

def moveForDueDates():
    print('\n| Updating Orders. Today\'s date:', today)
    for file in glob.iglob(gv.sortingDir + '**/*.pdf', recursive=True):
        friendlyName = getPdf.friendlyName(file)
        orderDueDate = getPdf.dueDate(file) 
        material = getPdf.material(file)
        orderSize = getPdf.size(file)
        repeat = getPdf.repeat(file)
        oddOrEven = getPdf.oddOrEven(file)   
        orderLength = getPdf.length(file)
        if orderDueDate < today:
            orderDueDate = '2 - Late/'
        elif orderDueDate > today:
            orderDueDate = '4 - Future/'
        else:
            orderDueDate = '3 - Today/'
        # Checks if order is over the maximum length of a roll and moves it to Needs Attention
        if material == 'Wv':
            if orderLength >= gv.dirLookupDict['MaterialLength']['Woven']:
                try:
                    shutil.copy(file, gv.needsAttention)
                    try:
                        os.remove(file)
                        continue
                    except:
                        print('|> Could not remove ', file)
                except OSError as err:
                    print(err)
        elif material == 'Sm':
            if orderLength >= gv.dirLookupDict['MaterialLength']['Smooth']:
                try:
                    shutil.copy(file, gv.needsAttention)
                    try:
                        os.remove(file)
                        continue
                    except:
                        print('|> Could not remove ', file)
                except OSError as err:
                    print(err)
        if orderSize == 'Samp':
            try:
                shutil.move(file, gv.sortingDir + orderDueDate + gv.dirLookupDict[material] + 'Sample/')
                print('| Updated:', friendlyName)
            except:
                try:
                    shutil.copy(file, gv.sortingDir + orderDueDate + gv.dirLookupDict[material] + 'Sample/')
                    os.remove(file)
                    print('| Updated:', friendlyName)
                except shutil.SameFileError:
                    continue
        else:
            try:
                shutil.move(file, gv.sortingDir + orderDueDate + gv.dirLookupDict[material] + 'Full/' + gv.dirLookupDict['RepeatDict'][repeat] + gv.dirLookupDict[oddOrEven])
                print('| Updated:', friendlyName)
            except:
                try:
                    shutil.copy(file, gv.sortingDir + orderDueDate + gv.dirLookupDict[material] + 'Full/' + gv.dirLookupDict['RepeatDict'][repeat] + gv.dirLookupDict[oddOrEven])
                    os.remove(file)
                    print('| Updated:', friendlyName)
                except shutil.SameFileError:
                    continue
    print('| Done updating orders based on Due Dates.')
    
    gv.needsAttentionDir = len(glob.glob(gv.needsAttention + '*.pdf'))
    if gv.needsAttentionDir > 0:
        print(f'\n| ****\n| 4 Needs Attention has {gv.needsAttentionDir} file(s) that need attention.\n| ****\n')  

def findJSONs(): #iterates over a given folder, unzips files, finds JSON files, and calls parseJSONDerulo
    os.chdir(gv.downloadDir)
    for roots, dirs, files in os.walk(gv.downloadDir):
        for file in files:
            ext = os.path.splitext(file)[-1].lower()
            if ext == '.zip':
                try:
                    with zf.ZipFile(file, 'r') as zip_ref:
                        zip_ref.extractall(gv.downloadDir)
                    os.remove(file)
                except:
                    print('Couldn\'t unzip file:', file)
    for roots, dirs, files in os.walk(gv.downloadDir):
        for file in files:
            ext = os.path.splitext(file)[-1].lower()
            if file.startswith('.'): #skips macOS X Hidden file '.DS_Store'
                continue
            elif ext == '.xml':
                try:
                    os.remove(file)
                except OSError:
                    print('| Could not remove ' + file)
            else:
                if ext == '.json':
                    with open(file) as file:
                        JSONDerulo = json.load(file)
                    parseJSONDerulo(JSONDerulo)
    for roots, dirs, files in os.walk(gv.downloadDir):
        for file in files:
            ext = os.path.splitext(file)[-1].lower()
            if ext == '.json':
                try:
                    os.remove(file)
                except OSError:
                    print('| Could not remove ' + file)
            else:
                try:
                    if (file.split('_')[-2] == 'bi') or (file.split('_')[-3] == 'lvd'):
                        os.remove(file)
                except IndexError:
                    continue

def parseJSONDerulo(JSON): #reads through an JSON file, finds the appropriate information for related PDFs, and renames files
    count = 1
    JSONitem = JSON['order']['item']
    orderNumber = JSON['orderNumber']
    keepTrackOfOrderNumber(orderNumber)
    orderDueDate = JSON['orderDueDate']
    shipVia = gv.shippingMethods[JSON['shippingInfo']['method']['shipvia']]
    try:
        for itemNum in range(len(JSONitem)):
            originalPDFName = JSONitem[itemNum]['filename']
            itemID = originalPDFName.split('_')[0]
            try:
                templateName = JSONitem[itemNum]['description'].split(' ')[2] + ' ' + JSONitem[itemNum]['description'].split(' ')[3]
            except IndexError:
                templateName = JSONitem[itemNum]['description'].split(' Wallpaper')[0]
            paperType = gv.substrate[JSONitem[itemNum]['paper']]
            quantity = JSONitem[itemNum]['quantityOrdered']
            height = JSONitem[itemNum]['height'] 
            width = JSONitem[itemNum]['width']
            repeat = JSONitem[itemNum]['wallpaperRepeat']
            orderTroubleNotes = JSON['order_trouble_notes']
            if width == '9':
                orderSize = 'Samp'
                length = '9.5'
                height = '9'
                width = '25'
            else:
                width = str(int(width) * int(quantity) + 1)
                height = str(int(height) + 4.25)
                if height == '148.25':
                    height = '146.25'
                orderSize = 'Full'
                length = str(getPdf.calculateLength(quantity, height))
                # See Length Notes at the end of the function for an explanation.
            newPDFName = orderNumber + '-' + str(count) + '-(' + orderDueDate + ')-' + shipVia + '-' + paperType + '-' + orderSize + '-Rp ' + repeat.split("'")[0] + '-Qty ' + quantity + '-' + templateName + '-L' + length + '-W' + width + '-H' + height
            renamePDF(originalPDFName, newPDFName)
            keepTrackOfPDF(orderNumber, originalPDFName) 
            count += 1
            if orderNumber in gv.orderItemsDict:
                gv.orderItemsDict[orderNumber][itemID] = {
                    'Status': 'Sorted',
                    'Due Date': orderDueDate,
                    'Shipping': shipVia,
                    'Material': paperType,
                    'Order Size': orderSize,
                    'Repeat': repeat.split('\'')[0],
                    'Quantity': quantity,
                    'Template': templateName,
                    'Length': length,
                    'Width': width,
                    'Height': height,
                    'OT Notes': orderTroubleNotes,
                    'File Path': gv.sortingDir + '2 - Late/' + gv.dirLookupDict[paperType] + gv.dirLookupDict[orderSize] + gv.dirLookupDict['RepeatDict'][int(repeat.split('\'')[0])] + gv.dirLookupDict[int(quantity) % 2] + newPDFName,
                }
            else:
                gv.orderItemsDict[orderNumber] = {
                    itemID : {
                        'Status': 'Sorted',
                        'Due Date': orderDueDate,
                        'Shipping': shipVia,
                        'Material': paperType,
                        'Order Size': orderSize,
                        'Repeat': repeat.split('\'')[0],
                        'Quantity': quantity,
                        'Template': templateName,
                        'Length': length,
                        'Width': width,
                        'Height': height,
                        'OT Notes': orderTroubleNotes,
                        'File Path': gv.sortingDir + '2 - Late/' + gv.dirLookupDict[paperType] + gv.dirLookupDict[orderSize] + gv.dirLookupDict['RepeatDict'][int(repeat.split('\'')[0])] + gv.dirLookupDict[int(quantity) % 2] + newPDFName,
                    }
                }
                    
    except KeyError:
        originalPDFName = JSONitem['filename']
        itemID = originalPDFName.split('_')[0]
        templateName = JSONitem['description'].split(' Wallpaper')[0]
        paperType = gv.substrate[JSONitem['paper']]
        quantity = JSONitem['quantityOrdered']
        height = JSONitem['height']
        width = JSONitem['width']
        repeat = JSONitem['wallpaperRepeat']
        orderTroubleNotes = JSON['order_trouble_notes']
        if width == '9':
            orderSize = 'Samp'
            length = '9.5'
            height = '9'
            width = '25'
        else:
            width = str(int(width) * int(quantity) + 1)
            height = str(int(height) + 4.25)
            if height == '148.25':
                height = '146.25'
            orderSize = 'Full'
            length = str(getPdf.calculateLength(quantity, height))

        newPDFName = orderNumber + '-' + str(count) + '-(' + orderDueDate + ')-' + shipVia + '-' + paperType + '-' + orderSize + '-Rp ' + repeat.split("'")[0] + '-Qty ' + quantity + '-' + templateName + '-L' + length + '-W' + width + '-H' + height
        renamePDF(originalPDFName, newPDFName)
        keepTrackOfPDF(orderNumber, originalPDFName) 
        count += 1
        if orderNumber in gv.orderItemsDict:
                gv.orderItemsDict[orderNumber][itemID] = {
                    'Status': 'Sorted',
                    'Due Date': orderDueDate,
                    'Shipping': shipVia,
                    'Material': paperType,
                    'Order Size': orderSize,
                    'Repeat': repeat.split('\'')[0],
                    'Quantity': quantity,
                    'Template': templateName,
                    'Length': length,
                    'Width': width,
                    'Height': height,
                    'OT Notes': orderTroubleNotes,
                    'File Path': gv.sortingDir + '2 - Late/' + gv.dirLookupDict[paperType] + gv.dirLookupDict[orderSize] + gv.dirLookupDict['RepeatDict'][int(repeat.split('\'')[0])] + gv.dirLookupDict[int(quantity) % 2] + newPDFName,
                }
        else:
            gv.orderItemsDict[orderNumber] = {
                itemID : {
                    'Status': 'Sorted',
                    'Due Date': orderDueDate,
                    'Shipping': shipVia,
                    'Material': paperType,
                    'Order Size': orderSize,
                    'Repeat': repeat.split('\'')[0],
                    'Quantity': quantity,
                    'Template': templateName,
                    'Length': length,
                    'Width': width,
                    'Height': height,
                    'OT Notes': orderTroubleNotes,
                    'File Path': gv.sortingDir + '2 - Late/' + gv.dirLookupDict[paperType] + gv.dirLookupDict[orderSize] + gv.dirLookupDict['RepeatDict'][int(repeat.split('\'')[0])] + gv.dirLookupDict[int(quantity) % 2] + newPDFName,
                }
            }
    
    ''' # Length Notes: I will never remember why I did this, so here are my notes. The length is the length of material an order will take up.
        # Length Notes: The above equation takes the quantity and divides it by two since we can fit two panels side by side.
        # Length Notes: it then multiplies that by the height to get the overall length of material.
        # Length Notes: after, it takes the quantity/2, rounds it down, and multiplies it by .5 for the .5" gap between each panel.
        # Length Notes: lastly, it takes the quantity % 2 to see if the quantity is odd or not. If the quantity is odd, then it will add on one more length of .5"
        # Length Notes: for the times that a panel is by itself and still has another .5" section.'''

def parseJsonLoop(JSON, JSONitem, orderNumber, itemNum, orderDueDate, shipVia):
    originalPDFName = JSONitem[itemNum]['filename']
    itemID = originalPDFName.split('_')[0]
    try:
        templateName = JSONitem[itemNum]['description'].split(' ')[2] + ' ' + JSONitem[itemNum]['description'].split(' ')[3]
    except IndexError:
        templateName = JSONitem[itemNum]['description'].split(' Wallpaper')[0]
    paperType = gv.substrate[JSONitem[itemNum]['paper']]
    quantity = JSONitem[itemNum]['quantityOrdered']
    height = JSONitem[itemNum]['height'] 
    width = JSONitem[itemNum]['width']
    repeat = JSONitem[itemNum]['wallpaperRepeat']
    orderTroubleNotes = JSON['order_trouble_notes']
    if width == '9':
        orderSize = 'Samp'
        length = '9.5'
        height = '9'
        width = '25'
    else:
        width = str(int(width) * int(quantity) + 1)
        height = str(int(height) + 4.25)
        if height == '148.25':
            height = '146.25'
        orderSize = 'Full'
        length = getPdf.calculateLength(quantity, height)
        # See Length Notes at the end of the function for an explanation.
    newPDFName = orderNumber + '-' + str(count) + '-(' + orderDueDate + ')-' + shipVia + '-' + paperType + '-' + orderSize + '-Rp ' + repeat.split("'")[0] + '-Qty ' + quantity + '-' + templateName + '-L' + length + '-W' + width + '-H' + height
    renamePDF(originalPDFName, newPDFName)
    keepTrackOfPDF(orderNumber, originalPDFName) 
    count += 1
    if orderNumber in gv.orderItemsDict:
        gv.orderItemsDict[orderNumber][itemID] = {
            'Status': 'Sorted',
            'Due Date': orderDueDate,
            'Shipping': shipVia,
            'Material': paperType,
            'Order Size': orderSize,
            'Repeat': repeat.split('\'')[0],
            'Quantity': quantity,
            'Template': templateName,
            'Length': length,
            'Width': width,
            'Height': height,
            'OT Notes': orderTroubleNotes,
            'File Path': gv.sortingDir + '2 - Late/' + gv.dirLookupDict[paperType] + gv.dirLookupDict[orderSize] + gv.dirLookupDict['RepeatDict'][int(repeat.split('\'')[0])] + gv.dirLookupDict[int(quantity) % 2] + newPDFName,
        }
    else:
        gv.orderItemsDict[orderNumber] = {
            itemID : {
                'Status': 'Sorted',
                'Due Date': orderDueDate,
                'Shipping': shipVia,
                'Material': paperType,
                'Order Size': orderSize,
                'Repeat': repeat.split('\'')[0],
                'Quantity': quantity,
                'Template': templateName,
                'Length': length,
                'Width': width,
                'Height': height,
                'OT Notes': orderTroubleNotes,
                'File Path': gv.sortingDir + '2 - Late/' + gv.dirLookupDict[paperType] + gv.dirLookupDict[orderSize] + gv.dirLookupDict['RepeatDict'][int(repeat.split('\'')[0])] + gv.dirLookupDict[int(quantity) % 2] + newPDFName,
            }
        }
    
    str((math.ceil(int(quantity)/2)*float(height) + ((math.floor(int(quantity)/2) * .5) + ((int(quantity) % 2) * .5))))

def renamePDF(old, new):
    extension = old.split(".")[-1]
    itemName = new + "." + extension
    try:
        shutil.copy(old, old + ' - temp')
        os.rename(old, itemName)
        os.rename(old + ' - temp', old)
    except OSError:
        print("\n| Error Renaming. PDF may not exist in package." + "\n| Original File Name: " + old + "\n| New Item Name: " + itemName + "\n| *** Please check order", itemName.split("-")[0],"***")

def keepTrackOfOrderNumber(orderNumber): #keeps track of the original PDF names to alert fulfillment to multi-paper type PDFs
    if orderNumber in gv.countOfRefPdfs:
        pass
    else:
        gv.countOfRefPdfs[orderNumber] = {}

def keepTrackOfPDF(orderNumber, pdfFileName):
    if pdfFileName in gv.countOfRefPdfs[orderNumber]:
        gv.countOfRefPdfs[orderNumber][pdfFileName] += 1
    else:
        gv.countOfRefPdfs[orderNumber][pdfFileName] = 1

def reportDuplicatePDFs(): #prints out any PDFs from keepTrackOfOrderNumber() that have a count of 2 or more
    for orderNumber in gv.countOfRefPdfs:
        for pdfName in gv.countOfRefPdfs[orderNumber]:
            if gv.countOfRefPdfs[orderNumber][pdfName] > 1:
                print('\n| The following Order has samples with multiple material types:')
                print('| ' + orderNumber + ': ' + pdfName.replace('_',' '))

def splitMultiPagePDFs():
    for file in glob.iglob(gv.downloadDir + '*.pdf'):
        try:
            pdf = pikepdf.Pdf.open(file)
            NumOfPages = len(pdf.pages)
        except:
            print(f'\n| Couldn\'t check the number of pages on {file}')
            pass
        NumOfPages = len(pdf.pages)
        if NumOfPages > 1:
                print(f'\n| {file} has more than one page in its PDF. Splitting now.')
                templateName = getPdf.templateName(file)
                namePt1 = file.split('Qty ')[0] + 'Qty '
                namePt2 = file.split(templateName)[1]
                repeat = getPdf.repeat(file) ##
                quantity = getPdf.quantity(file)
                for n, page in enumerate(pdf.pages):
                    dst = pikepdf.Pdf.new()
                    dst.pages.append(page)
                    dst.save(namePt1 + str(quantity) + '-' + templateName + ' Panel ' + str(n + 1) + namePt2)
                try:
                    os.remove(file)
                    print(f'\n| Finished splitting {file}')
                except:
                    print(f'\n| Split the pages of {file},\nbut couldn\'t remove the original.')

def sortPDFsByDetails():
    print('\n| Starting Sort Process. This may take a long time.')
    for file in glob.iglob(gv.downloadDir + '*.pdf'):
        dueDate = getPdf.dueDate(file)
        material = getPdf.material(file)
        orderSize = getPdf.size(file)
        repeat = getPdf.repeat(file)
        oddOrEven = getPdf.oddOrEven(file)
        orderLength = getPdf.length(file)
        # Checks if order is over the maximum length of a roll and moves it to Needs Attention
        if material == 'Wv':
            if orderLength >= gv.dirLookupDict['MaterialLength']['Woven']:
                try:
                    shutil.copy(file, gv.needsAttention)
                    try:
                        os.remove(file)
                        continue
                    except:
                        print('|> Could not remove ', file)
                except OSError as err:
                            print(err)
        elif material == 'Sm':
            if orderLength >= gv.dirLookupDict['MaterialLength']['Smooth']:
                try:
                    shutil.copy(file, gv.needsAttention)
                    try:
                        os.remove(file)
                        continue
                    except:
                        print('|> Could not remove ', file)
                except OSError as err:
                    print(err)
        # Sorts based on normal parameters.            
        if orderSize == 'Samp':
            if dueDate < date.today():
                try:
                    shutil.copy(file, gv.sortingDir + '2 - Late/' + gv.dirLookupDict[material] +gv.dirLookupDict[orderSize])
                    try:
                        os.remove(file)
                    except:
                        print('|> Could not remove ', file)
                except OSError as err:
                    print(err)
            elif dueDate > date.today():
                try:
                    shutil.copy(file, gv.sortingDir + '4 - Future/' + gv.dirLookupDict[material] + gv.dirLookupDict[orderSize])
                    try:
                        os.remove(file)
                    except:
                        print('|> Could not remove ', file)
                except OSError as err:
                    print(err)
            else:
                try:
                    shutil.copy(file, gv.sortingDir + '3 - Today/' + gv.dirLookupDict[material] + gv.dirLookupDict[orderSize])
                    try:
                        os.remove(file)
                    except:
                        print('|> Could not remove ', file)
                except OSError as err:
                    print(err)
        else:
            if dueDate < date.today():
                try:
                    shutil.copy(file, gv.sortingDir + '2 - Late/' + gv.dirLookupDict[material] +gv.dirLookupDict[orderSize] + gv.dirLookupDict['RepeatDict'][repeat] + gv.dirLookupDict[oddOrEven])
                    try:
                        os.remove(file)
                    except:
                        print('|> Could not remove ', file)
                except OSError as err:
                    print(err)
            elif dueDate > date.today():
                try:
                    shutil.copy(file, gv.sortingDir + '4 - Future/' + gv.dirLookupDict[material] + gv.dirLookupDict[orderSize] + gv.dirLookupDict['RepeatDict'][repeat] + gv.dirLookupDict[oddOrEven])
                    try:
                        os.remove(file)
                    except:
                        print('|> Could not remove ', file)
                except OSError as err:
                    print(err)
            else:
                try:
                    shutil.copy(file, gv.sortingDir + '3 - Today/' + gv.dirLookupDict[material] + gv.dirLookupDict[orderSize] + gv.dirLookupDict['RepeatDict'][repeat] + gv.dirLookupDict[oddOrEven])
                    try:
                        os.remove(file)
                    except:
                        print('|> Could not remove ', file)
                except OSError as err:
                    print(err)
    
    print('| Finished sorting files.')
    gv.needsAttentionDir = len(glob.glob(gv.needsAttention + '*.pdf'))
    if gv.needsAttentionDir > 0:
        print(f'\n| ****\n| 4 Needs Attention has {gv.needsAttentionDir} file(s) that need attention.\n| ****\n')

def buildDBSadNoises():
    print('| Building DB. Please hold.')
    fullOrdersDirectory = gv.sortingDir + '**/Full/*.pdf' 
    #300014839-2-(2022-02-15)-Stnd-Sm-Samp-Rp 2-Qty 1-Mod Herons-L9.5-W25-H9
    # buildDBSadNoises()
    # print('| Printing Current Order Database.')
    # for order in gv.orderItemsDict:
    #    print(f'|-{order}')
    #    for orderItemID in gv.orderItemsDict[order]:
    #        if gv.orderItemsDict[order][orderItemID]['Order Size'] == 'Full':
    #            print(f'|  -- {orderItemID}')
    #            print('|    --', gv.orderItemsDict[order][orderItemID]['Status'])
    #            print('|    --', gv.orderItemsDict[order][orderItemID]['Order Size'])
    #            print('|    --', gv.orderItemsDict[order][orderItemID]['Length'])
    #            print('|    --', gv.orderItemsDict[order][orderItemID]['Repeat'])
    for printPDF in glob.iglob(gv.sortingDir + '**/*.pdf', recursive=True):
        orderItemID = 1
        fileName = printPDF.split('/')[-1].split('.pdf')[0]
        orderNumber = fileName.split('-')[0]
        orderDueDate = datetime.date(datetime.strptime(fileName.split('(')[1].split(')')[0], '%Y-%m-%d'))
        shipVia = fileName.split('-')[5]
        material = fileName.split('-')[6]
        orderSize = fileName.split('-')[7]
        repeat = int(fileName.split('-')[8].split(' ')[1])
        quantity = int(fileName.split('-')[9].split(' ')[1])
        oddOrEven = quantity % 2
        templateName = fileName.split('-')[10]
        orderLength = float(fileName.split('-')[11].split('L')[1])
        orderWidth = int(fileName.split('-')[12].split('W')[1])
        orderHeight = float(fileName.split('-')[13].split('H')[1])
        if orderNumber[orderItemID] in gv.orderItemsDict:
            gv.orderItemsDict[orderNumber][orderItemID] = {
                'Status': 'Sorted',
                'Due Date': orderDueDate,
                'Shipping': shipVia,
                'Material': material,
                'Order Size': orderSize,
                'Repeat': repeat,
                'Quantity': quantity,
                'Odd': oddOrEven,
                'Template': templateName,
                'Length': orderLength,
                'Width': orderWidth,
                'Height': orderHeight,
                'File Path': fileName
            }
        else:
            gv.orderItemsDict[orderNumber] = {
                orderItemID : {
                    'Status': 'Sorted',
                    'Due Date': orderDueDate,
                    'Shipping': shipVia,
                    'Material': material,
                    'Order Size': orderSize,
                    'Repeat': repeat,
                    'Quantity': quantity,
                    'Template': templateName,
                    'Length': orderLength,
                    'Width': orderWidth,
                    'Height': orderHeight,
                    'File Path': fileName
                }
            }
    print('| DB Built.')

def removeOldOrders(folderToClean, days): #removes folders and contents older than X days
    olderThanDays = days
    for subFolder in folderToClean.values(): #gets subfolder path
        for parentFolder, folder, file in os.walk(subFolder[1] + '/'): #
            folderName = os.path.basename(parentFolder) #extracts just the folder name from the folder path
            oldestDate = date.today() - timedelta(days=olderThanDays) #makes a variable to compare the date against
            try:
                if datetime.date(datetime.strptime(folderName, '%Y-%m-%d')) < oldestDate: #compares the date of the folder name against the oldest date
                   print('| ' + folderName + ' is older than ' + str(olderThanDays) + ' days. Thanos snapped it.') #Lets the user know an old directory and its contents has been deleted
                   shutil.rmtree(parentFolder) #removes folder
                else:
                    continue
            except ValueError:
                continue

def transferFilesFromDrive():
    # Old name convention: 300014719(1)-Watercolor Herringbone-Wv-Samp-Rp 4-Qty 1-W9-H25
    # New name convention: 300013884-1-(2022-02-02)-Stnd-Wv-Samp-Rp 2-Qty 1-Watercolor Herringbone-L9.5-W25-H9
    print('\n| Checking for files in Google Drive.')
    for roots, dirs, files in os.walk(gv.driveLocation):
        ('\n| Renaming files in Google Drive to the new naming convention.')
        for file in files:
            if file.startswith('.'): #skips macOS Hidden file '.DS_Store'
                continue
            elif file.endswith('.pdf') != True:
                continue
            else:
                try:
                    pdfDict = {
                        'orderNumber': file.split('(')[0],
                        'orderItem': file.split('(')[1].split(')')[0],
                        'templateName': file.split('-')[1],
                        'material': file.split('-')[2],
                        'orderSize': file.split('-')[3],
                        'orderRepeat': file.split('-')[4],
                        'orderQuantity': file.split('-')[5].split('Qty ')[1],
                        'orderWidth': file.split('-')[6],
                        'orderHeight': file.split('-')[7].split('.pdf')[0],
                    }
                    pdfDict['orderLength'] = str((math.ceil(int(pdfDict['quantity'])/2)*float(pdfDict['height']) + ((math.floor(int(pdfDict['quantity'])/2) * .5) + ((int(pdfDict['quantity']) % 2) * .5))))

                    if pdfDict['orderSize'] == 'Samp':
                        pdfDict['orderWidth'] = 'W25'
                        pdfDict['orderHeight'] = 'H9'
                except IndexError:
                    try:
                        pdfDict = getPdf.getAll(file)
                    except:
                        print('| Couldn\'t handle', file.split('/')[-1])
                        print('| Sorry about that.')
                        continue
            newPDFName = pdfDict['orderNumber'] + '-' + pdfDict['orderItem'] + '-(' + str(date.today()) + ')-Prty-' + pdfDict['material'] + '-' + pdfDict['orderSize'] + '-Rp ' + str(pdfDict['orderRepeat']) + '-Qty ' + str(pdfDict['orderQuantity']) + '-' + pdfDict['templateName'] + '-L' + str(pdfDict['orderLength']) + '-W' + str(pdfDict['orderWidth']) + '-H' + str(pdfDict['orderHeight']) + '.pdf'
            try:
                os.rename(gv.driveLocation + '/' + file, gv.driveLocation + '/' + newPDFName)
            except:
                print('\n| Trouble renaming files.\n| File:', file)
                print('\n| Returning to Main Menu. Sorry about this.')
                return main()
                
    print('| Pausing to allow name changing to update.')
    time.sleep(4)
    print('| Resuming')
    print('| Moving files from Google Drive to today\'s sorted files.')
    for roots, dirs, files in os.walk(gv.driveLocation):
        for file in files:
            if file.startswith('.'): #skips macOS Hidden file '.DS_Store'
                continue
            elif file.endswith('.pdf') != True:
                continue
            else:
                pdfDict['orderRepeat'] = file.split('-')[8]
                pdfDict['orderQuantity'] = int(file.split('-')[9].split('Qty ')[1])
                if pdfDict['orderRepeat'] == 'Rp 2':
                    pdfDict['orderRepeat'] = 'Repeat 2/'
                else:
                    pdfDict['orderRepeat'] = 'Repeat Non-2/'
                if pdfDict['orderQuantity'] % 2 == 0:
                    pdfDict['orderQuantity'] = 'Even Panels/'
                else:
                    pdfDict['orderQuantity'] = 'Odd Panels/'
                print('| Moving file: ', file)
                print('| Source: ', gv.driveLocation)
                if pdfDict['orderSize'] == 'Full':
                    try:
                        shutil.move(gv.driveLocation + '/' + file, gv.sortingDir + '3 - Today/' + gv.dirLookupDict[pdfDict['material']] + gv.dirLookupDict[pdfDict['orderSize']]+ pdfDict['orderRepeat'] + pdfDict['orderQuantity'])
                        time.sleep(2)
                        print('| Successfully transferred! File:', file)
                    except shutil.Error:
                        shutil.copy(gv.driveLocation + '/' + file, gv.sortingDir + '3 - Today/' + gv.dirLookupDict[pdfDict['material']] + gv.dirLookupDict[pdfDict['orderSize']]+ pdfDict['orderRepeat'] + pdfDict['orderQuantity'])
                        try:
                            os.remove(gv.driveLocation + '/' + file)
                            time.sleep(2)
                            print('| Successfully transferred! File:', file)
                        except OSError:
                            print('|> Could not move ' + file)
                    except OSError as err:
                        print(err)    
                elif pdfDict['orderSize'] == 'Samp':
                    try:
                        shutil.move(gv.driveLocation + '/' + file, gv.sortingDir + '3 - Today/' + gv.dirLookupDict[pdfDict['material']] + gv.dirLookupDict[pdfDict['orderSize']])
                        time.sleep(2)
                        print('| Successfully transferred! File:', file)
                    except shutil.Error:
                        shutil.copy(gv.driveLocation + '/' + file, gv.sortingDir + '3 - Today/' + gv.dirLookupDict[pdfDict['material']] + gv.dirLookupDict[pdfDict['orderSize']])
                        try:
                            os.remove(gv.driveLocation + '/' + file)
                            time.sleep(2)
                            print('| Successfully transferred! File:', file)
                        except OSError:
                            print('|> Could not move ' + file)
                        except OSError as err:
                            print(err)
                    except PermissionError:
                        shutil.copy(gv.driveLocation + '/' + file, gv.sortingDir + '3 - Today/' + gv.dirLookupDict[pdfDict['material']] + gv.dirLookupDict[pdfDict['orderSize']])
                        try:
                            os.remove(gv.driveLocation + '/' + file)
                            time.sleep(2)
                            print('| Successfully transferred! File:', file)
                        except OSError:
                            print('|> Could not move ' + file)
                        except OSError as err:
                            print(err)
    print('\n| Finished transferring files from Google Drive.')
    moveForDueDates()
    return main()

try:
    startupChecks()
except:
    pass
main()
## End