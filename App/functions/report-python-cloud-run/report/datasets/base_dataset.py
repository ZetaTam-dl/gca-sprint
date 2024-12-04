from typing import Optional
import xarray as xr

from .datasetcontent import DatasetContent
from .esl import get_esl_content
from .shoremon import get_sedclass_content, get_shoremon_content, get_shoremon_fut_content


def get_dataset_content(dataset_id: str, xarr: xr.Dataset) -> Optional[DatasetContent]:
    match dataset_id:
        case "esl_gwl":
            return get_esl_content(xarr)
        case "sed_class":
            return get_sedclass_content(xarr)
        case "shore_mon":
            return get_shoremon_content(xarr)
        case "shore_mon_fut":
            return get_shoremon_fut_content(xarr)
        case _:
            return None
