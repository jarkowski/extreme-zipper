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

def logWinEvent(type, event_id, event_text):
    import win32evtlogutil
    import win32evtlog

    if type == "INFO":
        try:
            win32evtlogutil.ReportEvent(
                APP_FRIENDLYNAME,
                event_id,
                eventType=win32evtlog.EVENTLOG_INFORMATION_TYPE,
                strings=event_text,
            )
        except:
            pass
    elif type == "ERROR":
        try:
            win32evtlogutil.ReportEvent(
                APP_FRIENDLYNAME,
                event_id,
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
for file_path in os.listdir(TFTP_PATH):
    joined_path = os.path.join(TFTP_PATH, file_path)
    if os.path.exists(joined_path):
        if RESULTING_ZIP_FILEBASE in joined_path:
            os.remove(joined_path)
            log.info(f"Deleted old file: {joined_path}")
            logWinEvent("INFO", 0, [f"Deleted old file {joined_path}"])
        else:
            log.info(f"Skipped file: {joined_path}")
    else:
        log.info(f"File not found for deleting: {joined_path}")
        

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

log.info(SEPARATOR)

log.info(f"Checking which files to add:")
foldercount = len(relevant_folders_containing_configs)
for k in range(foldercount):
    for entry in os.listdir(relevant_folders_containing_configs[k]):
        for file_extension in SEARCH_FILE_EXTENSION:
            if file_extension in entry:
                fqdn_and_filename = os.path.join(relevant_folders_containing_configs[k], entry)
                files_to_put_in_zipfile.append(fqdn_and_filename)
                log.info(f"File {entry} has correct extension {file_extension}, adding to list.")


filename_for_zipfile = fr"{TFTP_PATH}\{current_date_time}-{RESULTING_ZIP_FILEBASE}{RESULTING_ZIP_EXTENSION}"

log.info(SEPARATOR)

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
    logWinEvent("INFO", 0, [f"Zip-file {filename_for_zipfile} created."])
except:
    log.error(r"Zip file error")
    logWinEvent("ERROR", 50, "Zip file error")