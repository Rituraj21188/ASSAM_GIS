import geopandas as gpd
import rasterio
from rasterstats import zonal_stats

raster_file = "Assam_LULC_2026.tif"
geojson_file = "assam_districts.geojson.json"

gdf = gpd.read_file(geojson_file)

with rasterio.open(raster_file) as src:
    if gdf.crs != src.crs:
        gdf = gdf.to_crs(src.crs)

# Classes 1 through 8 matching ESA/Dynamic World LULC
class_cols = {
    1: "pct_forest",
    2: "pct_shrub_tea",
    3: "pct_grassland",
    4: "pct_cropland",
    5: "pct_builtup",
    6: "pct_barren",
    8: "pct_water"
}

# Color mapping for the dominant class
dominant_colors = {
    "pct_forest": "#1b7837",
    "pct_shrub_tea": "#78c679",
    "pct_grassland": "#c2e699",
    "pct_cropland": "#fecc5c",
    "pct_builtup": "#e31a1c",
    "pct_barren": "#d95f0e",
    "pct_water": "#2b83ba"
}

stats = zonal_stats(gdf, raster_file, categorical=True)

for i, stat in enumerate(stats):
    if not stat:
        continue
    
    # Exclude 0 (NoData / Black border)
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

    # Set dominant category and hex color for map choropleth styling
    gdf.loc[i, "dominant_class"] = highest_col
    gdf.loc[i, "dominant_color"] = dominant_colors.get(highest_col, "#38bdf8")

gdf.to_file(geojson_file, driver="GeoJSON")
print("Finished updating GeoJSON with full LULC stats and dominant colors!")
