#!usr/bin/env python

import os, shutil, math, datetime, time, json, glob, pikepdf
import zipfile as zf
from pathlib import Path
from datetime import date, timedelta, datetime
from sqlitedict import SqliteDict
from PyPDF2 import PdfFileReader, PdfFileWriter, PdfFileMerger, utils
from io import StringIO
import subprocess

#Location for Caldera's Folders
if os.path.expanduser('~').split('/')[-1] == 'Trevor':
    calderaDir = '/opt/caldera/var/public/'
    driveLocation = '/Volumes/GoogleDrive/Shared drives/# Production/#LvD Test Fulfillment'
else:
    calderaDir = '/Volumes/Print Drive/caldera/public/'
    driveLocation = '/Volumes/GoogleDrive/Shared drives/# Production/#LvD Fulfillment'

orderdb = calderaDir + 'z_Storage/z_WallpaperDB/lvdOrderDatabase.sqlite'
ordersDict = SqliteDict(orderdb, autocommit=True)
BatchCounterDB = calderaDir + 'z_Storage/z_WallpaperDB/lvdGlobalBatchCounter.sqlite'
globalBatchCounter = SqliteDict(BatchCounterDB, autocommit=True)
#globalBatchCounter['BatchCounter'] = 1

BatchFoldersDir = calderaDir + '2 Batch Folders/'
downloadDir = calderaDir + '3 Downloaded/'
needsAttention = calderaDir + '4 Needs Attention/'
sortingDir = calderaDir + '5 Sorted for Print/'

dirLookupDict = { #Dictionary for dynamically creating a directory path for sorting based on lookup tables
    'Sm':'Smooth/', #Smooth Folders
    'Smooth':'Smooth/',
    'Wv':'Woven/', #Woven Folders
    'Woven':'Woven/',
    'Tr':'Traditional/', #Traditional Folders
    'Full':'Full/', #Full Folders
    'Samp':'Sample/',
    'Sample':'Sample/', #Sample Folders
    'RepeatDict':{
        2:'Repeat 2/', #2 Foot Repeats
        3:'Repeat Non-2/', #Non-2 Foot Repeats
        4:'Repeat Non-2/', #Non-2 Foot Repeats
        5:'Repeat Non-2/', #Non-2 Foot Repeats
        6:'Repeat Non-2/', #Non-2 Foot Repeats
        7:'Repeat Non-2/', #Non-2 Foot Repeats
        8:'Repeat Non-2/', #Non-2 Foot Repeats
        9:'Repeat Non-2/', #Non-2 Foot Repeats
        10:'Repeat Non-2/', #Non-2 Foot Repeats
        11:'Repeat Non-2/', #Non-2 Foot Repeats
        12:'Repeat Non-2/', #Non-2 Foot Repeats 
    },
    1:'Odd Panels/',
    0:'Even Panels/',
    'MaterialLength':{ #this should reflect printable length. Smooth rolls are 150 feet, but we have 148 printable feet on each roll.
        'Smooth':145 * 12,
        'Woven':98 * 12,
        'Traditional':98 * 12,
    },
}

substrate = {
    'Woven Peel and Stick':'Wv',
    'Woven':'Wv',
    'Wv':'Woven',
    'Smooth Peel and Stick':'Sm',
    'Smooth':'Sm',
    'Sm':'Smooth',
    'Traditional':'Tr'
    }

shippingMethods = {
    'Standard':'Stnd',
    'Sample Standard':'SmStnd',
    'International Standard':'InStnd',
    'Priority':'Prty',
    'International Priority':'InPrty',
    'Rush':'Rush',
}

pdfsToRename = {
    
}

countOfRefPDFs = { #Running count of PDFs that are referenced during sample creating. If a PDF is referenced more than once, the order and PDF are printed to alert fulfillment of dual-type samples
    
}

orderItemsDict = {
}

today = date.today()

### Definitions
### Definitions

def main():
    options = 1,2,3,4,5,6,0
    print('\n| Main Menu')
    print('| 1. Sort Orders')
    print('| 2. Download Orders from Google Drive')
    print('| 3. Batch Orders')
    print('| 4. Update Sorting Based on Due Dates')
    print('| 6. Test Batches')
    print('| 5. Quit')
    try:
        command = int(input('\n| Command > '))
    except ValueError:
        print('\n| Please enter a number, not text.')
        return main()
    while int(command) not in options:
        print('\n| Not a valid choice.')
        return main()
    if command == 1:
        findJSONs()
        reportDuplicatePDFs()
        splitMultiPagePDFs()
        if os.path.expanduser('~').split('/')[-1] == 'Trevor':
            checkRepeatSize()
        sortPDFsByDetails()
        buildDBSadNoises()
        return main()
    elif command == 2:
        transferFilesFromDrive()
        return main()
    elif command == 3:
        BatchOrdersMain()
        return main()
    elif command == 4:
        moveForDueDates()
        return main()
    elif command == 6:
        buildBatchController('Batch 1', 'Smooth', 150, 'Full')
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
                shutil.rmtree(BatchFoldersDir)
                os.mkdir(BatchFoldersDir)
                shutil.rmtree(downloadDir)
                shutil.copytree('/Users/Trevor/Desktop/Backup/Downloaded', downloadDir)
                # shutil.rmtree(sortingDir)
                # shutil.copytree('/Users/Trevor/Desktop/Backup/5 Sorted for Print', sortingDir)
                findJSONs()   
                reportDuplicatePDFs()
                #splitMultiPagePDFs()
                checkRepeatSize()
                sortPDFsByDetails()
            transferFromDrive = input('| Do you want to transfer files from drive?\n| This will copy the current directory to a test directory. > ')
            if transferFromDrive == 'y':
                shutil.rmtree('/Volumes/GoogleDrive/Shared drives/# Production/#LvD Test Fulfillment')
                shutil.copytree('/Volumes/GoogleDrive/Shared drives/# Production/#LvD Fulfillment', '/Volumes/GoogleDrive/Shared drives/# Production/#LvD Test Fulfillment')
                transferFilesFromDrive()
            buildABatch('Batch 1', 'Smooth', 150, 'Full')
            return main()
    print('\n| Job\'s Done!')

def startupChecks():
    checkOrderDirectoryStructure()
    checkBatchCounter()
    moveForDueDates()

def checkBatchCounter():
    if globalBatchCounter['BatchCounter'] > 9000:
        globalBatchCounter['BatchCounter'] = 1

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
    if Path(calderaDir + '# Past Orders/Original Files/').exists() == False:
        try:
            os.mkdir(calderaDir + '# Past Orders/Original Files')
        except:
            pass
    if Path(sortingDir + '1 - Late and OT/').exists() == True:
        try:
            os.mkdir(sortingDir + '1 - OT Orders/')
        except:
            pass
        buildSortedDirStructure(sortingDir + '1 - OT Orders/')
        try:
            os.mkdir(sortingDir + '2 - Late/')
        except:
            pass
        buildSortedDirStructure(sortingDir + '2 - Late/')
    if Path(sortingDir + '2 - Today/').exists() == True:
        try:
            os.mkdir(sortingDir + '3 - Today/')
        except:
            pass
        buildSortedDirStructure(sortingDir + '3 - Today/')
    if Path(sortingDir + '3 - Future/').exists() == True:
        try:
            os.mkdir(sortingDir + '4 - Future/')
        except:
            pass
        buildSortedDirStructure(sortingDir + '4 - Future/')
    return

def moveForDueDates():
    print('\n| Updating Orders. Today\'s date:', today)
    for file in glob.iglob(sortingDir + '**/*.pdf', recursive=True):
        fileName = file.split('/')[-1]
        orderDueDate = datetime.date(datetime.strptime(fileName.split('(')[1].split(')')[0], '%Y-%m-%d')) 
        material = fileName.split('-')[6]
        orderSize = fileName.split('-')[7]
        repeat = int(fileName.split('-')[8].split(' ')[1])
        oddOrEven = int(fileName.split('-')[9].split(' ')[1]) % 2   
        orderLength = float(fileName.split('-')[11].split('L')[1])
        if orderDueDate < today:
            orderDueDate = '2 - Late/'
        elif orderDueDate > today:
            orderDueDate = '4 - Future/'
        else:
            orderDueDate = '3 - Today/'
         # Checks if order is over the maximum length of a roll and moves it to Needs Attention
        if material == 'Wv':
            if orderLength >= dirLookupDict['MaterialLength']['Woven']:
                try:
                    shutil.copy(file, needsAttention)
                    try:
                        os.remove(file)
                        continue
                    except:
                        print('|> Could not remove ', file)
                except OSError as err:
                    print(err)
        elif material == 'Sm':
            if orderLength >= dirLookupDict['MaterialLength']['Smooth']:
                try:
                    shutil.copy(file, needsAttention)
                    try:
                        os.remove(file)
                        continue
                    except:
                        print('|> Could not remove ', file)
                except OSError as err:
                    print(err)
        if orderSize == 'Samp':
            try:
                shutil.move(file, sortingDir + orderDueDate + dirLookupDict[material] + 'Sample/')
                print('| Updated:', file.split('/')[-1])
            except:
                try:
                    shutil.copy(file, sortingDir + orderDueDate + dirLookupDict[material] + 'Sample/')
                    os.remove(file)
                    print('| Updated:', file.split('/')[-1])
                except shutil.SameFileError:
                    continue
        else:
            try:
                shutil.move(file, sortingDir + orderDueDate + dirLookupDict[material] + 'Full/' + dirLookupDict['RepeatDict'][repeat] + dirLookupDict[oddOrEven])
                print('| Updated:', file.split('/')[-1])
            except:
                try:
                    shutil.copy(file, sortingDir + orderDueDate + dirLookupDict[material] + 'Full/' + dirLookupDict['RepeatDict'][repeat] + dirLookupDict[oddOrEven])
                    os.remove(file)
                    print('| Updated:', file.split('/')[-1])
                except shutil.SameFileError:
                    continue
    print('| Done updating orders based on Due Dates.')
    
    needsAttentionDir = len(glob.glob(needsAttention + '*.pdf'))
    if needsAttentionDir > 0:
        print(f'\n| ****\n| 4 Needs Attention has {needsAttentionDir} file(s) that need attention.\n| ****\n')  

def findJSONs(): #iterates over a given folder, unzips files, finds JSON files, and calls parseJSONDerulo
    os.chdir(downloadDir)
    for roots, dirs, files in os.walk(downloadDir):
        for file in files:
            ext = os.path.splitext(file)[-1].lower()
            if ext == '.zip':
                try:
                    with zf.ZipFile(file, 'r') as zip_ref:
                        zip_ref.extractall(downloadDir)
                    os.remove(file)
                except:
                    print('Couldn\'t unzip file:', file)
    for roots, dirs, files in os.walk(downloadDir):
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
    for roots, dirs, files in os.walk(downloadDir):
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
    shipVia = shippingMethods[JSON['shippingInfo']['method']['shipvia']]
    try:
        for itemNum in range(len(JSONitem)):
            originalPDFName = JSONitem[itemNum]['filename']
            itemID = originalPDFName.split('_')[0]
            try:
                templateName = JSONitem[itemNum]['description'].split(' ')[2] + ' ' + JSONitem[itemNum]['description'].split(' ')[3]
            except IndexError:
                templateName = JSONitem[itemNum]['description'].split(' Wallpaper')[0]
            paperType = substrate[JSONitem[itemNum]['paper']]
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
                length = str((math.ceil(int(quantity)/2)*float(height) + ((math.floor(int(quantity)/2) * .5) + ((int(quantity) % 2) * .5))))
                # See Length Notes at the end of the function for an explanation.
            newPDFName = orderNumber + '-' + str(count) + '-(' + orderDueDate + ')-' + shipVia + '-' + paperType + '-' + orderSize + '-Rp ' + repeat.split("'")[0] + '-Qty ' + quantity + '-' + templateName + '-L' + length + '-W' + width + '-H' + height
            renamePDF(originalPDFName, newPDFName)
            keepTrackOfPDF(orderNumber, originalPDFName) 
            count += 1
            if orderNumber in orderItemsDict:
                orderItemsDict[orderNumber][itemID] = {
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
                    'File Path': sortingDir + '2 - Late/' + dirLookupDict[paperType] + dirLookupDict[orderSize] + dirLookupDict['RepeatDict'][int(repeat.split('\'')[0])] + dirLookupDict[int(quantity) % 2] + newPDFName,
                }
            else:
                orderItemsDict[orderNumber] = {
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
                        'File Path': sortingDir + '2 - Late/' + dirLookupDict[paperType] + dirLookupDict[orderSize] + dirLookupDict['RepeatDict'][int(repeat.split('\'')[0])] + dirLookupDict[int(quantity) % 2] + newPDFName,
                    }
                }
                    
    except KeyError:
        originalPDFName = JSONitem['filename']
        itemID = originalPDFName.split('_')[0]
        templateName = JSONitem['description'].split(' Wallpaper')[0]
        paperType = substrate[JSONitem['paper']]
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
            length = str((math.ceil(int(quantity)/2)*float(height) + ((math.floor(int(quantity)/2) * .5) + ((int(quantity) % 2) * .5))))
        newPDFName = orderNumber + '-' + str(count) + '-(' + orderDueDate + ')-' + shipVia + '-' + paperType + '-' + orderSize + '-Rp ' + repeat.split("'")[0] + '-Qty ' + quantity + '-' + templateName + '-L' + length + '-W' + width + '-H' + height
        renamePDF(originalPDFName, newPDFName)
        keepTrackOfPDF(orderNumber, originalPDFName) 
        count += 1
        if orderNumber in orderItemsDict:
                orderItemsDict[orderNumber][itemID] = {
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
                    'File Path': sortingDir + '2 - Late/' + dirLookupDict[paperType] + dirLookupDict[orderSize] + dirLookupDict['RepeatDict'][int(repeat.split('\'')[0])] + dirLookupDict[int(quantity) % 2] + newPDFName,
                }
        else:
            orderItemsDict[orderNumber] = {
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
                    'File Path': sortingDir + '2 - Late/' + dirLookupDict[paperType] + dirLookupDict[orderSize] + dirLookupDict['RepeatDict'][int(repeat.split('\'')[0])] + dirLookupDict[int(quantity) % 2] + newPDFName,
                }
            }
    
    ''' # Length Notes: I will never remember why I did this. Here are my notes. The length is the length of material an order will take up.
        # Length Notes: The above equation takes the quantity and divides it by two since we can fit two panels side by side.
        # Length Notes: it then multiplies that by the height to get the overall length of material.
        # Length Notes: after, it takes the quantity/2, rounds it down, and multiplies it by .5 for the .5" gap between each panel.
        # Length Notes: lastly, it takes the quantity % 2 to see if the quantity is odd or not. If the quantity is odd, then it will add on one more length of .5"
        # Length Notes: for the times that a panel is by itself and still has another .5" section.'''

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
    if orderNumber in countOfRefPDFs:
        pass
    else:
        countOfRefPDFs[orderNumber] = {}

def keepTrackOfPDF(orderNumber, pdfFileName):
    if pdfFileName in countOfRefPDFs[orderNumber]:
        countOfRefPDFs[orderNumber][pdfFileName] += 1
    else:
        countOfRefPDFs[orderNumber][pdfFileName] = 1

def reportDuplicatePDFs(): #prints out any PDFs from keepTrackOfOrderNumber() that have a count of 2 or more
    for orderNumber in countOfRefPDFs:
        for pdfName in countOfRefPDFs[orderNumber]:
            if countOfRefPDFs[orderNumber][pdfName] > 1:
                print('\n| The following Order has samples with multiple material types:')
                print('| ' + orderNumber + ': ' + pdfName.replace('_',' '))

def splitMultiPagePDFs():
    for file in glob.iglob(downloadDir + '*.pdf'):
        try:
            pdf = pikepdf.Pdf.open(file)
            NumOfPages = len(pdf.pages)
        except:
            print(f'| Couldn\'t check the number of pages on {file}')
            pass
        if NumOfPages > 1:
                print(f'| {file} has more than one page in its PDF. Splitting now.')
                templateName = file.split('-')[10] ##
                namePt1 = file.split('Qty ')[0] + 'Qty '
                namePt2 = file.split(templateName)[1]
                repeat = file.split('-')[8] ##
                quantity = int(file.split('-')[9].split(' ')[1])
                for n, page in enumerate(pdf.pages):
                    dst = pikepdf.Pdf.new()
                    dst.pages.append(page)
                    dst.save(namePt1 + str(quantity) + '-' + templateName + ' Panel ' + str(n + 1) + namePt2)
                try:
                    os.remove(file)
                    print(f'| Finished splitting {file}')
                except:
                    print(f'| Split the pages of {file},\nbut couldn\'t remove the original.')

def sortPDFsByDetails():
    print('\n| Starting Sort Process. This may take a long time.')
    for file in glob.iglob(downloadDir + '*.pdf'):
        dueDate = datetime.date(datetime.strptime(file.split('(')[1].split(')')[0], '%Y-%m-%d'))
        material = file.split('-')[6]
        orderSize = file.split('-')[7]
        repeat = int(file.split('-')[8].split(' ')[1])
        oddOrEven = int(file.split('-')[9].split(' ')[1]) % 2
        orderLength = float(file.split('-')[11].split('L')[1])
        # Checks if order is over the maximum length of a roll and moves it to Needs Attention
        if material == 'Wv':
            if orderLength >= dirLookupDict['MaterialLength']['Woven']:
                try:
                    shutil.copy(file, needsAttention)
                    try:
                        os.remove(file)
                        continue
                    except:
                        print('|> Could not remove ', file)
                except OSError as err:
                            print(err)
        elif material == 'Sm':
            if orderLength >= dirLookupDict['MaterialLength']['Smooth']:
                try:
                    shutil.copy(file, needsAttention)
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
                    shutil.copy(file, sortingDir + '2 - Late/' + dirLookupDict[material] +dirLookupDict[orderSize])
                    try:
                        os.remove(file)
                    except:
                        print('|> Could not remove ', file)
                except OSError as err:
                    print(err)
            elif dueDate > date.today():
                try:
                    shutil.copy(file, sortingDir + '4 - Future/' + dirLookupDict[material] + dirLookupDict[orderSize])
                    try:
                        os.remove(file)
                    except:
                        print('|> Could not remove ', file)
                except OSError as err:
                    print(err)
            else:
                try:
                    shutil.copy(file, sortingDir + '3 - Today/' + dirLookupDict[material] + dirLookupDict[orderSize])
                    try:
                        os.remove(file)
                    except:
                        print('|> Could not remove ', file)
                except OSError as err:
                    print(err)
        else:
            if dueDate < date.today():
                try:
                    shutil.copy(file, sortingDir + '2 - Late/' + dirLookupDict[material] +dirLookupDict[orderSize] + dirLookupDict['RepeatDict'][repeat] + dirLookupDict[oddOrEven])
                    try:
                        os.remove(file)
                    except:
                        print('|> Could not remove ', file)
                except OSError as err:
                    print(err)
            elif dueDate > date.today():
                try:
                    shutil.copy(file, sortingDir + '4 - Future/' + dirLookupDict[material] + dirLookupDict[orderSize] + dirLookupDict['RepeatDict'][repeat] + dirLookupDict[oddOrEven])
                    try:
                        os.remove(file)
                    except:
                        print('|> Could not remove ', file)
                except OSError as err:
                    print(err)
            else:
                try:
                    shutil.copy(file, sortingDir + '3 - Today/' + dirLookupDict[material] + dirLookupDict[orderSize] + dirLookupDict['RepeatDict'][repeat] + dirLookupDict[oddOrEven])
                    try:
                        os.remove(file)
                    except:
                        print('|> Could not remove ', file)
                except OSError as err:
                    print(err)
    
    print('| Finished sorting files.')
    needsAttentionDir = len(glob.glob(needsAttention + '*.pdf'))
    if needsAttentionDir > 0:
        print(f'\n| ****\n| 4 Needs Attention has {needsAttentionDir} file(s) that need attention.\n| ****\n')

def buildDBSadNoises():
    print('| Building DB. Please hold.')
    fullOrdersDirectory = sortingDir + '**/Full/*.pdf' 
    #300014839-2-(2022-02-15)-Stnd-Sm-Samp-Rp 2-Qty 1-Mod Herons-L9.5-W25-H9
    # buildDBSadNoises()
    # print('| Printing Current Order Database.')
    # for order in orderItemsDict:
    #    print(f'|-{order}')
    #    for orderItemID in orderItemsDict[order]:
    #        if orderItemsDict[order][orderItemID]['Order Size'] == 'Full':
    #            print(f'|  -- {orderItemID}')
    #            print('|    --', orderItemsDict[order][orderItemID]['Status'])
    #            print('|    --', orderItemsDict[order][orderItemID]['Order Size'])
    #            print('|    --', orderItemsDict[order][orderItemID]['Length'])
    #            print('|    --', orderItemsDict[order][orderItemID]['Repeat'])
    for printPDF in glob.iglob(sortingDir + '**/*.pdf', recursive=True):
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
        if orderNumber[orderItemID] in orderItemsDict:
            orderItemsDict[orderNumber][orderItemID] = {
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
            orderItemsDict[orderNumber] = {
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

def BatchOrdersMain():
    options = 1,2,3,4,5,0
    print('\n| Main Menu > Batch Orders')
    print('| 1. Batch Smooth Full')
    print('| 2. Batch Smooth Samples')
    print('| 3. Batch Woven Full')
    print('| 4. Batch Woven Samples')
    print('| 5. Combine Batches')
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
            BatchingController('Smooth', 'Full')
            return BatchOrdersMain()
        elif confirm == False:
            print('\n| Returning to Batch Orders.')
            return BatchOrdersMain()
    elif command == 2:
        confirm = confirmBatch('Smooth', 'Sample')
        if confirm == True:
            BatchingController('Smooth', 'Sample')
            return BatchOrdersMain()
        elif confirm == False:
            print('\n| Returning to Batch Orders.')
            return BatchOrdersMain()
    elif command == 3:
        confirm = confirmBatch('Woven', 'Full')
        if confirm == True:
            BatchingController('Woven', 'Full')
            return BatchOrdersMain()
        elif confirm == False:
            print('\n| Returning to Batch Orders.')
            return BatchOrdersMain()
    elif command == 4:
        confirm = confirmBatch('Woven', 'Sample')
        if confirm == True:
            BatchingController('Woven', 'Sample')
            return BatchOrdersMain()
        elif confirm == False:
            print('\n| Returning to Batch Orders.')
            return BatchOrdersMain()
    elif command == 5:
        material = input('| Material please > ')
        combineBatchFoldersController(material)
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

def BatchingController(material, orderSize):
    print('\n| Starting', material, orderSize, 'Full Batching.')
    materialLength = int(input('\n| Please input your starting material length in feet > '))
    # while materialLength != type(int):
    #     materialLength = int(input('\n| Please input your starting material length in feet > '))
    BatchDir = BatchDirBuilder(material, orderSize)
    if orderSize == 'Full':
        findOrdersForPrint2Ptv2(BatchDir, material, orderSize, (int(materialLength)*12))
        removeEmptyBatchFolders(True)
        #combineBatchFoldersController(material)
        BatchDir = BatchDirBuilder(material, orderSize)
        findOrdersForPrint4Ptv2(BatchDir, material, orderSize, (int(materialLength)*12))
        removeEmptyBatchFolders(True)
    else:
        findSampleOrdersForPrint(BatchDir, material, orderSize, (int(materialLength * 12)))
    print('\n| Finished Batching', material, orderSize, 'orders.')

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

def findSampleOrdersForPrint(BatchDir, material, orderSize, materialLength):
    OTOrders = sortingDir + '1 - OT Orders/' + dirLookupDict[material] + dirLookupDict[orderSize]
    lateOrders = sortingDir + '2 - Late/' + dirLookupDict[material] + dirLookupDict[orderSize]
    todayOrders = sortingDir + '3 - Today/' + dirLookupDict[material] + dirLookupDict[orderSize] 
    futureOrders = sortingDir + '4 - Future/' + dirLookupDict[material] + dirLookupDict[orderSize]
    curBatchDirLength = 0
    oddCount = 1
    if (curBatchDirLength < (materialLength - 10)):
        for sample in glob.iglob(lateOrders + '*.pdf'):
            if (curBatchDirLength + float(sample.split('/')[9].split('-')[11].split('L')[1]) > (materialLength * 1.01)):
                newBatchName = BatchDir.split('/')[6].split(' L')[0] + ' L' + str(curBatchDirLength)
                os.rename(BatchDir, BatchFoldersDir + newBatchName)
                print('\n| Batch with OT/Late Orders Finished.\n| Batch Folder: ', newBatchName, '\n| Length:', str(round(curBatchDirLength/12, 2)), 'feet (' + str(curBatchDirLength), 'inches)')
                BatchDir = BatchDirBuilder(material, orderSize)
                materialLength = input('| Please input your material length. > ')
                return findSampleOrdersForPrint(BatchDir, material, orderSize, int(materialLength)*12)
                # return findSampleOrdersForPrint(BatchDir, material, orderSize, dirLookupDict['MaterialLength'][material])
            else:
                try:
                    shutil.move(sample, BatchDir)
                    if oddCount == 0:
                        curBatchDirLength += float(sample.split('/')[9].split('-')[11].split('L')[1])
                        oddCount = 1
                    else:
                        oddCount = 0
                except shutil.Error:
                    shutil.copy(sample, BatchDir)
                    try:
                        os.remove(sample)
                    except OSError:
                        print('|> Could not remove ' + sample)
                except FileNotFoundError:
                    print('|> Couldn\'t find sample to move. \n|> File: ', sample)
    if (curBatchDirLength < (materialLength - 10)):
        for sample in glob.iglob(todayOrders + '*.pdf'):
            if (curBatchDirLength + float(sample.split('/')[9].split('-')[11].split('L')[1]) > (materialLength * 1.01)):
                newBatchName = BatchDir.split('/')[6].split(' L')[0] + ' L' + str(curBatchDirLength)
                os.rename(BatchDir, BatchFoldersDir + newBatchName)
                print('\n| Batch Finished.\n| Batch Folder: ', newBatchName, '\n| Length:', str(round(curBatchDirLength/12, 2)), 'feet (' + str(curBatchDirLength), 'inches)')
                BatchDir = BatchDirBuilder(material, orderSize)
                materialLength = input('| Please input your material length. > ')
                return findSampleOrdersForPrint(BatchDir, material, orderSize, int(materialLength)*12)
                # return findSampleOrdersForPrint(BatchDir, material, orderSize, dirLookupDict['MaterialLength'][material])
            else:
                try:
                    shutil.move(sample, BatchDir)
                    if oddCount == 0:
                        curBatchDirLength += float(sample.split('/')[9].split('-')[11].split('L')[1])
                        oddCount = 1
                    else:
                        oddCount = 0
                except shutil.Error:
                    shutil.copy(sample, BatchDir)
                    try:
                        os.remove(sample)
                    except OSError:
                        print('|> Could not remove ' + sample)
                except FileNotFoundError:
                    print('|> Couldn\'t find sample to move. \n|> File: ', sample)
    if (curBatchDirLength < (materialLength - 10)):
        for sample in glob.iglob(futureOrders + '*.pdf'):
            if (curBatchDirLength + float(sample.split('/')[9].split('-')[11].split('L')[1]) > (materialLength * 1.01)):
                newBatchName = BatchDir.split('/')[6].split(' L')[0] + ' L' + str(curBatchDirLength)
                os.rename(BatchDir, BatchFoldersDir + newBatchName)
                print('\n| Batch Finished.\n| Batch Folder: ', newBatchName, '\n| Length:', str(round(curBatchDirLength/12, 2)), 'feet (' + str(curBatchDirLength), 'inches)')
                BatchDir = BatchDirBuilder(material, orderSize)
                materialLength = input('| Please input your material length. > ')
                return findSampleOrdersForPrint(BatchDir, material, orderSize, int(materialLength)*12)
                # return findSampleOrdersForPrint(BatchDir, material, orderSize, dirLookupDict['MaterialLength'][material])
            else:
                try:
                    shutil.move(sample, BatchDir)
                    if oddCount == 0:
                        curBatchDirLength += float(sample.split('/')[9].split('-')[11].split('L')[1])
                        oddCount = 1
                    else:
                        oddCount = 0
                except shutil.Error:
                    shutil.copy(sample, BatchDir)
                    try:
                        os.remove(sample)
                    except OSError:
                        print('|> Could not remove ' + sample)
                except FileNotFoundError:
                    print('|> Couldn\'t find sample to move. \n|> File: ', sample)                
    newBatchName = BatchDir.split('/')[6].split(' L')[0] + ' L' + str(curBatchDirLength)
    print('\n| Batch Finished.\n| Batch Folder: ', newBatchName, '\n| Length:', str(round(curBatchDirLength/12, 2)), 'feet (' + str(curBatchDirLength), 'inches)')
    os.rename(BatchDir, BatchFoldersDir + newBatchName)
    return

def findFullRp2EvenOrdersForPrint(BatchDir, material, orderSize, materialLength):
    OTOrders = sortingDir + '1 - OT Orders/' + dirLookupDict[material] + dirLookupDict[orderSize]
    lateOrders = sortingDir + '2 - Late/' + dirLookupDict[material] + dirLookupDict[orderSize]
    todayOrders = sortingDir + '3 - Today/' + dirLookupDict[material] + dirLookupDict[orderSize] 
    futureOrders = sortingDir + '4 - Future/' + dirLookupDict[material] + dirLookupDict[orderSize]
    curBatchDirLength = 0
    while len(glob.glob(sortingDir + '*/'+ dirLookupDict[material] + dirLookupDict[orderSize] + 'Repeat 2/Even Panels/*.pdf'))>0:
        if (curBatchDirLength < (materialLength - 0.85)):
            for order in glob.iglob(lateOrders + 'Repeat 2/Even Panels/*.pdf'):
                if (curBatchDirLength + float(order.split('/')[11].split('-')[11].split('L')[1]) > (materialLength * 1.01)):
                    newBatchName = BatchDir.split('/')[6].split(' L')[0] + ' L' + str(curBatchDirLength)
                    os.rename(BatchDir, BatchFoldersDir + newBatchName)
                    print('\n| Batch with OT/Late Orders Finished.\n| Batch Folder: ', newBatchName, '\n| Length:', str(round(curBatchDirLength/12, 2)), 'feet (' + str(curBatchDirLength), 'inches)')
                    BatchDir = BatchDirBuilder(material, orderSize)
                    return findFullRp2EvenOrdersForPrint(BatchDir, material, orderSize, dirLookupDict['MaterialLength'][material])
                else:
                    try:
                        shutil.move(order, BatchDir)
                        curBatchDirLength += float(order.split('/')[11].split('-')[11].split('L')[1])
                    except shutil.Error:
                        shutil.copy(order, BatchDir)
                        curBatchDirLength += float(order.split('/')[11].split('-')[11].split('L')[1])
                        try:
                            os.remove(order)
                        except OSError:
                            print('|> Could not remove ' + order)
                    except FileNotFoundError:
                        print('|> Couldn\'t find order to move. \n|> File: ', order)
        if (curBatchDirLength < (materialLength - 0.85)):
            for order in glob.iglob(todayOrders + 'Repeat 2/Even Panels/*.pdf'):
                if (curBatchDirLength + float(order.split('/')[11].split('-')[11].split('L')[1]) > (materialLength * 1.01)):
                    continue
                else:
                    try:
                        shutil.move(order, BatchDir)
                        curBatchDirLength += float(order.split('/')[11].split('-')[11].split('L')[1])
                    except shutil.Error:
                        shutil.copy(order, BatchDir)
                        curBatchDirLength += float(order.split('/')[11].split('-')[11].split('L')[1])
                        try:
                            os.remove(order)
                        except OSError:
                            print('|> Could not remove ' + order)
                    except FileNotFoundError:
                        print('|> Couldn\'t find order to move. \n|> File: ', order)
        if (curBatchDirLength < (materialLength - 0.85)):
            for order in glob.iglob(futureOrders + 'Repeat 2/Even Panels/*.pdf'):
                if (curBatchDirLength + float(order.split('/')[11].split('-')[11].split('L')[1]) > (materialLength * 1.01)):
                    continue
                else:
                    try:
                        shutil.move(order, BatchDir)
                        curBatchDirLength += float(order.split('/')[11].split('-')[11].split('L')[1])
                    except shutil.Error:
                        shutil.copy(order, BatchDir)
                        curBatchDirLength += float(order.split('/')[11].split('-')[11].split('L')[1])
                        try:
                            os.remove(order)
                        except OSError:
                            print('|> Could not remove ' + order)
                    except FileNotFoundError:
                        print('|> Couldn\'t find order to move. \n|> File: ', order)    
    
    newBatchName = BatchDir.split('/')[6].split(' L')[0] + ' L' + str(curBatchDirLength)
    print('\n| Batch Finished.\n| Batch Folder: ', newBatchName, '\n| Length:', str(round(curBatchDirLength/12, 2)), 'feet (' + str(curBatchDirLength), 'inches)')
    os.rename(BatchDir, BatchFoldersDir + newBatchName)
    return

def findFullRp2OddOrdersForPrint(BatchDir, material, orderSize, materialLength):
    OTOrders = sortingDir + '1 - OT Orders/' + dirLookupDict[material] + dirLookupDict[orderSize]
    lateOrders = sortingDir + '2 - Late/' + dirLookupDict[material] + dirLookupDict[orderSize]
    todayOrders = sortingDir + '3 - Today/' + dirLookupDict[material] + dirLookupDict[orderSize] 
    futureOrders = sortingDir + '4 - Future/' + dirLookupDict[material] + dirLookupDict[orderSize]
    curBatchDirLength = 0
    oddCount = 0
    oddCountHeight = 0
    if (curBatchDirLength < (materialLength - 0.85)):
        for order in glob.iglob(lateOrders + 'Repeat 2/Odd Panels/*.pdf'):
            if (curBatchDirLength + float(order.split('/')[11].split('-')[11].split('L')[1]) > (materialLength * 1.01)):
                newBatchName = BatchDir.split('/')[6].split(' L')[0] + ' L' + str(curBatchDirLength)
                os.rename(BatchDir, BatchFoldersDir + newBatchName)
                BatchDir = BatchDirBuilder(material, orderSize)
                print('| ' + BatchDir)
                return findFullRp2OddOrdersForPrint(BatchDir, material, orderSize, dirLookupDict['MaterialLength'][material])
            else:
                currentOrderLength = order.split('/')[11].split('-')[13]
                for orderToMatch in glob.iglob(lateOrders + 'Repeat 2/Odd Panels/*' + currentOrderLength): #don't need to include the .pdf in the filename here as it's included in currentOrderLength
                    if (curBatchDirLength + (float(order.split('/')[11].split('-')[11].split('L')[1]) + float(orderToMatch.split('/')[11].split('-')[11].split('L')[1])) - float(orderToMatch.split('/')[11].split('-')[13].split('H')[1].split('.pdf'))[0] > (materialLength * 1.01)): 
                        continue
                    else:
                        try:
                            shutil.move(order, BatchDir)
                            shutil.move(orderToMatch, BatchDir)
                        except shutil.Error:
                            shutil.copy(order, BatchDir)
                            try:
                                os.remove(order)
                            except OSError:
                                print('|> Could not remove ' + order)
                        except FileNotFoundError:
                            print('|> Couldn\'t find order to move. \n|> File: ', order)
    if (curBatchDirLength < (materialLength - 0.85)):
        for order in glob.iglob(todayOrders + 'Repeat 2/Odd Panels/*.pdf'):
            if (curBatchDirLength + float(order.split('/')[11].split('-')[11].split('L')[1]) > (materialLength * 1.01)):
                continue
            else:
                try:
                    shutil.move(order, BatchDir)
                    if oddCount == 0:
                        curBatchDirLength += float(order.split('/')[11].split('-')[11].split('L')[1])
                        oddCount = 1
                        oddCountHeight = float(order.split('/')[11].split('-')[13].split('H')[1].split('.pdf')[0])
                    else:
                        while oddCount == 1:
                            for oddOrder in glob.iglob(lateOrders + 'Repeat 2/Odd Panels/*H' + str(oddCountHeight) +'.pdf'):
                                if (curBatchDirLength + float(oddOrder.split('/')[11].split('-')[11].split('L')[1]) > (materialLength * 1.01)):
                                    continue
                                else:
                                    shutil.move(oddOrder, BatchDir)
                                    oddCount = 0
                                    oddCountHeight = 0
                            print('| Couldn\'t find any matching, odd-paneled heights.')
                            oddCount = 0        
                except shutil.Error:
                    shutil.copy(order, BatchDir)
                    try:
                        os.remove(order)
                    except OSError:
                        print('|> Could not remove ' + order)
                except FileNotFoundError:
                    print('|> Couldn\'t find order to move. \n|> File: ', order)
    if (curBatchDirLength < (materialLength - 0.85)):
        for order in glob.iglob(futureOrders + 'Repeat 2/Odd Panels/*.pdf'):
            if (curBatchDirLength + float(order.split('/')[11].split('-')[11].split('L')[1]) > (materialLength * 1.01)):
                continue
            else:
                try:
                    shutil.move(order, BatchDir)
                    if oddCount == 0:
                        curBatchDirLength += float(order.split('/')[11].split('-')[11].split('L')[1])
                        oddCount = 1
                        oddCountHeight = float(order.split('/')[11].split('-')[13].split('H')[1].split('.pdf')[0])
                    else:
                        while oddCount == 1:
                            for oddOrder in glob.iglob(lateOrders + 'Repeat 2/Odd Panels/*H' + str(oddCountHeight) +'.pdf'):
                                if (curBatchDirLength + float(oddOrder.split('/')[11].split('-')[11].split('L')[1]) > (materialLength * 1.01)):
                                    continue
                                else:
                                    shutil.move(oddOrder, BatchDir)
                                    oddCount = 0
                                    oddCountHeight = 0
                            print('| Couldn\'t find any matching, odd-paneled heights.')
                            oddCount = 0        
                except shutil.Error:
                    shutil.copy(order, BatchDir)
                    try:
                        os.remove(order)
                    except OSError:
                        print('|> Could not remove ' + order)
                except FileNotFoundError:
                    print('|> Couldn\'t find order to move. \n|> File: ', order)

def transferFilesFromDrive():
    # Old name convention: 300014719(1)-Watercolor Herringbone-Wv-Samp-Rp 4-Qty 1-W9-H25
    # New name convention: 300013884-1-(2022-02-02)-Stnd-Wv-Samp-Rp 2-Qty 1-Watercolor Herringbone-L9.5-W25-H9
    print('\n| Checking for files in Google Drive.')
    for roots, dirs, files in os.walk(driveLocation):
        ('\n| Renaming files in Google Drive to the new naming convention.')
        for file in files:
            if file.startswith('.'): #skips macOS Hidden file '.DS_Store'
                continue
            elif file.endswith('.pdf') != True:
                continue
            else:
                try:
                    orderNumber = file.split('(')[0]
                    orderItem = file.split('(')[1].split(')')[0]
                    templateName = file.split('-')[1]
                    material = file.split('-')[2]
                    orderSize = file.split('-')[3]
                    orderRepeat = file.split('-')[4]
                    orderQuantity = file.split('-')[5]
                    quantity = orderQuantity.split('Qty ')[1]
                    orderWidth = file.split('-')[6]
                    orderHeight = file.split('-')[7].split('.pdf')[0]
                    if orderSize == 'Samp':
                        orderWidth = 'W25'
                        orderHeight = 'H9'
                    height = orderHeight.split('H')[1]
                    orderLength = str((math.ceil(int(quantity)/2)*float(height) + ((math.floor(int(quantity)/2) * .5) + ((int(quantity) % 2) * .5))))
                except IndexError:
                    print('| Couldn\'t handle', file.split('/')[-1])
                    print('| Sorry about that.')
                    continue
            newPDFName = orderNumber + '-' + orderItem + '-(' + str(date.today()) + ')-Prty-' + material + '-' + orderSize + '-' + orderRepeat + '-' + orderQuantity + '-' + templateName + '-L' + orderLength + '-' + orderWidth + '-' + orderHeight + '.pdf'
            try:
                os.rename(driveLocation + '/' + file, driveLocation + '/' + newPDFName)
            except:
                print('\n| Trouble renaming files.\n| File:', file)
                print('\n| Returning to Main Menu. Sorry about this.')
                return main()
                
    print('| Pausing to allow name changing to update.')
    time.sleep(4)
    print('| Resuming')
    print('| Moving files from Google Drive to today\'s sorted files.')
    for roots, dirs, files in os.walk(driveLocation):
        for file in files:
            if file.startswith('.'): #skips macOS Hidden file '.DS_Store'
                continue
            elif file.endswith('.pdf') != True:
                continue
            else:
                orderRepeat = file.split('-')[8]
                orderQuantity = int(file.split('-')[9].split('Qty ')[1])
                if orderRepeat == 'Rp 2':
                    orderRepeat = 'Repeat 2/'
                else:
                    orderRepeat = 'Repeat Non-2/'
                if orderQuantity % 2 == 0:
                    orderQuantity = 'Even Panels/'
                else:
                    orderQuantity = 'Odd Panels/'
                print('| Moving file: ', file)
                print('| Source: ', driveLocation)
                if orderSize == 'Full':
                    try:
                        shutil.move(driveLocation + '/' + file, sortingDir + '3 - Today/' + dirLookupDict[material] + dirLookupDict[orderSize]+ orderRepeat + orderQuantity)
                        time.sleep(2)
                        print('| Successfully transferred! File:', file)
                    except shutil.Error:
                        shutil.copy(driveLocation + '/' + file, sortingDir + '3 - Today/' + dirLookupDict[material] + dirLookupDict[orderSize]+ orderRepeat + orderQuantity)
                        try:
                            os.remove(driveLocation + '/' + file)
                            time.sleep(2)
                            print('| Successfully transferred! File:', file)
                        except OSError:
                            print('|> Could not move ' + file)
                    except OSError as err:
                        print(err)    
                elif orderSize == 'Samp':
                    try:
                        shutil.move(driveLocation + '/' + file, sortingDir + '3 - Today/' + dirLookupDict[material] + dirLookupDict[orderSize])
                        time.sleep(2)
                        print('| Successfully transferred! File:', file)
                    except shutil.Error:
                        shutil.copy(driveLocation + '/' + file, sortingDir + '3 - Today/' + dirLookupDict[material] + dirLookupDict[orderSize])
                        try:
                            os.remove(driveLocation + '/' + file)
                            time.sleep(2)
                            print('| Successfully transferred! File:', file)
                        except OSError:
                            print('|> Could not move ' + file)
                        except OSError as err:
                            print(err)
                    except PermissionError:
                        shutil.copy(driveLocation + '/' + file, sortingDir + '3 - Today/' + dirLookupDict[material] + dirLookupDict[orderSize])
                        try:
                            os.remove(driveLocation + '/' + file)
                            time.sleep(2)
                            print('| Successfully transferred! File:', file)
                        except OSError:
                            print('|> Could not move ' + file)
                        except OSError as err:
                            print(err)
    print('\n| Finished transferring files from Google Drive.')
    return main()

def BatchDirBuilder(material, orderSize):
    BatchDir = BatchFoldersDir + 'Batch #' + str(globalBatchCounter['BatchCounter']) + ' ' + today.strftime('%m-%d-%y') + ' ' + material + ' ' + orderSize + ' L0'
    globalBatchCounter['BatchCounter'] += 1
    #BatchDir = doesDirExist(material, orderSize)
    os.mkdir(BatchDir)
    print('| New Batch Folder: Batch #' + str(globalBatchCounter['BatchCounter']-1))
    print()
    return BatchDir

def BatchMaterialSelector():
    print('\n| Please select a material type: \n| 1. Smooth\n| 2. Woven')#\n| 3. Traditional (Don\'t.)')
    options = 1,2,3
    try:
        material = int(input('| Which material do you want to make? > '))
    except ValueError:
        print('\n| Please enter a number, not text.')
        return BatchMaterialSelector()
    while int(material) not in options:
        print('\n| Not a valid choice.')
        return BatchMaterialSelector()
    if material == 1:
        return 'Smooth'
    elif material == 2:
        return 'Woven'
    elif material == 3:
        print('Traditional? No.')
        return BatchMaterialSelector()
    else:
        print('| Invalid material choice. Returning.')
        return BatchMaterialSelector()

def BatchOrderSizeSelector():
    print('\n| Please select a material size: \n| 1. Sample\n| 2. Full')
    options = 1,2
    try:
        orderSize = int(input('| Which size do you want to make? > '))
    except ValueError:
        print('\n| Please enter a number, not text.')
        return BatchOrderSizeSelector()
    while int(orderSize) not in options:
        print('\n| Not a valid choice.')
        return BatchOrderSizeSelector()
    if orderSize == 1:
        return 'Sample'
    elif orderSize == 2:
        return 'Full'
    else:
        print('| Invalid size choice. Returning.')
        return BatchOrderSizeSelector()

def BatchMaterialLengthSelector():
    print('| Do you want to choose the length of material for each Batch, only the first, or consider all Batches full length? \n| 1. Each Batch\n| 2. Only the First\n| 3. All Full Length')
    options = 1,2,3
    try:
        orderSize = int(input('| Please make a selection: > '))
    except ValueError:
        print('\n| Please enter a number, not text.')
        return BatchMaterialLengthSelector()
    while int(orderSize) not in options:
        print('\n| Not a valid choice.')
        return BatchMaterialLengthSelector()
    if orderSize == 1:
        orderSize = 'Each'
    elif orderSize == 2:
        orderSize = 'First'
    elif orderSize == 3:
        orderSize = 'Full'
    else:
        print('| Invalid size choice. Returning.')
        return BatchMaterialLengthSelector()

def combineBatchFoldersController(material):
    loopCounter = 0
    while loopCounter < 3:
        loopCounter += 1
        findBatchFoldersToCombine(material)
        
def getMaterialLength(material):
    try:
        materialLength = int(input('\n| Combining Full ' + material + ' Batch folders.\n| Please enter a material length > ')) * 12
        return materialLength
    except ValueError:
        print('\n| Please enter a number, not text.')
        return getMaterialLength()

def findBatchFoldersToCombine(material):
  
    materialLength = getMaterialLength(material)

    for BatchFolder in glob.iglob(BatchFoldersDir + '*' + material + ' Full*'):
        BatchLength = float(BatchFolder.split('/')[-1].split(' ')[-1].split('L')[1])
        # Checks if Batch Order Length is less that 85% of the specified Material Length
        if BatchLength < (materialLength * .85):
            # If it is less than 85%, then it begins to iterate through other Batch folders to find ones to combine.
            for BatchFolderToJoin in glob.iglob(BatchFoldersDir + '*' + material + ' Full*'):
                BatchLengthToJoin = float(BatchFolderToJoin.split('/')[-1].split(' ')[-1].split('L')[1])
                # If the Batch folder and the potential folder to join are the same folder, skips that iteration.
                if BatchFolderToJoin == BatchFolder:
                    continue
                # If the total length of the Batch folder and the potential folder to join is less than the material length, iteratethrough Batch folder to join and moves each pdf to the original folder.
                if BatchLength + BatchLengthToJoin < materialLength:
                    combineBatchFolders(BatchFolder, BatchLength, BatchFolderToJoin, BatchLengthToJoin, material)

def combineBatchFolders(BatchFolder, BatchLength, BatchFolderToJoin, BatchLengthToJoin, material):
    combinedBatchDir = BatchDirBuilder(material, 'Full')

    for printPDF in glob.iglob(BatchFolder + '/*.pdf'):
        try:
            shutil.move(printPDF, combinedBatchDir)
        except shutil.Error:
            shutil.copy(printPDF, combinedBatchDir)
            try:
                os.remove(printPDF)
            except OSError:
                print('|> Could not remove', printPDF.split('/')[-1])
    for printPDF in glob.iglob(BatchFolderToJoin + '/*.pdf'):
        try:
            shutil.move(printPDF, combinedBatchDir)
        except shutil.Error:
            shutil.copy(printPDF, combinedBatchDir)
            try:
                os.remove(printPDF)
            except OSError:
                print('|> Could not remove', printPDF.split('/')[-1])

    evenLengths = []
    #oddLengths = ()
    newBatchLength = 0

    for printPDF in glob.iglob(combinedBatchDir + '/*.pdf'):
        printPDFLength = float(printPDF.split('/')[-1].split('-')[11].split('L')[1])
        evenLengths.append(printPDFLength)

    for lengthEntry in evenLengths:
        newBatchLength += lengthEntry
    
    newBatchName = combinedBatchDir.split('/')[6].split(' L')[0] + ' L' + str(newBatchLength)
    os.rename(combinedBatchDir, BatchFoldersDir + newBatchName)
    removeEmptyBatchFolders(False)
    return combineBatchFoldersController(material)

def removeEmptyBatchFolders(safe):
    for BatchFolder in glob.iglob(BatchFoldersDir + '*'):
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

def findOrdersForPrint2Ptv2(BatchDir, material, orderSize, materialLength):
    OTOrders = sortingDir + '1 - OT Orders/' + dirLookupDict[material] + dirLookupDict[orderSize]
    lateOrders = sortingDir + '2 - Late/' + dirLookupDict[material] + dirLookupDict[orderSize]
    todayOrders = sortingDir + '3 - Today/' + dirLookupDict[material] + dirLookupDict[orderSize] 
    futureOrders = sortingDir + '4 - Future/' + dirLookupDict[material] + dirLookupDict[orderSize]
    foldersToCheck2p = glob.glob(sortingDir + '*/' + dirLookupDict[material] + dirLookupDict[orderSize] + 'Repeat 2/*/*.pdf')
    curBatchDirLength = 0
    findOdd = False
    oddMatchHeight = 0
    loopCounter = 0
    while len(foldersToCheck2p) > 0:
        ### Come back to this later. For some reason, the folders to check variable doesn't update so python always evaluates it to more than 0 after it's initially created. I plugged in a loop counter to temporarily fix it.
        #foldersToCheck = glob.glob(sortingDir + '*/' + dirLookupDict[material] + dirLookupDict[orderSize] + 'Repeat 2/*/*.pdf')
        while (curBatchDirLength < (materialLength - 0.9)) and loopCounter < 1:
            for order in glob.iglob(lateOrders + 'Repeat 2/*/*.pdf'):
                orderLength = float(order.split('/')[-1].split('-')[11].split('L')[1])
                orderOdd = int(order.split('/')[-1].split('-')[9].split('Qty ')[1])
                orderHeight = float(order.split('/')[-1].split('-')[-1].split('H')[1].split('.pdf')[0])
                if orderLength > materialLength:
                    print('| Order is too large to add to this order.\n| File:', order.split('/')[-1])
                    print('| Continuing.')
                    continue
                elif (curBatchDirLength + orderLength) > (materialLength * 1.02):
                    print('| Order will exceed material length.\n| File:', order.split('/')[-1])
                    print('| Continuing.')
                    continue
                else:
                    if (findOdd == False) and (orderOdd % 2 == 0):
                        if (curBatchDirLength + orderLength) > (materialLength * 1.02):
                            print('| Order will exceed material length.\n| File:', order.split('/')[-1])
                            print('| Continuing.')
                            continue    
                        else:
                            try:
                                shutil.move(order, BatchDir)
                                curBatchDirLength += orderLength
                                findOdd = False
                            except shutil.Error:
                                shutil.copy(order, BatchDir)
                                curBatchDirLength += orderLength
                                findOdd = False
                                try:
                                    os.remove(order)
                                except OSError:
                                    print('|> Could not remove ' + order)
                            except FileNotFoundError:
                                print('|> Couldn\'t find order to move. \n|> File: ', order)
                    elif (findOdd == False) and (orderOdd % 2 == 1):
                        if (curBatchDirLength + orderLength) > (materialLength * 1.02):
                            print('| Order will exceed material length.\n| File:', order.split('/')[-1])
                            print('| Continuing.')
                            continue
                        else:
                            try:
                                shutil.move(order, BatchDir)
                                curBatchDirLength += orderLength
                                findOdd = True
                                oddMatchHeight = orderHeight
                            except shutil.Error:
                                shutil.copy(order, BatchDir)
                                curBatchDirLength += orderLength
                                findOdd = True
                                oddMatchHeight = orderHeight
                                try:
                                    os.remove(order)
                                except OSError:
                                    print('|> Could not remove ' + order)
                            except FileNotFoundError:
                                print('|> Couldn\'t find order to move. \n|> File: ', order)
                    elif (findOdd == True) and (orderOdd % 2 == 0):
                        continue
                    elif (findOdd == True) and (orderOdd % 2 == 1):
                        if oddMatchHeight != orderHeight:
                            continue
                        else:
                            if (curBatchDirLength + (orderLength - orderHeight)) > (materialLength * 1.02):
                                print('| Order will exceed material length.\n| File:', order.split('/')[-1])
                                print('| Continuing.')
                                continue
                            else:
                                try:
                                    shutil.move(order, BatchDir)
                                    curBatchDirLength += (orderLength - (orderHeight+0.5))
                                    findOdd = False
                                    oddMatchHeight = 0
                                except shutil.Error:
                                    shutil.copy(order, BatchDir)
                                    curBatchDirLength += (orderLength - (orderHeight+0.5))
                                    findOdd = False
                                    oddMatchHeight = 0
                                    try:
                                        os.remove(order)
                                    except OSError:
                                        print('|> Could not remove ' + order)
                                except FileNotFoundError:
                                    print('|> Couldn\'t find order to move. \n|> File: ', order)
            for order in glob.iglob(todayOrders + 'Repeat 2/*/*.pdf'):
                orderLength = float(order.split('/')[-1].split('-')[11].split('L')[1])
                orderOdd = int(order.split('/')[-1].split('-')[9].split('Qty ')[1])
                orderHeight = float(order.split('/')[-1].split('-')[-1].split('H')[1].split('.pdf')[0])
                if orderLength > materialLength:
                    print('| Order is too large to add to this order.\n| File:', order.split('/')[-1])
                    print('| Continuing.')
                    continue
                elif (curBatchDirLength + orderLength) > (materialLength * 1.02):
                    print('| Order will exceed material length.\n| File:', order.split('/')[-1])
                    print('| Continuing.')
                    continue
                else:
                    if (findOdd == False) and (orderOdd % 2 == 0):
                        if (curBatchDirLength + orderLength) > (materialLength * 1.02):
                            print('| Order will exceed material length.\n| File:', order.split('/')[-1])
                            print('| Continuing.')
                            continue    
                        else:
                            try:
                                shutil.move(order, BatchDir)
                                curBatchDirLength += orderLength
                                findOdd = False
                            except shutil.Error:
                                shutil.copy(order, BatchDir)
                                curBatchDirLength += orderLength
                                findOdd = False
                                try:
                                    os.remove(order)
                                except OSError:
                                    print('|> Could not remove ' + order)
                            except FileNotFoundError:
                                print('|> Couldn\'t find order to move. \n|> File: ', order)
                    elif (findOdd == False) and (orderOdd % 2 == 1):
                        if (curBatchDirLength + orderLength) > (materialLength * 1.02):
                            print('| Order will exceed material length.\n| File:', order.split('/')[-1])
                            print('| Continuing.')
                            continue
                        else:
                            try:
                                shutil.move(order, BatchDir)
                                curBatchDirLength += orderLength
                                findOdd = True
                                oddMatchHeight = orderHeight
                            except shutil.Error:
                                shutil.copy(order, BatchDir)
                                curBatchDirLength += orderLength
                                findOdd = True
                                oddMatchHeight = orderHeight
                                try:
                                    os.remove(order)
                                except OSError:
                                    print('|> Could not remove ' + order)
                            except FileNotFoundError:
                                print('|> Couldn\'t find order to move. \n|> File: ', order)
                    elif (findOdd == True) and (orderOdd % 2 == 0):
                        continue
                    elif (findOdd == True) and (orderOdd % 2 == 1):
                        if oddMatchHeight != orderHeight:
                            continue
                        else:
                            if (curBatchDirLength + (orderLength - orderHeight)) > (materialLength * 1.02):
                                print('| Order will exceed material length.\n| File:', order.split('/')[-1])
                                print('| Continuing.')
                                continue
                            else:
                                try:
                                    shutil.move(order, BatchDir)
                                    curBatchDirLength += (orderLength - (orderHeight+0.5))
                                    findOdd = False
                                    oddMatchHeight = 0
                                except shutil.Error:
                                    shutil.copy(order, BatchDir)
                                    curBatchDirLength += (orderLength - (orderHeight+0.5))
                                    findOdd = False
                                    oddMatchHeight = 0
                                    try:
                                        os.remove(order)
                                    except OSError:
                                        print('|> Could not remove ' + order)
                                except FileNotFoundError:
                                    print('|> Couldn\'t find order to move. \n|> File: ', order)        
            for order in glob.iglob(futureOrders + 'Repeat 2/*/*.pdf'):
                orderLength = float(order.split('/')[-1].split('-')[11].split('L')[1])
                orderOdd = int(order.split('/')[-1].split('-')[9].split('Qty ')[1])
                orderHeight = float(order.split('/')[-1].split('-')[-1].split('H')[1].split('.pdf')[0])
                if orderLength > materialLength:
                    print('| Order is too large to add to this order.\n| File:', order.split('/')[-1])
                    print('| Continuing.')
                    continue
                elif (curBatchDirLength + orderLength) > (materialLength * 1.02):
                    print('| Order will exceed material length.\n| File:', order.split('/')[-1])
                    print('| Continuing.')
                    continue
                else:
                    if (findOdd == False) and (orderOdd % 2 == 0):
                        if (curBatchDirLength + orderLength) > (materialLength * 1.02):
                            print('| Order will exceed material length.\n| File:', order.split('/')[-1])
                            print('| Continuing.')
                            continue    
                        else:
                            try:
                                shutil.move(order, BatchDir)
                                curBatchDirLength += orderLength
                                findOdd = False
                            except shutil.Error:
                                shutil.copy(order, BatchDir)
                                curBatchDirLength += orderLength
                                findOdd = False
                                try:
                                    os.remove(order)
                                except OSError:
                                    print('|> Could not remove ' + order)
                            except FileNotFoundError:
                                print('|> Couldn\'t find order to move. \n|> File: ', order)
                    elif (findOdd == False) and (orderOdd % 2 == 1):
                        if (curBatchDirLength + orderLength) > (materialLength * 1.02):
                            print('| Order will exceed material length.\n| File:', order.split('/')[-1])
                            print('| Continuing.')
                            continue
                        else:
                            try:
                                shutil.move(order, BatchDir)
                                curBatchDirLength += orderLength
                                findOdd = True
                                oddMatchHeight = orderHeight
                            except shutil.Error:
                                shutil.copy(order, BatchDir)
                                curBatchDirLength += orderLength
                                findOdd = True
                                oddMatchHeight = orderHeight
                                try:
                                    os.remove(order)
                                except OSError:
                                    print('|> Could not remove ' + order)
                            except FileNotFoundError:
                                print('|> Couldn\'t find order to move. \n|> File: ', order)
                    elif (findOdd == True) and (orderOdd % 2 == 0):
                        continue
                    elif (findOdd == True) and (orderOdd % 2 == 1):
                        if oddMatchHeight != orderHeight:
                            continue
                        else:
                            if (curBatchDirLength + (orderLength - orderHeight)) > (materialLength * 1.02):
                                print('| Order will exceed material length.\n| File:', order.split('/')[-1])
                                print('| Continuing.')
                                continue
                            else:
                                try:
                                    shutil.move(order, BatchDir)
                                    curBatchDirLength += (orderLength - (orderHeight+0.5))
                                    findOdd = False
                                    oddMatchHeight = 0
                                except shutil.Error:
                                    shutil.copy(order, BatchDir)
                                    curBatchDirLength += (orderLength - (orderHeight+0.5))
                                    findOdd = False
                                    oddMatchHeight = 0
                                    try:
                                        os.remove(order)
                                    except OSError:
                                        print('|> Could not remove ' + order)
                                except FileNotFoundError:
                                    print('|> Couldn\'t find order to move. \n|> File: ', order)
                    else:
                        try:
                            shutil.move(order, BatchDir)
                            curBatchDirLength += (orderLength - (orderHeight+0.5))
                            findOdd = False
                            oddMatchHeight = 0
                        except shutil.Error:
                            shutil.copy(order, BatchDir)
                            curBatchDirLength += (orderLength - (orderHeight+0.5))
                            findOdd = False
                            oddMatchHeight = 0
                            try:
                                os.remove(order)
                            except OSError:
                                print('|> Could not remove ' + order)
                        except FileNotFoundError:
                            print('|> Couldn\'t find order to move. \n|> File: ', order)
            loopCounter += 1
        else:
            newBatchName = BatchDir.split('/')[6].split(' L')[0] + ' L' + str(curBatchDirLength)
            os.rename(BatchDir, BatchFoldersDir + newBatchName)
            print('\n| Batch Finished.\n| Batch Folder: ', newBatchName, '\n| Length:', str(round(curBatchDirLength/12, 2)), 'feet (' + str(curBatchDirLength), 'inches)')
            curBatchDirLength = 0
            BatchDir = BatchDirBuilder(material, orderSize)
            #materialLength = input('| Please input your material length. > ')
            return findOrdersForPrint2Ptv2(BatchDir, material, orderSize, int(materialLength))

def findOrdersForPrint4Ptv2(BatchDir, material, orderSize, materialLength):
    OTOrders = sortingDir + '1 - OT Orders/' + dirLookupDict[material] + dirLookupDict[orderSize]
    lateOrders = sortingDir + '2 - Late/' + dirLookupDict[material] + dirLookupDict[orderSize]
    todayOrders = sortingDir + '3 - Today/' + dirLookupDict[material] + dirLookupDict[orderSize] 
    futureOrders = sortingDir + '4 - Future/' + dirLookupDict[material] + dirLookupDict[orderSize]
    foldersToCheckN2p = glob.glob(sortingDir + '*/' + dirLookupDict[material] + dirLookupDict[orderSize] + 'Repeat Non-2/*/*.pdf')
    curBatchDirLength = 0
    findOdd = False
    oddMatchHeight = 0
    loopCounter = 0
    while len(foldersToCheckN2p) > 0:
        ### Come back to this later. For some reason, the folders to check variable doesn't update so python always evaluates it to more than 0 after it's initially created. I plugged in a loop counter to temporarily fix it.
        #foldersToCheck = glob.glob(sortingDir + '*/' + dirLookupDict[material] + dirLookupDict[orderSize] + 'Repeat 2/*/*.pdf')
        while (curBatchDirLength < (materialLength - 0.9)) and loopCounter < 1:
            for order in glob.iglob(lateOrders + 'Repeat Non-2/*/*.pdf'):
                orderLength = float(order.split('/')[-1].split('-')[11].split('L')[1])
                orderOdd = int(order.split('/')[-1].split('-')[9].split('Qty ')[1])
                orderHeight = float(order.split('/')[-1].split('-')[-1].split('H')[1].split('.pdf')[0])
                if orderLength > materialLength:
                    print('| Order is too large to add to this order.\n| File:', order.split('/')[-1])
                    print('| Continuing.')
                    continue
                elif (curBatchDirLength + orderLength) > (materialLength * 1.02):
                    print('| Order will exceed material length.\n| File:', order.split('/')[-1])
                    print('| Continuing.')
                    continue
                else:
                    if (findOdd == False) and (orderOdd % 2 == 0):
                        if (curBatchDirLength + orderLength) > (materialLength * 1.02):
                            print('| Order will exceed material length.\n| File:', order.split('/')[-1])
                            print('| Continuing.')
                            continue    
                        else:
                            try:
                                shutil.move(order, BatchDir)
                                curBatchDirLength += orderLength
                                findOdd = False
                            except shutil.Error:
                                shutil.copy(order, BatchDir)
                                curBatchDirLength += orderLength
                                findOdd = False
                                try:
                                    os.remove(order)
                                except OSError:
                                    print('|> Could not remove ' + order)
                            except FileNotFoundError:
                                print('|> Couldn\'t find order to move. \n|> File: ', order)
                    elif (findOdd == False) and (orderOdd % 2 == 1):
                        if (curBatchDirLength + orderLength) > (materialLength * 1.02):
                            print('| Order will exceed material length.\n| File:', order.split('/')[-1])
                            print('| Continuing.')
                            continue
                        else:
                            try:
                                shutil.move(order, BatchDir)
                                curBatchDirLength += orderLength
                                findOdd = True
                                oddMatchHeight = orderHeight
                            except shutil.Error:
                                shutil.copy(order, BatchDir)
                                curBatchDirLength += orderLength
                                findOdd = True
                                oddMatchHeight = orderHeight
                                try:
                                    os.remove(order)
                                except OSError:
                                    print('|> Could not remove ' + order)
                            except FileNotFoundError:
                                print('|> Couldn\'t find order to move. \n|> File: ', order)
                    elif (findOdd == True) and (orderOdd % 2 == 0):
                        continue
                    elif (findOdd == True) and (orderOdd % 2 == 1):
                        if oddMatchHeight != orderHeight:
                            continue
                        else:
                            if (curBatchDirLength + (orderLength - orderHeight)) > (materialLength * 1.02):
                                print('| Order will exceed material length.\n| File:', order.split('/')[-1])
                                print('| Continuing.')
                                continue
                            else:
                                try:
                                    shutil.move(order, BatchDir)
                                    curBatchDirLength += (orderLength - (orderHeight+0.5))
                                    findOdd = False
                                    oddMatchHeight = 0
                                except shutil.Error:
                                    shutil.copy(order, BatchDir)
                                    curBatchDirLength += (orderLength - (orderHeight+0.5))
                                    findOdd = False
                                    oddMatchHeight = 0
                                    try:
                                        os.remove(order)
                                    except OSError:
                                        print('|> Could not remove ' + order)
                                except FileNotFoundError:
                                    print('|> Couldn\'t find order to move. \n|> File: ', order)
            for order in glob.iglob(todayOrders + 'Repeat Non-2/*/*.pdf'):
                orderLength = float(order.split('/')[-1].split('-')[11].split('L')[1])
                orderOdd = int(order.split('/')[-1].split('-')[9].split('Qty ')[1])
                orderHeight = float(order.split('/')[-1].split('-')[-1].split('H')[1].split('.pdf')[0])
                if orderLength > materialLength:
                    print('| Order is too large to add to this order.\n| File:', order.split('/')[-1])
                    print('| Continuing.')
                    continue
                elif (curBatchDirLength + orderLength) > (materialLength * 1.02):
                    print('| Order will exceed material length.\n| File:', order.split('/')[-1])
                    print('| Continuing.')
                    continue
                else:
                    if (findOdd == False) and (orderOdd % 2 == 0):
                        if (curBatchDirLength + orderLength) > (materialLength * 1.02):
                            print('| Order will exceed material length.\n| File:', order.split('/')[-1])
                            print('| Continuing.')
                            continue    
                        else:
                            try:
                                shutil.move(order, BatchDir)
                                curBatchDirLength += orderLength
                                findOdd = False
                            except shutil.Error:
                                shutil.copy(order, BatchDir)
                                curBatchDirLength += orderLength
                                findOdd = False
                                try:
                                    os.remove(order)
                                except OSError:
                                    print('|> Could not remove ' + order)
                            except FileNotFoundError:
                                print('|> Couldn\'t find order to move. \n|> File: ', order)
                    elif (findOdd == False) and (orderOdd % 2 == 1):
                        if (curBatchDirLength + orderLength) > (materialLength * 1.02):
                            print('| Order will exceed material length.\n| File:', order.split('/')[-1])
                            print('| Continuing.')
                            continue
                        else:
                            try:
                                shutil.move(order, BatchDir)
                                curBatchDirLength += orderLength
                                findOdd = True
                                oddMatchHeight = orderHeight
                            except shutil.Error:
                                shutil.copy(order, BatchDir)
                                curBatchDirLength += orderLength
                                findOdd = True
                                oddMatchHeight = orderHeight
                                try:
                                    os.remove(order)
                                except OSError:
                                    print('|> Could not remove ' + order)
                            except FileNotFoundError:
                                print('|> Couldn\'t find order to move. \n|> File: ', order)
                    elif (findOdd == True) and (orderOdd % 2 == 0):
                        continue
                    elif (findOdd == True) and (orderOdd % 2 == 1):
                        if oddMatchHeight != orderHeight:
                            continue
                        else:
                            if (curBatchDirLength + (orderLength - orderHeight)) > (materialLength * 1.02):
                                print('| Order will exceed material length.\n| File:', order.split('/')[-1])
                                print('| Continuing.')
                                continue
                            else:
                                try:
                                    shutil.move(order, BatchDir)
                                    curBatchDirLength += (orderLength - (orderHeight+0.5))
                                    findOdd = False
                                    oddMatchHeight = 0
                                except shutil.Error:
                                    shutil.copy(order, BatchDir)
                                    curBatchDirLength += (orderLength - (orderHeight+0.5))
                                    findOdd = False
                                    oddMatchHeight = 0
                                    try:
                                        os.remove(order)
                                    except OSError:
                                        print('|> Could not remove ' + order)
                                except FileNotFoundError:
                                    print('|> Couldn\'t find order to move. \n|> File: ', order)        
            for order in glob.iglob(futureOrders + 'Repeat Non-2/*/*.pdf'):
                orderLength = float(order.split('/')[-1].split('-')[11].split('L')[1])
                orderOdd = int(order.split('/')[-1].split('-')[9].split('Qty ')[1])
                orderHeight = float(order.split('/')[-1].split('-')[-1].split('H')[1].split('.pdf')[0])
                if orderLength > materialLength:
                    print('| Order is too large to add to this order.\n| File:', order.split('/')[-1])
                    print('| Continuing.')
                    continue
                elif (curBatchDirLength + orderLength) > (materialLength * 1.02):
                    print('| Order will exceed material length.\n| File:', order.split('/')[-1])
                    print('| Continuing.')
                    continue
                else:
                    if (findOdd == False) and (orderOdd % 2 == 0):
                        if (curBatchDirLength + orderLength) > (materialLength * 1.02):
                            print('| Order will exceed material length.\n| File:', order.split('/')[-1])
                            print('| Continuing.')
                            continue    
                        else:
                            try:
                                shutil.move(order, BatchDir)
                                curBatchDirLength += orderLength
                                findOdd = False
                            except shutil.Error:
                                shutil.copy(order, BatchDir)
                                curBatchDirLength += orderLength
                                findOdd = False
                                try:
                                    os.remove(order)
                                except OSError:
                                    print('|> Could not remove ' + order)
                            except FileNotFoundError:
                                print('|> Couldn\'t find order to move. \n|> File: ', order)
                    elif (findOdd == False) and (orderOdd % 2 == 1):
                        if (curBatchDirLength + orderLength) > (materialLength * 1.02):
                            print('| Order will exceed material length.\n| File:', order.split('/')[-1])
                            print('| Continuing.')
                            continue
                        else:
                            try:
                                shutil.move(order, BatchDir)
                                curBatchDirLength += orderLength
                                findOdd = True
                                oddMatchHeight = orderHeight
                            except shutil.Error:
                                shutil.copy(order, BatchDir)
                                curBatchDirLength += orderLength
                                findOdd = True
                                oddMatchHeight = orderHeight
                                try:
                                    os.remove(order)
                                except OSError:
                                    print('|> Could not remove ' + order)
                            except FileNotFoundError:
                                print('|> Couldn\'t find order to move. \n|> File: ', order)
                    elif (findOdd == True) and (orderOdd % 2 == 0):
                        continue
                    elif (findOdd == True) and (orderOdd % 2 == 1):
                        if oddMatchHeight != orderHeight:
                            continue
                        else:
                            if (curBatchDirLength + (orderLength - orderHeight)) > (materialLength * 1.02):
                                print('| Order will exceed material length.\n| File:', order.split('/')[-1])
                                print('| Continuing.')
                                continue
                            else:
                                try:
                                    shutil.move(order, BatchDir)
                                    curBatchDirLength += (orderLength - (orderHeight+0.5))
                                    findOdd = False
                                    oddMatchHeight = 0
                                except shutil.Error:
                                    shutil.copy(order, BatchDir)
                                    curBatchDirLength += (orderLength - (orderHeight+0.5))
                                    findOdd = False
                                    oddMatchHeight = 0
                                    try:
                                        os.remove(order)
                                    except OSError:
                                        print('|> Could not remove ' + order)
                                except FileNotFoundError:
                                    print('|> Couldn\'t find order to move. \n|> File: ', order)
                    else:
                        try:
                            shutil.move(order, BatchDir)
                            curBatchDirLength += (orderLength - (orderHeight+0.5))
                            findOdd = False
                            oddMatchHeight = 0
                        except shutil.Error:
                            shutil.copy(order, BatchDir)
                            curBatchDirLength += (orderLength - (orderHeight+0.5))
                            findOdd = False
                            oddMatchHeight = 0
                            try:
                                os.remove(order)
                            except OSError:
                                print('|> Could not remove ' + order)
                        except FileNotFoundError:
                            print('|> Couldn\'t find order to move. \n|> File: ', order)
            loopCounter += 1
        else:
            newBatchName = BatchDir.split('/')[6].split(' L')[0] + ' L' + str(curBatchDirLength)
            os.rename(BatchDir, BatchFoldersDir + newBatchName)
            print('\n| Batch Finished.\n| Batch Folder: ', newBatchName, '\n| Length:', str(round(curBatchDirLength/12, 2)), 'feet (' + str(curBatchDirLength), 'inches)')
            BatchDir = BatchDirBuilder(material, orderSize)
            #materialLength = input('| Please input your material length. > ')
            return findOrdersForPrint4Ptv2(BatchDir, material, orderSize, int(materialLength))

def checkRepeatSize():
    for printPDF in glob.iglob(downloadDir + '*.pdf'):
        printPDFFull = printPDF.split('/')[-1].split('-')[7]
        printPDFrepeat = int(printPDF.split('/')[-1].split('-')[8].split('Rp ')[1])
        if printPDFFull == 'Full':
            if printPDFrepeat % 2 == 1:
                try:
                    shutil.move(printPDF, needsAttention)
                    print('| File has an odd repeat and has been moved to 4 Needs Attention')
                    print('| File:', printPDF.split('/')[-1])
                except shutil.Error:
                    shutil.copy(printPDF, needsAttention)
                    try:
                        os.remove(printPDF)
                    except OSError:
                        print('|> Could not successfully remove file.')
                        print('|> File:', printPDF)
                except FileNotFoundError:
                    print('| Couldn\'t find the following file.')
                    print('| File:', printPDF)
            elif printPDFrepeat == 2:
                continue
            elif printPDFrepeat > 2:
                try:
                    cropMultiPanelPDFs(printPDF)
                except utils.PdfReadError:
                    print('| Couldn\'t crop the panels for the following order. Please check non-repeat 2 folders.')
                    continue

def cropMultiPanelPDFs(printPDFToSplit):
    orderDict = {
        'fileName':printPDFToSplit.split('.pdf')[0],
        'orderNumber': printPDFToSplit.split('/')[-1].split('-')[0],
        'orderItem': printPDFToSplit.split('-')[1],
        'orderDueDate': datetime.date(datetime.strptime(printPDFToSplit.split('(')[1].split(')')[0], '%Y-%m-%d')),
        'shipVia': printPDFToSplit.split('-')[5],
        'material': printPDFToSplit.split('-')[6],
        'orderSize': printPDFToSplit.split('-')[7],
        'repeat': int(printPDFToSplit.split('-')[8].split('Rp ')[1]),
        'repeatPanels': int(int(printPDFToSplit.split('-')[8].split('Rp ')[1]) / 2),
        'quantity': int(printPDFToSplit.split('-')[9].split('Qty ')[1]),
        'oddOrEven': int(printPDFToSplit.split('-')[9].split('Qty ')[1]) % 2,
        'templateName': printPDFToSplit.split('-')[10],
        'orderLength': float(printPDFToSplit.split('-')[11].split('L')[1]),
        'orderWidth': int(printPDFToSplit.split('-')[12].split('W')[1]),
        'orderHeight': float(printPDFToSplit.split('-')[13].split('H')[1].split('.pdf')[0]),
        'multiPagePDFs' : [],
        'PDFPanelsToCombine' : [],
        }
    
    orderDict['CroppedPDFName'] = orderDict['fileName'].split(orderDict['templateName'])[0] + orderDict['templateName'] + ' Split' + orderDict['fileName'].split(orderDict['templateName'])[1] + '.pdf'

    print('| Working file\n| ', printPDFToSplit)
    for entry in orderDict:
        print('|    ', orderDict[entry])

    os.chdir(downloadDir)
    for page in range(orderDict['repeatPanels']):
        writer = PdfFileWriter()
        inputPDF = open(printPDFToSplit,'rb')
        cropPDF = PdfFileReader(inputPDF)
        page = cropPDF.getPage(0)
        print('| File:', printPDFToSplit.split('/')[-1])
        print('| Width:', (page.mediaBox.getUpperRight_x())/72, 'inches, Height:', (page.mediaBox.getUpperRight_y()/72))
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
            printPDFName = downloadDir + orderDict['orderNumber'] + '-' + orderDict['orderItem'] + '-' + str(cropCount + 1) + '.pdf'
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
        print('\n| File:', PDF, '\n| File has %d pages.' % printPDF.getNumPages())

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
    
    for PDF in orderDict['multiPagePDFs']:
        os.remove(PDF)
    
    print(orderDict['PDFPanelsToCombine'])

    splitAndCombinedPDF = combineSplitPDFS(orderDict['PDFPanelsToCombine'], orderDict['CroppedPDFName'])

    print('| File has been split apart, cropped, and recombined.\n| File:', splitAndCombinedPDF.split('/')[-1])

    if Path(calderaDir + '# Past Orders/Original Files/').exists() == False:
        os.mkdir(calderaDir + '# Past Orders/Original Files')
    
    storageDir = calderaDir + '# Past Orders/Original Files/'
    
    try:
        shutil.move(printPDFToSplit, storageDir)
    except shutil.Error:
        shutil.copy(printPDFToSplit, storageDir)
        os.remove(printPDFToSplit)

    for PDF in orderDict['PDFPanelsToCombine']:
        os.remove(PDF)

def combineSplitPDFS(listOfPDFs, saveLocation):
    masterPDF = PdfFileMerger()

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

def possibleOrders():
    OTOrders = glob.iglob(sortingDir + '1 - OT Orders/' + '**/*.pdf', recursive=True)
    lateOrders = glob.iglob(sortingDir + '2 - Late/' + '**/*.pdf', recursive=True)
    todayOrders = glob.iglob(sortingDir + '3 - Today/' + '**/*.pdf', recursive=True) 
    futureOrders = glob.iglob(sortingDir + '4 - Future/' + '**/*.pdf', recursive=True)
    
    possibleOrders = {
            'Wv' : {
                'orderTroubles' : [],
                'lateOrders' : [],
                'todaysOrders' : [],
                'futureOrders' : [],
            },
            'Sm' : {
                'orderTroubles' : [],
                'lateOrders' : [],
                'todaysOrders' : [],
                'futureOrders' : [],
            },
            'Tr' : {
                'orderTroubles' : [],
                'lateOrders' : [],
                'todaysOrders' : [],
                'futureOrders' : [],
            },
        }

    for printPDF in OTOrders:
        pdfMaterial = printPDF.split('/')[-1].split('-')[6]
        possibleOrders[pdfMaterial]['orderTroubles'].append(printPDF)
    for printPDF in lateOrders:
        pdfMaterial = printPDF.split('/')[-1].split('-')[6]
        possibleOrders[pdfMaterial]['lateOrders'].append(printPDF)
    for printPDF in todayOrders:
        pdfMaterial = printPDF.split('/')[-1].split('-')[6]
        possibleOrders[pdfMaterial]['todaysOrders'].append(printPDF)
    for printPDF in futureOrders:
        pdfMaterial = printPDF.split('/')[-1].split('-')[6]
        possibleOrders[pdfMaterial]['futureOrders'].append(printPDF)
            
    return possibleOrders

def buildBatchController(material, materialLength):
    # OTOrders = sortingDir + '1 - OT Orders/' + dirLookupDict[material] + dirLookupDict[orderSize]
    # lateOrders = sortingDir + '2 - Late/' + dirLookupDict[material] + dirLookupDict[orderSize]
    # todayOrders = sortingDir + '3 - Today/' + dirLookupDict[material] + dirLookupDict[orderSize] 
    # futureOrders = sortingDir + '4 - Future/' + dirLookupDict[material] + dirLookupDict[orderSize]

    BatchLength = 0
    lengthForFull = materialLength * 0.85
    
    readyToPrint = possibleOrders()

    BatchDir = BatchFoldersDir + 'Batch Being Built'
    os.mkdir(BatchDir)

    if (len(orderTroubles) > 0) and (len(lateOrders) > 0):
        print('| Creating Batches for Order Troubles and Late Orders.')
        mainBuildBatchLoop(orderTroubles, lengthForFull, BatchDir, material)  




    '''
    Lets do some pseudo code!
    First, get the total length of material (let's say 150 for smooth)
    then, look for full 2' repeat orders 
    add them to the current Batch until the Batch length is 
    repeat until Batch is 85% of material length OR until there are no more full, 2' repeat orders
    once 85% of material length is exceeded, search for 13% worth of samples OR until there are no additional samples
    once that 13% has been met or exceeded, add 5% of color guides.
    Once that 5% has been met, complete the Batch.

    '''

    # findFull2pOrders()
    # findSampleOrders()
    # findColorGuides()

    return

def mainBuildBatchLoop(listOfPdfsToBatch, adjustedMaterialLength, BatchDir):
    curBatchDirLength = 0
    findOdd = False
    oddMatchHeight = 0
    loopCounter = 0
    
    while (curBatchDirLength < adjustedMaterialLength) and (loopCounter < 1):
        for printPDF in listOfPdfsToBatch:
            pdfName = printPDF.split('/'[-1]).split('.pdf')[0]
            friendlyPdfName = printPDF.split('-')[0], printPDF.split('-')[10], printPDF.split('-')[1] 
            pdfLength = float(pdfName.split('-')[11].split('L')[1])
            pdfOdd = int(pdfName.split('-')[9].split('Qty ')[1]) % 2
            pdfHeight = float(pdfName.split('-')[-1].split('H')[1])
            if (curBatchDirLength + pdfLength) > (adjustedMaterialLength * 1.02):
                print('| PDF will exceed material length.\n| PDF:', friendlyPdfName)
                print()
            else:
                if (findOdd == False) and (pdfOdd == 0):
                    success = tryToMovePDF(printPDF, BatchDir, friendlyPdfName, pdfLength)
                    if success == True:
                        findOdd = False
                elif (findOdd == False) and (pdfOdd == 1):
                    success = tryToMovePDF(printPDF, BatchDir, friendlyPdfName, pdfLength)
                    if success == True:
                        findOdd = True
                        oddMatchHeight = pdfHeight
                elif (findOdd == True) and (pdfOdd == 0):
                    continue
                elif (findOdd == True) and (pdfOdd == 1):
                    if oddMatchHeight != pdfHeight:
                        continue
                    else:
                        success = tryToMovePDF(printPDF, BatchDir, friendlyPdfName, pdfLength)
                        if success == True:
                            findOdd = False
                            oddMatchHeight = 0
        loopCounter += 1

def tryToMovePDF(printPDF, BatchDir, friendlyPdfName, pdfLength):
    try:
        shutil.move(printPDF, BatchDir)
        curBatchDirLength += pdfLength
        return True
    except shutil.Error:
        shutil.copy(printPDF, BatchDir)
        curBatchDirLength += pdfLength
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

startupChecks()
main()
## End