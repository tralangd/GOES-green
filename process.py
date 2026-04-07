#!/usr/bin/env python3

import argparse
import glob
import numpy as np
import os
import sys

from PIL import Image
import pillow_jxl
Image.MAX_IMAGE_PIXELS = 500000000 # increase default limit

'''
We have to make a tough decision here:

either re-read ALL JXL images in a single run, then write a single 17GB file at the end
or
break into smaller batches, writing multiple 17GB files along the way, only to merge them into a singe 17GB file at the end

we need to save histogram information of the amount of times each BGRV-quadruplet is seen
which requires a [256 x 256 x 256 x 256] uint32 array
(256 because the input data is quantized as 8-bit intensities, and uint32 to ensure bin counts do not overflow)
this results in 2^20 Bytes or ~17 GB worth of uncompressed data that needs to be stored IN MEMORY

the memory requirement is reasonable for a single run,
but if we ever want to add to the dataset, then we would need to process the ENTIRE JXL library over again
or worse, if the process is interrupted, we would have to start over from the beginning

so the more reasonable option here is to write out to intermediate files, and then merge them later
this method allows for the addition of new data without requiring a complete restart

unfortunately, loading two of these intermediate files simultaneously in order to merge them requires 34 GB memory
we can get around this restriction by using memory mapping to read these files directly from disk, in smaller portions at a time
consequently, these intermediate files will need to be written to disk as UNCOMPRESSED RAW BINARY
'''

def process(batchsize):

    # verify that the batch count is positive
    if batchsize <= 0:
        raise ValueError("Input parameter \'count\' must be positive")
    
    # list of previously processed timestamps
    timestamp_list_file = "data/BIN/all.txt"

    # if all.txt does not exist, create it
    os.makedirs(os.path.dirname(timestamp_list_file), exist_ok=True)
    if not os.path.exists(timestamp_list_file):
        with open(timestamp_list_file, 'w') as f:
            pass # empty file

    # read all.txt into 'done' list
    with open(timestamp_list_file, 'r') as file:
        timestamps_done = [line.strip() for line in file.readlines()]
    
    # loop through all timestamps in JXL folder
    timestamps = os.listdir("data/JXL")
    timestamps_new = []
    for timestamp in timestamps:

        # if the "timestamp" actually a file instead of a directory, skip it
        if not os.path.isdir(f"data/JXL/{timestamp}"):
            continue

        # if timestamp is not in the 'done' list then it needs to be processed
        if timestamp not in timestamps_done:
            timestamps_new.append(timestamp)

    print("Found" , len(timestamps_new) , "new timestamps to process")
    if len(timestamps_new) < batchsize:
        print("Count of new timestamps is less than requested batch size. Exiting.")
        sys.exit()

    ts_so_far = 1
    ts_total = len(timestamps_new)

    # repeat in batches until new list is less than batch size
    while len(timestamps_new) >= batchsize:

        # get the index number of the next batch
        batch_num = len(glob.glob("data/BIN/batch_*.txt"))
        if os.path.isfile("data/BIN/batch_merged.txt"): # overcounted by one if this file exists
            batch_num = batch_num - 1

        outfile = f"data/BIN/batch_{batch_num:04d}"
        histogram = np.zeros( shape=(256,256,256,256) , dtype=np.uint32 )

        # now iterate through the next 'batchsize' number of timestamps
        for timestamp in timestamps_new[:batchsize]:

            B = Image.open(f"data/JXL/{timestamp}/HIMAWARI-8_AHI_B01_{timestamp}_FLDK.jxl")
            G = Image.open(f"data/JXL/{timestamp}/HIMAWARI-8_AHI_B02_{timestamp}_FLDK.jxl")
            R = Image.open(f"data/JXL/{timestamp}/HIMAWARI-8_AHI_B03_{timestamp}_FLDK.jxl")
            V = Image.open(f"data/JXL/{timestamp}/HIMAWARI-8_AHI_B04_{timestamp}_FLDK.jxl")

            # check that images are grayscale and without alpha
            if len(B.getbands()) != 1 or len(B.getbands()) != 1 or len(B.getbands()) != 1 or len(B.getbands()) != 1:
                raise ValueError("Unexpected iamge depth. Was expecting single channel (grayscale and without alpha)")
            # check that all iamges are 11000 x 11000
            if B.size != (11000,11000) or G.size != (11000,11000) or R.size != (11000,11000) or V.size != (11000,11000):
                raise ValueError("Unexpected iamge size. Was expecting 11000 x 11000 pixels.")
            
            # for each pixel in the imageset
            for ii in range(0,11000):
                for jj in range(0,11000):

                    b = B.getpixel((ii,jj))
                    g = G.getpixel((ii,jj))
                    r = R.getpixel((ii,jj))
                    v = V.getpixel((ii,jj))

                    # exceptions:
                    # skip if any value is less than 8
                    # skip if any value is equal to 255
                    cond_1 = b < 8 or g < 8 or r < 8 or v < 8
                    cond_2 = b == 255 or g == 255 or r == 255 or v == 255
                    if not (cond_1 or cond_2):
                        histogram[b,g,r,v] += 1

                    # status update every 1 %
                    if ii%110 == 0 :
                        print("\r", f"Processing timestamp {ts_so_far}/{ts_total} at {int(100 * ii/11000)}%    ", end='')

            # ii == 10999 special case
            print("\r", f"Processing timestamp {ts_so_far}/{ts_total} at 100%    ", end='')
            
            # increment counter
            ts_so_far += 1

        # once done, write histogram to file
        print("\nWriting output array")
        histogram.tofile(f"{outfile}.bin")

        # append information to all.txt
        with open("data/BIN/all.txt", 'a') as file:
            file.write('\n')
            file.write('\n'.join(timestamps_new[:batchsize]))
        # write batch information to batch.txt
        with open(f"data/BIN/batch_{batch_num:04d}.txt", 'w') as file:
            file.write('\n'.join(timestamps_new[:batchsize]))

        # remove first 'batchsize' timestamps from timestamps_new list
        del timestamps_new[:batchsize]

        # increment batch number
        batch_num += 1

    print("Batch processing complete." , len(timestamps_new) , "timestamps remain (reason: less than batch size)")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Process all new JXL files and save batched data to disk.")

    parser.add_argument("--count",
                    type=int,
                    default=30,
                    help='number of timestamps to batch in a single output file. (default is 30)',
                    )
    
    args = parser.parse_args()

    process(batchsize=args.count)
