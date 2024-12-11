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
import pystac_client
import rioxarray as rio

from .utils import plot_to_base64
from .datasetcontent import DatasetContent
from utils.gentext import describe_data

def get_slr_content(polygon: Polygon) -> DatasetContent:
    """Get content for the dataset"""
    dataset_id = "slr"
    title = "Sea Level Rise Projection"
    text = "Here we generate some content based on the dataset"
    #text = describe_data(xarr, dataset_id)

    image_base64 = create_slr_plot(polygon)
    return DatasetContent(
        dataset_id=dataset_id,
        title=title,
        text=text,
        image_base64=image_base64,
    )

def create_slr_plot(polygon):
    # Set stac URL
    STAC_url = "https://raw.githubusercontent.com/openearth/coclicodata/main/current/catalog.json"

    # Open the catalog
    catalog = pystac_client.Client.open(STAC_url)

    # Get the AR6 collection
    collection = catalog.get_child("slp")

    # Get all items to iterate over
    items = collection.get_all_items()


    ssps = ["high_end", "ssp126", "ssp245", "ssp585"]
    msls = ["msl_h"]
    years = ["2031","2041","2051", "2061", "2071", "2081", "2091", "2101","2111","2121","2131","2141","2151"]

    filtered_items = []

    slps = []

    # Iterate over all ssps, ens and years
    for ssp in ssps:
        for msl in msls:
            for year in years:
                # Get the item
                item = collection.get_item(f"{ssp}\{msl}\{year}.tif")
                
                # Get href
                href = item.assets["data"].href

                # Load tif into xarray
                ds = rio.open_rasterio(href, masked=True)

                # First clip to bounding box of polygon
                ds_clip = ds.rio.clip_box(*polygon.bounds, allow_one_dimensional_raster=True)

                ds_point = ds_clip.sel(x=polygon.centroid.x, y=polygon.centroid.y, method="nearest")

                # Check if nearest pixel to centroid has data, if not use max of ds_clip
                if not ds_point.notnull().values:

                    # Find the maximum value in the dataset
                    max_value = ds_clip.max()

                    # Find the coordinates of the max value
                    max_coords = ds_clip.where(ds == max_value, drop=True)

                    # Retrieve the coordinates (x, y) for the maximum value
                    max_x = max_coords.coords['x'].values
                    max_y = max_coords.coords['y'].values

                    # Select the dataset at the coordinates of the maximum value
                    ds_point = ds_clip.sel(x=max_x, y=max_y)

                # Retrieve the point value
                value = ds_point.values.item()

                # Append the result as a dictionary
                slps.append({
                    'ssp': ssp,
                    'msl': msl,
                    'year': year,
                    'value': value
                })

    fig, ax = plt.subplots(1,1, figsize=(5,5))

    # Now, directly use the results to plot
    for ssp in ssps:
        # Filter the data for the current ssp
        ssp_values = [slp['value'] for slp in slps if slp['ssp'] == ssp]
        ssp_years = [slp['year'] for slp in slps if slp['ssp'] == ssp]

        # Plot the data for this ssp
        ax.plot(ssp_years, ssp_values, label=ssp, marker='o')

    ax.set_xlabel("Year")
    ax.set_ylabel("Sea Level Rise [mm]")
    ax.set_xticks(ssp_years, ssp_years, rotation=45)
    ax.set_title("Timeline for Different SSPs")
    ax.legend()

    return plot_to_base64(fig)