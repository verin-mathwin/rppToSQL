import rppReader
import geopandas as gpd
from shapely.geometry import LineString



man = True

def recordsToShp(recordpd):
    coords = recordpd.apply(lambda x: LineString([[float(x['longitude-start']), float(x['latitude-start'])], [float(x['longitude-end']), float(x['latitude-end'])]]), axis=1)
    for a in coords:
        print(a)
    recordpd.info()
    recGPD = gpd.GeoDataFrame(recordPandas, geometry=coords, crs='EPSG:4979')
    hasData = recGPD.dropna(axis='index', subset=['latitude-start', 'longitude-start', 'latitude-end', 'longitude-end'])
    hasData.dropna(axis='columns', how='all')
    hasData.to_file(outshp)
    



recordPandas = rppReader.workflowHandler(rppLink, False, False, False, outFile, manualRiWorldUsed=man, segments=True)
recordsToShp(recordPandas)
recordPandas.to_csv(outcsv)
