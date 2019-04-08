# Chapter2_Satellite_Rangeland

## Project Summary
This repository contains codes for the second chapter of my dissertation, where I'm mapping forage production of California rangelands using multisensor remote sensing satellite data and climate data. 

![Chapter2](https://user-images.githubusercontent.com/17130674/55708321-7d16e980-599a-11e9-80db-fdad540ae9ec.png)

## Code Descriptions

### 1. I_LandsatARD_Preprocessing.py

This code performs all the necessary preprocessing, including unzipping, clipping, and quality control, onto the zipped Landsat ARD downloads. The ARD images are downloaded using the [EarthExplorer Bulk Download Application](EarthExplorer Bulk Download Application (BDA))

- **packages**: os, gdal, osr, copy, numpy, shutil, glob, math, json, ogr, datetime, and sys

- **input**: Landsat ARD downloads (.tar)

- **output**: preprocessed images (.tif)

### 2. II_Prepare_LandsatNDVI.py

This code deletes the all-black NDVI scenes and generate a mask for each NDVI images (for later data fusion).

- **packages**: os, numpy, gdal and osr

- **input**: Landsat NDVI images (.tif)

- **output**: qa_masks (.tif)

## Contacts

Reach out to me at my website at https://gracehliu.weebly.com/contact.html.
