"""
Script to extract and zip the most recent configuration backups from Extreme
Management Center Archive. Parameters are imported from filewalk.ini.
"""

APP_FRIENDLYNAME = r"Filewalk Extreme Zipper script"

import configparser
import json
import sys
from datetime import datetime
from zipfile import ZipFile
import os
import zipfile
import logging
import logging.handlers

# Define function to add log entries to windows event log:


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


# Read config from INI file:

filewalk_config = configparser.ConfigParser()
filewalk_config.read("filewalk.ini")

EXTREME_ARCHIVE_BASE_DIRECTORY = filewalk_config.get(
    "config", "EXTREME_ARCHIVE_BASE_DIRECTORY"
)
TFTP_PATH = filewalk_config.get("config", "TFTP_PATH")
RESULTING_ZIP_FILEBASE = filewalk_config.get("config", "RESULTING_ZIP_FILEBASE")
RESULTING_ZIP_EXTENSION = filewalk_config.get("config", "RESULTING_ZIP_EXTENSION")
RESULTING_ZIP_USEDATE = filewalk_config.getboolean("config", "RESULTING_ZIP_USEDATE")
RESULTING_ZIP_MAX_BYTES = filewalk_config.getint("config", "RESULTING_ZIP_MAX_BYTES")
LOGFILE = filewalk_config.get("config", "LOGFILE")
DEBUGLOG_ENABLE = filewalk_config.getboolean("config", "DEBUGLOG_ENABLE")
SEARCH_SUBDIRECTORIES = json.loads(
    filewalk_config.get("config", "SEARCH_SUBDIRECTORIES")
)
SEARCH_FILE_EXTENSION = json.loads(
    filewalk_config.get("config", "SEARCH_FILE_EXTENSION")
)
SEPARATOR = r"----------------------------------------"

# Prepare strings with current date/time:

current_date = str(datetime.now().strftime("%Y_%m_%d"))
current_date_time = str(datetime.now().strftime("%Y_%m_%d_%H_%M_%S"))

# Prepare log handler for file logging and console logging:

log = logging.getLogger("")
if DEBUGLOG_ENABLE == True:
    log.setLevel(logging.DEBUG)
else:
    log.setLevel(logging.INFO)
loghandler_file = logging.handlers.RotatingFileHandler(
    LOGFILE, maxBytes=(1024 * 512), backupCount=9
)
loghandler_console = logging.StreamHandler(sys.stdout)
format_of_logmessage_file = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s"
)
format_of_logmessage_console = logging.Formatter("%(levelname)s - %(message)s")
loghandler_file.setFormatter(format_of_logmessage_file)
loghandler_console.setFormatter(format_of_logmessage_console)
log.addHandler(loghandler_file)
log.addHandler(loghandler_console)

# Iniitialize lists:

folders_containing_configs = []  # List every subdir in SEARCH_SUBDIRECTORIES
relevant_folders_containing_configs = []  # Most recent enty in every folders_to_search.
files_to_put_in_zipfile = []  # All files from every relevant folders


log.info(SEPARATOR)
if DEBUGLOG_ENABLE == True:
    log.info(r"Starting with DEBUG log enabled.")
else:
    log.info(
        r"Starting with DEBUG log disabled. Set 'DEBUGLOG_ENABLE = True' in filewalk.ini to see all messages."
    )

log.info(SEPARATOR)
log.info(f"Removing old zip-files from TFTP path")

# Deleting of old zip files, making sure only the files with correct filebase are deleted,
# preventing deleting of other files in TFTP directory:

file_delete_count_success = 0
file_delete_count_failed = 0
file_delete_count_skipped = 0

if os.path.exists(TFTP_PATH):
    for file_in_tftp_path in os.listdir(TFTP_PATH):
        joined_path_file = os.path.join(TFTP_PATH, file_in_tftp_path)
        if RESULTING_ZIP_FILEBASE in joined_path_file:
            try:
                os.remove(joined_path_file)
                file_delete_count_success += 1
                log.info(f"Deleted old file: {joined_path_file}")
                logWinEvent("INFO", [f"Deleted old file {joined_path_file}"])
            except:
                file_delete_count_failed += 1
                log.error(f"Tried to delete {joined_path_file}, but failed.")
                logWinEvent(
                    "ERROR", [f"Tried to delete {joined_path_file} but failed."]
                )
        else:
            file_delete_count_skipped += 1
            log.debug(
                f"Skipped file {joined_path_file}. "
                f"It did not contain '{RESULTING_ZIP_FILEBASE}' and wasn't deleted."
            )
else:
    log.error(f"The TFTP-Path {TFTP_PATH} could not be found.")
    logWinEvent("ERROR", [f"The TFTP-Path {TFTP_PATH} could not be found."])
    sys.exit(f"The TFTP-Path {TFTP_PATH} could not be found.")

log.info(f"Old files removed successfully: {file_delete_count_success}")
if file_delete_count_failed > 0:
    log.error(f"Old files removal failed: {file_delete_count_failed}")
else:
    log.info(f"Old files removal failed: 0")
log.info(f"Files skipped: {file_delete_count_skipped}")

# Checking if configured base directory is usable:

if not (os.path.exists(EXTREME_ARCHIVE_BASE_DIRECTORY)):
    log.error(
        f"The base directory {EXTREME_ARCHIVE_BASE_DIRECTORY} could not be found."
    )
    logWinEvent(
        "ERROR",
        [f"The base directory {EXTREME_ARCHIVE_BASE_DIRECTORY} could not be found."],
    )
    sys.exit(f"The base directory {EXTREME_ARCHIVE_BASE_DIRECTORY} could not be found.")

log.info(SEPARATOR)

# Checking the base directory for configured subdirectories, and the grab the
# youngest directory in every subdirectory.
# The result is the list relevant_folders_containing_configs[].

log.info(f"Checking for Subdirectories to search for configs-files to include.")
for file_or_folder in SEARCH_SUBDIRECTORIES:
    searchdir = os.path.join(EXTREME_ARCHIVE_BASE_DIRECTORY, file_or_folder)
    for target_file in os.listdir(searchdir):
        folder = os.path.join(searchdir, target_file)
        if os.path.isdir(folder):
            folders_containing_configs.append(folder)
            log.debug(f"Folder {folder} found.")
    folders_containing_configs.sort()
    try:
        youngest_folder = folders_containing_configs[0]
        relevant_folders_containing_configs.append(youngest_folder)
        log.debug(f"Folder {youngest_folder} is the youngest and will be included.")
    except:
        pass
        log.error(f"{file_or_folder} should contain subfolders, but didn't.")
    finally:
        folders_containing_configs = []  # Set to zero before next loop for next folder

log.info(SEPARATOR)

# Selecting all files from all relevant folders, as long as they match on of
# the configured file extensions:

log.info(f"Checking which files to add")
foldercount = len(relevant_folders_containing_configs)
for k in range(foldercount):
    for target_file in os.listdir(relevant_folders_containing_configs[k]):
        for file_extension in SEARCH_FILE_EXTENSION:
            if file_extension in target_file:
                fqdn_and_filename = os.path.join(
                    relevant_folders_containing_configs[k], target_file
                )
                files_to_put_in_zipfile.append(fqdn_and_filename)
                log.debug(
                    f"File {target_file} has correct extension {file_extension}, adding to list."
                )

log.info(SEPARATOR)

# Generating the filename for the result ZIP file:

if RESULTING_ZIP_USEDATE == True:
    zipfile_filename = rf"{TFTP_PATH}\{current_date_time}-{RESULTING_ZIP_FILEBASE}{RESULTING_ZIP_EXTENSION}"
    new_zipfile_to_generate = ZipFile(zipfile_filename, mode="w")
    log.info(f"Generating new zip file {zipfile_filename}")
else:
    zipfile_filename = rf"{TFTP_PATH}\{RESULTING_ZIP_FILEBASE}{RESULTING_ZIP_EXTENSION}"
    new_zipfile_to_generate = ZipFile(zipfile_filename, mode="w")
    log.info(f"Generating new zip file {zipfile_filename}")

# Adding files to ZIP file:

for n in files_to_put_in_zipfile:
    new_zipfile_to_generate.write(n)
    log.debug(f"Adding config-file {n} to zipfile.")
new_zipfile_to_generate.close()

log.info(SEPARATOR)

# Simple test if the generated file is a valif ZIP file:

try:
    zipfile.ZipFile(zipfile_filename)
    log.info(f"Zip-file {zipfile_filename} tested - Success.")
    logWinEvent("INFO", [f"Zip-file {zipfile_filename} tested - Success."])
except:
    log.error(r"Error while testing the Zip-file.")
    logWinEvent("ERROR", "Error while testing the Zip-file.")
    sys.exit(r"Error while testing the Zip-file.")

# Checking that the resulting ZIP file does not exceed the configured limit. If
# it exceed the limit, add _OVERSIZE_ to the filename. This will prevent the file
# beeing picked up by the transfer script:

try:
    zipfile_filesize = os.path.getsize(zipfile_filename)
    log.debug(f"File size is {zipfile_filesize} bytes.")
except FileNotFoundError:
    log.error(r"Error while checking size of Zip-file.")
    logWinEvent("ERROR", "Error while checking size of Zip-file.")
    sys.exit(r"Error while checking size of Zip-file.")

if zipfile_filesize >= (RESULTING_ZIP_MAX_BYTES):
    log.error(
        f"Resulting file exceeds configured limit of {RESULTING_ZIP_MAX_BYTES} bytes, renaming with _OVERSIZE_."
    )
    logWinEvent(
        "ERROR",
        f"Resulting file exceeds configured limit of {RESULTING_ZIP_MAX_BYTES} bytes, renaming with _OVERSIZE_.",
    )
    old_filename = zipfile_filename
    new_filname = f"{zipfile_filename}_OVERSIZE_"
    try:
        os.rename(old_filename, new_filname)
    except:
        log.error(f"Error renaming the ZIP file.")
        logWinEvent(
            "ERROR",
            f"Error renaming the ZIP file.",
        )
