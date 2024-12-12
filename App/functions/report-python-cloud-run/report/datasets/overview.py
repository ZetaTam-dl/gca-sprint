# Packages for loading data
import geopandas as gpd
import matplotlib.pyplot as plt
import xarray as xr
# Packages for plotting
from resilientplotterclass import rpc
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
plt.rcParams["svg.fonttype"] = "none"
import numpy as np
from shapely import Polygon  # type: ignore

from .utils import plot_to_base64
from .datasetcontent import DatasetContent
from utils.gentext import describe_data


world = gpd.read_file(
    Path(__file__).parent.parent.parent / "data" / "world_administrative.zip"
)

def get_overview(polygon: Polygon) -> DatasetContent:
    """Get overview"""
    dataset_id = "overview"
    title = "Overview"
    text = "Here we generate some content based on all datasets"

    image_base64 = create_satellite_img(polygon)
    return DatasetContent(
        dataset_id=dataset_id,
        title=title,
        text=text,
        image_base64=image_base64,
    )


def create_satellite_img(polygon: Polygon):
    gdf_aoi= gpd.GeoDataFrame({'Name': ['Custom'], 'geometry': [polygon]}, crs='EPSG:4326')
    bounds = gdf_aoi.bounds.values[0]
    center = [(bounds[0] + bounds[2]) / 2, (bounds[1] + bounds[3]) / 2]
    length = max([bounds[2] - bounds[0], bounds[3] - bounds[1]])
    buffer = 0.01
    xlims = [center[0] - length/2 - buffer, center[0] + length/2 + buffer]
    ylims = [center[1] - length/2 - buffer, center[1] + length/2 + buffer]

    # Plot data
    fig, ax = plt.subplots(figsize=(5, 5))
    rpc.geometries(gdf_aoi, ax=ax, facecolor='none', edgecolor='white', linewidth=1)
    ax.set_xlim(xlims)
    ax.set_ylim(ylims)
    rpc.basemap(crs=gdf_aoi.crs, map_type='satellite', ax=ax)
    ax.grid(False)
    
    return plot_to_base64(fig)
