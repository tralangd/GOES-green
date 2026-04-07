#!/usr/bin/env python3

import argparse
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
import os
import sys

from PIL import Image
import pillow_jxl
Image.MAX_IMAGE_PIXELS = 500000000 # increase default limit


def show_image(TS):

    # let datetime handle timestamp validation
    datetime.strptime(str(TS) , "%Y%m%d%H%M")

    # string format for filenames
    TIMESTAMP = str(TS)[0:8] + '_' + str(TS)[8:12]

    # validate requested timestamp files exist
    p1 = os.path.isfile(f"../data/JXL/{TIMESTAMP}/HIMAWARI-8_AHI_B01_{TIMESTAMP}_FLDK.jxl")
    p2 = os.path.isfile(f"../data/JXL/{TIMESTAMP}/HIMAWARI-8_AHI_B02_{TIMESTAMP}_FLDK.jxl")
    p3 = os.path.isfile(f"../data/JXL/{TIMESTAMP}/HIMAWARI-8_AHI_B03_{TIMESTAMP}_FLDK.jxl")
    p4 = os.path.isfile(f"../data/JXL/{TIMESTAMP}/HIMAWARI-8_AHI_B04_{TIMESTAMP}_FLDK.jxl")
    # if unsuccessful
    if not (p1 and p2 and p3 and p4):
        #print the error message and exit the program
        sys.exit(f"JXL Images for timestamp {TIMESTAMP} not found.")

    # read in LUT
    LUT = np.fromfile("../data/LUT.bin", dtype=np.uint8).reshape(256,256,256)

    B = Image.open(f"../data/JXL/{TIMESTAMP}/HIMAWARI-8_AHI_B01_{TIMESTAMP}_FLDK.jxl").resize((1000,1000),Image.LANCZOS)
    G = Image.open(f"../data/JXL/{TIMESTAMP}/HIMAWARI-8_AHI_B02_{TIMESTAMP}_FLDK.jxl").resize((1000,1000),Image.LANCZOS)
    R = Image.open(f"../data/JXL/{TIMESTAMP}/HIMAWARI-8_AHI_B03_{TIMESTAMP}_FLDK.jxl").resize((1000,1000),Image.LANCZOS)
    V = Image.open(f"../data/JXL/{TIMESTAMP}/HIMAWARI-8_AHI_B04_{TIMESTAMP}_FLDK.jxl").resize((1000,1000),Image.LANCZOS)

    # AHI Green Channel
    img_ahi = Image.merge('RGB', (R,G,B))
    plt.figure(1)
    plt.imshow(np.array(img_ahi))
    plt.axis('off')
    plt.title('AHI Band 02\n(0.51um \'Green\')')

    # TrueColor Synthetic Green
    G_tc = Image.fromarray( np.uint8( 0.45*np.float32(np.array(B)) + 0.45*np.float32(np.array(R)) + 0.10*np.float32(np.array(V)) ) )
    img_tc = Image.merge('RGB', (R,G_tc,B))
    plt.figure(2)
    plt.imshow(np.array(img_tc))
    plt.axis('off')
    plt.title('CIMSS Natural True Color\n(Green = 0.45*Blue + 0.45*Red + 0.10*Veggie)')
    
    # LUT Synthetic Green
    G_lut = Image.fromarray(LUT[np.array(B),np.array(R),np.array(V)])
    img_lut = Image.merge('RGB', (R,G_lut,B))
    plt.figure(3)
    plt.imshow(np.array(img_lut))
    plt.axis('off')
    plt.title('Color Lookup Table\n(This Work)')
    
#   # DEBUG
#   # save figures for README.md
#   plt.figure(1)
#   plt.savefig(f'{TIMESTAMP}_AHI.png', dpi=300, bbox_inches='tight')
#   plt.figure(2)
#   plt.savefig(f'{TIMESTAMP}_TC.png', dpi=300, bbox_inches='tight')
#   plt.figure(3)
#   plt.savefig(f'{TIMESTAMP}_LUT.png', dpi=300, bbox_inches='tight')
#   # END DEBUG

    plt.show()


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Visually Compare RGB Images generated from AHI Band 02, CIMSS True Color, and this work's Color LUT.")
    
    parser.add_argument("--timestamp",
                type=int,
                help='Choose a specific timestamp for output image generation.',
                )
    
    args = parser.parse_args()

    show_image(TS=args.timestamp)
    