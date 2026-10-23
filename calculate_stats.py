import geopandas as gpd
import rasterio
from rasterstats import zonal_stats

raster_file = "Assam_LULC_2026.tif"
geojson_file = "assam_districts.geojson.json"

# 1. Read GeoJSON and filter strictly for Polygons / MultiPolygons
gdf = gpd.read_file(geojson_file)
gdf = gdf[gdf.geometry.type.isin(["Polygon", "MultiPolygon"])].copy()
gdf = gdf.reset_index(drop=True)

# 2. Match Raster CRS for exact zonal extraction
with rasterio.open(raster_file) as src:
    raster_crs = src.crs

if gdf.crs != raster_crs:
    gdf_projected = gdf.to_crs(raster_crs)
else:
    gdf_projected = gdf

# 3. Class keys matching your ESA / Dynamic World bands (1 to 8)
class_cols = {
    1: "pct_forest",
    2: "pct_shrub_tea",
    3: "pct_grassland",
    4: "pct_cropland",
    5: "pct_builtup",
    6: "pct_barren",
    8: "pct_water"
}

dominant_colors = {
    "pct_forest": "#1b7837",
    "pct_shrub_tea": "#78c679",
    "pct_grassland": "#c2e699",
    "pct_cropland": "#fecc5c",
    "pct_builtup": "#e31a1c",
    "pct_barren": "#d95f0e",
    "pct_water": "#2b83ba"
}

# 4. Run zonal statistics
stats = zonal_stats(gdf_projected, raster_file, categorical=True)

for i, stat in enumerate(stats):
    if not stat:
        continue
    
    # Exclude NoData (0)
    valid_total = sum(count for val, count in stat.items() if val > 0)
    
    highest_col = "pct_cropland"
    highest_pct = -1.0

    for code, col_name in class_cols.items():
        count = stat.get(code, 0)
        pct = round((count / valid_total) * 100, 2) if valid_total > 0 else 0.0
        gdf.loc[i, col_name] = pct
        
        if pct > highest_pct:
            highest_pct = pct
            highest_col = col_name

    gdf.loc[i, "dominant_class"] = highest_col
    gdf.loc[i, "dominant_color"] = dominant_colors.get(highest_col, "#fecc5c")

# 5. Ensure final output GeoJSON is explicitly in standard EPSG:4326 (WGS84 Lat/Lon for Leaflet)
gdf = gdf.to_crs(epsg=4326)
gdf.to_file(geojson_file, driver="GeoJSON")
print(f"Successfully processed and updated {len(gdf)} district polygons in WGS84!")
