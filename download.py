#!/usr/bin/env python3

import argparse
import boto3
from botocore import UNSIGNED
from botocore.config import Config
from datetime import datetime
import os
from tqdm import tqdm


def download(years, months, days, hours, minutes):

    # set up the S3 client
    S3_CLIENT = boto3.client("s3", region_name="us-east-1", config=Config(signature_version=UNSIGNED))
    BUCKET = "noaa-himawari8"

    # bands to download
    bands = ["B01", "B02", "B03", "B04"]

    # for each combination of time units
    for year in years:
        for month in months:
            for day in days:
                for hour in hours:
                    for minute in minutes:

                        # if the date is invalid, silently skip it
                        try:
                            datetime(year, month, day, hour, minute)
                        except ValueError:
                            continue

                        TIMESTAMP = f"{year}{month:02d}{day:02d}_{hour:02d}{minute:02d}"
                        LOCAL_DIR = f"data/DAT/{TIMESTAMP}"

                        # skip if local directory already exists
                        if os.path.exists(LOCAL_DIR):
                            print(f"{TIMESTAMP} already downloaded.")
                            continue
                        
                        # create a temporary directory to catch interrupted downloads
                        TEMP_DIR = f"data/DAT/{TIMESTAMP}_temp"
                        # if the previous attempt was interrupted, delete the last aplhabetical file and continue 
                        if os.path.exists(TEMP_DIR):
                            print(f"Previous download attempt for {TIMESTAMP} was interrupted. Resuming.")
                            RESUME = True
                        else:
                            os.makedirs(TEMP_DIR)
                            RESUME = False

                        S3_FILE_PATH = f"AHI-L1b-FLDK/{year}/{month:02d}/{day:02d}/{hour:02d}{minute:02d}"
                        S3_FILE_PREFIX = f"HS_H08_{year}{month:02d}{day:02d}_{hour:02d}{minute:02d}"

                        # download bands B01, B02, B03, B04, all 10 segments each
                        for band in ["B01", "B02", "B03", "B04"]:

                            # image resolution depends on band number
                            if band == "B03":
                                resolution = "R05"
                            else:
                                resolution = "R10"

                            for segment in ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10"]:

                                S3_FILE_KEY = f"{S3_FILE_PATH}/{S3_FILE_PREFIX}_{band}_FLDK_{resolution}_S{segment}10.DAT.bz2"
                                LOCAL_NAME =  f"{TEMP_DIR}/{S3_FILE_PREFIX}_{band}_FLDK_{resolution}_S{segment}10.DAT.bz2"

                                # download the file with progress bar
                                object_size = S3_CLIENT.head_object(Bucket=BUCKET, Key=S3_FILE_KEY)["ContentLength"]

                                # if resuming from interuppted attempt
                                if RESUME:
                                    # if the local file exists
                                    if os.path.exists(LOCAL_NAME):
                                        local_size = os.path.getsize(LOCAL_NAME)
                                        # if file exists and is correct size, skip it
                                        if local_size == object_size:
                                            continue
                                        # if file exists but is smaller than expected, delete it and redownload
                                        else:
                                            os.remove(LOCAL_NAME)

                                # download with progress bar
                                with tqdm(total=object_size, unit="B", unit_scale=True, desc=LOCAL_NAME) as pbar:
                                    S3_CLIENT.download_file(
                                        Bucket=BUCKET,
                                        Key=S3_FILE_KEY,
                                        Filename=LOCAL_NAME,
                                        Callback=lambda bytes_transferred: pbar.update(bytes_transferred)
                                        )
                                    
                        # rename the temporary directory to the final directory name
                        os.rename(TEMP_DIR, LOCAL_DIR)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Download Himawari-8 B01 B02 B03 B04 .DAT files.")
    
    parser.add_argument("--years",
                        type=int,
                        nargs='+',
                        help='list of years in range 2016-2022',
                        choices=range(2016, 2023)
                        )
    
    parser.add_argument("--months",
                        type=int,
                        nargs='+',
                        help='list of months in range 01-12',
                        choices=range(1, 13)
                        )
    
    parser.add_argument("--days",
                        type=int,
                        nargs='+',
                        help='list of days in range 01-31',
                        choices=range(1, 32)
                        )
    
    parser.add_argument("--hours",
                        type=int,
                        nargs='+',
                        help='list of hours in range 00-23',
                        choices=range(0, 24)
                        )
    
    parser.add_argument("--minutes",
                        type=int,
                        nargs='+',
                        help='list of minutes in range 0-50 (in increments of 10)',
                        choices=range(0, 60, 10)
                        )
    
    args = parser.parse_args()

    download(years=args.years, months=args.months, days=args.days, hours=args.hours, minutes=args.minutes)
