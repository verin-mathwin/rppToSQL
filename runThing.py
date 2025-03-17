import rppReader
import findAllRPP
import geopandas as gpd
import os
from shapely.geometry import LineString

rootFolder = r"YOUR_ROOT_FOLDER_PATH_HERE"

man = True
collateInRoot = True

def recordsToShp(recordpd):
    """
    Converts record data to a Shapefile using GeoPandas.
    has issue with attribute names. Will fix later.

    :param recordpd: Pandas DataFrame containing record data with latitude and longitude.
    :return: None. Writes a shapefile to disk.
    """
    coords = recordpd.apply(lambda x: LineString([[float(x['longitude-start']), float(x['latitude-start'])], [float(x['longitude-end']), float(x['latitude-end'])]]), axis=1)
    for a in coords:
        print(a)
    recordpd.info()
    # Convert DataFrame to GeoDataFrame
    recGPD = gpd.GeoDataFrame(recordpd, geometry=coords, crs='EPSG:4979')
    
    # Drop rows with missing coordinate data
    hasData = recGPD.dropna(axis='index', subset=['latitude-start', 'longitude-start', 'latitude-end', 'longitude-end'])
    
    # Drop completely empty columns
    hasData.dropna(axis='columns', how='all')
    
    # Save to Shapefile
    hasData.to_file(outshp)
    


fileList = findAllRPP.finder(rootFolder)
basenameComplete = []
for a in fileList:
    print("Running ", a)
    hostFolder = os.path.dirname(a)
    baseName = os.path.splitext(os.path.basename(a))[0]
    if baseName in basenameComplete:
        print("Duplicate file")
        exit()
    pathfolder = hostFolder
    if collateInRoot:  # if we want to slot them all in the same folder
        pathfolder = rootFolder

    # Define output file paths
    outFile = os.path.join(pathfolder, baseName + ".db")
    outcsv = os.path.join(pathfolder, baseName + ".csv")
    outshp = os.path.join(pathfolder, baseName + ".shp")

    # Process RPP file and extract data
    recordPandas = rppReader.workflowHandler(a, False, False, False, outFile, manualRiWorldUsed=man, segments=True)

    # Convert records to Shapefile
    recordsToShp(recordPandas)

    # Save records to CSV
    recordPandas.to_csv(outcsv)
    

