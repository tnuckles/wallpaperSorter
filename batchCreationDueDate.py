#!usr/bin/env python

import os, shutil, math, datetime, glob
from PyPDF2 import utils
from datetime import  datetime


import wallpaperSorterVariables as gv
import getPdfData as getPdf
import pdf_splitter
import add_macos_tag as set_tag

today = datetime.today()

# Definitions

def batchCreationController():
    material, material_length, care_about_length = getMaterialAndRollLength()
    full_pdfs_to_batch, samplePdfsToBatch = getListOfPdfs(material)
    sort_pdfs_by_length(full_pdfs_to_batch)
    total_full_length, total_sample_length = getTotalLengthOfPdfs(full_pdfs_to_batch, samplePdfsToBatch)
    if care_about_length == True:
        if (total_full_length + total_sample_length) > ((material_length * .8)):
            length_for_full = decide_full_sample_split(total_full_length, total_sample_length, material_length)
            new_batch_dict = build_batch_list(material_length, length_for_full, full_pdfs_to_batch, samplePdfsToBatch, total_sample_length)
            make_batch_folder(new_batch_dict, material)
        else:
            print('| Remaning PDFs will not fill more than 80' + "%" + ' of a roll. Waiting for new orders to make a batch.')
    elif care_about_length == False:
        length_for_full = decide_full_sample_split(total_full_length, total_sample_length, material_length)
        new_batch_dict = build_batch_list(material_length, length_for_full, full_pdfs_to_batch, samplePdfsToBatch, total_sample_length)
        make_batch_folder(new_batch_dict, material)
    
    return batchCreationController()

def getMaterialAndRollLength():
    options = 1,2,3,4,5,6
    print('\n| Specify material and roll length:')
    print('| 1. Smooth, 150 Feet')
    print('| 2. Woven, 100 Feet')
    print('| 3. Smooth, Custom Length')
    print('| 4. Woven, Custom Length')
    print('| 5. Smooth, 150 Feet, Disregard Length')
    print('| 6. Woven, 100 Feet, Disregard Length')
    try:
        command = int(input('\n| Command > '))
    except ValueError:
        print('\n| Please enter a whole number, not text.')
    while int(command) not in options:
        print('\n| Not a valid choice.')
        return getMaterialAndRollLength()
    if command == 1:
        confirm = confirmBatch('Smooth', 144)
        if confirm == True:
            return 'Smooth', 144*12, True
        else:
            return getMaterialAndRollLength()
    elif command == 2:
        confirm = confirmBatch('Woven', 94)
        if confirm == True:
            return 'Woven', 94*12, True
        else:
            return getMaterialAndRollLength()
    elif command == 3:
        try:
            length = int(input('\n| Please enter your Smooth length in feet > '))
        except ValueError:
            print('| Invalid input.')
            return getMaterialAndRollLength()
        confirm = confirmBatch('Smooth', length)
        if confirm:
            return 'Smooth', length
        else:
            return getMaterialAndRollLength()
    elif command == 4:
        try:
            length = int(input('\n| Please enter your Woven length in feet > '))
        except ValueError:
            print('| Invalid input.')
            return getMaterialAndRollLength()
        confirm = confirmBatch('Woven', length)
        if confirm:
            return 'Woven', length
        else:
            return getMaterialAndRollLength()
    elif command == 5:
        confirm = confirmBatch('Smooth', 144)
        if confirm == True:
            return 'Smooth', 144*12, False
        else:
            return getMaterialAndRollLength()
    elif command == 6:
        confirm = confirmBatch('Woven', 94)
        if confirm == True:
            return 'Woven', 94*12, False
        else:
            return getMaterialAndRollLength()

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

def getListOfPdfs(material):
    pdf_material = gv.dirLookupDict[material]
    fullPdfsToBatch = {
        'OTOrders' : glob.glob(gv.sortingDir + '1 - OT Orders/' + pdf_material + 'Full/**/*.pdf', recursive=True),
        'lateOrders' : glob.glob(gv.sortingDir + '2 - Late/' + pdf_material + 'Full/**/*.pdf', recursive=True),
        'todayOrders' : glob.glob(gv.sortingDir + '3 - Today/' + pdf_material + 'Full/**/*.pdf', recursive=True),
        'futureOrders' : glob.glob(gv.sortingDir + '4 - Future/' + pdf_material + 'Full/**/*.pdf', recursive=True),
        }
    samplePdfsToBatch = {
        'OTOrders' : glob.glob(gv.sortingDir + '1 - OT Orders/' + pdf_material + 'Sample/*.pdf', recursive=True),
        'lateOrders' : glob.glob(gv.sortingDir + '2 - Late/' + pdf_material + 'Sample/*.pdf', recursive=True),
        'todayOrders' : glob.glob(gv.sortingDir + '3 - Today/' + pdf_material + 'Sample/*.pdf', recursive=True),
        'futureOrders' : glob.glob(gv.sortingDir + '4 - Future/' + pdf_material + 'Sample/*.pdf', recursive=True),
        }
    return fullPdfsToBatch, samplePdfsToBatch

def sort_pdfs_by_length(pdf_array):
    for due_date in pdf_array:
        list_to_sort = []
        sorted_list = []
        for print_pdf in pdf_array[due_date]:
            pdf_length = getPdf.length(print_pdf)
            list_to_sort.append((pdf_length, print_pdf))
        list_to_sort.sort(reverse=True, key=lambda pdf: pdf[0])
        pdf_array[due_date] = list_to_sort
        for print_pdf in pdf_array[due_date]:
            sorted_list.append(print_pdf[1])
        pdf_array[due_date] = sorted_list
    return pdf_array

def getTotalLengthOfPdfs(fullPdfsToBatch, samplePdfsToBatch):  
    fullLength = 0
    sampleLength = 0
    for dueDate in fullPdfsToBatch:
        for printPdf in fullPdfsToBatch[dueDate]:
            fullLength += getPdf.length(printPdf)
    for dueDate in samplePdfsToBatch:
        for printPdf in samplePdfsToBatch[dueDate]:
            sampleLength += getPdf.length(printPdf)
    sampleLength = math.floor(sampleLength / 2)
    return fullLength, sampleLength

def decide_full_sample_split(full_length, sample_length, material_length):
    percent_length_for_full = .80
    
    if full_length < (material_length * percent_length_for_full):
        percent_length_for_full = 1 - round(full_length / material_length, 2)
        return percent_length_for_full
    elif sample_length > material_length * .30:
        return percent_length_for_full
    elif sample_length == 0:
        percent_length_for_full = 1
        return percent_length_for_full
    else:
        percent_length_for_full = 1 - round(sample_length / material_length, 2)
        return percent_length_for_full

def add_fill_ins(new_batch_dict):
    color_guides = gv.calderaDir + 'z_Storage/Utility/LvD Color Chart Rotated.pdf'
    roll_stickers = gv.calderaDir + 'z_Storage/Utility/LvD Roll-Stickers Rotated.pdf'
    batch_length = new_batch_dict['length']
    batch_list = new_batch_dict['list']
    
    batch_list.append(color_guides)
    batch_length += 9.5
    batch_list.append(color_guides)
    batch_list.append(color_guides)
    batch_length += 9.5
    batch_list.append(color_guides)
    batch_list.append(color_guides)
    batch_length += 9.5
    batch_list.append(roll_stickers)
    return new_batch_dict

def tryToMovePDF(printPDF, BatchDir, friendlyPdfName):
    try:
        shutil.move(printPDF, BatchDir + '/')
        return
    except shutil.Error:
        shutil.copy(printPDF, BatchDir)
        try:
            os.remove(printPDF)
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

def build_batch_list(material_length, length_for_full, full_pdfs_to_batch, samplePdfsToBatch, total_sample_length):
    new_batch = {
        'list_of_pdfs': [],
        'batch_length': 0
    }

    length_for_full = math.floor(material_length * length_for_full)
    length_for_samples = 0
    find_odd = False
    odd_match_height = 0
    sample_odd_count = True
    batch_length = 0
    batch_list = []
    loop_counter = 0

    while (batch_length < length_for_full) and (loop_counter == 0):
        for due_date in full_pdfs_to_batch:
            for print_pdf in full_pdfs_to_batch[due_date]:
                pdf_length = getPdf.length(print_pdf)
                pdf_odd_or_even = getPdf.oddOrEven(print_pdf)
                pdf_height = getPdf.height(print_pdf)
                if (batch_length + pdf_length) > (length_for_full):
                    continue
                else:
                    if (find_odd == False) and (pdf_odd_or_even == 0):
                        batch_list.append(print_pdf)
                        batch_length += pdf_length
                    elif (find_odd == False) and (pdf_odd_or_even == 1):
                        batch_list.append(print_pdf)
                        batch_length += pdf_length
                        find_odd = True
                        odd_match_height = pdf_height
                    elif (find_odd == True) and (pdf_odd_or_even == 0):
                        continue
                    elif (find_odd == True) and (pdf_odd_or_even == 1):
                        if odd_match_height != pdf_height:
                            continue
                        else:
                            batch_list.append(print_pdf)
                            length_to_add = pdf_length - (pdf_height + .5)
                            batch_length += length_to_add
                            find_odd = False
                            odd_match_height = 0
                    
        loop_counter += 1
    
    length_for_samples = material_length - batch_length - 10
    if length_for_samples > total_sample_length:
        for due_date in samplePdfsToBatch:
            sample_height_counter = ''
            for print_pdf in samplePdfsToBatch[due_date]:
                if sample_height_counter == False:
                    pdf_length = getPdf.length(print_pdf)
                    batch_list.append(print_pdf)
                    sample_height_counter = True
                else:
                    pdf_length = getPdf.length(print_pdf)
                    batch_list.append(print_pdf)
                    batch_length += pdf_length
                    sample_height_counter = False
    else:
        for due_date in samplePdfsToBatch:
            for print_pdf in samplePdfsToBatch[due_date]:
                pdf_length = getPdf.length(print_pdf)
                pdf_odd_or_even = getPdf.oddOrEven(print_pdf)
                pdf_height = getPdf.height(print_pdf)
                if (batch_length + pdf_length) > material_length:
                    break
                else:
                    if (sample_odd_count == False) and (pdf_odd_or_even == 0):
                        batch_list.append(print_pdf)
                        batch_length += pdf_length
                    elif (sample_odd_count == False) and (pdf_odd_or_even == 1):
                        batch_list.append(print_pdf)
                        batch_length += pdf_length
                        sample_odd_count = True
                    elif (sample_odd_count == True) and (pdf_odd_or_even == 0):
                        continue
                    elif (sample_odd_count == True) and (pdf_odd_or_even == 1):
                            batch_list.append(print_pdf)
                            length_to_add = pdf_length - (pdf_height + .5)
                            batch_length += length_to_add
                            sample_odd_count = False

    new_batch['list_of_pdfs'] = batch_list
    new_batch['batch_length'] = batch_length

    if (new_batch['batch_length'] > 1900) or (batch_length > 1900):
        print(batch_length)
        print(new_batch['batch_length'])
        print(length_for_samples)
        print(length_for_full)
        print(material_length)
        print(total_sample_length)

    return new_batch

def make_batch_folder(new_batch_dict, material):
    batch_directory = gv.batchFoldersDir + 'Batch #' + str(gv.globalBatchCounter['batchCounter']) + ' ' + material + ' L' + str(new_batch_dict['batch_length'])
    batch_number = str(gv.globalBatchCounter['batchCounter'])
    os.mkdir(batch_directory)
    gv.globalBatchCounter['batchCounter'] += 1
    tag = 'Hotfolder'
    for print_pdf in new_batch_dict['list_of_pdfs']:
        pdf_friendly_name = getPdf.friendlyName
        if print_pdf.split('/')[-1] == 'LvD Color Chart Rotated.pdf':
            shutil.copy(print_pdf, batch_directory)
        elif print_pdf.split('/')[-1] == 'LvD Roll-Stickers Rotated.pdf':
            shutil.copy(print_pdf, batch_directory)
        else:
            pdf_friendly_name = getPdf.friendlyName
            tryToMovePDF(print_pdf, batch_directory, pdf_friendly_name)
    print('\n| New Batch:', batch_number)
    print('| Material:', material)
    print('| Length:', new_batch_dict['batch_length'])
    batch_orders = glob.iglob(batch_directory + '/*.pdf')
    for print_pdf in batch_orders:
        pdf_repeat = getPdf.repeat(print_pdf)
        pdf_order_size = getPdf.size(print_pdf)
        if (pdf_repeat > 2) and (pdf_order_size == 'Full'):
            try:
                pdf_splitter.cropMultiPanelPDFs(print_pdf, batch_directory)
            except utils.PdfReadError: 
                print('| Couldn\'t split file. In case it\'s needed, a copy of the original file is in "#Past Orders/Original Files"')
                print('| PDF:', getPdf.friendlyName(print_pdf))
                tag = 'Manual'
    set_tag.apply_tag(tag, batch_directory)
    
    divide_batch_into_full_and_sample(batch_directory)

def divide_batch_into_full_and_sample(batch_directory):
    full_pdfs = glob.glob(batch_directory + '/*-Full-*.pdf')
    sample_pdfs = glob.glob(batch_directory + '/*-Samp-*.pdf')
    os.mkdir(batch_directory + '/Full/')
    os.mkdir(batch_directory + '/Samples/')
    full_dir = batch_directory + '/Full/'
    sample_dir = batch_directory + '/Samples/'
    for print_pdf in full_pdfs:
        shutil.move(print_pdf, full_dir)
    for print_pdf in sample_pdfs:
        shutil.move(print_pdf, sample_dir)

     

