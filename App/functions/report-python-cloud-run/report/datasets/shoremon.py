# Packages for loading data
import geopandas as gpd
import pystac_client
import matplotlib.pyplot as plt
from shapely.geometry import Polygon
import xarray as xr

# Packages for interactive plotting
import holoviews as hv
import geoviews as gv
import hvplot.xarray
import hvplot.pandas

# Packages for plotting
from resilientplotterclass import rpc
from pathlib import Path
import matplotlib

matplotlib.use("Agg")
from matplotlib import colors
from matplotlib import pyplot as plt

plt.rcParams["svg.fonttype"] = "none"
import numpy as np
import xarray as xr

import geopandas as gpd  # type: ignore

from .utils import plot_to_base64
from .datasetcontent import DatasetContent

world = gpd.read_file(
        Path(__file__).parent.parent.parent / "data" / "world_administrative.zip"
    )

def get_sedclass_content(xarr: xr.Dataset) -> DatasetContent:
    """Get content for the dataset"""
    dataset_id = "sediment_label"
    title = "Beach Sediment Classification"
    text = "Here we generate some content based on the the dataset" ##TODO: to be filled in by LLM

    image_base64 = create_sedclass_plot(xarr)
    return DatasetContent(
        dataset_id=dataset_id,
        title=title,
        text=text,
        image_base64=image_base64,
    )


def get_shoremon_content(xarr: xr.Dataset) -> DatasetContent:
    """Get content for the dataset"""
    dataset_id = "changerate"
    title = "The Shoreline Monitor"
    text = "Here we generate some content based on the the dataset" ##TODO: to be filled in by LLM

    image_base64 = create_shoremon_plot(xarr)
    return DatasetContent(
        dataset_id=dataset_id,
        title=title,
        text=text,
        image_base64=image_base64,
    )


def get_shoremon_fut_content(xarr: xr.Dataset) -> DatasetContent:
    """Get content for the dataset"""
    dataset_id = ["sp_rcp45_p50", "sp_rcp85_p50"]
    title = "The Shoreline Monitor - Future Projection"
    text = "Here we generate some content based on the the dataset" ##TODO: to be filled in by LLM

    image_base64 = create_shoremon_fut_plot(xarr)
    return DatasetContent(
        dataset_id=dataset_id,
        title=title,
        text=text,
        image_base64=image_base64,
    )


def create_sedclass_plot(xarr):
    sediment_classes_dict = {0: 'sand', 1: 'mud', 2: 'coastal cliff', 3: 'vegetated', 4: 'other'}
    color_dict = {0:'yellow', 1:'brown', 2:'blue', 3:'green', 4:'gray'}

    from matplotlib.colors import ListedColormap,Normalize
    import matplotlib as mpl

    existing_values  = np.unique(xarr['sediment_label'])
    existing_class   = [sediment_classes_dict[val] for val in existing_values]
    existing_color   = [color_dict[val] for val in existing_values]
    
    sediment_classes = [sediment_classes_dict[i] for i in xarr['sediment_label'].values]
    xarr['sediment_class'] = xr.DataArray(sediment_classes, dims='stations')

    cmap = ListedColormap(existing_color)
    norm = Normalize(vmin=0, vmax=cmap.N)
    cb = mpl.cm.ScalarMappable(norm=norm, cmap=cmap)

    portion = []

    for type in existing_class:
        port = len(np.where(xarr['sediment_class'] == type)[0]) / len(xarr['sediment_class'])
        portion.append(port)

    # Plot the data
    fig, ax = plt.subplots(2, 1, figsize=(5, 10), height_ratios=[1,1])
    
    base = world.boundary.plot(
        ax=ax[0], edgecolor="grey", facecolor="grey", alpha=0.1, zorder=0
    )

    aspect = len(existing_class) / 0.8
    p = rpc.scatter(xarr, ax=ax[0], 
                    x='lon', y='lat', 
                    hue='sediment_label', 
                    edgecolor='none', cmap=cmap, 
                    add_colorbar=False
                    )
    
    cbar = plt.colorbar(cb, ax=ax[0], 
                        **{'label': 'Sediment classes', 'pad': 0.01, 
                           'fraction': 0.05,'aspect':aspect})
    cbar.set_ticks(ticks=np.arange(0.5, len(existing_color), 1), labels=existing_class)

    ax[1].pie(portion, labels=existing_class, autopct='%1.1f%%', colors=existing_color)

    lonmin = min(xarr.lon.values)
    lonmax = max(xarr.lon.values)
    latmin = min(xarr.lat.values)
    latmax = max(xarr.lat.values)

    xlim = [lonmin - 0.1, lonmax + 0.1]
    ylim = [latmin - 0.1, latmax + 0.1]

    ax[0].set(
        xlabel="lon",
        ylabel="lat",
        xlim=xlim,
        ylim=ylim,
    )

    ax[0].set_aspect(1/np.cos(np.mean(ylim)*np.pi/180))
    ax[0].grid(False)


    return plot_to_base64(fig)


def create_shoremon_plot(xarr):
    fig, ax = plt.subplots(1, 1, figsize=(10, 10))

    base = world.boundary.plot(
        ax=ax, edgecolor="grey", facecolor="grey", alpha=0.1, zorder=0
    )

    p = rpc.scatter(xarr, ax=ax, 
                    x='lon', y='lat', 
                    hue='changerate', 
                    vmin=-5, vmax=5, 
                    edgecolor='none', cmap='RdYlGn', 
                    add_colorbar=False
                    )

    from mpl_toolkits.axes_grid1 import make_axes_locatable
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size=0.25, pad=0.10)
    plt.colorbar(p, cax=cax, label='Shoreline Change Rate [m/yr]')

    lonmin = min(xarr.lon.values)
    lonmax = max(xarr.lon.values)
    latmin = min(xarr.lat.values)
    latmax = max(xarr.lat.values)

    xlim = [lonmin - 0.1, lonmax + 0.1]
    ylim = [latmin - 0.1, latmax + 0.1]

    ax.set(
        xlabel="lon",
        ylabel="lat",
        xlim=xlim,
        ylim=ylim,
    )

    ax.set_aspect(1/np.cos(np.mean(ylim)*np.pi/180))
    ax.grid(False)
    
    return plot_to_base64(fig)


def create_shoremon_fut_plot(xarr):
    scenariolist = ['sp_rcp45_p50', 'sp_rcp85_p50']
    yearlist = [2021, 2050, 2100]


    fig, ax = plt.subplots(2, 2, figsize=(15, 15))
                
    for yr in range(0,2):
        for scenario in scenariolist:
            if scenario == 'sp_rcp45_p50':
                scenarioname = 'RCP4.5'
                jj = 0
            elif scenario == 'sp_rcp85_p50':
                scenarioname = 'RCP8.5'
                jj = 1

            diff = xarr.diff('time', 1).sel(time=str(yearlist[yr + 1]))

            base = world.boundary.plot(
                    ax=ax[yr, jj], edgecolor="grey", facecolor="grey", alpha=0.1, zorder=0
                )
            
            p = rpc.scatter(diff / (yearlist[yr + 1] - yearlist[yr]), 
                            ax=ax[yr, jj], 
                            x='lon', y='lat', 
                            vmin=-5, vmax=5, 
                            hue=scenario, 
                            edgecolor='none', cmap='RdYlGn', 
                            add_colorbar=False)

            from mpl_toolkits.axes_grid1 import make_axes_locatable
            divider = make_axes_locatable(ax[yr, jj])
            cax = divider.append_axes("right", size=0.25, pad=0.10)
            plt.colorbar(p, cax=cax, label='Average Shoreline Change Rate [m/yr]')

            lonmin = min(xarr.lon.values)
            lonmax = max(xarr.lon.values)
            latmin = min(xarr.lat.values)
            latmax = max(xarr.lat.values)

            xlim = [lonmin - 0.1, lonmax + 0.1]
            ylim = [latmin - 0.1, latmax + 0.1]

            ax[yr, jj].set(
                xlabel="lon",
                ylabel="lat",
                xlim=xlim,
                ylim=ylim,
            )

            ax[yr, jj].set_aspect(1/np.cos(np.mean(ylim)*np.pi/180))
            ax[yr, jj].grid(False)
            ax[yr, jj].set_title('50%ile Future Prediction between Year {}'.format(yearlist[yr+1]) + ' and Year {}'.format(yearlist[yr]) + '\n' + '- Scenario {}'.format(scenarioname))

    return plot_to_base64(fig)
