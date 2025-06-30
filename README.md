# 🗺️ SshiGeocoder

**SshiGeocoder** is a simple Python module for batch geocoding, spatial joins, and geospatial visualization. It uses OpenStreetMap’s Nominatim via `geopy`, and supports GeoPandas for spatial operations and Folium for interactive maps.

---

## 📦 Features

- ✅ Batch geocode location names using OpenStreetMap
- ✅ Spatial join with polygons (e.g., shapefiles)
- ✅ Generate interactive maps with markers and popups
- ✅ Input: list or DataFrame
- ✅ Output: GeoDataFrame with geometry

---

### 📁 Project Structure

```text
geocoder/
├── data/               # Folder for input/output data
├── src/                # Source code
│   └── geocoder.py     # Main geocoding module
├── .gitignore          # Git ignore rules
├── example.ipynb       # Example usage notebook
├── readme.md           # Project documentation
├── requirements.txt    # Python dependencies
```


## 🛠 Installation

Install the required dependencies:

```bash
pip install -r requirements.txt
```

---

## 🚀 Usage Example

```python
from sshi_geocoder import SshiGeocoder
import pandas as pd

# Initialize geocoder
geocoder = SshiGeocoder(country_code='ID')  # For Indonesia

# Load polygon shapefile
polygon_gdf = geocoder.load_shapefile('path/to/shapefile.shp')

# Geocode from a list of location strings
locations = ['Surabaya, Indonesia', 'Jakarta, Indonesia']
gdf_locations = geocoder.geocode_locations(locations)

# Or from a DataFrame column
df = pd.DataFrame({'city': ['Bandung, Indonesia', 'Medan, Indonesia']})
gdf_locations = geocoder.geocode_locations(df, location_column='city')

# Spatial join with polygons
joined = geocoder.get_intersect(gdf_locations, polygon_gdf)

# Visualize results
map_object = geocoder.visualize_gdf(gdf_locations, popup_column='address')
map_object.save('map.html')
```

---

## 🧠 API Overview

### `SshiGeocoder(country_code: str, user_agent: str = 'sshi-geocoder')`

Initialize the geocoder with:
- `country_code`: e.g., `'id'` for Indonesia
- `user_agent`: required by Nominatim

---

### `geocode_locations(locations, location_column=None, exactly_one=False)`

Geocode a list or DataFrame of location names.

- `locations`: list of strings or DataFrame
- `location_column`: required if input is a DataFrame
- Returns: `GeoDataFrame` with `longitude`, `latitude`, `address`, and `geometry`

---

### `load_shapefile(filepath)`

Loads shapefile or GeoJSON into a GeoDataFrame.

---

### `get_intersect(data_location, polygon)`

Performs a spatial join to determine **which administrative region (polygon)** each **geocoded point** falls into.

- `data_location`: GeoDataFrame containing point geometries (from geocoding)
- `polygon`: GeoDataFrame containing administrative boundary polygons
- Returns: GeoDataFrame where each point is enriched with the attributes of the polygon it falls within

**Example:** For a geocoded point representing `Jakarta`, this function will identify whether it falls within `Kelurahan A`, `District B`, etc.

---

### `visualize_gdf(gdf, popup_column=None, map_location=None, zoom_start=10)`

Visualizes GeoDataFrame on an interactive map.

- Supports both Points and Polygons
- Returns: `folium.Map` object

---

## ⚠️ Notes

- Geocoding is rate-limited by OpenStreetMap’s Nominatim.
- You can customize the `__geocode()` method to use other geocoding services like Google Maps or GeocodeEarth.
- Make sure all spatial data uses the same CRS (e.g., `EPSG:4326`).

---