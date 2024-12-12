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
        case 'overview':
            None

        case 'sediment_class':
            var = 'sediment_label'
                        
            # Create data dictionary
            # data_dict = {}
            # data_dict['lon'] = {'value': np.round(xarr['lon'].values, 2), 'long_name': xarr['lon'].attrs['long_name'], 'units': xarr['lon'].attrs['units']}
            # data_dict['lat'] = {'value': np.round(xarr['lat'].values, 2), 'long_name': xarr['lat'].attrs['long_name'], 'units': xarr['lat'].attrs['units']}
            # data_dict[var] = {'value': np.round(xarr[var].values, 0), 'long_name': xarr[var].attrs['long_name']}
            
            # Create changerate classes dictionary
            #classes_dict = {'sand': 0, 'mud': 1, 'coastal cliff': 2, 'vegetated': 3, 'other': 4}

            sand_port  = np.round(len(np.where(xarr[var].values == 0)[0]) / len(xarr[var].values) * 100, 1)
            mud_port   = np.round(len(np.where(xarr[var].values == 1)[0]) / len(xarr[var].values) * 100, 1)
            cliff_port = np.round(len(np.where(xarr[var].values == 2)[0]) / len(xarr[var].values) * 100, 1)
            veg_port   = np.round(len(np.where(xarr[var].values == 3)[0]) / len(xarr[var].values) * 100, 1)
            other_port = np.round(len(np.where(xarr[var].values == 4)[0]) / len(xarr[var].values) * 100, 1)

            prompt = """
            You are a coastal scientist tasked with writing a concise paragraph (maximum 100 words) for a report describing the state of the coast.
            The dataset contains the proportion of different materials existing along a coastline. There are 5 different numbers under the dataset here.
            The first one is the proportion of sand in percentage. The second one is the propotion of mud in percentage.
            The third one is the proportion of coastal cliff in percentage. The fourth one is the proportion of vegetated area in percentage.
            The last one is the propotion of other materials in percentage.
            You should summarise the dataset and list the proportions of each material. You should describe what material is the majority of the coast and how materials are distributed along the shoreline. 
            Ensure the description is clear, professional, and aligned with the dataset's trends. Begin your paragraph with: "The coast in this area is characterized by...".
            
            * Dataset: {} {} {} {} {}
            """.format(sand_port, mud_port, cliff_port, veg_port, other_port)


        case 'world_pop':
            var = 'pop_tot'

            lon = np.round(xarr['lon'].values, 4)
            lat = np.round(xarr['lat'].values, 4) 
            pop = np.round(xarr[var].values, 0)


            prompt = """
            You are a coastal scientist tasked with writing a concise paragraph (maximum 100 words) for a report describing the state of the coast.
            This paragraph is related to human population living along coastlines. Higher population along a coastline means that there will be higher potential loss,
            including property and human loss, if there is any coastal hazard. Smaller loss or impact if ther population is smaller.
            You should summarise the population and its distribution along the coast. You should also spot if there is any important location, where you can find a high population.
            There are three individual datasets for you. The first dataset is the longitude of locations. The second dataset is the latitude of locations. The third dataset is the human population at locations.
            You should at least specify at which longitude and latitude where we can find a substantial amount of population.
            Ensure the description is clear, professional, and aligned with the dataset's trends. Begin your paragraph with: "The coast in this area is characterized by...".
            
            * Dataset 1: {}
            * Dataset 2: {}
            * Dataset 3: {}
            """.format(lon, lat, pop)



        case 'shoreline_change':
            var = 'changerate'
            
            # Create data dictionary
            data_dict = {}
            data_dict['lon'] = {'value': np.round(xarr['lon'].values, 2), 'long_name': xarr['lon'].attrs['long_name'], 'units': xarr['lon'].attrs['units']}
            data_dict['lat'] = {'value': np.round(xarr['lat'].values, 2), 'long_name': xarr['lat'].attrs['long_name'], 'units': xarr['lat'].attrs['units']}
            data_dict[var] = {'value': np.round(xarr[var].values, 2), 'long_name': xarr[var].attrs['long_name'], 'units': xarr[var].attrs['units']}

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

        case 'land_sub':
            None

        case 'esl':
            None

        case 'future_shoreline_change':
            None

    return prompt