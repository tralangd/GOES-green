#!/usr/bin/env python3

import argparse
import glob
import os
import shutil
import subprocess
import sys


def convert():
        
        home = os.getcwd()

        # loop through all .DAT files and convert them to .TIF files
        timestamps = os.listdir("data/DAT")
        for timestamp in timestamps:

            # if the "timestamp" was a file instead of a directory, silently skip it
            if not os.path.isdir(f"data/DAT/{timestamp}"):
                continue

            # if the timestamp has already been processed
            if os.path.exists(f"data/TIF/{timestamp}"):
                continue
                
            # otherwise proceed

            # create a temporary directory to catch interrupted conversions
            TEMP_DIR = f"data/TIF/{timestamp}_temp"
            if os.path.exists(TEMP_DIR):
                print(f"Previous conversion attempt for {timestamp} was interrupted. Restarting.")
                shutil.rmtree(TEMP_DIR)
            os.makedirs(TEMP_DIR)

            # cd into temporary directory
            os.chdir(TEMP_DIR)

            # conserve memory by converting one band at a time
            bands = ["B01", "B02", "B03", "B04"]
            for band in bands:
                    
                print(f"Converting timestamp {timestamp} band {band}")

                # normally, the shell would expand the wildcard in the command, but since we're using subprocess, we need to do it ourselves
                files = glob.glob(f"{home}/data/DAT/{timestamp}/*_{band}_*.DAT.bz2")

                # call geo2grid
                process = subprocess.Popen(["geo2grid", "-r", "ahi_hsd", "-w", "geotiff",
                                            "-p", band, "-f", *files],
                                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                                            )
                stdout, stderr = process.communicate()

            # return from temporary directory
            os.chdir(home)
            
            # determine success by checking if all 4 expected output files exist
            # geo2grid writes output files to directory script was called from
            # these Himawari-8 DAT files also lack seconds information, geo2grid will asssume seconds are 00
            p1 = os.path.isfile(f"{TEMP_DIR}/HIMAWARI-8_AHI_B01_{timestamp}00_FLDK.tif")
            p2 = os.path.isfile(f"{TEMP_DIR}/HIMAWARI-8_AHI_B02_{timestamp}00_FLDK.tif")
            p3 = os.path.isfile(f"{TEMP_DIR}/HIMAWARI-8_AHI_B03_{timestamp}00_FLDK.tif")
            p4 = os.path.isfile(f"{TEMP_DIR}/HIMAWARI-8_AHI_B04_{timestamp}00_FLDK.tif")
            # if unsuccessful
            if not (p1 and p2 and p3 and p4):
                # print the error message and exit the program
                sys.exit(f"Conversion for timestamp {timestamp} failed. Check error message logfile.")
            # else if successful
            else:
                # move and rename the temporary directory to the final directory
                os.rename(TEMP_DIR, f"data/TIF/{timestamp}")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Convert downloaded .DAT files to .TIF files. This function does not take any arguments.")
    
    args = parser.parse_args()

    convert()
