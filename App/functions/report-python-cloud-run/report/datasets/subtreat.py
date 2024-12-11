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

from .utils import plot_to_base64
from .datasetcontent import DatasetContent

world = gpd.read_file(
        Path(__file__).parent.parent.parent / "data" / "world_administrative.zip"
    )

def get_sub_threat_content(xarr: xr.Dataset) -> DatasetContent:
    """Get content for the dataset"""
    dataset_id = "land_sub"
    title = "Land Subsidence"
    text = "Here we generate some content based on the dataset" ##TODO

    image_base64 = create_sub_treat_plot(xarr)
    return DatasetContent(
        dataset_id=dataset_id,
        title=title,
        text=text,
        image_base64=image_base64,
    )


def create_sub_treat_plot(xarr: xr.Dataset):
    fig, ax = plt.subplots(1, 1, figsize=(10, 10))

    base = world.boundary.plot(
        ax=ax, edgecolor="grey", facecolor="grey", alpha=0.1, zorder=0
    )

    p = rpc.scatter(xarr, ax=ax, data_type='data',
                    x='lon', y='lat', 
                    hue='epsi', 
                    edgecolor='none', cmap='RdYlGn', 
                    add_colorbar=True, cbar_kwargs={'label': 'Land Subsidence Index'}
                    )

    from mpl_toolkits.axes_grid1 import make_axes_locatable
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size=0.25, pad=0.10)

    lonmin = min(xarr.lon.values)
    lonmax = max(xarr.lon.values)
    latmin = min(xarr.lat.values)
    latmax = max(xarr.lat.values)

    xlim = [lonmin - 0.1, lonmax + 0.1]
    ylim = [latmin - 0.1, latmax + 0.1]

    ax.set(
        xlim=xlim,
        ylim=ylim,
    )

    ax.set_aspect(1/np.cos(np.mean(ylim)*np.pi/180))
    ax.grid(False)

    fig.tight_layout()


    return plot_to_base64(fig)