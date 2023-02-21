# extreme-zipper

This script is intended to be used with Extreme Management Center (EMC) 8.5 Linux. It can be used to extract the latest device backups from the file system, add them to a zip file and place the zip file into the TFTP folder.

The zip-file can then be downloaded to one or more switches. In the event of a larger outage, it can be used to bootstrap the environment when the EMC server is not available. This is especially helpful when the EMC is installed in a virtual environment which is dependent on the network that it is managing.
