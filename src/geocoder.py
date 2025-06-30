import pandas as pd
import geopandas as gpd
from tqdm import tqdm
from shapely.geometry import Point, Polygon, MultiPolygon
from geopy.geocoders import Nominatim, GeocodeEarth, GoogleV3
import folium


class SshiGeocoder:
    def __init__(self, country_code: str, user_agent: str = 'sshi-geocoder'):
        self.user_agent = user_agent
        self.country_code = country_code
    
    def __geocode(self, location:str, exactly_one:bool=False):
        geolocator = Nominatim(user_agent=self.user_agent)
        """Geocode a single location."""
        try:
            return geolocator.geocode(location, exactly_one=exactly_one, country_codes=self.country_code, timeout=10)
        except Exception as e:
            print(f"Error geocoding {location}: {e}")
            return None

    def load_shapefile(self, filepath):
        gdf = gpd.read_file(filepath)
        return gdf
        
    def geocode_locations(self, 
                          locations:list[str]|pd.DataFrame, 
                          location_column:str=None,
                          exactly_one:bool=False):
        
        list_result = []
        if isinstance(locations, pd.DataFrame) and (location_column==None):
            raise ValueError("location_column must be specified when passing a DataFrame.")
        
        if isinstance(locations, list):
            df = pd.DataFrame({'location':locations})
            col_name = 'location'
        else:
            df = locations
            col_name = location_column
        
        for i, row in tqdm(df.iterrows(), total=len(df), desc='geocode locations'):
            row_dict = row.to_dict()
            loc_res = self.__geocode(location=row_dict.get(
                col_name), exactly_one=exactly_one)
            
            if isinstance(loc_res, list) and len(loc_res)>0:
                for loc in loc_res:
                    row_dict['longitude'] = loc.longitude
                    row_dict['latitude'] = loc.latitude
                    row_dict['address'] = loc.address
                    list_result.append(row_dict)
            else:
                row_dict['longitude'] = None
                row_dict['latitude'] = None
                row_dict['address'] = None
                list_result.append(row_dict)
        
        df_res = pd.DataFrame(list_result)
        
        df_res['geometry'] = df_res.apply(
            lambda x: Point(x['longitude'], x['latitude']) if pd.notnull(x['longitude']) and pd.notnull(x['latitude']) else None,
            axis=1
        )
        
        gdf_res = gpd.GeoDataFrame(
            df_res, geometry='geometry', crs="EPSG:4326")
        return gdf_res
        
    def get_intersect(self, data_location: gpd.GeoDataFrame, polygon: gpd.GeoDataFrame):
        data_location = data_location.dropna(subset=['geometry'])
        # Pastikan kedua GeoDataFrame punya CRS yang sama
        if data_location.crs != polygon.crs:
            polygon = polygon.to_crs(data_location.crs)

        # Spatial join: cari point dalam polygon
        joined = gpd.sjoin(
            data_location, polygon,
            how='left', predicate='within',
            lsuffix='point', rsuffix='polygon'
        )

        # Rename geometry kolom biar bisa punya 2 geometry
        joined = joined.rename(
            columns={'geometry': 'point_geometry', 'geometry_polygon': 'polygon_geometry'})

        # Ambil geometry polygon dari 'geometry_polygon' (hasil join), karena udah ke-rename otomatis
        if 'geometry_polygon' in joined.columns:
            joined = joined.rename(
                columns={'geometry_polygon': 'polygon_geometry'})

        # Simpan kedua geometry
        joined['polygon_geometry'] = polygon.loc[joined['index_polygon']].geometry.values
        joined = joined.set_geometry('point_geometry')

        return joined

    def visualize_gdf(self, gdf: gpd.GeoDataFrame, map_location: tuple = None, zoom_start: int = 10):
        # Hitung center dari point_geometry
        if map_location is None and 'point_geometry' in gdf.columns:
            valid_points = gdf['point_geometry'][gdf['point_geometry'].notnull()]
            if not valid_points.empty:
                mean_x = valid_points.x.mean()
                mean_y = valid_points.y.mean()
                map_location = (mean_y, mean_x)
            else:
                map_location = (0, 0)

        m = folium.Map(location=map_location, zoom_start=zoom_start)

        # Buat layer untuk point dan polygon
        polygon_layer = folium.FeatureGroup(name='Polygon Layer', show=True)
        point_layer = folium.FeatureGroup(name='Point Layer', show=True)

        for _, row in gdf.iterrows():
            # Buat popup content dari semua kolom non-geometry
            popup_data = row.drop(
                labels=[col for col in row.index if 'geometry' in col], errors='ignore')
            popup_html = "<br>".join(
                [f"<b>{k}</b>: {v}" for k, v in popup_data.items()])

            # Point marker
            if 'point_geometry' in row and isinstance(row['point_geometry'], Point):
                pt = row['point_geometry']
                folium.Marker(
                    location=[pt.y, pt.x],
                    popup=folium.Popup(popup_html, max_width=300),
                    icon=folium.Icon(color='blue', icon='info-sign')
                ).add_to(point_layer)

            # Polygon
            if 'polygon_geometry' in row and isinstance(row['polygon_geometry'], (Polygon, MultiPolygon)):
                folium.GeoJson(
                    row['polygon_geometry'],
                    name='Polygon',
                    popup=folium.Popup(popup_html, max_width=300),
                    style_function=lambda x: {
                        'fillColor': 'orange',
                        'color': 'red',
                        'weight': 2,
                        'fillOpacity': 0.3
                    }
                ).add_to(polygon_layer)

        polygon_layer.add_to(m)
        point_layer.add_to(m)
        folium.LayerControl().add_to(m)

        return m
