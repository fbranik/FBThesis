import sys
from statistics import NormalDist

sys.path.append('/Users/fbran/Documents/Projects/FBThesis/PlotsAndModels/tools')
from PrintMetricsAndFeatures import printMetricsAndFeatures
import pandas as pd
import numpy as np
import tensorflow as tf
import tensorflow_decision_forests as tfdf

tf.random.set_seed(147)


def trainAndTest(arisData, features, targetColumn, arisUnseenData, pureArisData, scenarioName='mainModel',
                 test_size=0.4,
                 labelName='Communication_Time',
                 importanceType='INV_MEAN_MIN_DEPTH'):
    # #### Random Forest Regression

    rfModel = tfdf.keras.RandomForestModel(task=tfdf.keras.Task.REGRESSION,
                                           random_seed=147, num_trees=400,
                                           compute_oob_variable_importances=True,
                                           num_oob_variable_importances_permutations=2,
                                           max_depth=5)
    arisData = arisData[features + [targetColumn]]
    trainSet, testSet = split_dataset(arisData, test_ratio=test_size)
    # testSet,  validationSet = split_dataset(testSetTemp, test_ratio=0.5)

    trainDs = tfdf.keras.pd_dataframe_to_tf_dataset(trainSet, label=targetColumn, task=tfdf.keras.Task.REGRESSION)
    testDs = tfdf.keras.pd_dataframe_to_tf_dataset(testSet, label=targetColumn, task=tfdf.keras.Task.REGRESSION)

    # validationDs = tfdf.keras.pd_dataframe_to_tf_dataset(validationSet, label=targetColumn, task=tfdf.keras.Task.REGRESSION)

    testDsUnseenData = tfdf.keras.pd_dataframe_to_tf_dataset(arisUnseenData, label=targetColumn,
                                                             task=tfdf.keras.Task.REGRESSION)

    rfModel.fit(trainDs)
    # , validation_data=validationDs, num_folds=5)
    rfModel.compile(metrics=["mse"])

    trainPredictions = rfModel.predict(trainDs)
    testPredictions = rfModel.predict(testDs)
    testUnseenDataPredictions = rfModel.predict(testDsUnseenData)

    rfTestMetrics = printMetricsAndFeatures('Random_Forest_Testing_Score',
                                            testSet[targetColumn], testPredictions)[0]

    rfTestMetrics['Name'] = f'Testing_Metrics_({targetColumn})'

    rfTrainMetrics = printMetricsAndFeatures('Random_Forest_Training_Score',
                                             trainSet[targetColumn], trainPredictions)[0]

    rfTrainMetrics['Name'] = f'Training_Metrics_({targetColumn})'
    rfTestingUnseenDataMetrics, _ = printMetricsAndFeatures('Random_Forest_Testing_Score',
                                                            arisUnseenData[targetColumn], testUnseenDataPredictions, )

    rfTestingUnseenDataMetrics['Name'] = f'UnseenData_only_Metrics_({targetColumn})'

    rfMetrics = pd.concat([rfTrainMetrics, rfTestMetrics, rfTestingUnseenDataMetrics])

    first_column = rfMetrics.pop('Name')
    rfMetrics.insert(0, 'Name', first_column)

    for idx, actualTime in enumerate(trainSet[targetColumn]):
        pureArisData.loc[pureArisData[targetColumn] == actualTime,
        [f'RF_Model_{labelName}']] = trainPredictions[idx]

        pureArisData.loc[pureArisData[targetColumn] == actualTime,
        [f'RF_Model_{labelName}_Percentage_Error']] = (trainPredictions[idx] - actualTime) / actualTime

    for idx, actualTime in enumerate(testSet[targetColumn]):
        pureArisData.loc[pureArisData[targetColumn] == actualTime,
        [f'RF_Model_{labelName}']] = testPredictions[idx]

        pureArisData.loc[pureArisData[targetColumn] == actualTime,
        [f'RF_Model_{labelName}_Percentage_Error']] = (testPredictions[idx] - actualTime) / actualTime

    for idx, rowId in enumerate(arisUnseenData['row_id']):
        arisUnseenData.loc[arisUnseenData['row_id'] == rowId, [f'RF_Model_{labelName}']] = \
            testUnseenDataPredictions[idx]

    rfInspector = rfModel.make_inspector()
    try:
        importances = rfInspector.variable_importances()[importanceType]
    except KeyError:
        raise ValueError(
                f"No_{rfInspector}_importances_found_in_the_given_inspector_object"
        )

    rfImportances = {}
    for f in importances:
        rfImportances[f[0].name] = f[1]

        ### Gradient boosting

    gBoostModel = tfdf.keras.GradientBoostedTreesModel(task=tfdf.keras.Task.REGRESSION,
                                                       random_seed=147
                                                       )

    trainSet, testSet = split_dataset(arisData, test_ratio=test_size)
    # testSet, validationSet = split_dataset(testSetTemp, test_ratio=0.5)

    trainDs = tfdf.keras.pd_dataframe_to_tf_dataset(trainSet, label=targetColumn, task=tfdf.keras.Task.REGRESSION)
    testDs = tfdf.keras.pd_dataframe_to_tf_dataset(testSet, label=targetColumn, task=tfdf.keras.Task.REGRESSION)

    # validationDs = tfdf.keras.pd_dataframe_to_tf_dataset(validationSet, label=targetColumn, task=tfdf.keras.Task.REGRESSION)

    testDsUnseenData = tfdf.keras.pd_dataframe_to_tf_dataset(arisUnseenData, label=targetColumn,
                                                             task=tfdf.keras.Task.REGRESSION)

    gBoostModel.fit(trainDs)
    # , validation_data=validationDs, num_folds=5)
    gBoostModel.compile(metrics=["mse"])

    trainPredictions = gBoostModel.predict(trainDs)
    testPredictions = gBoostModel.predict(testDs)
    testUnseenDataPredictions = gBoostModel.predict(testDsUnseenData)

    gBoostTestMetrics = printMetricsAndFeatures('Gradient_Boosting_Testing_Score',
                                                testSet[targetColumn], testPredictions)[0]

    gBoostTestMetrics['Name'] = f'Testing_Metrics_({targetColumn})'

    gBoostTrainMetrics = printMetricsAndFeatures('Gradient_Boosting_Training_Score',
                                                 trainSet[targetColumn], trainPredictions)[0]

    gBoostTrainMetrics['Name'] = f'Training_Metrics_({targetColumn})'
    gBoostTestingUnseenDataMetrics, _ = printMetricsAndFeatures('Gradient_Boosting_Testing_Score',
                                                                arisUnseenData[targetColumn],
                                                                testUnseenDataPredictions, )

    gBoostTestingUnseenDataMetrics['Name'] = f'UnseenData_only_Metrics_({targetColumn})'

    for idx, actualTime in enumerate(trainSet[targetColumn]):
        pureArisData.loc[pureArisData[targetColumn] == actualTime,
        [f'Gradient_Boosting_Model_{labelName}']] = trainPredictions[idx]

        pureArisData.loc[pureArisData[targetColumn] == actualTime,
        [f'Gradient_Boosting_Model_{labelName}_Percentage_Error']] = (trainPredictions[
                                                                          idx] - actualTime) / actualTime

    for idx, actualTime in enumerate(testSet[targetColumn]):
        pureArisData.loc[pureArisData[targetColumn] == actualTime,
        [f'Gradient_Boosting_Model_{labelName}']] = testPredictions[idx]

        pureArisData.loc[pureArisData[targetColumn] == actualTime,
        [f'Gradient_Boosting_Model_{labelName}_Percentage_Error']] = (testPredictions[idx] - actualTime) / actualTime

    for idx, rowId in enumerate(arisUnseenData['row_id']):
        arisUnseenData.loc[arisUnseenData['row_id'] == rowId, [f'Gradient_Boosting_Model_{labelName}']] = \
            testUnseenDataPredictions[idx]

        # pureArisData.loc[pureArisData[targetColumn] == actualTime,
        # [f'Gradient_Boosting_Model_{labelName}']] = testUnseenDataPredictions[idx]
        #
        # pureArisData.loc[pureArisData[targetColumn] == actualTime,
        # [f'Gradient_Boosting_Model_{labelName}_Percentage_Error']] = (testUnseenDataPredictions[idx] - actualTime) / actualTime

    gBoostInspector = gBoostModel.make_inspector()
    try:
        importances = gBoostInspector.variable_importances()[importanceType]
    except KeyError:
        raise ValueError(
                f"No_{gBoostInspector}_importances_found_in_the_given_inspector_object"
        )

    gBoostImportances = {}
    for f in importances:
        gBoostImportances[f[0].name] = f[1]

    tuner = tfdf.tuner.RandomSearch(num_trials=100, use_predefined_hps=True, )
    tunedGBoostModel = tfdf.keras.GradientBoostedTreesModel(task=tfdf.keras.Task.REGRESSION,
                                                            random_seed=147, tuner=tuner)

    '''
    num_trees=400,
    growing_strategy="BEST_FIRST_GLOBAL",
    max_depth=5, 
    '''

    trainSet, testSet = split_dataset(arisData, test_ratio=test_size)
    # testSet, validationSet = split_dataset(testSetTemp, test_ratio=0.5)

    trainDs = tfdf.keras.pd_dataframe_to_tf_dataset(trainSet, label=targetColumn, task=tfdf.keras.Task.REGRESSION)
    testDs = tfdf.keras.pd_dataframe_to_tf_dataset(testSet, label=targetColumn, task=tfdf.keras.Task.REGRESSION)

    # validationDs = tfdf.keras.pd_dataframe_to_tf_dataset(validationSet, label=targetColumn, task=tfdf.keras.Task.REGRESSION)

    testDsUnseenData = tfdf.keras.pd_dataframe_to_tf_dataset(arisUnseenData, label=targetColumn,
                                                             task=tfdf.keras.Task.REGRESSION)

    tunedGBoostModel.fit(trainDs)
    # , validation_data=validationDs, num_folds=5)
    tunedGBoostModel.compile(metrics=["mse"])

    trainPredictions = tunedGBoostModel.predict(trainDs)
    testPredictions = tunedGBoostModel.predict(testDs)
    testUnseenDataPredictions = tunedGBoostModel.predict(testDsUnseenData)

    tunedGBoostTestMetrics = printMetricsAndFeatures('Tuned_Gradient_Boosting_Testing_Score',
                                                     testSet[targetColumn], testPredictions)[0]

    tunedGBoostTestMetrics['Name'] = f'Testing_Metrics_({targetColumn})'

    tunedGBoostTrainMetrics = printMetricsAndFeatures('Tuned_Gradient_Boosting_Training_Score',
                                                      trainSet[targetColumn], trainPredictions)[0]

    tunedGBoostTrainMetrics['Name'] = f'Training_Metrics_({targetColumn})'
    tunedGBoostTestingUnseenDataMetrics, _ = printMetricsAndFeatures('Tuned_Gradient_Boosting_Testing_Score',
                                                                     arisUnseenData[targetColumn],
                                                                     testUnseenDataPredictions, )

    tunedGBoostTestingUnseenDataMetrics['Name'] = f'UnseenData_only_Metrics_({targetColumn})'

    for idx, actualTime in enumerate(trainSet[targetColumn]):
        pureArisData.loc[pureArisData[targetColumn] == actualTime,
        [f'Tuned_Gradient_Boosting_Model_{labelName}']] = trainPredictions[idx]

        pureArisData.loc[pureArisData[targetColumn] == actualTime,
        [f'Tuned_Gradient_Boosting_Model_{labelName}_Percentage_Error']] = (trainPredictions[
                                                                                idx] - actualTime) / actualTime

    for idx, actualTime in enumerate(testSet[targetColumn]):
        pureArisData.loc[pureArisData[targetColumn] == actualTime,
        [f'Tuned_Gradient_Boosting_Model_{labelName}']] = testPredictions[idx]

        pureArisData.loc[pureArisData[targetColumn] == actualTime,
        [f'Tuned_Gradient_Boosting_Model_{labelName}_Percentage_Error']] = (testPredictions[
                                                                                idx] - actualTime) / actualTime

    for idx, rowId in enumerate(arisUnseenData['row_id']):
        arisUnseenData.loc[arisUnseenData['row_id'] == rowId, [f'Tuned_Gradient_Boosting_Model_{labelName}']] = \
            testUnseenDataPredictions[idx]

        # pureArisData.loc[pureArisData[targetColumn] == actualTime,
        # [f'Tuned_Gradient_Boosting_Model_{labelName}']] = testUnseenDataPredictions[idx]
        #
        # pureArisData.loc[pureArisData[targetColumn] == actualTime,
        # [f'Tuned_Gradient_Boosting_Model_{labelName}_Percentage_Error']] = (testUnseenDataPredictions[idx] - actualTime) / actualTime

    tunedGBoostInspector = tunedGBoostModel.make_inspector()
    try:
        importances = tunedGBoostInspector.variable_importances()[importanceType]
    except KeyError:
        raise ValueError(
                f"No_{tunedGBoostInspector}_importances_found_in_the_given_inspector_object"
        )

    tunedGBoostImportances = {}
    for f in importances:
        tunedGBoostImportances[f[0].name] = f[1]
    # rfModel.summary()

    # gBoostModel.summary()

    gBoostWholeDataMetrics, _ = printMetricsAndFeatures('Gradient_Boosting_Whole_Score',
                                                        pureArisData[targetColumn],
                                                        pureArisData[f'Gradient_Boosting_Model_{labelName}'], )

    gBoostWholeDataMetrics['Name'] = f'WholeData_Metrics_({targetColumn})'

    TunedGBoostWholeDataMetrics, _ = printMetricsAndFeatures('Tuned_Gradient_Boosting_Whole_Score',
                                                             pureArisData[targetColumn],
                                                             pureArisData[
                                                                 f'Tuned_Gradient_Boosting_Model_{labelName}'], )

    TunedGBoostWholeDataMetrics['Name'] = f'WholeData_Metrics_({targetColumn})'
    #
    gBoostMetrics = pd.concat(
            [gBoostTrainMetrics, gBoostTestMetrics, gBoostTestingUnseenDataMetrics, gBoostWholeDataMetrics])
    tunedGBoostMetrics = pd.concat(
            [tunedGBoostTrainMetrics, tunedGBoostTestMetrics, tunedGBoostTestingUnseenDataMetrics,
             TunedGBoostWholeDataMetrics])

    first_column = gBoostMetrics.pop('Name')
    gBoostMetrics.insert(0, 'Name', first_column)

    first_column = tunedGBoostMetrics.pop('Name')
    tunedGBoostMetrics.insert(0, 'Name', first_column)
    rfMetrics['Model'] = 'Random Forest'
    gBoostMetrics['Model'] = 'Gradient Boosting'
    tunedGBoostMetrics['Model'] = 'Tuned Gradient Boosting'

    rfImportances['Model'] = 'Random Forest'
    gBoostImportances['Model'] = 'Gradient Boosting'
    tunedGBoostImportances['Model'] = 'Tuned Gradient Boosting'

    metricsTemp = [rfMetrics, gBoostMetrics, tunedGBoostMetrics]
    importancesTemp = [rfImportances, gBoostImportances, tunedGBoostImportances]

    metrics = pd.concat(metricsTemp)
    importances = pd.DataFrame.from_records(importancesTemp)

    importances.to_csv(f'{scenarioName}Importances.csv', sep=',', mode='w', index=False)
    metrics.to_csv(f'{scenarioName}Metrics.csv', sep=',', mode='w', index=False)

    return


def split_dataset(dataset, test_ratio=0.30):
    np.random.seed(117147)  # scales 117147
    test_indices = np.random.rand(len(dataset), ) < test_ratio

    return dataset[~test_indices], dataset[test_indices]


def confidence_interval(data, confidence=0.95):
    dist = NormalDist.from_samples(data)
    z = NormalDist().inv_cdf((1 + confidence) / 2.)
    h = dist.stdev * z / ((len(data) - 1) ** .5)
    return dist.mean - h, dist.mean + h


def calculate_ratio(df, series, targetColumn):
    min_value = series.iloc[0]

    for value in series:
        ratio = value / min_value
        min_value = value

        df.loc[(df[targetColumn] == value), targetColumn + 'Ratio'] = ratio
