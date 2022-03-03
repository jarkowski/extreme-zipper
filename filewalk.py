"""
Script to extract and zip the most recent configuration backups from Extreme
Management Center Archive.
"""

import configparser
import json
import sys
from datetime import datetime
from zipfile import ZipFile
import os
import zipfile
import logging
import logging.handlers

APP_FRIENDLYNAME = r"Filewalk Extreme Zipper script"

def logWinEvent(type, event_text):
    import win32evtlogutil
    import win32evtlog

    if type == "INFO":
        try:
            win32evtlogutil.ReportEvent(
                APP_FRIENDLYNAME,
                0,
                eventType=win32evtlog.EVENTLOG_INFORMATION_TYPE,
                strings=event_text,
            )
        except:
            pass
    elif type == "ERROR":
        try:
            win32evtlogutil.ReportEvent(
                APP_FRIENDLYNAME,
                50,
                eventType=win32evtlog.EVENTLOG_ERROR_TYPE,
                strings=event_text,
            )
        except:
            pass


filewalk_config = configparser.ConfigParser()
filewalk_config.read("filewalk.ini")

EXTREME_ARCHIVE_BASE_DIRECTORY  = filewalk_config.get("config", "EXTREME_ARCHIVE_BASE_DIRECTORY")
TFTP_PATH                       = filewalk_config.get("config", "TFTP_PATH") 
RESULTING_ZIP_FILEBASE          = filewalk_config.get("config", "RESULTING_ZIP_FILEBASE")         
RESULTING_ZIP_EXTENSION         = filewalk_config.get("config", "RESULTING_ZIP_EXTENSION")                   
LOGFILE                         = filewalk_config.get("config", "LOGFILE") 
SEARCH_SUBDIRECTORIES           = json.loads(filewalk_config.get("config", "SEARCH_SUBDIRECTORIES"))
SEARCH_FILE_EXTENSION           = json.loads(filewalk_config.get("config", "SEARCH_FILE_EXTENSION"))
SEPARATOR                       = r"----------------------------------------"

current_date = str(datetime.now().strftime('%Y_%m_%d'))
current_date_time = str(datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))

log = logging.getLogger("")
log.setLevel(logging.DEBUG)
loghandler_file = logging.handlers.RotatingFileHandler(
    LOGFILE,
    maxBytes=(1024*512),
    backupCount=9
)
loghandler_console = logging.StreamHandler(sys.stdout)
format_of_logmessage_file = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
format_of_logmessage_console = logging.Formatter("%(levelname)s - %(message)s")
loghandler_file.setFormatter(format_of_logmessage_file)
loghandler_console.setFormatter(format_of_logmessage_console)
log.addHandler(loghandler_file)
log.addHandler(loghandler_console)

folders_containing_configs = []          # List every subdir in SEARCH_SUBDIRECTORIES
relevant_folders_containing_configs = [] # Most recent enty in every folders_to_search.
files_to_put_in_zipfile = []             # All files from every relevant folders              

log.info(SEPARATOR)

log.info(f"Removing old zip-files from TFTP path:")

if os.path.exists(TFTP_PATH):
    for file_in_tftp_path in os.listdir(TFTP_PATH):
        joined_path_file = os.path.join(TFTP_PATH, file_in_tftp_path)
        if RESULTING_ZIP_FILEBASE in joined_path_file:
            try:
                os.remove(joined_path_file)
                log.info(f"Deleted old file: {joined_path_file}")
                logWinEvent("INFO", [f"Deleted old file {joined_path_file}"])
            except:
                log.error(f"Tried to delete {joined_path_file}, but failed.")
                logWinEvent("ERROR", [f"Tried to delete {joined_path_file} but failed."])       
        else:
            log.info(f"Skipped file: {joined_path_file}")
else:
    log.error(f"The TFTP-Path {TFTP_PATH} could not be found.")
    logWinEvent("ERROR", [f"The TFTP-Path {TFTP_PATH} could not be found."])
    sys.exit(f"The TFTP-Path {TFTP_PATH} could not be found.")
        

for file_or_folder in SEARCH_SUBDIRECTORIES:
    searchdir = os.path.join(EXTREME_ARCHIVE_BASE_DIRECTORY, file_or_folder)
    for target_file in os.listdir(searchdir):
        folder = os.path.join(searchdir, target_file)
        if os.path.isdir(folder):
            folders_containing_configs.append(folder)
    folders_containing_configs.sort()
    most_recent_folder = folders_containing_configs[0]
    relevant_folders_containing_configs.append(most_recent_folder)
    folders_containing_configs = []   # Set to zero before next loop for next folder

log.info(SEPARATOR)

log.info(f"Checking which files to add:")
foldercount = len(relevant_folders_containing_configs)
for k in range(foldercount):
    for target_file in os.listdir(relevant_folders_containing_configs[k]):
        for file_extension in SEARCH_FILE_EXTENSION:
            if file_extension in target_file:
                fqdn_and_filename = os.path.join(relevant_folders_containing_configs[k], target_file)
                files_to_put_in_zipfile.append(fqdn_and_filename)
                log.info(f"File {target_file} has correct extension {file_extension}, adding to list.")

log.info(SEPARATOR)

filename_for_zipfile = fr"{TFTP_PATH}\{current_date_time}-{RESULTING_ZIP_FILEBASE}{RESULTING_ZIP_EXTENSION}"
new_zipfile_to_generate = ZipFile(filename_for_zipfile, mode ="w")
log.info(f"Generating new zip file {filename_for_zipfile}")
for n in files_to_put_in_zipfile:
    new_zipfile_to_generate.write(n)
    log.info(f"Adding config-file {n} to zipfile.")
new_zipfile_to_generate.close

log.info(SEPARATOR)

try:
    zipfile.ZipFile(filename_for_zipfile)
    log.info(f"Zip-file {filename_for_zipfile} created.")
    log.info(r"Done.")
    logWinEvent("INFO", [f"Zip-file {filename_for_zipfile} created."])
except:
    log.error(r"Zip file error")
    logWinEvent("ERROR", "Zip file error")