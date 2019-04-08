
# coding: utf-8

# In[2]:


# This code deletes the all-black NDVIclean scenes and generate a mask for each NDVIclean(for later data fusion)
import os
import numpy as np
import gdal,osr

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

Sitename = ['SFREC','HREC','Hwy36','SLO']
HHHVVV = {'SFREC':'002008','HREC':'001007_008','Hwy36':'002007','SLO':'002011'}
for site in Sitename:   
    Landsat_NDVIclean_Path = '/z0/lh349796/Rangeland/landsat_data/ARD/'+HHHVVV[site]+'/II_Input_data/'+site
    for filename in os.listdir(Landsat_NDVIclean_Path):
        if filename.endswith('NDVIclean.tif'):
            print('1.1-'+site+'-working on '+ filename)
            file = os.path.join(Landsat_NDVIclean_Path,filename)
            data = raster2array(file,1)
            rastersum = np.sum(data)
            pixelnum = data.shape[0]*data.shape[1]
            if rastersum<pixelnum*0.05*0.1:
                print('1.1-'+site+'-removed-'+ str(rastersum))
                os.remove(file)
            else:
                print('1.1-'+site+'-mask generated-'+ str(rastersum))
                data[data!=0] = 1
                outfile = os.path.join(Landsat_NDVIclean_Path,file[:-13]+'mask.tif')
                array2raster(file,outfile,data)
                

