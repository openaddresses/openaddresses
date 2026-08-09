#!/usr/bin/python

# Given an input QSC.gpkg file identify and output all the latitudes gaps which avoid all input polygons
# This is so we can split out data download request from QSC into two different areas of QLD that avoid clipping polygons.
# DISCLAIMER this file was written with AI assistance

import geopandas as gpd
from shapely.geometry import box

print(f"Read file...")
gdf = gpd.read_file("QSC.gpkg")

# 1. Collect y-intervals per polygon part
print(f"collect intervals...")
intervals = []
for geom in gdf.geometry:
    if geom is None or geom.is_empty:
        continue
    parts = geom.geoms if hasattr(geom, "geoms") else [geom]
    for part in parts:
        _, ymin, _, ymax = part.bounds
        intervals.append((ymin, ymax))

# 2. Merge overlapping/touching intervals
print(f"merge...")
intervals.sort()
merged = [list(intervals[0])]
for lo, hi in intervals[1:]:
    if lo <= merged[-1][1]:
        merged[-1][1] = max(merged[-1][1], hi)
    else:
        merged.append([lo, hi])

# 3. Build gap rectangles spanning the data's x-extent
xmin, _, xmax, _ = gdf.total_bounds

print(f"build gaps...")
gap_geoms, gap_attrs = [], []
for i in range(len(merged) - 1):
    y_lo = merged[i][1]        # top of block below
    y_hi = merged[i + 1][0]    # bottom of block above
    if y_hi - y_lo <= 0:       # skip degenerate/zero-height gaps
        continue
    gap_geoms.append(box(xmin, y_lo, xmax, y_hi))
    gap_attrs.append({
        "y_min": y_lo,
        "y_max": y_hi,
        "height": y_hi - y_lo,
        "y_mid": (y_lo + y_hi) / 2,   # a safe horizontal line
    })

print(f"ouptu gaps...")
gaps_gdf = gpd.GeoDataFrame(gap_attrs, geometry=gap_geoms, crs=gdf.crs)
gaps_gdf.to_file("gaps.gpkg", driver="GPKG")

print(f"Wrote {len(gaps_gdf)} gap polygons to gaps.gpkg")
