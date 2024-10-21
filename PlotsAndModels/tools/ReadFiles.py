import re
from os import getcwd

import numpy as np
import pandas as pd
from fs.filesize import binary as binarySize

binarySizes = {
        'KiB': 2 ** 10,
        'MiB': 2 ** 20,
        'GiB': 2 ** 30
}


def stringSizeToNumber(stringSize: str):
    for iSuffix, iMul in binarySizes.items():
        if iSuffix in stringSize:
            return iMul * float(stringSize.replace(iSuffix, ''))


def readOutFile(fileName, sizeInBytes=False, sizes=None, convFile=False):
    fp = open('{}/{}'.format(str(getcwd()), fileName), encoding="utf8", errors='ignore')
    try:
        line = fp.readline()
    except:
        line = fp.readline()
    version = ''
    numProcs = ''
    list4DF = []
    while line:
        if line.startswith("Jacobi X"):
            version = "Variable Stencil"
            tempMatchObj = re.search(
                    r'Jacobi\s+X\s+(\d+)\s+Y\s+(\d+)\s+Px\s+(\d+)\s+Py\s+(\d+)\s+Iter\s+(\d+)',
                    line).groups()
            arrayXSize = int(tempMatchObj[0])
            arrayYSize = int(tempMatchObj[1])
            numProcs = int(tempMatchObj[2]) * int(tempMatchObj[3])
            timeIter = int(tempMatchObj[4])
            compDataSize = arrayXSize * arrayYSize * 8 / numProcs
        if line.startswith("GaussSeidel X"):
            version = "GaussSeidel"
            tempMatchObj = re.search(
                    r'GaussSeidel\s+X\s+(\d+)\s+Y\s+(\d+)\s+Px\s+(\d+)\s+Py\s+(\d+)\s+Iter\s+(\d+)',
                    line).groups()
            arrayXSize = int(tempMatchObj[0])
            arrayYSize = int(tempMatchObj[1])
            numProcs = int(tempMatchObj[2]) * int(tempMatchObj[3])
            compDataSize = arrayXSize * arrayYSize * 8 / numProcs
            timeIter = int(tempMatchObj[4])
        if line.startswith("NAS BT X"):
            version = "NAS BT"
            tempMatchObj = re.search(
                    r'NAS BT\s+X\s+(\d+)\s+Y\s+(\d+)\s+Px\s+(\d+)\s+Py\s+(\d+)\s+Iter\s+(\d+)',
                    line).groups()
            arrayXSize = int(tempMatchObj[0])
            arrayYSize = int(tempMatchObj[1])
            numProcs = int(tempMatchObj[2]) * int(tempMatchObj[3])
            compDataSize = arrayXSize * arrayYSize * 8
            timeIter = int(tempMatchObj[4])
        if line.startswith("JacobiSG X"):
            version = "JacobiSG"
            tempMatchObj = re.search(
                    r'JacobiSG\s+X\s+(\d+)\s+Y\s+(\d+)\s+Px\s+(\d+)\s+Py\s+(\d+)\s+Iter\s+(\d+)',
                    line).groups()
            arrayXSize = int(tempMatchObj[0])
            arrayYSize = int(tempMatchObj[1])
            numProcs = int(tempMatchObj[2]) * int(tempMatchObj[3])
            timeIter = int(tempMatchObj[4])
            compDataSize = arrayXSize * arrayYSize * 8 / numProcs
        elif line.startswith("Num. Dummy MSGs"):
            tempMatchObj = re.search(r'Num\. Dummy MSGs\s+(\d+)', line).groups()
            numDummyMSGs = int(tempMatchObj[0])
        elif line.startswith("MSG Size"):
            tempMatchObj = re.search(r'MSG Size.*?\s+(\d+)', line).groups()
            MSGSize = int(tempMatchObj[0])
        elif line.startswith("ComputationTime"):
            tempMatchObj = re.search(r'ComputationTime\s+(\d+\.\d+)', line).groups()
            compTime = float(tempMatchObj[0]) / timeIter
        elif line.startswith("CommsTime"):
            tempMatchObj = re.search(r'CommsTime\s+(\d+\.\d+)', line).groups()
            commsTime = float(tempMatchObj[0]) / timeIter
        elif line.startswith("TotalTime"):
            tempMatchObj = re.search(r'TotalTime\s+(\d+\.\d+)', line).groups()
            totalTime = float(tempMatchObj[0]) / timeIter
        elif line.startswith("Extra"):
            tempMatchObj = re.search(r'Extra Iterations\s+(\d+)', line).groups()
            extraItrs = float(tempMatchObj[0])
        elif line.startswith("Socket Barrier"):
            version = "Socket Barrier Jacobi"
            tempMatchObj = re.search(
                    r'Socket Barrier Jacobi\s+X\s+(\d+)\s+Y\s+(\d+)\s+Px\s+(\d+)\s+Py\s+(\d+)\s+Iter\s+(\d+)',
                    line).groups()
            arrayXSize = int(tempMatchObj[0])
            arrayYSize = int(tempMatchObj[1])
            numProcs = int(tempMatchObj[2]) * int(tempMatchObj[3])
            timeIter = int(tempMatchObj[4])
            compDataSize = arrayXSize * arrayYSize * 8 / numProcs

        elif line.startswith("-"):
            sizeUnitJson = "KiB"
            # MSGSize = int(MSGSize * 8)
            if not sizeInBytes:
                MSGSize = int(MSGSize / 1024)
                if MSGSize >= 1024:
                    sizeUnitJson = "MiB"
                    MSGSize = int(MSGSize / 1024)
                iKey = f'{MSGSize} {sizeUnitJson}'

            else:
                iKey = MSGSize

                if MSGSize >= 1024 * 1024:
                    sizeUnitJson = "MiB"

            if sizes is None:
                list4DF.append([version, numProcs, numDummyMSGs, iKey, extraItrs, compDataSize, compTime, commsTime,
                                totalTime])
            elif iKey in sizes:
                list4DF.append([version, numProcs, numDummyMSGs, iKey, extraItrs, compDataSize, compTime, commsTime,
                                totalTime])

        else:
            pass

        try:
            line = fp.readline()
        except:
            line = fp.readline()

    fp.close()
    outDF = pd.DataFrame(list4DF, columns=['Application', 'Number of Processes', 'Number of Messages',
                                           'Size of Messages', 'Extra Iterations (Computation)',
                                           'Working Set Size (Computation)', 'Computation Time',
                                           'Communication Time', 'Total Time'])
    return outDF


def reReadOutFiles(primitiveColumns, computationalLoadType, workingSetSize, commCompBarriers, numberOfNodes,
                   processesPerNode, numberOfMessages, msgSizes, arisDataCSVFileName, outfileDirectory):
    files = []
    arisDatasetAnalysisDF = pd.DataFrame(columns=primitiveColumns)

    for iComputationalLoadType in computationalLoadType:
        for iWorkingSetSize in workingSetSize:
            for iCommCompBarriers in commCompBarriers:
                for iNumberOfNodes in numberOfNodes:
                    for iProcessesPerNode in processesPerNode:
                        for iNumberOfMessages in numberOfMessages:
                            for idxMsgSize, imsgSizes in enumerate(msgSizes):
                                iNumberOfProcesses = iNumberOfNodes * iProcessesPerNode
                                iFile = f'{iComputationalLoadType + iCommCompBarriers}_{iNumberOfNodes}n_{iNumberOfProcesses}_{iWorkingSetSize}_{iNumberOfMessages}_{imsgSizes}.csv'
                                files.append(iFile)
                                iOutDF = pd.read_csv(
                                        f"{outfileDirectory}/{iFile}").head(
                                        iNumberOfProcesses)  # Barriers
                                newRow = {
                                        'Total Time'                     : [
                                                np.mean(iOutDF['Total Time'].astype(float))],
                                        'Total Time STD'                 : [np.std(iOutDF['Total Time'].astype(float))],
                                        'Computation Time'               : [
                                                np.mean(iOutDF['Computation Time'].astype(float))],
                                        'Computation Time STD'           : [
                                                np.std(iOutDF['Computation Time'].astype(float))],
                                        'Measured Communication Time'    : [
                                                np.mean(iOutDF['Measured Communication Time'].astype(float))],
                                        'Measured Communication Time STD': [
                                                np.std(iOutDF['Measured Communication Time'].astype(float))],
                                        'Derived Communication Time'     : [
                                                np.mean(iOutDF['Derived Communication Time'].astype(float))],
                                        'Derived Communication Time STD' : [
                                                np.std(iOutDF['Derived Communication Time'].astype(float))],
                                        'Number of Nodes'                : [iNumberOfNodes],
                                        'Processes per Node'             : [iProcessesPerNode],
                                        'Total Processes'                : [iNumberOfNodes * iProcessesPerNode],
                                        'Working Set Size'               : [iWorkingSetSize],
                                        'Working Set Size (Bytes)'       : [stringSizeToNumber(iWorkingSetSize)],
                                        'Message Size'                   : [
                                                binarySize(np.mean(iOutDF['Message Size'].astype(float) * 8)).replace(
                                                        ' ',
                                                        '')],
                                        'Message Size Mul.'              : [imsgSizes],
                                        'Message Size (Bytes)'           : [
                                                np.mean(iOutDF['Message Size'].astype(float))],
                                        'Number of Messages'             : [iNumberOfMessages],
                                        'Computational Load Type'        : [iComputationalLoadType],
                                }
                                tempDF = pd.DataFrame.from_dict(newRow)

                                arisDatasetAnalysisDF = pd.concat([arisDatasetAnalysisDF, tempDF])

    return arisDatasetAnalysisDF


def readMPIExchangeFile(file):
    fp = open(file)
    line = fp.readline()
    while line:
        if '# Benchmarking Exchange' in line:
            line = fp.readline()
            tempMatchObj = re.search(r'processes\s+=\s+(\d+)', line).groups()
            numProcesses = int(tempMatchObj[0])
            line = fp.readline()
            continue


def readMPIBenchmarkFile(file: str, msgSizes=None):
    outdict = {}
    tempDict = {}
    if msgSizes is None:
        msgSizes = []
    newNumProcesses = False
    newEntry = False
    numProcesses = 0
    fp = open(file)
    line = fp.readline()
    while line:
        if '# Benchmarking Exchange' in line:
            newNumProcesses = True
            line = fp.readline()
            continue

        if newNumProcesses:
            tempMatchObj = re.search(r'processes\s+=\s+(\d+)', line).groups()
            numProcesses = int(tempMatchObj[0])
            newNumProcesses = False
            line = fp.readline()
            continue

        tempMatchObj = re.search(r'\s+(\d+)\s+\d+\s+\d+\.\d+\s+\d+\.\d+\s+(\d+\.\d+)\s+(\d+\.\d+)', line)
        if tempMatchObj is not None:
            tempMatches = tempMatchObj.groups()
            bytesSize = int(tempMatches[0])
            time = float(tempMatches[1])
            # print(bytesSize, time)
            if bytesSize in msgSizes:
                newEntry = True

        if newEntry:
            if bytesSize == msgSizes[0]:
                outdict[numProcesses] = {}
            newEntry = False
            msgSize = bytesSize / 1024
            msgSizeUnit = "KiB"
            if msgSize > 1023:
                msgSize /= 1024
                msgSizeUnit = "MiB"
            tempDict[f'{int(msgSize)} {msgSizeUnit}'] = 128 * round(time * 10 ** (-6), 6)
            if bytesSize == msgSizes[-1]:
                outdict[numProcesses].update(tempDict)

        line = fp.readline()

    fp.close()
    return outdict
