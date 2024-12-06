import os
from openai import AzureOpenAI
import numpy as np
import xarray as xr

def describe_data(xarr: xr.Dataset, dataset_id: str) -> str:
     # Create prompt
    prompt = make_prompt(xarr, dataset_id)

    # Load environment variables
    api_version = '2024-03-01-preview'
    api_base_url = os.getenv('OPENAI_API_BASE')
    api_key = os.getenv('AZURE_OPENAI_API_KEY')
    deployment_name = os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME')

    # Initialise large language model
    model = AzureOpenAI(
        api_key=api_key,
        api_version=api_version,
        base_url=f'{api_base_url}/deployments/{deployment_name}',
    )

    # Trigger model
    response = model.chat.completions.create(
        model=os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME'),
        messages=[
            {'role': 'system', 'content': prompt},
        ],
        max_tokens=1000,
        temperature=0.1,
    )

    # Return response
    return response.choices[0].message.content


def make_prompt(xarr: xr.Dataset, dataset_id: str) -> str:
    match dataset_id: 
        case 'shoreline_change':
            var = 'changerate'
                # Create data dictionary
            data_dict = {}
            data_dict['lon'] = {'value': np.round(xarr['lon'].values, 2), 'long_name': xarr['lon'].attrs['long_name'], 'units': xarr['lon'].attrs['units']}
            data_dict['lat'] = {'value': np.round(xarr['lat'].values, 2), 'long_name': xarr['lat'].attrs['long_name'], 'units': xarr['lat'].attrs['units']}
            data_dict['changerate'] = {'value': np.round(xarr[var].values, 2), 'long_name': xarr[var].attrs['long_name'], 'units': xarr[var].attrs['units']}

            # Create changerate classes dictionary
            classes_dict = {}
            classes_dict['extreme_accretion'] = {'min': 5, 'max': np.inf, 'unit': xarr[var].attrs['units']}
            classes_dict['severe_accretion'] = {'min': 3, 'max': 5, 'unit': xarr[var].attrs['units']}
            classes_dict['intense_accretion'] = {'min': 1, 'max': 3, 'unit': xarr[var].attrs['units']}
            classes_dict['accretion'] = {'min': 0.5, 'max': 1, 'unit': xarr[var].attrs['units']}
            classes_dict['stable'] = {'min': -0.5, 'max': 0.5, 'unit': xarr[var].attrs['units']}
            classes_dict['erosion'] = {'min': -1, 'max': -0.5, 'unit': xarr[var].attrs['units']}
            classes_dict['intense_erosion'] = {'min': -3, 'max': -1, 'unit': xarr[var].attrs['units']}
            classes_dict['severe_erosion'] = {'min': -5, 'max': -3, 'unit': xarr[var].attrs['units']}
            classes_dict['extreme_erosion'] = {'min': -np.inf, 'max': -5, 'unit': xarr[var].attrs['units']}

            prompt = """
            You are a coastal scientist tasked with writing a concise paragraph (maximum 100 words) for a report describing the state of the coast.
            Use the dataset below, which contains coastal change rates (positive values indicate accretion, negative values indicate erosion).
            Categorize the observed change rates using the coastal erosion classes, also provided below. Ensure the description is clear, professional,
            and aligned with the dataset's trends. Begin your paragraph with: "The coast in this area is characterized by...".
            
            * Dataset: {}
            * coastal erosion classes: {}
            """.format(str(data_dict), str(classes_dict))

    return prompt