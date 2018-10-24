#!python
# This program will read the NDVI and NDVI Anomaly values from a given point (in lon/lat).
# This connection string is needed for pulling data from the "postgres" database, which contains all NDVI data for countries, states, and districts.
# It is not needed by this program, but is included here because it shows the credentials to access the already-populated data set.
# connectionString = psycopg2.connect("dbname='*****' user='******' host='********' password='********'")

import os, psycopg2, glob2, gzip, rasterio
from math import floor

# Input values
year = 2012
dayOfYr = 213
lonX = -123
latY = 37

dayOfYr = dayOfYr - (dayOfYr % 8 - 1) # Find the beginning of the 8-day set
lonXRow = floor((180 + lonX) / 9) # Row (0 to 19)
latYCol = floor((90 - latY) / 9) # Column (0 to 39)
xy = 'x%02dy%02d'%(lonXRow,latYCol) # Formatted for file names
xPix = int(round(floor(180 + lonX) % 9 * 444.4444))
yPix = int(round(floor(90 - latY) % 9 * 444.4444))
baseURL = "wget -nd -nv -N -c -t 3 -R '*5v3*' -R '*DOY.tif*' ftp://gimms.gsfc.nasa.gov/MODIS/std/GMYD09Q1/tif/NDVI"
for pathSuffix in ['/%s/%03d/*%s*'%(year,dayOfYr,xy),'_anom_S2003-2015/%s/%03d/*%s*'%(year,dayOfYr,xy)]:
	os.system(baseURL + pathSuffix)

anFl = 'GMYD09Q1.A%s%03d.08d.latlon.%s.6v1.NDVI_anom_S2003-2015.tif.gz'%(year,dayOfYr,xy)
ndFl = 'GMYD09Q1.A%s%03d.08d.latlon.%s.6v1.NDVI.tif.gz'%(year,dayOfYr,xy)
for fl in [anFl,ndFl]:
	try:
		with gzip.open(fl,'rb') as aZ:
			with open(fl[0:-3],'w+b') as aT: aT.write(aZ.read())
	except Exception as gzAf:
		print 'Could not extract', gzAf
		continue

dat = rasterio.open(ndFl[0:-3])
dat = dat.read(1)
print 'NDVI:',dat[xPix][yPix] * .004

dat = rasterio.open(anFl[0:-3])
dat = dat.read(1)
print 'Anomaly:',(dat[xPix][yPix] -125) * .008


for f in glob2.glob('GMY*.tif*'):
	os.remove(f)
