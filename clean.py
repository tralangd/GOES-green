#!/usr/bin/env python3

import argparse
import glob
import os
import sys


def convert_size(size_bytes):
    for unit in ['B', 'KiB', 'MiB', 'GiB']:
        if size_bytes < 1024:
            return f"{size_bytes:.3f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} TiB"


def clean(DAT, TIF, JXL, BIN):

    if not (DAT or TIF or JXL or BIN):
        print("You need to use an agrument flag. Try --help for help")
        sys.exit(0)

    DAT_delete_list = []
    TIF_delete_list = []
    JXL_delete_list = []
    BIN_delete_list = []

    DAT_storage_reduce = 0
    TIF_storage_reduce = 0
    JXL_storage_reduce = 0
    BIN_storage_reduce = 0

    if DAT:
        
        DAT_timestamps = os.listdir("data/DAT")
        TIF_timestamps = os.listdir("data/TIF")

        # for each folder in DAT directory
        for timestamp in DAT_timestamps:

            # if 'timestamp' is not a folder, skip
            if not os.path.isdir(f"data/DAT/{timestamp}"):
                continue

            # if timestamp is also a path in TIF folder
            # then we know it has already been converted
            if timestamp in TIF_timestamps:

                files = glob.glob(f"data/DAT/{timestamp}/*.DAT.bz2")

                for file in files:
                    DAT_delete_list.append(file)
                    DAT_storage_reduce += os.path.getsize(file)

    if TIF:
        
        TIF_timestamps = os.listdir("data/TIF")
        JXL_timestamps = os.listdir("data/JXL")

        # for each folder in TIF directory
        for timestamp in TIF_timestamps:

            # if 'timestamp' is not a folder, skip
            if not os.path.isdir(f"data/TIF/{timestamp}"):
                continue

            # if timestamp is also a path in JXL folder
            # then we know it has already been converted
            if timestamp in JXL_timestamps:

                files = glob.glob(f"data/TIF/{timestamp}/*.tif")

                for file in files:
                    TIF_delete_list.append(file)
                    TIF_storage_reduce += os.path.getsize(file)

                files = glob.glob(f"data/TIF/{timestamp}/*.log")

                for file in files:
                    TIF_delete_list.append(file)
                    TIF_storage_reduce += os.path.getsize(file)

    if JXL:
                
        JXL_timestamps = os.listdir("data/JXL")

        with open("data/BIN/all.txt", 'r') as file:
            BIN_timestamps = [line.strip() for line in file.readlines()]

        # for each filder in JXL directory
        for timestamp in JXL_timestamps:

            # if 'timestamp' is not a folder, skip
            if not os.path.isdir(f"data/JXL/{timestamp}"):
                continue

            # if timestamp is included in all.txt file
            # then we know it has already been converted
            if timestamp in BIN_timestamps:

                files = glob.glob(f"data/JXL/{timestamp}/*.jxl")

                for file in files:
                    JXL_delete_list.append(file)
                    JXL_storage_reduce += os.path.getsize(file)

    if BIN:

        # this is the last step, so there is nothing to check against
        # we make our delete list by inspecting which files have been merged
        # and only include those that have not been deleted previously
        with open("data/BIN/batch_merged.txt", 'r') as file:
            batchfiles = [line.strip() for line in file.readlines()]
        for file in batchfiles:
            if os.path.isfile(file):
                BIN_delete_list.append(file)
        for batch in BIN_delete_list:
            BIN_storage_reduce += os.path.getsize(batch)

    if DAT:
        print( "Found" , len(DAT_delete_list) , "DAT files (" , convert_size(DAT_storage_reduce) , ")" )
    if TIF:
        print( "Found" , len(TIF_delete_list) , "TIF files (" , convert_size(TIF_storage_reduce) , ")" )
    if JXL:
        print( "Found" , len(JXL_delete_list) , "JXL files (" , convert_size(JXL_storage_reduce) , ")" )
    if BIN:
        print( "Found" , len(BIN_delete_list) , "BIN files (" , convert_size(BIN_storage_reduce) , ")" )

    if 0 == ( len(DAT_delete_list) + len(TIF_delete_list) + len(JXL_delete_list) + len(BIN_delete_list) ):
        print("Nothing to delete. Exiting.")
        sys.exit(0)

    attempts = 0
    response = ''
    while not (response == 'y' or response == 'n'):
        
        if attempts == 3:
            print("Too many invalid attempts. Exiting.")
            sys.exit(0)

        response = input("Are you sure you want to delete these files? [y/n] ")
        response = response.strip().lower()
        attempts = attempts + 1

        if not (response == 'y' or response == 'n'):
            print("Please type 'y' or 'n'")
    
    if response == 'n':
        print("User aborted clean")
        sys.exit(0)
    
    if response == 'y':

        print("Cleaning files...")

        for file in (DAT_delete_list + TIF_delete_list + JXL_delete_list + BIN_delete_list):
            os.remove(file)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Delete files that are no longer strictly needed. Accepts multiple options.")

    parser.add_argument("--dat",
                        action="store_true",
                        help="Delete all .DAT.bz2 files that have already been converted to .TIF"
                        )
    
    parser.add_argument("--tif",
                        action="store_true",
                        help="Delete all .TIF files that have already been converted to .JXL"
                        )
    
    parser.add_argument("--jxl",
                        action="store_true",
                        help="Delete all .JXL files that have already been processed to .BIN"
                        )
    
    parser.add_argument("--bin",
                        action="store_true",
                        help="Delete all batch_XXXX.bin files that have been merged into batch_merged.bin"
                        )

    args = parser.parse_args()

    clean(DAT=args.dat, TIF=args.tif, JXL=args.jxl, BIN=args.bin)
    