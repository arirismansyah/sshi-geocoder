import pandas as pd
import geopandas as gpd
from tqdm import tqdm
from shapely.geometry import Point
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
        
        df_res = pd.DataFrame(list_result)
        
        df_res['geometry'] = df_res.apply(
            lambda x: Point(x['longitude'], x['latitude']) if pd.notnull(x['longitude']) and pd.notnull(x['latitude']) else None,
            axis=1
        )
        gdf_res = gpd.GeoDataFrame(
            df_res, geometry='geometry', crs="EPSG:4326")
        return gdf_res
        
    def get_intersect(self, data_location:gpd.GeoDataFrame, polygon:gpd.GeoDataFrame):
        joined = gpd.sjoin(data_location, polygon, how='left', predicate='within')
        return joined
    
    def visualize_gdf(self, gdf: gpd.GeoDataFrame, popup_column: str = None, map_location: tuple = None, zoom_start: int = 10):

        if map_location is None:
            # Try to center map on mean of points
            if not gdf.empty and gdf.geometry.is_valid.all():
                mean_x = gdf.geometry.x.mean()
                mean_y = gdf.geometry.y.mean()
                map_location = (mean_y, mean_x)
            else:
                map_location = (0, 0)

        m = folium.Map(location=map_location, zoom_start=zoom_start)

        for _, row in gdf.iterrows():
            geom = row.geometry
            if geom and geom.geom_type == 'Point':
                popup = str(row[popup_column]) if popup_column and popup_column in row else None
                folium.Marker(
                    location=[geom.y, geom.x],
                    popup=popup
                ).add_to(m)
            elif geom and geom.geom_type in ['Polygon', 'MultiPolygon']:
                folium.GeoJson(geom).add_to(m)

        return m
