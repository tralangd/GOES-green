#!/usr/bin/env python3

import argparse
import glob
import numpy as np
import os


def merge():

    # use glob to pick all potential batch_XXXX.bin files to be merged
    batchfiles_all = glob.glob("data/BIN/batch_*.bin")
    # glob will also pick up batch_merged.bin if it exists, and it needs to be removed from list
    if os.path.isfile("data/BIN/batch_merged.bin"):
        batchfiles_all.remove("data/BIN/batch_merged.bin")
    # get list of batch_XXXX.bin files that have already been merged
    if os.path.isfile("data/BIN/batch_merged.txt"):
        with open("data/BIN/batch_merged.txt", 'r') as file:
            batchfiles_done = [line.strip() for line in file.readlines()]
    else:
        batchfiles_done = []
    # finally, make list of batch_XXXX.bin files that will be merged in this run
    batchfiles_new = []
    for batch in batchfiles_all:
        if batch not in batchfiles_done:
            batchfiles_new.append(batch)

    # if batch_merged.bin does not exist, use zeros array as our starting point
    if not os.path.isfile("data/BIN/batch_merged.bin"):
        print("File \'data/BIN/batch_merged.bin\' not found. Performing first-time initialization.")
        histogram = np.zeros( shape=(256,256,256,256) , dtype=np.uint32 )
    # otherwise use the existing batch_merged.bin as out starting point
    else:
        histogram = np.fromfile("data/BIN/batch_merged.bin", dtype=np.uint32).reshape(256,256,256,256)

    outfile = "data/BIN/batch_merged_temp.bin"
    # if batch_merged_temp.bin already exists, then throw an error
    # it means the file was not properly renamed to batch_merged.bin on last run
    if os.path.isfile(outfile):
        raise ValueError(f"Exiting. Outfile \'{os.curdir()}/{outfile}\' already exists. Proceeding could overwrite existing data.")

    # for each batch file to be merged
    for filename in batchfiles_new:

        # initialize memmap file
        batch = np.memmap(filename, dtype=np.uint32, mode='r', shape=(256,256,256,256))

        # iterate over [256 x 256] slices of the 256^4 array
        for ii in range(0,256):

            print("\r", f"Merging {os.path.basename(filename)} {ii+1} of 256     ", end='')

            # read slice from file and add to merged file
            histogram[ii,:,:,:] += batch[ii,:,:,:] # ii must go first for for fast reading from disk

        # memmap has no destructor, so we need to delete it completely in order to read the next one
        del batch

    # write histogram to file
    print("\nWriting merged output array")
    histogram.tofile(outfile)

    # if the script made it to this point:
    # delete the original batch_merged (if it exists)
    if os.path.isfile("data/BIN/batch_merged.bin"):
        os.remove("data/BIN/batch_merged.bin")
    # rename temp
    os.rename(outfile,"data/BIN/batch_merged.bin")
    # append batch names to batch_merged.txt
    # append information to all.txt
    with open("data/BIN/batch_merged.txt", 'a') as file:
        file.write('\n'.join(batchfiles_new))
        file.write('\n')
    

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Merge batched data into a single data file. This function does not take any arguments.")
    
    args = parser.parse_args()

    merge()
