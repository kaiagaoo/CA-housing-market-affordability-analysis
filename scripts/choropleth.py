import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
# read data and preprocess
df = pd.read_csv("county_market_tracker.tsv", sep="\t")
df[['county_name', 'state_abbrev']] = df['REGION'].str.split(', ', expand=True)
df_ca = df[df['state_abbrev'] == "CA"].copy()
df_ca['county_name'] = df_ca['county_name'].str.replace(' County','', regex=False).str.lower()
df_ca['year'] = pd.to_datetime(df_ca['PERIOD_BEGIN']).dt.year

df_other = pd.read_csv("CA.csv")
df_other.head()
df_other['county_name'] = df_other['County'].str.replace(' County','', regex=False).str.lower()

df_merged = df_ca.merge(df_other, on='county_name', how='left')

df_merged['year'] = pd.to_datetime(df_merged['PERIOD_BEGIN']).dt.year

cols_to_keep = ['county_name', 'year', 'MEDIAN_SALE_PRICE', 'HOMES_SOLD_YOY', 'Value (Dollars)']

df_grouped_final = (
    df_merged[cols_to_keep]
    .groupby(['county_name','year'], as_index=False)
    .agg({
        'MEDIAN_SALE_PRICE':'median',
        'HOMES_SOLD_YOY':'median',
        'Value (Dollars)': 'first'  
    })
)

year_to_plot = 2022
df_plot = df_grouped_final[df_grouped_final['year'] == year_to_plot].copy()

# https://www.census.gov/geographies/mapping-files/time-series/geo/carto-boundary-file.html download cb_2018_us_county_20m.zip
from matplotlib.animation import FuncAnimation
if df_grouped_final['Value (Dollars)'].dtype == 'O': 
    df_grouped_final['Value (Dollars)'] = df_grouped_final['Value (Dollars)'].astype(str).str.replace(',', '').astype(float)
else:
    df_grouped_final['Value (Dollars)'] = df_grouped_final['Value (Dollars)'].astype(float)


df_grouped_final['color_value'] = df_grouped_final['MEDIAN_SALE_PRICE'] / df_grouped_final['Value (Dollars)']


df_grouped_final['bubble_size'] = df_grouped_final['HOMES_SOLD_YOY'].abs() * 5000  # 可调节比例

# getting the county geometries
gdf_counties = gpd.read_file("cb_2018_us_county_20m.shp")
gdf_ca = gdf_counties[gdf_counties['STATEFP'] == '06'].copy()
gdf_ca['county_name'] = gdf_ca['NAME'].str.lower().str.replace(' county','', regex=False)

# merging geometries with data
gdf_merged = gdf_ca.merge(df_grouped_final, on='county_name', how='left')

# getting representative points for bubble locations
gdf_merged['coords'] = gdf_merged['geometry'].apply(lambda x: x.representative_point().coords[:])
gdf_merged['coords'] = [coords[0] for coords in gdf_merged['coords']]


years = sorted(gdf_merged['year'].unique())


fig, ax = plt.subplots(1, 1, figsize=(12, 12))


gdf_ca.plot(ax=ax, color='lightgrey', edgecolor='white')


scatter = ax.scatter([], [], s=[], c=[], cmap='OrRd', alpha=0.7, edgecolor='k')
cbar = plt.colorbar(scatter, ax=ax)
cbar.set_label('MEDIAN_SALE_PRICE / Value (Dollars)')
ax.axis('off')


def update(year):
    df_year = gdf_merged[gdf_merged['year'] == year]
    scatter.set_offsets([c for c in df_year['coords']])
    scatter.set_sizes(df_year['bubble_size'])
    scatter.set_array(df_year['color_value'])
    ax.set_title(f'California Counties Bubble Map ({year})', fontsize=16)


ani = FuncAnimation(fig, update, frames=years, repeat=True, interval=1000)  # interval=1000ms

# ani.save('ca_counties_animation.mp4', writer='ffmpeg', dpi=150)
ani.save('ca_counties_animation.gif', writer='pillow', dpi=150)

plt.show()