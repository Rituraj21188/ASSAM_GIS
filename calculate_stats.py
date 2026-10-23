import geopandas as gpd
import rasterio
from rasterstats import zonal_stats

raster_file = "Assam_LULC_2026.tif"
geojson_file = "assam_districts.geojson.json"

gdf = gpd.read_file(geojson_file)

with rasterio.open(raster_file) as src:
    if gdf.crs != src.crs:
        gdf = gdf.to_crs(src.crs)

class_names = {
    1: "pct_forest",
    2: "pct_tea_agro",
    3: "pct_cropland",
    4: "pct_water",
    5: "pct_builtup",
    6: "pct_barren"
}

stats = zonal_stats(gdf, raster_file, categorical=True)

for i, stat in enumerate(stats):
    total = sum(stat.values()) if stat else 0
    for code, col in class_names.items():
        count = stat.get(code, 0)
        gdf.loc[i, col] = round((count / total) * 100, 2) if total > 0 else 0

# Overwrite the GeoJSON in the repo
gdf.to_file(geojson_file, driver="GeoJSON")
print("Updated GeoJSON with calculated zonal percentages!")
