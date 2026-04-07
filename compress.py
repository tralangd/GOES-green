#!/usr/bin/env python3

import argparse
import os
import shutil
import subprocess
import sys


def compress():

        home = os.getcwd()

        # loop through all .TIF files and convert them to .JXL files
        timestamps = os.listdir("data/TIF")
        for timestamp in timestamps:

            # if the "timestamp" was a file instead of a directory, silently skip it
            if not os.path.isdir(f"data/TIF/{timestamp}"):
                continue

            # if the timestamp has already been processed
            if os.path.exists(f"data/JXL/{timestamp}"):
                continue
                
            # otherwise proceed

            # create a temporary directory to catch interrupted conversions
            TEMP_DIR = f"data/JXL/{timestamp}_temp"
            if os.path.exists(TEMP_DIR):
                print(f"Previous conversion attempt for {timestamp} was interrupted. Restarting.")
                shutil.rmtree(TEMP_DIR)
            os.makedirs(TEMP_DIR)

            # cd into temporary directory
            os.chdir(TEMP_DIR)

            # convert one band at a time
            bands = ["B01", "B02", "B03", "B04"]
            for band in bands:
                    
                print(f"Compressing timestamp {timestamp} band {band}")

                infile = f"{home}/data/TIF/{timestamp}/HIMAWARI-8_AHI_{band}_{timestamp}00_FLDK.tif"
                outfile_png = f"{home}/data/JXL/{timestamp}_temp/HIMAWARI-8_AHI_{band}_{timestamp}_FLDK.png"
                outfile_jxl = f"{home}/data/JXL/{timestamp}_temp/HIMAWARI-8_AHI_{band}_{timestamp}_FLDK.jxl"

                # gdal_translate native JPEG-XL compression option is suboptimal

                # so convert to PNG first, which strips geospatial data
                # also strip alpha channel and resize B03 "red" to 11000 x 11000 to match other channels
                process = subprocess.Popen(["gdal_translate", infile, outfile_png, "-b", "1", "-outsize", "11000", "11000"],
                                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=0)
                # update on each character to show progress bar
                while True:
                    chunk = process.stdout.read(1)  
                    if not chunk:
                        break
                    sys.stdout.buffer.write(chunk)
                    sys.stdout.buffer.flush()
                process.wait()

                # then use cjxl to convert to lossless JXL
                process = subprocess.Popen(["cjxl", outfile_png, outfile_jxl, "--distance=0"],
                                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=0)
                # update on each character to show progress bar
                while True:
                    chunk = process.stdout.read(1)  
                    if not chunk:
                        break
                    sys.stdout.buffer.write(chunk)
                    sys.stdout.buffer.flush()
                process.wait()

            # return from temporary directory
            os.chdir(home)

            # determine success by checking if all 4 expected output files exist
            p1 = os.path.isfile(f"{TEMP_DIR}/HIMAWARI-8_AHI_B01_{timestamp}_FLDK.jxl")
            p2 = os.path.isfile(f"{TEMP_DIR}/HIMAWARI-8_AHI_B02_{timestamp}_FLDK.jxl")
            p3 = os.path.isfile(f"{TEMP_DIR}/HIMAWARI-8_AHI_B03_{timestamp}_FLDK.jxl")
            p4 = os.path.isfile(f"{TEMP_DIR}/HIMAWARI-8_AHI_B04_{timestamp}_FLDK.jxl")
            # if unsuccessful
            if not (p1 and p2 and p3 and p4):
                #print the error message and exit the program
                sys.exit(f"Conversion for timestamp {timestamp} failed.")
            # else if successful
            else:
                # delete .png and .png.aux.xml (contains removed geospatial data) files
                files = [f"{TEMP_DIR}/HIMAWARI-8_AHI_B01_{timestamp}_FLDK.png" , f"{TEMP_DIR}/HIMAWARI-8_AHI_B01_{timestamp}_FLDK.png.aux.xml",
                         f"{TEMP_DIR}/HIMAWARI-8_AHI_B02_{timestamp}_FLDK.png" , f"{TEMP_DIR}/HIMAWARI-8_AHI_B02_{timestamp}_FLDK.png.aux.xml",
                         f"{TEMP_DIR}/HIMAWARI-8_AHI_B03_{timestamp}_FLDK.png" , f"{TEMP_DIR}/HIMAWARI-8_AHI_B03_{timestamp}_FLDK.png.aux.xml",
                         f"{TEMP_DIR}/HIMAWARI-8_AHI_B04_{timestamp}_FLDK.png" , f"{TEMP_DIR}/HIMAWARI-8_AHI_B04_{timestamp}_FLDK.png.aux.xml"]
                for file in files:
                    if os.path.exists(file):
                        os.remove(file)
                # move and rename the temporary directory to the final directory
                os.rename(TEMP_DIR, f"data/JXL/{timestamp}")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Strip geospatial data from TIF files and convert to JXL. This function does not take any arguments.")
    
    args = parser.parse_args()

    compress()
