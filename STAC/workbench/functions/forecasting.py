import numpy as np
import pandas as pd
import matplotlib.pyplot as plt 
import warnings

import statsmodels.api as sm
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.exponential_smoothing.ets import ETSModel


class local_forecasting():

    def __init__(self, ds, transect, steps, alpha = 0.05):
        """
        Parameters:
            - ds (xr.ArrayDataset): dataset containing annual shoreline positions resolution.
            - transect (str): transect in a hotspot in the ds dataset.
            - steps (int): number of steps (years) in the future to which the forecasting extends.
   
        """

        self.params_sarima = [(1, 0, 0), (0, 1, 0), (0, 0, 1), (2, 0, 0), (0, 2, 0), (0, 0, 2)]
        self.seas_sarima = [(1, 0, 0, 12), (0, 1, 0, 12), (0, 0, 1, 12), (2, 0, 0, 12), (0, 2, 0, 12), (0, 0, 2, 12)]

        self.ds = ds
        self.transect = transect
        self.steps = steps
        self.alpha = alpha


    def find_timeseries(self):
        """
        This function extracts the timeseries of shoreline positions for a given transect. Outliers are also removed from this
        timeseries.

        Returns:
            - A tuple containing:
                - y (pd.DataFrame): timeseries of the shoreline positions with the outliers removed
                - a (float): changerate of the timeseries in y in m/yr
                - b (float): intercept of the timeseries in y in m
        """

        station = list(self.ds['transect_id'].values).index(str.encode(f'{self.transect}'))
        self.station = station
        a, b = self.ds.isel(stations=station)["changerate"].values, self.ds.isel(stations=station)["intercept"].values
        y = pd.DataFrame(data = (self.ds.isel(stations=station)["sp"].values), index = self.ds.time, columns = ['shoreline positions'])
        outl_idx = [i for i,x in enumerate(self.ds.isel(stations= self.station)['outliers'].values) if x == 1]
        
        y.iloc[outl_idx] = np.nan
        y.index.freq = 'AS'
        
        return y, a, b
    
    def create_models(self):
        
        """
        ML algorithms are trained on the data for several combinations of parameters.


        Returns:
            - models (dict): dictionary containing the ML algorithms trained on the data and with several combinations of parameters
        """

        y, a, b = self.find_timeseries()

        models = {
                'ARIMA': {
                    'params': self.params_sarima + self.params_sarima,
                    'seasonal_params': self.seas_sarima + [None] * len(self.params_sarima),
                    'func': lambda p, sp: ARIMA(y, 
                                                order=p, 
                                                seasonal_order=sp).fit() if sp != None else 
                                                ARIMA(y, 
                                                order=p).fit()
                },
                'SARIMAX': {
                    'params': self.params_sarima + self.params_sarima,
                    'seasonal_params': self.seas_sarima + [None] * len(self.params_sarima),
                    'func': lambda p, sp: SARIMAX(y, 
                                                order=p, 
                                                seasonal_order=sp).fit()
                },
                'ETSModel': {
                    'params': [{ 'error': 'add', 'trend': t, 'seasonal': s, 'damped': d}
                                for t in ['add', None]
                                for s in ['add', None]
                                for d in [True, False] if not (t is None and d)],
                    'seasonal_params': [None],
                    'func': lambda p,sp: ETSModel(y.values[:, 0], 
                                                error= p['error'], 
                                                trend= p['trend'],
                                                damped_trend = p['damped'],
                                                seasonal= p['seasonal'], 
                                                seasonal_periods=12).fit()
                            }
                        }
        
        return models
        
    
    def best_aic_model(self):

        """
        Function that choses the best ML model based on the aic metric.

        Returns:
            - min_model (-): model with the least aic.
        """

        aic_results = {}

        warnings.filterwarnings("ignore")

        forecast_models = self.create_models()

        for model_name, model_dict in forecast_models.items():
            aic_results[model_name] = {}
            params = model_dict['params']
            seasonal_params = model_dict['seasonal_params']
            func = model_dict['func']
            for p in params:
                for sp in seasonal_params:
                    fitted_model = func(p, sp)
                    aic = fitted_model.aic
                    aic_results[model_name][aic] = fitted_model

        min_model = [(k1, min(k2.keys()), aic_results[k1][min(k2.keys())]) for k1, k2 in aic_results.items()]

        return min_model
    

    def prediction_s_arima(self, model):
        
        """
        Function that makes a prediction using either the ARIMA or SARIMAX model.

        Parameters;
            - model (-): should be of the class ARIMA or SARIMAX.

        Returns:
            - A tuple containing:
                - y50 (pd.Series): the mean values of the prediction.
                - y_conf (pd.DataFrame): the lower and upper values of the prediction corresponding to the confidence interval of alpha.
        """

        forecast = model.get_forecast(self.steps)
        
        y50 = forecast.predicted_mean
        y_conf = forecast.conf_int(alpha = self.alpha)

        return y50, y_conf


    def prediction_est(self, model, y):
        
        """
        Function that makes a prediction using the Exponential Smoothing (EST) model.

        Parameters;
            - model (-): should be of the class EST.

        Returns:
            - A tuple containing:
                - y50 (pd.Series): the mean values of the prediction.
                - y_conf (pd.DataFrame): the lower and upper values of the prediction corresponding to the confidence interval of alpha.
        """

        offset1 = pd.DateOffset(years=1)
        offset2 = pd.DateOffset(years = self.steps - 1)

        ys = y.index[-1] + offset1
        index = pd.date_range(ys, ys + offset2, freq = 'AS')
        y50 = pd.Series(model.forecast(self.steps), index= index)
        
        simulations = model.simulate(
                                nsimulations= self.steps,
                                repetitions= 500,
                                anchor='end',
                                    )

        lower_ci = np.quantile(simulations, q= 1 - self.alpha, axis = 1)
        upper_ci = np.quantile(simulations, q= self.alpha, axis = 1)
        y_conf = pd.DataFrame(data={'lower': lower_ci, 'upper': upper_ci}, index=index)

        return y50, y_conf
    
    def plot(self):
        
        """
        Function that makes visualizes for each model the future forecast corresponding to the parameters with the lowest AIC value.

        """

        fig, ax = plt.subplots(3, 1, figsize=(20, 15), sharey = True)

        y, a, b = self.find_timeseries()
        best_models = self.best_aic_model()

        for i, bm in enumerate(best_models):
            if bm[0] != 'ETSModel':
                pred_uc, pred_ci = self.prediction_s_arima(bm[2])
            else:
                pred_uc, pred_ci = self.prediction_est(bm[2], y)

            timetot = y.index.union(pred_uc.index)
            ax[i].plot(y.index, y.values, 'ko', label="shoreline positions")
            ax[i].plot(pred_uc.index, pred_uc.values, 'go', label=f"{bm[0]} forecast")
            ax[i].fill_between(pred_ci.index,
                            pred_ci.iloc[:, 0],
                            pred_ci.iloc[:, 1], 
                            color='k', 
                            alpha=.25,
                            label = f'conf. int.')
            outl_idx = [i for i,x in enumerate(self.ds.isel(stations= self.station)['outliers'].values) if x == 1]
            outliers, outliers_time = y.values[outl_idx], y.index[outl_idx]
            ax[i].plot(outliers_time, outliers, 'ro', label="outliers")
            ax[i].plot(y.index, np.arange(0, len(y)) * a, color = 'b', label = f'lin. fit ({round(float(a), 1)} m/yr)')
            ax[i].plot(timetot, np.arange(len(timetot)) * a, color = 'b')
            ax[i].set_xlabel("Time [years]")
            ax[i].set_ylabel("Shoreline Position [m]")
            
            ax[i].grid()
            ax[i].axvline(pd.to_datetime('2021-07-01'), color = 'r', linestyle = '--', alpha= 0.4)
            ax[i].legend(loc = 'upper left')

        fig.suptitle(
                "Shoreline positions over time for transect %s"%self.ds.isel(stations=self.station)["transect_id"].values.tolist().decode("utf-8") 
            )
        fig.tight_layout()





         