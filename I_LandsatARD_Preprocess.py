
# coding: utf-8

# In[143]:


import os
from osgeo import gdal
import osr
from copy import deepcopy
import numpy as np

## Define functions
def raster2array(rasterfn,i):
    raster = gdal.Open(rasterfn)
    band = raster.GetRasterBand(i)
    return band.ReadAsArray()

def array2raster(rasterfn,newRasterfn,array):
    raster = gdal.Open(rasterfn)
    geotransform = raster.GetGeoTransform()
    originX = geotransform[0]
    originY = geotransform[3]
    pixelWidth = geotransform[1]
    pixelHeight = geotransform[5]
    cols = raster.RasterXSize
    rows = raster.RasterYSize

    driver = gdal.GetDriverByName('GTiff')
    outRaster = driver.Create(newRasterfn, cols, rows, 1, gdal.GDT_Float32)
    outRaster.SetGeoTransform((originX, pixelWidth, 0, originY, 0, pixelHeight))
    outband = outRaster.GetRasterBand(1)
    outband.WriteArray(array)
    outRasterSRS = osr.SpatialReference()
    outRasterSRS.ImportFromWkt(raster.GetProjectionRef())
    outRaster.SetProjection(outRasterSRS.ExportToWkt())    
    
bit_flags = {
        "5": {
            "Fill": [0],
            "Clear": [1],
            "Water": [2],
            "Cloud Shadow": [3],
            "Snow": [4],
            "Cloud": [5],
            "Low Cloud Confidence": [6],
            "Medium Cloud Confidence": [7],
            "High Cloud Confidence": [6, 7]
        },
        "7": {
            "Fill": [0],
            "Clear": [1],
            "Water": [2],
            "Cloud Shadow": [3],
            "Snow": [4],
            "Cloud": [5],
            "Low Cloud Confidence": [6],
            "Medium Cloud Confidence": [7],
            "High Cloud Confidence": [6, 7]
        },
        "8": {
            "Fill": [0],
            "Clear": [1],
            "Water": [2],
            "Cloud Shadow": [3],
            "Snow": [4],
            "Cloud": [5],
            "Low Cloud Confidence": [6],
            "Medium Cloud Confidence": [7],
            "High Cloud Confidence": [6, 7],
            "Low Cirrus Confidence": [8],
            "Medium Cirrus Confidence": [9],
            "High Cirrus Confidence": [8, 9],
            "Terrain Occlusion": [10]
        }
    }
# import numpy as np
# a=raster2array('C:\\Users\\GraceLiu\Downloads\\LC08_CU_001008_20170824_20181121_C01_V01_SR\\LC08_CU_001008_20170824_20181121_C01_V01_PIXELQA.tif',1)
# test = a[1000:1010,1000:1010]
# sensor = 'L8'
# output_bands = ['Cloud Shadow','Water',"High Cloud Confidence"]#"High Cloud Confidence"]
# use bit logic to return only target values
def extract_bits(in_rasterarray,sensor,output_bands):
    in_rasterarray = raster2array(in_rasterarray,1) 
    bit_bool_output = np.ones([in_rasterarray.shape[0],in_rasterarray.shape[1]])
    for bv in output_bands:
        bit_bool = np.zeros([in_rasterarray.shape[0],in_rasterarray.shape[1]])
        for row in range(in_rasterarray.shape[0]):
            for col in range(in_rasterarray.shape[1]):
                v = in_rasterarray[row,col]
                bit_value = bit_flags[sensor][bv]           
                if len(bit_value) == 1:  # single bit
                    # copy the dictionary and remove the desired single bit element
                    temp_bit_flags = deepcopy(bit_flags[sensor])
                    del temp_bit_flags[bv]
                    # search the rest of dictionary and see if the desired bit exists in other elements (2-bit attribute)
                    two_bit_elem = bit_value[0] in [p for q in temp_bit_flags.values() for p in q]
                    if two_bit_elem:
                        print(two_bit_elem)
                        # if the bit exists in a 2-bit element, check the status of the adjacent bit
                        for flags, value in bit_flags[sensor].iteritems():
                            # if previous bit is 1, then pass
                            if value == [bit_value[0]-1,bit_value[0]]:
                                if v & 1 << (bit_value[0]-1) > 0: # Check the neighbour bit
                                    pass
                                else:
                                    bit_bool[row,col]=(v & 1 << bit_value[0] > 0)
                            # if next bit is 1, then pass
                            elif value == [bit_value[0],bit_value[0]+1]:
                                if v & 1 << (bit_value[0]+1) > 0: # Check the neighbour bit
                                    pass
                                else:
                                    bit_bool[row,col]=(v & 1 << bit_value[0] > 0)
                    else:
                        bit_bool[row,col]=(v & 1 << bit_value[0] > 0)

                elif len(bit_value) > 1:  # 2+ bits
                    bits = []
                    for b in bit_value:
                        bits.append(v & 1 << b > 0)
                    if all(bits):
                        bit_bool[row,col]=(True)
                    else:
                        bit_bool[row,col]=(False)
        # return raster values that match bit(s)
        bit_bool=1-bit_bool
        bit_bool_output=np.multiply(bit_bool_output, bit_bool)
    return(bit_bool_output)

# In[33]:


# This code is for processing the raw ARD data to clean NDVI
# ########################################################################################################################
# ###~~~~~~~~~~~~~~STEP ONE Unzip/Clipping/reproject/QC~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
# ########################################################################################################################
import shutil
import glob,math,json,ogr
from datetime import datetime
from osgeo.gdalnumeric import *
from osgeo.gdalconst import *
import sys

# # Define Directories
Satellites = ['LT05','LE07','LC08']
SiteName = 'SFREC'
Projection = 'EPSG:32610'#WGS84 EPSG:4326'; EPSG:32610 WGS84 utm zone 10 N #'EPSG:26910'# NAD83  utm zone 10 N
ARD_Box = '-2143000 2098000 -2130000 2084000'## xmin ymax xmax ymin
UTM_Box = '642770 4342784 649834 4352876'## xmin ymin xmax ymax
# need to add the te_srs parameter in gralwarp because 042035 is in UTM 11
HHHVVV = '002008' # Horizontal tile number and Vertical tile number
Landsat_org_tar_Path ='/z0/Group/Satellite_Data/LandSat/ARD/'+HHHVVV #Zipped file directory
Landsat_Raw_Path = '/z0/Group/Satellite_Data/LandSat/ARD/'+HHHVVV+ '_Unziped' # Where extracted data are saved
Landsat_Clip_Path = '/z0/lh349796/Rangeland/landsat_data/ARD/'+HHHVVV+'/I_Clipped_data/'+ SiteName + '/'#'/z0/lh349796/Rangeland/landsat_data/ARD//I_Reprojected_data/'+ SiteName
Landsat_Inputs_Path = '/z0/lh349796/Rangeland/landsat_data/ARD/'+HHHVVV+'/II_Input_data/'+ SiteName + '/'#'/z0/lh349796/Rangeland/landsat_data/ARD/I_Clipped_data/'+ SiteName #Where reprojected and clipped data are saved
Cloud_threshold = {
        "5": ["Cloud Shadow","Cloud","High Cloud Confidence"],
        "7": ["Cloud Shadow","Cloud","High Cloud Confidence"],
        "8": ["Cloud Shadow","Cloud","High Cloud Confidence","High Cirrus Confidence"]
    }

if not os.path.exists(Landsat_Raw_Path):
    os.makedirs(Landsat_Raw_Path)
if not os.path.exists(Landsat_Clip_Path):
    os.makedirs(Landsat_Clip_Path)
if not os.path.exists(Landsat_Inputs_Path):
    os.makedirs(Landsat_Inputs_Path)
    
## Define functions
def ClipbyBox(rasterfn,orirasterfn,cliprasterfn,bound):
    current_file = os.path.join(orirasterfn, rasterfn)
    export_file = os.path.join(cliprasterfn, rasterfn)
    os.system('gdal_translate -of GTiff -projwin ' + bound + ' "' + current_file + '" "' + export_file + '"')

    
#~Step1.1: unzip .tar files
# ## for python 3.5+
# Files = glob.glob(Landsat_org_tar_Path + '/**/*.tar', recursive=True)
# ## Landsat_org_tar_Path/     the dir
# ## **/       every file and dir under my_path
# ## *.tar     every file that ends with '.tar'
# for python 3.5-
# import fnmatch
# Files = []
# for root, dirnames, filenames in os.walk(Landsat_org_tar_Path):
#     for filename in fnmatch.filter(filenames, '*.tar'):
#         Files.append(os.path.join(root, filename))
# for file in Files:
#     if file.endswith("SR.tar"):
#         print("1.1-Extracting "+file)
#         # FileName = os.path.join(Landsat_org_tar_Path, file)
#         os.system('tar xvf "' + file + '" -C ' + Landsat_Raw_Path)
## Loop through file directory, create a list of date and band
date = []
for file in os.listdir(Landsat_Raw_Path):
    if file.endswith(".tif"):
        date.append(file.split('_')[3])
Datelist = list(set(date))
# #~Step1.2: Clip XXX.tif using ard box
# In_Directory = [Landsat_Raw_Path]
# print("1.2-Reprojecting and cliping...")
# for directory in In_Directory:
#     for file in os.listdir(directory):
#         if file.startswith(('LT05','LE07')):
#             if file.endswith(('SRB3.tif','SRB4.tif','PIXELQA.tif')):
#                 print('1.2-Working on '+ file)
#                 ClipbyBox(file,Landsat_Raw_Path, Landsat_Clip_Path,ARD_Box)
#         elif file.startswith('LC08'):
#             if file.endswith(('SRB4.tif','SRB5.tif','PIXELQA.tif')):
#                 print('1.2-Working on '+ file)
#                 ClipbyBox(file,Landsat_Raw_Path, Landsat_Clip_Path,ARD_Box)
#     print("1.2-Done!")
#~Step1.3: Calculate NDVI.tif and NDVIclean.tif
for date in Datelist:
    print('1.3-Calculating NDVI for '+date + '...')
    for satellite in Satellites:
        print('1.3-Finding ' + satellite +'...')
        paths = glob.glob(os.path.join(Landsat_Clip_Path,satellite+'*'+date+'_[0-9]*SRB*.tif'))
        if paths:
            QA_path = glob.glob(os.path.join(Landsat_Clip_Path,satellite+'*'+date+'_[0-9]*PIXELQA.tif'))
            if QA_path:
                infile = QA_path[0]
                sensor = os.path.basename(QA_path[0])[3]
                print('1.3-unpacking QA band for L'+ sensor + ' ' + date)
                qa_mask = extract_bits(infile,sensor,Cloud_threshold[sensor])#0 means noise pixel 1 means clean pixel
                print ('1.3-QA band ' + os.path.basename(QA_path[0]) + 'unpacked'   )
            else:
                print('1.3-QA band does not exists for' + satellite + ' ' + date)
            paths.sort(key = lambda x: x.split('_')[-1])
            if len(paths)<2:
                print('1.3-missing RED or NIR band needed for calculating NDVI...')
            elif len(paths)==2:
                RED = raster2array(paths[0],1)
                NIR = raster2array(paths[1],1)
                NDVI = (1.0*NIR-RED)/(NIR+RED)
                filename = os.path.basename(paths[0])[:-8]+'NDVI.tif'
                array2raster(paths[0],os.path.join(Landsat_Clip_Path,filename),NDVI)
                NDVI_clean = np.multiply(NDVI,qa_mask)
                filename = os.path.basename(paths[0])[:-8]+'NDVIclean.tif'
                array2raster(paths[0],os.path.join(Landsat_Clip_Path,filename),NDVI_clean)
      #else:
      #    print('1.3-no '+ satellite + ' image exists for ' + date)
#~Step1.4: clip and reproject NDVIclean.tif
In_Directory = [Landsat_Clip_Path]
for directory in In_Directory:
    for file in os.listdir(directory):
        if file.endswith('NDVIclean.tif'):
            current_file = os.path.join(directory, file)
            export_file = os.path.join(Landsat_Inputs_Path, file)
            print("Reprojecting -raster data will be resampled when being reprojected - and clipping data " + file)
            os.system('gdalwarp -overwrite -t_srs "' + Projection + '" -tr 30 30 -r near -te ' + UTM_Box + ' "' + current_file + '" "' + export_file + '"')
            print("done!")

