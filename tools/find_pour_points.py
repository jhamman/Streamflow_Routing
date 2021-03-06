#!/usr/local/bin/python
"""
Find the outlet location of basins in a grid
"""
import numpy as np
from netCDF4 import Dataset
import time as tm
import argparse
import os,sys

def main():
    input_file, output_file, verbose = process_command_line()

    #Load input Rasters (Basin Mask and Accumulated Upstream Area)
    #Input rasters need to be the same size

    if verbose:
        print 'Reading input file: %s' %input_file
    f = Dataset(input_file,'r')
    Basin_ID = f.variables['Basin_ID'][:]
    Source_Area = f.variables['Source_Area'][:]
    lons = f.variables['lon'][:]
    lats = f.variables['lat'][:]
    f.close()

    res = lons[1]-lons[0]
    
    #Make arrays of same dimensions as input arrays of lat/lon values
    x,y = np.meshgrid(lons,lats)

    #Setup basin in/out arrays
    basin_ids = np.arange(np.min(Basin_ID),np.max(Basin_ID))
    num_basins = len(basin_ids)

    basin = np.zeros(num_basins,dtype='i')
    max_area =  np.zeros(num_basins,dtype='i')
    x_outlet = np.zeros(num_basins,dtype='f')
    y_outlet = np.zeros(num_basins,dtype='f')
    min_x = np.zeros(num_basins,dtype='f')
    max_x = np.zeros(num_basins,dtype='f')
    min_y = np.zeros(num_basins,dtype='f')
    max_y = np.zeros(num_basins,dtype='f')
    
    #Loop over every basin id, finding the maximum upstream area [and location]
    #and record the basin#,longitude,latitude,area
    if verbose:
        sys.stdout.write('Done reading input file...\n ')
        sys.stdout.write('Searching in %i basins for pour points\n' % num_basins)

    for i,j in enumerate(basin_ids):
        if verbose:
            sys.stdout.write('On basin %i of %i' % (i,num_basins))
            sys.stdout.flush()
            sys.stdout.write('\r')
        basin[i]=np.int(j)
        inds = np.nonzero(Basin_ID==j)
        x_basin = x[inds]
        y_basin = y[inds]
        max_area[i] = np.int(max(Source_Area[inds]))
        max_ind = np.argmax(Source_Area[inds])
        x_outlet[i] = x_basin[max_ind]
        y_outlet[i] = y_basin[max_ind]
        min_x[i] = min(x_basin)
        max_x[i] = max(x_basin)+res
        min_y[i] = min(y_basin)
        max_y[i] = max(y_basin)+res

    if verbose:
        print 'writing to outfile:', output_file
    if os.path.splitext(output_file)[1] != '.nc':    
        write_ascii_file(basin, x_outlet, y_outlet, max_area, min_x, min_y,
                         max_x, max_y, output_file)
    else:
        write_netcdf_file(basin, x_outlet, y_outlet, max_area, min_x, min_y,
                          max_x, max_y, output_file)

    return

def write_netcdf_file(basin, x_outlet, y_outlet, max_area, min_x, min_y,
                        max_x, max_y, out_file):
    """
    save the list of pour points as a comma seperated text file
    This file is directly importable into arcgis for validation purposes
    """
    f = Dataset(out_file,'w', format='NETCDF4')
    # set dimensions
    points = f.createDimension('points', None)
    # initialize variables
    OIDs = f.createVariable('OID','i8',('points',))
    x_outlets = f.createVariable('x_outlet','f8',('points',))
    y_outlets = f.createVariable('y_outlet','f8',('points',))
    max_areas = f.createVariable('max_area','i8',('points',))
    min_xs = f.createVariable('min_x','f8',('points',))
    min_ys = f.createVariable('min_y','f8',('points',))
    max_xs = f.createVariable('max_x','f8',('points',))
    max_ys = f.createVariable('max_y','f8',('points',))
    
    # write attributes for netcdf
    f.description = 'Pour Points'
    f.history += ' '.join(sys.argv) + '\n'
    f.history = 'Created: {}\n'.format(tm.ctime(tm.time()))
    f.source = sys.argv[0] # prints the name of script used
    
    OIDs.long_name = 'Basin Identifier'
    OIDs.standard_name = 'OID'

    x_outlets.long_name = 'longitude_coordinate_of_pour_point'
    x_outlets.standard_name = 'longitude'
    x_outlets.units = 'degrees_east'

    y_outlets.long_name = 'latitude_coordinate_of_pour_point'
    y_outlets.standard_name = 'latitude'
    y_outlets.units = 'degrees_north'

    max_areas.long_name = 'upstream_basin_area'
    max_areas.description = 'number of upstream grid cells'
    max_areas.standard_name = 'longitude'
    max_areas.units = 'grid_cells'

    min_xs.long_name = 'minimum_longitude_coordinate_of_basin'
    min_xs.standard_name = 'min_longitude'
    min_xs.units = 'degrees_east'

    min_ys.long_name = 'minimum_latitude_coordinate_of_basin'
    min_ys.standard_name = 'min_latitude'
    min_ys.units = 'degrees_north'

    max_xs.long_name = 'maximum_longitude_coordinate_of_basin'
    max_xs.standard_name = 'max_longitude'
    max_xs.units = 'degrees_east'

    max_ys.long_name = 'maximum_latitude_coordinate_of_basin'
    max_ys.standard_name = 'max_latitude'
    max_ys.units = 'degrees_north'

    OIDs[:] = basin
    x_outlets[:] = x_outlet
    y_outlets[:] = y_outlet
    max_areas[:] = max_areas
    min_xs[:] = min_x
    min_ys[:] = min_y
    max_x[:] = max_x
    max_y[:] = max_y

    f.close()
    return
    
def write_ascii_file(basin, x_outlet, y_outlet, max_area, min_x, min_y,
                        max_x, max_y, out_file):
    """
    save the list of pour points as a comma seperated text file
    This file is directly importable into arcgis for validation purposes
    """
    fmt = ['%i', '%.10f', '%.10f', '%i', '%.10f', '%.10f', '%.10f', '%.10f']
    out = np.column_stack((basin,x_outlet,y_outlet,max_area,
                            min_x,min_y,max_x,max_y))
    header = 'OID, longitude, latitude, basin_area, min_lon, min_lat, \
    max_lon, max_lat\n'
    with file(out_file,'w') as outfile:
        outfile.write(header)
        np.savetxt(outfile,out,fmt=fmt,delimiter=',')
    return

def process_command_line():
    """
    Parse arguments and assign flags for further loading of variables, for
    information on input arguments, type ConvolutionSystemTests -h
    """
    desc = """Finds pour points in routing model input netcdf
    Input file is required to have the following variables:
     - Basin_ID
     - Source_Area
    Will return a text file or netcdf depending on output_file's file sufix"""
    # Parse arguments
    parser = argparse.ArgumentParser(description=desc,
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("input_file",
                        help="Input netCDF file contianing variables \
                        Basin_ID and Source_Area")
    parser.add_argument("output_file", metavar='outfile.<txt|nc>',
                        help="Output file (suffix dependent)")
    parser.add_argument("-v","--verbose",action='store_true',
                        help="Turn on Verbose Output")
    args = parser.parse_args()
    input_file = args.input_file
    output_file = args.output_file
    verbose = args.verbose
    
    return input_file, output_file, verbose
#################################
if __name__ == '__main__':
    main()
