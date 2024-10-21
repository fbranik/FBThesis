import pandas as pd

from tools.DashApp import createDashApp
from tools.ReadFiles import reReadOutFiles

readOutFiles = False
arisDataCSV = 'mainModel/mainModelData.csv'

computationalLoadType = ['MemoryBound']  # , 'ComputeBound16']
commCompBarriers = ['NoBarrier']
applicationNames = ['Memory Bound', 'Compute Bound16', 'Compute Bound32']
application = []
for iType in computationalLoadType:
    for iBarrier in commCompBarriers:
        application.append(iType + iBarrier)

workingSetSize = ['2MiB', '8MiB', '32MiB', '128MiB', '256MiB', '512MiB']
numberOfNodes = [64]  #[4, 8, 16, 32, 64]
processesPerNode = [2, 4, 8, 16, 20]
numberOfMessages = [2, 4, 8]

msgSizes = [1, 5, 10, 50, 100]
# msgSizes = ['32KiB', '256KiB', '2MiB', '16MiB']

primitiveColumns = ['Total Time',
                    'Computation Time', 'Derived Communication Time',
                    'Measured Communication Time',
                    'Number of Nodes', 'Processes per Node',
                    'Working Set Size', 'Working Set Size (Bytes)',
                    'Message Size', 'Message Size (Bytes)']

label = 'Measured_Communication_Time'

features = ['Working Set Size', 'Computational Load Type', 'Message Size', 'Number of Messages',
            'Number of Nodes', 'Processes per Node']

featuresTrain = ['Working_Set_Size_(Bytes)', 'Computational_Load_Type', 'Message_Size_(Bytes)', 'Number_of_Messages',
                 'Number_of_Nodes', 'Processes_per_Node']

times = ['Computation Time', 'Measured Communication Time',
         'Derived Communication Time', 'Total Time', 'Communication to Total Time Ratio']

forBoxPlot = []

if readOutFiles:
    outfileDirectory = "./outfiles/constantMessageSize"

    arisDatasetAnalysisDF = reReadOutFiles(primitiveColumns, computationalLoadType, workingSetSize, commCompBarriers,
                                           numberOfNodes, processesPerNode, numberOfMessages, msgSizes, arisDataCSV,
                                           outfileDirectory)

    arisDatasetAnalysisDF['Communication to Total Time Ratio'] = (arisDatasetAnalysisDF['Measured Communication Time']
                                                                  / arisDatasetAnalysisDF['Total Time'])

    print('All Data', arisDatasetAnalysisDF.shape[0])

    condition = (
            (arisDatasetAnalysisDF['Communication to Total Time Ratio'] >= 0.1) &
            (arisDatasetAnalysisDF['Communication to Total Time Ratio'] <= 0.8)
    )
    arisDatasetAnalysisDF = arisDatasetAnalysisDF.loc[condition]
    arisDatasetAnalysisDF.to_csv(arisDataCSV, sep=',', mode='w', index=False)
else:
    arisDatasetAnalysisDF = pd.read_csv(arisDataCSV, sep=',')


arisDatasetAnalysisDF.columns = arisDatasetAnalysisDF.columns.str.replace('_', ' ')

dashApp = createDashApp(arisDatasetAnalysisDF, features, times, processesPerNode, msgSizes,
                        numberOfMessages, workingSetSize, numberOfNodes)

dashApp.run(jupyter_mode="external", debug=True, dev_tools_silence_routes_logging=False, port=8051)
