# This should be compatible with both Python 2 and 3.
import arcpy
import time
import os
from datetime import date, timedelta, datetime
import logging
import json
try:
    import urllib.request as rq
except ImportError:
    import urllib2 as rq

def generate_wgs84_data(zone_name, shapefile_path, dstring, lgr):
    """ Take feature, convert to EPSG:4326, then convert it to GeoJSON
        that CrowdFiber can use.
    """
    try:
        in_shp = "%s%s_%s.shp" % (shapefile_path, zone_name, dstring)
        out_shp = "%s%s_%s_wgs84.shp" % (shapefile_path, zone_name, dstring)
        out_geojson = "%s%s_%s_wgs84.json" % (shapefile_path, zone_name, dstring)
        out_cs = arcpy.SpatialReference(4326)

        arcpy.Project_management(in_shp, out_shp, out_cs)
        arcpy.FeaturesToJSON_conversion(in_features = out_shp,
                                        out_json_file = out_geojson,
                                        format_json = "NOT_FORMATTED",
                                        include_z_values = "NO_Z_VALUES",
                                        include_m_values = "NO_M_VALUES",
                                        geoJSON = "GEOJSON")
    except:
        lgr.exception("Couldn't generate GeoJSON for %s" % (zone_name))

def push_to_crowdfiber(zone_name, zone_id, shapefile_path, dstring, base_url, api_key, lgr):
    """ Push feature via CrowdFiber API to CrowdFiber
    """
    try:
        generate_wgs84_data(zone_name, shapefile_path, dstring, lgr)
        endpoint = "%s/api/v1/campaigns/2/zones/%s" % (base_url, zone_id)
        out_geojson = "%s%s_%s_wgs84.json" % (shapefile_path, zone_name, dstring)

        headers = {"Content-type": "application/json",
                   "Accept": "application/json",
                   "Authorization": "Token token=%s" % (api_key)}

        values = {"zone": {"geom": open(out_geojson, "r").read()}}
        req = rq.Request(endpoint, json.dumps(values).encode("utf-8"), headers=headers)
        req.get_method = lambda: 'PATCH'
        response = rq.urlopen(req)
        lgr.info("Successfully pushed %s to CrowdFiber" % (zone_name))
    except:
        lgr.exception("There was an issue with %s" % (zone_name))

# CrowdFiber - Constants
CF_API_KEY = "API_KEY_GOES_HERE"
CF_BASE_URL = "https://mycrowdfiber.site.com"

#Date variables
datestring = time.strftime("%Y_%m_%d", time.localtime())
yesterday = datetime.strftime(datetime.now() - timedelta(7), '%Y_%m_%d')

currentyear = datetime.now().year
next_year = currentyear + 1
Two_year = currentyear + 2

#Location of SDE Database
path = "C:\\assuming\\youre\\using\\windows\\your\\path\\lookslike\\this.sde\\"
arcpy.env.workspace = path

#Location of where shapefiles will be saved
saveloc = ("C:\\location\\of\\databackups\\" + datestring + "\\")
arcpy.env.overwriteOutput = True

#Creating new folder
if not os.path.exists(saveloc):
    os.makedirs(saveloc)

#create log
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s")
log_file_handler = logging.FileHandler("C:\\location\\of\\crowdfiber.log")
log_file_handler.setFormatter(formatter)
logger.addHandler(log_file_handler)

def main():
    try:

    ##Export of Shapefiles##
        zone_id = 1
        feature_class_to_access = "name_of_feature_class"
        new_feature_name = "name_of_new_feature_layer"
        #Create layer, select features and merge features to new feature
        # This may or may not be what you need, but the gist is that you need to get from
        # data inside ArcGIS into GeoJSON somehow
        arcpy.MakeFeatureLayer_management(path + feature_class_to_access, new_feature_name)
        arcpy.SelectLayerByAttribute_management(new_feature_name, "NEW_SELECTION", "SOME QUERY GOES HERE")
        arcpy.Dissolve_management(new_feature_name, saveloc + new_feature_name + "_" + datestring + ".shp")
        logger.info(new_feature_name + "_" + datestring + " has been created")

        # Push to CrowdFiber
        push_to_crowdfiber(new_feature_name, zone_id, saveloc, datestring, CF_BASE_URL, CF_API_KEY, logger)

    except:
        logger.exception("Something went wrong")

main()

log_file_handler.close()
