#!/usr/bin/env python3

import argparse
import numpy as np
from scipy.interpolate import griddata
from scipy.ndimage import gaussian_filter


def generate_LUT():

    # read batch_merged.bin into memory
    print("Reading data file batch_merged.bin")
    histogram = np.fromfile("data/BIN/batch_merged.bin", dtype=np.uint32).reshape(256,256,256,256)

    # initialize LUT
    print("Computing known values")
    LUT_base = np.zeros( shape=(256,256,256) , dtype=np.uint8 )

    # flatten data along the "green" dimension
    for b in range(0,256):
        for r in range(0,256):
            for v in range(0,256):

                # only consider data valid if there are more than 1000 samples for this BRV triplet
                count = np.sum(np.uint64(histogram[b,:,r,v]))
                if count > 1000:

                    # treat distribution of greens as a probability mass function
                    # flatten by taking the expected value of the PMF
                    weighted_sum = np.uint64(0)
                    for g in range(0,256):
                        weighted_sum += np.uint64(g) * np.uint64(histogram[b,g,r,v])

                    LUT_base[b,r,v] = np.uint8(weighted_sum / count)

                else:
                    LUT_base[b,r,v] = np.uint8(0)

            print("\r", f"{float(100*(b*256 + r + 1)/65536) : .4f} %", end='')

    # free memory
    del histogram

#    # DEBUG
#    # write LUT_base to file
#    # this is only used for README.md figures
#    print("\nWriting lookup table to data/LUT_base.bin")
#    LUT_base.tofile('data/LUT_base.bin')
#    # END DEBUG

    # need mask to interpolate entries which did not have any histogram data
    print("\nInterpolating unknown values")
    LUT_mask = LUT_base != 0

    # force boundary conditions (12 edges of cube)
    # boundary conditions are set to average of brv triple along that edge
    LUT_base[0  , 0   , :  ] = np.uint8( (  0 +   0 + np.arange(0,256))/3 )
    LUT_base[0  , :   , 0  ] = np.uint8( (  0 +   0 + np.arange(0,256))/3 )
    LUT_base[:  , 0   , 0  ] = np.uint8( (  0 +   0 + np.arange(0,256))/3 )
    LUT_base[0  , 255 , :  ] = np.uint8( (  0 + 255 + np.arange(0,256))/3 )
    LUT_base[255, 0   , :  ] = np.uint8( (  0 + 255 + np.arange(0,256))/3 )
    LUT_base[0  , :   , 255] = np.uint8( (  0 + 255 + np.arange(0,256))/3 )
    LUT_base[255, :   , 0  ] = np.uint8( (  0 + 255 + np.arange(0,256))/3 )
    LUT_base[:  , 0   , 255] = np.uint8( (  0 + 255 + np.arange(0,256))/3 )
    LUT_base[:  , 255 , 0  ] = np.uint8( (  0 + 255 + np.arange(0,256))/3 )
    LUT_base[255, 255 , :  ] = np.uint8( (255 + 255 + np.arange(0,256))/3 )
    LUT_base[255, :   , 255] = np.uint8( (255 + 255 + np.arange(0,256))/3 )
    LUT_base[:  , 255 , 255] = np.uint8( (255 + 255 + np.arange(0,256))/3 )
    # update mask
    LUT_mask[0  , 0   , :  ] = True
    LUT_mask[0  , :   , 0  ] = True
    LUT_mask[:  , 0   , 0  ] = True
    LUT_mask[0  , 255 , :  ] = True
    LUT_mask[255, 0   , :  ] = True
    LUT_mask[0  , :   , 255] = True
    LUT_mask[255, :   , 0  ] = True
    LUT_mask[:  , 0   , 255] = True
    LUT_mask[:  , 255 , 0  ] = True
    LUT_mask[255, 255 , :  ] = True
    LUT_mask[255, :   , 255] = True
    LUT_mask[:  , 255 , 255] = True

    # interpolating the whole 3D LUT in one go takes an unreasonably long time to complete
    # instead, take a shortcut by interpolating 2D slices in each of the three coordinate directions

    LUT_x = np.zeros( shape=(256,256,256) , dtype=np.float32 )
    grid_y, grid_z = np.mgrid[ 0:256 , 0:256 ]
    for ii in range(0,256):
        y, z = np.nonzero(LUT_mask[ii,:,:])
        LUT_x[ii,:,:] = griddata(points=(y,z), values=LUT_base[ii,y,z], xi=(grid_y,grid_z), method='linear')
        print("\r", f"Stage 1 of 3 at {float(100*(ii+1)/256) : .2f} %   ", end='')

    LUT_y = np.zeros( shape=(256,256,256) , dtype=np.float32 )
    grid_x, grid_z = np.mgrid[ 0:256 , 0:256 ]
    for ii in range(0,256):
        x, z = np.nonzero(LUT_mask[:,ii,:])
        LUT_y[:,ii,:] = griddata(points=(x,z), values=LUT_base[x,ii,z], xi=(grid_x,grid_z), method='linear')
        print("\r", f"Stage 2 of 3 at {float(100*(ii+1)/256) : .2f} %   ", end='')

    LUT_z = np.zeros( shape=(256,256,256) , dtype=np.float32 )
    grid_x, grid_y = np.mgrid[ 0:256 , 0:256 ]
    for ii in range(0,256):
        x, y = np.nonzero(LUT_mask[:,:,ii])
        LUT_z[:,:,ii] = griddata(points=(x,y), values=LUT_base[x,y,ii], xi=(grid_x,grid_y), method='linear')
        print("\r", f"Stage 3 of 3 at {float(100*(ii+1)/256) : .2f} %   ", end='')

    # DEBUG
    # replace NaN entries with average of index values
    # not sure what is causing this, but seems to only be occuring on the boundary
    LUT_average = (LUT_x + LUT_y + LUT_z)/3
    nan_indices = np.argwhere(np.isnan(LUT_average))
    for id in nan_indices:
        LUT_average[id[0],id[1],id[2]] = (id[0]+id[1]+id[2])/3
    # END DEBUG

    # first take the average of the three results
    # then perform a 3D gaussian blur to smooth out artifacts caused by the interpolation
    # lastly convert the data to uint8
    LUT = np.uint8(gaussian_filter(input=LUT_average, sigma=2))

    # write LUT to file
    print("\nWriting lookup table to data/LUT.bin")
    LUT.tofile('data/LUT.bin')

    print("Done!")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Retrieve, flatten, and interpolate values collected in batch_merged.bin")
    
    args = parser.parse_args()

    generate_LUT()
