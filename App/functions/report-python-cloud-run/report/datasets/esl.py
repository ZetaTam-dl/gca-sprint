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
from utils.gentext import describe_data

# from matplotlib import colors ##TODO

world = gpd.read_file(
    Path(__file__).parent.parent.parent / "data" / "world_administrative.zip"
)

def get_esl_content(xarr: xr.Dataset) -> DatasetContent:
    """Get content for ESL dataset"""
    dataset_id = "esl"
    title = "Extreme Sea Level"
    text = "Here we generate some content based on the ESL dataset"

    image_base64 = create_esl_plot(xarr)
    return DatasetContent(
        dataset_id=dataset_id,
        title=title,
        text=text,
        image_base64=image_base64,
    )


def create_esl_plot(xarr):
    GWL = 0  # look at ds.gwl.values for options
    GWLs = "present-day"
    # ens = 50 # look at ds.ensemble.values for options
    rp = 50.0  # look at ds.rp.values for options

    xarr = xarr.sel(gwl=GWL, rp=rp)  # filter the other params

    # cmap = matplotlib.cm.RdYlGn_r
    # norm = colors.BoundaryNorm(np.arange(0, 7.5, 0.5), cmap.N)

    lonmin = min(xarr.lon.values)
    lonmax = max(xarr.lon.values)
    latmin = min(xarr.lat.values)
    latmax = max(xarr.lat.values)

    xlim = [lonmin - 0.1, lonmax + 0.1]
    ylim = [latmin - 0.1, latmax + 0.1]

    fig, ax = plt.subplots(1, 1, figsize=(10,10))

    base = world.boundary.plot(
        ax=ax, edgecolor="grey", facecolor="grey", alpha=0.1, zorder=0
    )

    rpc.scatter(xarr.sel(ensemble=5), data_type='data',
                ax=ax,
                x='lon', y='lat',
                hue='esl',
                cmap='RdYlGn_r',
                add_colorbar=False)
    
    xarr['lat'].values = xarr['lat'].values + 0.01

    rpc.scatter(xarr.sel(ensemble=50), data_type='data',
            ax=ax,
            x='lon', y='lat',
            hue='esl',
            cmap='RdYlGn_r',
            add_colorbar=False)
    
    xarr['lat'].values = xarr['lat'].values + 0.01

    rpc.scatter(xarr.sel(ensemble=95), data_type='data',
            ax=ax,
            x='lon', y='lat', 
            vmin=np.nanmin(xarr.sel(ensemble=5).esl.values),
            vmax=np.nanmax(xarr.sel(ensemble=95).esl.values),
            hue='esl',
            cmap='RdYlGn_r',
            add_colorbar=True, cbar_kwargs={'label':'ESL [m]'})

    # im1 = ax.scatter(
    #     xarr.lon.values,
    #     xarr.lat.values,
    #     10 * xarr.sel(ensemble=5).esl.values,
    #     xarr.sel(ensemble=5).esl.values,
    #     cmap=cmap,
    #     norm=norm,
    #     zorder=1,
    # )
    # # plt.set_clim(0,5)
    # im2 = ax.scatter(
    #     xarr.lon.values,
    #     xarr.lat.values + 0.1,
    #     10 * xarr.sel(ensemble=50).esl.values,
    #     xarr.sel(ensemble=50).esl.values,
    #     cmap=cmap,
    #     norm=norm,
    #     zorder=1,
    # )
    # im3 = ax.scatter(
    #     xarr.lon.values,
    #     xarr.lat.values + 0.2,
    #     10 * xarr.sel(ensemble=95).esl.values,
    #     xarr.sel(ensemble=95).esl.values,
    #     cmap=cmap,
    #     norm=norm,
    #     zorder=1,
    # )
    
    ax.set_title("%s-year extreme sea level for %s global warming level" % (rp, GWLs))

    ax.set(

        xlim=xlim,
        ylim=ylim,
    )

    ax.set_aspect(1/np.cos(np.mean(ylim)*np.pi/180))
    ax.grid(False)

    # fig.colorbar(im1, ax=ax)
    # im1.set_clim(0, 7)

    # cax = fig.add_axes(
    #     [
    #         ax.get_position().x1 + 0.01,
    #         ax.get_position().y0,
    #         0.02,
    #         ax.get_position().height,
    #     ]
    # )  # to give colorbar own axes
    # plt.colorbar(im1, cax=cax)  # Similar to fig.colorbar(im, cax = cax)
    # cax.set_title("ESL in meters")
    # #
    fig.tight_layout()
    
    return plot_to_base64(fig)
