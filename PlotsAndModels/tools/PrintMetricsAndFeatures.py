from IPython.display import display
from numpy import sqrt
from pandas import DataFrame
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_percentage_error


def printMetricsAndFeatures(title: str, actualData, predictedData, featureImportances=None, returnDfs=True):
    metricsList = []

    r2Score = r2_score(actualData, predictedData)
    metricsList.append(round(float(r2Score), 3))

    rmse = float(format(sqrt(mean_squared_error(actualData, predictedData)), '.3f'))
    metricsList.append(round(float(rmse), 3))

    mape = mean_absolute_percentage_error(actualData, predictedData, multioutput="raw_values")
    metricsList.append(round(float(mape[0]), 3))

    metricsDf = DataFrame([metricsList],
                          columns=['R^2', 'RMSE', 'MAPE'])

    if featureImportances is not None:
        importancesDf = DataFrame([featureImportances['importances']],
                                  columns=featureImportances['features'])
        display('Feature Importances')
        display(importancesDf)
    else:
        importancesDf = []
    if returnDfs:
        return metricsDf, importancesDf
    else:
        display(title)
        display(metricsDf)
