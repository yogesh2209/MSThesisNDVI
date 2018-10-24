#!/usr/bin/python
#coding=utf-8
####
#########
###############
# IMPORTANT!
# Run this program as the database admin (postgres) so the files in the database directory will be accessible.
###############
#########
####

#wget -r -nv -c -t 3 -R '*5v3*' -R '*DOY.tif*' ftp://gimms.gsfc.nasa.gov/MODIS/std/GMYD09Q1/tif/NDVI/2008/209*
#wget -r -nv -c -t 3 -R '*5v3*' -R '*DOY.tif*' ftp://gimms.gsfc.nasa.gov/MODIS/std/GMYD09Q1/tif/NDVI_anom_S2003-2015/2008/209*

import fiona, psycopg2, warnings, gzip, sys, os, glob2, datetime, shutil, rasterio
import numpy as np, numpy.ma as ma, rasterstats as r
from collections import defaultdict; from math import floor; from cStringIO import StringIO; from osgeo import gdal; from shapely.geometry import shape
warnings.filterwarnings("ignore"); np.set_printoptions(threshold=np.nan)

gdal.SetConfigOption('GDAL_CACHEMAX', '256')


def main():
	#
	admGlobMod = 'Ukraine*' if '-demo' in sys.argv else '';
	#

	try: con = psycopg2.connect("dbname='postgres' user='' host='' password=''")
	except: con = psycopg2.connect("dbname='' user='' host='localhost' password=''")

	cur = con.cursor(); con.autocommit = True

	initTable = 'DROP TABLE IF EXISTS new_masked_ndvi;' if '-drop' in sys.argv else ''; print initTable

	cur.execute('%sCREATE TABLE IF NOT EXISTS new_masked_ndvi (region_id text, country text, state text, district text, start_date date, ndvi real, ndvi_count integer, anomaly real, anomaly_count integer, centr_lon real, centr_lat real, PRIMARY KEY (centr_lon, centr_lat, start_date));'%(initTable))

	path = '/database/gimms.gsfc.nasa.gov/';	tmp = '/dev/shm/'; files = defaultdict(str)
	admShp2 = glob2.glob('/database/gimms.gsfc.nasa.gov/shapefiles/admin2_*%s.shp'%(admGlobMod))

	if '-update' in sys.argv:
		# Select the oldest of all countries' last-updates
		cur.execute('SELECT DISTINCT country, MAX(start_date) FROM new_masked_ndvi GROUP BY country ORDER BY MAX(start_date) LIMIT 1')
		updateStart = cur.fetchone()[1] + datetime.timedelta(days=8)
		updateStartDay = updateStart.timetuple().tm_yday
		baseURL = "wget -r -nv -N -c -t 3 -R '*5v3*' -R '*DOY.tif*' ftp://gimms.gsfc.nasa.gov/MODIS/std/GMYD09Q1/tif/NDVI"
		os.chdir('/database/')

		for yrStart in xrange(updateStart.year, datetime.date.today().year + 1):
			dayOfYrStart = updateStartDay if yrStart == updateStart.year else 1
			for dayOfYr in xrange(dayOfYrStart, 365, 8):
				#This 'for' loop downloads both the NDVI and Anomaly files per year/day-of-year pair.
				for pathSuffix in ['/%s/%s*'%(yrStart,dayOfYr),'_anom_S2003-2015/%s/%s*'%(yrStart,dayOfYr)]:
					os.system(baseURL + pathSuffix)

	for fp in glob2.glob(path + '*/**/*.tif.gz'):	files[os.path.split(fp)[1]] = os.path.split(fp)[0]


	def freeSpace():
		freeSpace = os.statvfs('/dev/shm')		# Clear tmp space
		if (freeSpace[2] - freeSpace[3]) * 1.125 > freeSpace[2]:
			delFiles={}
			for fl in glob2.glob('/dev/shm/*.tif'):	delFiles[str(os.path.getctime(fl))] = fl

			delFileKeys = sorted(delFiles.keys())

			print '\n\t*\tFree space: %s, Used space: %s\t*\n'%(freeSpace[3], freeSpace[2] - freeSpace[3])
			print '\t\t\tDeleting %s files, starting with %s\n'%(int(len(delFileKeys) / 1.125), delFiles[delFileKeys[0]])

			for dF in xrange(int(len(delFileKeys) / 1.125)): os.remove(delFiles[delFileKeys[dF]])


	def getSt(shp,f,xy):
		shp=shp; f=f; xy=xy; x=int(xy[1:3]); y=int(xy[4:6])
		# Just get the data (raster_out) - calculating stats further down
		with rasterio.open(f) as src:
			affine = src.affine
			dat = src.read(1)
		xyMask = mask[y*4000:y*4000+4000,x*4000:x*4000+4000]

		statsMask = tuple(xmea for xmea in r.zonal_stats(shp, xyMask, stats='count', geojson_out=True, raster_out=True, affine=affine, nodata=None) if floor((180 + xmea['properties']['mini_raster_affine'][2]) / 9) == int(xy[1:3]) and floor((90 - xmea['properties']['mini_raster_affine'][5]) / 9) == int(xy[4:6]))

		stats = tuple(mea for mea in r.zonal_stats(shp, dat, stats='count', geojson_out=True, raster_out=True, affine=affine, nodata=None) if floor((180 + mea['properties']['mini_raster_affine'][2]) / 9) == int(xy[1:3]) and floor((90 - mea['properties']['mini_raster_affine'][5]) / 9) == int(xy[4:6]))
		return [stats, statsMask]

	def getSQLRecords():
		cur.execute('SELECT DISTINCT country FROM new_masked_ndvi')
		return cur.fetchall()


	if '-demo' not in sys.argv and '-update' not in sys.argv: # IF THIS IS NOT DEMO MODE OR UPDATE MODE...
		records = [recor[0].replace('\xc3\x83\xc2\x85','').lower() for recor in getSQLRecords()]
		# COUNTRY FILTER
		# for filter in ('antarctica','greenland'):	records.append(filter)
		# for filter in ('antarctica','greenland'):	records.append(filter)
	else:
		records = []


	# Open the mask file
	print 'Opening mask file...'
	mask = gdal.Open('/database/gimms.gsfc.nasa.gov/mask.tif')
	print 'Mask file opened'; sys.stdout.flush()
	mask = np.array(mask.GetRasterBand(1).ReadAsArray())
	print 'Mask read into array'; sys.stdout.flush()

	enALS = 2
	for adLevShp in [admShp2]: #This is really just a single-element array since we're only doing Admin Level 2 files.
		for shapeFile in adLevShp:
			lcShapeFile = shapeFile.decode('utf-8').lower()[0:-4] + str(enALS); continu = False

			for rec in records:	continu = True if rec in lcShapeFile else continu

			if continu is True:	continue # Skip this shapefile -=- its records are in the database

			countryDateAnom = defaultdict(dict); countryDateNDVI = defaultdict(dict)
			print '\nShapefile: %s'%(shapeFile); sys.stdout.flush()

			with fiona.open(shapeFile) as shp:
				# Country ident value comes from either the ISO or ISO2 code.
				name0 = 'NAME_ENGLI'; name1 = 'NAME_ENGLI'; name2 = 'NAME_ENGLI'; ident = 'ISO2'
				try:
					shp[0]['properties'][name0]
				except:
					name0 = 'NAME_0'; name1 = 'NAME_1'; name2 = 'NAME_1'; ident = 'HASC_1'
					try:
						shp[0]['properties']['NAME_2'];	name2 = 'NAME_2'; ident = 'HASC_2'
					except:
						pass

				xyList = [];
				for x in xrange(int(floor((180 + shp.bounds[0]) / 9)), int(floor((180 + shp.bounds[2]) / 9)) + 1):
					for y in xrange(int(floor((90 - shp.bounds[3]) / 9)), int(floor((90 - shp.bounds[1]) / 9)) + 1):
						if 1 in mask[y*4000:y*4000+4000,x*4000:x*4000+4000]:
							xyList.append('x%02dy%02d'%(x,y))
						else:
							print 'x%02dy%02d removed due to mask'%(x,y)

				if '-update' in sys.argv:
					yrStart = updateStart.year # Reset for use further down.
					dayOfYrStart = updateStartDay
				else:
					dayOfYrStart = 1
					yrStart = 2002

				# for doy in xrange(209,265,8):
				for doy in xrange(dayOfYrStart,365,8):
					for xy in xyList:
						print '\nXY:%s'%(xy); sys.stdout.flush()

						fdoy = '%03d'%(doy)
						print '\n %s :: '%(fdoy),; sys.stdout.flush()
						for yr in xrange(yrStart,datetime.datetime.now().year + 1):

                        anFl =
                'GMYD09Q1.A%s%s.08d.latlon.%s.6v1.NDVI_anom_S2003-2015.tif.gz'%(yr,fdoy,xy)
							ndFl = 'GMYD09Q1.A%s%s.08d.latlon.%s.6v1.NDVI.tif.gz'%(yr,fdoy,xy)
							if anFl in files.keys() and ndFl in files.keys():
								aF = tmp + anFl[0:-3]	# Anomaly .tif file
								if not os.path.isfile(aF):
									try:
										with gzip.open(os.path.join(files[anFl],anFl),'rb') as aZ:
											with open(aF,'w+b') as aT: aT.write(aZ.read())
									except Exception as gzAf:
										print 'Could not extract', gzAf
										continue

								try:
									aStatsX = getSt(shp,aF,xy)
									aStats = aStatsX[0]
									aMaskStats = aStatsX[1]
									if aStats == ():

										print '! No Data, Skipping this year for this xy for this doy !'
										continue
								except Exception as aStErr:
									print '\tCould not get stats', aStErr
									continue

								print '%s'%(str(yr)[-2:]),; sys.stdout.flush()

								for aStI,aSt in enumerate(aStats): #For each Admin Level 2
                                    #area in the current country (shp file):
									lonLatCentroid =
                                            (aSt['properties']
                                             ['mini_raster_affine'][2],
                                            aSt['properties']
                                             ['mini_raster_affine'][5])
									
									try: aSt['properties'][name0]
									except: continue

									names = '%s:%s:%s'%(aSt['properties'][name0], aSt['properties'][name1], aSt['properties'][name2])
									namesDay = '%s:%s'%(names,fdoy)
									namesDayYear = '%s:%s'%(namesDay,yr)
									regionID = aSt['properties'][ident]
									if regionID is None or regionID == u'':	regionID = aSt['properties']['ISO']

									aMask = [~np.bool_(aMaskStats[aStI]
                                        ['properties']['mini_raster_array']).flatten()]
									aData = ma.masked_array(np.float32
                                        (aSt['properties']['mini_raster_array'])
                                        .flatten(), aMask)

									anom = (ma.masked_outside(aData,0,250).compressed() - 125) * .008
									try:
										countryDateAnom[namesDayYear]['level'] = enALS
										countryDateAnom[namesDayYear]['rId'] = regionID
										countryDateAnom[namesDayYear]['lonlatcentroid'] = lonLatCentroid
										countryDateAnom[namesDayYear]['anom'] = (countryDateAnom[namesDayYear]['anom'] + np.mean(anom)) / 2 if 'anom' in countryDateAnom[namesDayYear].keys() else np.mean(anom)
										countryDateAnom[namesDayYear]['anomcount'] = countryDateAnom[namesDayYear]['anomcount'] + len(anom) if 'anomcount' in countryDateAnom[namesDayYear].keys() else len(anom)
									except:
										continue
								# End anomaly loop

								nF = tmp + ndFl[0:-3]	# NDIV .tif file
								if not os.path.isfile(nF):
									freeSpace()
									try:
										with gzip.open(os.path.join(files[ndFl],ndFl),'rb') as nZ:
											with open(nF,'w+b') as nT: nT.write(nZ.read())
									except Exception as gzNf:
										print 'Could not extract', gzNf
										continue

								try:
									nStatsX = getSt(shp,nF,xy)
									nStats = nStatsX[0]
									nMaskStats = nStatsX[1]

									if nStats == ():

										print '! No Data, Skipping this grid point !'
										continue # Will skip to the next year for this day/xy
								except Exception as nStErr:
									print 'Could not get stats', nStErr
									continue

								for nStI,nSt in enumerate(nStats):
									lonLatCentroid = (nSt['properties']
                                                      ['mini_raster_affine'][2],
                                                      nSt['properties']
                                                      ['mini_raster_affine'][5])
									try:
										nSt['properties'][name0]
									except:
										continue

									names = '%s:%s:%s'%(nSt['properties'][name0], nSt['properties'][name1], nSt['properties'][name2])
									namesDay = '%s:%s'%(names,fdoy)
									namesDayYear = '%s:%s'%(namesDay,yr)
									regionID = nSt['properties'][ident]
									if regionID is None or regionID == u'':	regionID = nSt['properties']['ISO']

									nMask = [~np.bool_(nMaskStats[nStI]
                                                ['properties']
                                                ['mini_raster_array']).flatten()]
									nData = ma.masked_array
                                    (np.float32(nSt['properties']
                                        ['mini_raster_array']).flatten(),
                                                nMask)

									ndvi = ma.masked_outside(nData,0,250).compressed() * .004
									try:
										countryDateNDVI[namesDayYear]['level'] = enALS
										countryDateNDVI[namesDayYear]['rId'] = regionID
										countryDateNDVI[namesDayYear]['lonlatcentroid'] = lonLatCentroid
										countryDateNDVI[namesDayYear]['ndvi'] = (countryDateNDVI[namesDayYear]['ndvi'] + np.mean(ndvi)) / 2 if 'ndvi' in countryDateNDVI[namesDayYear].keys() else np.mean(ndvi)
										countryDateNDVI[namesDayYear]['ndvicount'] = countryDateNDVI[namesDayYear]['ndvicount'] + len(ndvi) if 'ndvicount' in countryDateNDVI[namesDayYear].keys() else len(ndvi)
									except:
										continue
									
								# End ndvi loop
							# Last line of yr loop

						# Last line of xy loop

					# Run after all inner loops -- once per country / shape file:
					# After all 8-day blocks, write to the db

					if 'countryDateAnom' in vars() and 'countryDateNDVI' in vars():
						for cDAK, cDAV in countryDateAnom.iteritems():
							try:
								placeDate = cDAK.split(':')
								p = placeDate[0:3] # Country, State, City
								d = placeDate[3::] # Day-of-year, year
								key = '%s:%s:%s:%s:%s'%(p[0],p[1],p[2],d[0],d[1])
								print key

								if countryDateAnom[key].has_key('anom'):
									regionID = countryDateAnom[key]['rId']
									centroid = countryDateAnom[key]['lonlatcentroid']
									level = countryDateAnom[key]['level']

									anom = countryDateAnom[key]['anom'];
									if anom == 'nan':	anom = -1
									anomCt = countryDateAnom[key]['anomcount']
								else:
									continue

								if countryDateNDVI[key].has_key('ndvi'):
									ndvi = countryDateNDVI[key]['ndvi']
									if ndvi == 'nan':	ndvi = 0
									ndviCt = countryDateNDVI[key]['ndvicount']
								else:
									continue

								startDate = datetime.datetime(int(d[1]),1,1) + datetime.timedelta(int(d[0]) - 1)
								if level == 1:
									p[2] = ''
								elif level == 0:
									p[2] = ''; p[1] = ''

								sqlInsertData = "'%s', '%s', '%s', '%s', '%s', %s, %s, %s, %s, %s, %s"%(regionID, p[0].replace("'","''"), p[1].replace("'","''"), p[2].replace("'","''"), startDate, ndvi, ndviCt, anom, anomCt, centroid[0], centroid[1])

								print '\nWriting to database %s\n'%(sqlInsertData)

								sqlInsert = 'INSERT INTO new_masked_ndvi VALUES(%s);'%(sqlInsertData)
								sqlInsertError = None

								try:
									cur.execute(sqlInsert)
								except Exception as sqlInsertError:
									print '\nSQL INSERT Error:', sqlInsertError, sqlInsert

							except Exception as sqlEx:
								print sqlEx
								continue

					# Last line of doy loop (each shape file for each year, for all 8-day blocks)

			# Last line of unused admin level loop
	# Last line of main function
print 'Starting main function'
main()
