"""
Script to extract and zip the most recent configuration backups from Extreme
Management Center Archive.

"""

from datetime import datetime
from datetime import date
from importlib.metadata import files
from itertools import count
from operator import contains
from os import listdir
from os.path import isfile, join
from zipfile import ZipFile
import time
import os
import zipfile

EXTREME_ARCHIVE_BASE_DIRECTORY  = r"C:\py\zippings"        
SEARCH_SUBDIRECTORIES           = ["FolderA", "FolderB"]   
SEARCH_FILE_EXTENSION           = [".zip", ".cfg"]         
TFTP_PATH                       = r"C:\py\zippings\tftp"   
RESULTING_ZIP_FILEBASE          = r"switchbackup"          
RESULTING_ZIP_EXTENSION         = r".zip"                  
TOTAL_CONFIGS_EXPECTED          = 6

def space(count):
    print (r" ")
    print (r"-"*count)
    print (r" ")

folders_containing_configs = []          # List every subdir in SEARCH_SUBDIRECTORIES
relevant_folders_containing_configs = [] # Most recent enty in every folders_to_search.
files_to_put_in_zipfile = []                           

space(40)

print(f"Removing old zip-files from TFTP path:")
for file_path in os.listdir(TFTP_PATH):
    joined_path = os.path.join(TFTP_PATH, file_path)
    if os.path.exists(joined_path):
        if RESULTING_ZIP_FILEBASE in joined_path:
            os.remove(joined_path)
            print(f"Deleted file: {joined_path}")
        else:
            print(f"Skipped file: {joined_path}")
    else:
        print(f"File not found for deleting: {joined_path}")
        

for file_or_folder in SEARCH_SUBDIRECTORIES:
    searchdir = os.path.join(EXTREME_ARCHIVE_BASE_DIRECTORY, file_or_folder)
    for entry in os.listdir(searchdir):
        folder = os.path.join(searchdir, entry)
        if os.path.isdir(folder):
            folders_containing_configs.append(folder)
    folders_containing_configs.sort()
    most_recent_folder = folders_containing_configs[0]
    relevant_folders_containing_configs.append(most_recent_folder)
    folders_containing_configs = []   # Set to zero before next loop for next folder

space(40)

print(f"Checking which files to add:")
foldercount = len(relevant_folders_containing_configs)
for k in range(foldercount):
    for entry in os.listdir(relevant_folders_containing_configs[k]):
        for file_extension in SEARCH_FILE_EXTENSION:
            if file_extension in entry:
                fqdn_and_filename = os.path.join(relevant_folders_containing_configs[k], entry)
                files_to_put_in_zipfile.append(fqdn_and_filename)
                print(f"File {entry} has correct extension {file_extension}, adding to list.")


current_date_time = str(datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
filename_for_zipfile = fr"{TFTP_PATH}\{current_date_time}-{RESULTING_ZIP_FILEBASE}{RESULTING_ZIP_EXTENSION}"

space(40)

new_zipfile_to_generate = ZipFile(filename_for_zipfile, mode ="w")
print(f"Generating new zip file {filename_for_zipfile}")
for n in files_to_put_in_zipfile:
    new_zipfile_to_generate.write(n)
    print(f"Adding config-file {n} to zipfile.")
new_zipfile_to_generate.close

space(40)

try:
    zipfile.ZipFile(filename_for_zipfile)
    print(f"Zip-file {filename_for_zipfile} saved.")
    print(r"Done.")
except:
    print(r"Zip file error")


