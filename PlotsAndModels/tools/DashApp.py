import re
import time

import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output
from plotly.subplots import make_subplots

mediaFolder = "./tests/"

def create_table(df):
    columns, values = df.columns, df.values
    header = [html.Tr([html.Th(col) for col in columns])]
    rows = [html.Tr([html.Td(cell) for cell in row]) for row in values]
    table = [html.Thead(header), html.Tbody(rows)]
    return table


def createDashApp(arisDatasetAnalysisDF, features, times, processesPerNode, msgSizes,
                  numberOfMessages, workingSetSize, numberOfNodes, ):
    app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

    app.layout = dmc.MantineProvider(
            id="app-theme",
            theme={
                    "colorScheme": "light",
            },
            inherit=True,
            withGlobalStyles=True,
            withNormalizeCSS=True,
            children=dmc.Tabs([
                    dmc.TabsList(
                            [
                                    dmc.Tab("Time vs Working Set", value="commVsWorkingSet"),
                                    dmc.Tab("Measurements Comparison", value="measurementsComparison"),
                            ]
                    ),
                    dmc.TabsPanel(value="commVsWorkingSet", children=[

                            dmc.Table(
                                    verticalSpacing="sm",
                                    horizontalSpacing=10,
                                    children=[
                                            html.Tr([
                                                    html.Td([
                                                            dmc.Select(
                                                                    id='colorModeCommVsWorkingSet',
                                                                    value='Processes per Node',
                                                                    data=features,
                                                                    style={'text-align': 'left',
                                                                           },
                                                                    clearable=False
                                                            ),
                                                    ], style={"padding-top": "10px", "padding-left": "10px"}),
                                                    html.Td([
                                                            dmc.Select(
                                                                    id='displayedValueCommVsWorkingSet',
                                                                    value=times[0],
                                                                    data=times,
                                                                    style={'text-align': 'left',
                                                                           },
                                                                    clearable=False
                                                            ), ],
                                                            style={"padding-top": "10px", "padding-left": "10px"}),
                                                    html.Td([
                                                            dmc.Checkbox(id="checkboxCommVsWorkingSet",
                                                                         label="Average Lines per Feature Value",
                                                                         mb=10)
                                                            ,
                                                    ], style={"padding-top": "10px", "padding-left": "10px"})
                                            ]),
                                            html.Tr([
                                                    html.Td([dcc.Graph(id="graphCommVsWorkingSet")], colSpan=5,
                                                            style={"padding-left": "10px", "padding-top": "20px"}),
                                            ]),

                                    ])
                    ]),
                    dmc.TabsPanel(value="measurementsComparison", children=[
                            dmc.Table(
                                    verticalSpacing="sm",
                                    horizontalSpacing=10,
                                    children=[
                                            html.Tr([
                                                    html.Td([dcc.Graph(id="graphMeasurementsComparison")],
                                                            rowSpan=6,
                                                            style={"padding": "10px"}),
                                            ]),
                                            html.Tr([
                                                    html.Td([
                                                            html.P('Colored Feature:'),
                                                            dmc.Select(
                                                                    id='colorMeasurementsComparison',
                                                                    value='Processes per Node',
                                                                    data=features,
                                                                    style={'text-align'   : 'left',
                                                                           'padding-right': '10px'},
                                                                    clearable=False
                                                            )
                                                    ], style={"width": "450px", "padding-right": "20px"}),
                                            ]),

                                            html.Tr([
                                                    html.Td([
                                                            html.P('X Time'),
                                                            dmc.Select(
                                                                    id='xTimeMeasurementsComparison',
                                                                    value='Tuned Gradient Boosting Model Communication Time',
                                                                    data=times + ['RF Model Communication Time',
                                                                                  'Gradient Boosting Model Communication Time',
                                                                                  'Tuned Gradient Boosting Model Communication Time'],
                                                                    style={'text-align'   : 'left',
                                                                           'padding-right': '10px'},
                                                                    clearable=False
                                                            )
                                                    ], style={"width": "450px", "padding-right": "20px"}),
                                            ]),
                                            html.Tr([
                                                    html.Td([
                                                            html.P('Y Time'),
                                                            dmc.Select(
                                                                    id='yTimeMeasurementsComparison',
                                                                    value=times[2],
                                                                    data=times + ['RF Model Communication Time',
                                                                                  'Gradient Boosting Model Communication Time',
                                                                                  'Tuned Gradient Boosting Model Communication Time'],
                                                                    style={'text-align'   : 'left',
                                                                           'padding-right': '10px'},
                                                                    clearable=False
                                                            )
                                                    ], style={"width": "450px", "padding-right": "20px"}),
                                            ]),
                                    ])
                    ]),

            ], placement='right', value="commVsWorkingSet", orientation='vertical', variant='outline')
    )

    @app.callback(
            Output("graphCommVsWorkingSet", "figure"),
            Input("checkboxCommVsWorkingSet", "checked"),
            Input("colorModeCommVsWorkingSet", "value"),
            Input("displayedValueCommVsWorkingSet", "value"),
    )
    def generateTimeVsWorkingSetChart(checkboxCommVsWorkingSet, colorModeCommVsWorkingSet,
                                      displayedValueCommVsWorkingSet):
        plottedDataDf = arisDatasetAnalysisDF.copy(deep=True)
        # [arisDatasetAnalysisDF['Barrier'] != 'SocketBarrier'].copy(deep=True)

        categoryOrders = {
                'Working Set Size':
                    list(plottedDataDf.sort_values(by='Working Set Size (Bytes)')['Working Set Size'].unique()),
                'Message Size'    :
                    list(plottedDataDf.sort_values(by='Message Size (Bytes)')['Message Size'].unique()),
        }

        if colorModeCommVsWorkingSet != 'Working Set Size' and colorModeCommVsWorkingSet != 'Message Size':

            if type(plottedDataDf[colorModeCommVsWorkingSet].loc[0]) is str:
                if plottedDataDf[colorModeCommVsWorkingSet].loc[0].isnumeric():
                    plottedDataDf[colorModeCommVsWorkingSet] = plottedDataDf[colorModeCommVsWorkingSet].astype(int)

            categoryOrders[colorModeCommVsWorkingSet] = (
                    list(plottedDataDf.sort_values(by=colorModeCommVsWorkingSet)[colorModeCommVsWorkingSet].astype(
                            str).unique()))

        plottedDataDf.sort_values(by=colorModeCommVsWorkingSet, inplace=True)

        plottedDataDf[colorModeCommVsWorkingSet] = plottedDataDf[colorModeCommVsWorkingSet].astype(str)

        if checkboxCommVsWorkingSet:
            plotType = px.line

            for iWorkSize in plottedDataDf['Working Set Size'].unique():
                for iValue in plottedDataDf[colorModeCommVsWorkingSet].unique():
                    iCond = (plottedDataDf[colorModeCommVsWorkingSet] == iValue) & (
                            plottedDataDf['Working Set Size'] == iWorkSize)

                    iMean = plottedDataDf.loc[iCond, displayedValueCommVsWorkingSet].mean(axis=0)
                    plottedDataDf.loc[iCond, displayedValueCommVsWorkingSet] = iMean
            plottedDataDf.drop_duplicates(displayedValueCommVsWorkingSet, keep='first', inplace=True)
            plottedDataDf.sort_values(by='Working Set Size (Bytes)', inplace=True)

        else:
            plotType = px.scatter

        figCompVsComm = plotType(plottedDataDf, x=plottedDataDf['Working Set Size (Bytes)'],
                                 y=plottedDataDf[displayedValueCommVsWorkingSet],
                                 color=plottedDataDf[colorModeCommVsWorkingSet],
                                 symbol=plottedDataDf[colorModeCommVsWorkingSet], log_x=True,
                                 template="ggplot2", color_discrete_sequence=px.colors.qualitative.Bold,
                                 hover_data=features + times,
                                 category_orders=categoryOrders,
                                 )

        figCompVsComm.update_traces(
                marker=dict(size=5, symbol="diamond"),
        )
        sizeTicks = []
        for iSize in plottedDataDf.sort_values(by='Working Set Size (Bytes)')['Working Set Size'].unique():
            sizeTicks.append(iSize)

        figCompVsComm.update_layout(
                font_family="CMU Serif",
                font=dict(size=16),
                xaxis=dict(

                        tickmode='array',
                        tickangle=270,
                        tickvals=np.sort(plottedDataDf['Working Set Size (Bytes)'].unique()),
                        ticktext=sizeTicks,
                )
        )

        figCompVsComm.update_layout(
                uirevision=True,
                autosize=False,
                width=1490,
                height=800,
                yaxis_title=displayedValueCommVsWorkingSet,
                legend=dict(traceorder='normal',
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="left",
                            x=0)
                , legend_title=colorModeCommVsWorkingSet

        )

        if colorModeCommVsWorkingSet not in features:
            figCompVsComm.update_layout(
                    uirevision=True,
                    coloraxis={"colorscale": 'Agsunset'},
            )

        return figCompVsComm

    @app.callback(
            Output("graphMeasurementsComparison", "figure"),
            Input("colorMeasurementsComparison", "value"),
            Input("xTimeMeasurementsComparison", "value"),
            Input("yTimeMeasurementsComparison", "value"),
    )
    def generateMeasurementsComparisonChart(colorMeasurementsComparison, xTimeMeasurementsComparison,
                                            yTimeMeasurementsComparison):
        plottedDataDf = arisDatasetAnalysisDF.copy(deep=True)

        categoryOrders = {
                'Working Set Size':
                    list(plottedDataDf.sort_values(by='Working Set Size (Bytes)')['Working Set Size'].unique()),
                'Message Size'    :
                    list(plottedDataDf.sort_values(by='Message Size (Bytes)')['Message Size'].unique()),
        }

        if colorMeasurementsComparison != 'Working Set Size' and colorMeasurementsComparison != 'Message Size':
            categoryOrders[colorMeasurementsComparison] = (
                    list(plottedDataDf.sort_values(by=colorMeasurementsComparison)[
                             colorMeasurementsComparison].unique()))

        plottedDataDf.sort_values(by=colorMeasurementsComparison, inplace=True)
        plottedDataDf[colorMeasurementsComparison] = plottedDataDf[colorMeasurementsComparison].astype(str)

        p1 = max(max(plottedDataDf[xTimeMeasurementsComparison]),
                 max(plottedDataDf[yTimeMeasurementsComparison]))
        p2 = min(min(plottedDataDf[xTimeMeasurementsComparison]),
                 min(plottedDataDf[yTimeMeasurementsComparison]))

        fig2 = px.line(x=[p2, p1], y=[p2, p1])
        fig2.update_traces(line_color='#b8cff5', line_width=2)

        fig1 = px.scatter(plottedDataDf, x=plottedDataDf[xTimeMeasurementsComparison],
                          y=plottedDataDf[yTimeMeasurementsComparison],
                          color=plottedDataDf[colorMeasurementsComparison],
                          color_discrete_sequence=px.colors.qualitative.Vivid, hover_data=features,
                          category_orders=categoryOrders)

        figMeasurementsComparison = go.Figure(data=fig2.data + fig1.data)
        figMeasurementsComparison.update_layout(
                uirevision=True,
                autosize=False,
                width=1100,
                height=940,
                xaxis_title=xTimeMeasurementsComparison,
                yaxis_title=yTimeMeasurementsComparison, template="ggplot2",
                coloraxis={"colorscale": [(0, "blue"), (0.5, "purple"), (1, "red")]},
                font_family="CMU Serif",
                font=dict(size=16),
        )

        figMeasurementsComparison.update_layout(
                legend=dict(traceorder='normal',
                            title_text='Processes per Node',
                            font_size=14,
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="left",
                            x=0)
        )

        # figMeasurementsComparison.write_image(mediaFolder + f"bigMessagesModel_coloredPpN.pdf")
        # time.sleep(4)
        # figMeasurementsComparison.write_image(mediaFolder + f"bigMessagesModel_coloredPpN.pdf")
        return figMeasurementsComparison

    def generateCommLinesChart():
        subplot_titles = []
        reversedPpN = list(reversed(processesPerNode))

        for mulIdx, imsgSizes in enumerate(msgSizes):
            subplot_titles.append(f'Message Size = {imsgSizes} *  Working Set Size')

        fig = make_subplots(rows=len(msgSizes), cols=1,
                            subplot_titles=subplot_titles,
                            shared_xaxes=True, shared_yaxes=True,
                            vertical_spacing=0.06)
        x = [2, 8, 32, 128, 256, 512]
        for mulIdx, imsgSizes in enumerate(msgSizes):
            for numMsgIdx, iNumberOfMessages in enumerate(numberOfMessages):
                y = []
                yLower = []
                yUpper = []
                for idx, iWsSize in enumerate(workingSetSize):
                    iCond = (
                            (arisDatasetAnalysisDF['Working Set Size'] == iWsSize) &
                            (arisDatasetAnalysisDF['Message Size Mul.'] == imsgSizes) &
                            (arisDatasetAnalysisDF['Number of Messages'] == iNumberOfMessages)
                    )

                    iMean = np.mean(arisDatasetAnalysisDF.loc[iCond, ['Communication Time']].values[0][0])
                    iSTD = np.std(arisDatasetAnalysisDF.loc[iCond, ['Communication Time']].values[0][0])

                    y.append(iMean)
                    if iMean - iSTD >= 0:
                        yLower.append(iMean - iSTD)
                    else:
                        yLower.append(0)
                    yUpper.append(iMean + iSTD)
                if mulIdx == 0:
                    fig.add_trace(
                            go.Scatter(
                                    x=x,
                                    y=y,
                                    line=dict(color=px.colors.qualitative.Dark2[numMsgIdx]),
                                    name=f'{iNumberOfMessages} Messages',
                                    mode='lines+markers',
                            ), row=mulIdx + 1, col=1
                    )
                else:
                    fig.add_trace(
                            go.Scatter(
                                    x=x,
                                    y=y,
                                    line=dict(color=px.colors.qualitative.Dark2[numMsgIdx]),
                                    name=f'{iNumberOfMessages} Messages',
                                    mode='lines+markers',
                                    showlegend=False
                            ), row=mulIdx + 1, col=1
                    )
                fig.update_xaxes(
                        tickmode='array',
                        tickvals=x, row=numMsgIdx + 1, col=1
                )
                fillColor = px.colors.qualitative.Dark2[numMsgIdx].replace('rgb', 'rgba')
                fillColor = re.sub('[)]', ', 0.2)', fillColor)

                fig.add_trace(go.Scatter(
                        x=x,
                        y=yUpper,
                        mode='lines',
                        marker=dict(color=fillColor),
                        line=dict(width=0),
                        showlegend=False
                ), row=mulIdx + 1, col=1
                )
                fig.add_trace(go.Scatter(
                        x=x,
                        y=yLower,
                        marker=dict(color=fillColor),
                        line=dict(width=0),
                        mode='lines',
                        fillcolor=fillColor,
                        fill='tonexty',
                        showlegend=False
                ), row=mulIdx + 1, col=1
                )

            fig.update_layout(
                    uirevision=True,
                    autosize=False,
                    width=1000,
                    height=1500, template="ggplot2",
                    title={
                            'text'   : f"64 Nodes, 20 PpN",
                            'y'      : 0.99,
                            'x'      : 0.5,
                            'xanchor': 'center',
                            'yanchor': 'top'
                    }
                    # title={'text': r'$\text{4 Nodes,  20 Processors per Node, 8 Messages,  }\sqrt{\text{Working Set Size }}\text{ Message Size}$', },
            )
            if imsgSizes < 50:
                fig.update_yaxes(tickmode="array", tickvals=np.arange(0, 2.5, 0.5), range=[0, 2.1], row=mulIdx + 1,
                                 col=1)

            fig.update_yaxes(title_text="Communication Time (seconds)", row=3, col=1)
            fig.update_xaxes(title_text="Working Set Size per Process", row=len(msgSizes), col=1)
            fig.update_layout(
                    legend=dict(traceorder='normal',
                                orientation="h",
                                yanchor="bottom",
                                y=1.02,
                                xanchor="left",
                                x=0.26,
                                )
                    ,
                    xaxis=dict(
                            tickmode='array',
                            tickvals=x,
                            ticktext=workingSetSize,
                    )
            )
            fig.update_layout(
                    font_family="CMU Serif",
                    font=dict(size=16),
                    uirevision=True,
                    autosize=False,
            )

            for mulIdx, imsgSizes in enumerate(msgSizes):
                fig.update_xaxes(type="log", dtick=0.30102999566, row=mulIdx + 1, col=1)

            fig.update_xaxes(
                    tickmode='array',
                    tickvals=x,
                    ticktext=workingSetSize,
                    row=len(msgSizes), col=1
            )
            fig.write_image(mediaFolder + f"64_20_VarComm_Plot.pdf")
            time.sleep(4)
            fig.write_image(mediaFolder + f"64_20_VarComm_Plot.pdf")

        return fig

    def generateBoxPlotCharts():
        subplot_titles = []
        reversedPpN = list(reversed(processesPerNode))
        for numNodesIdx, iNumNodes in enumerate(numberOfNodes):
            subplot_titles.append(f'{iNumNodes} Nodes')
        fig = make_subplots(rows=2, cols=1,
                            subplot_titles=subplot_titles,
                            shared_xaxes=True, shared_yaxes=True,
                            vertical_spacing=0.1)
        for numNodesIdx, iNumNodes in enumerate(numberOfNodes):
            for idx, iWsSize in enumerate(workingSetSize):
                iCond = (
                        (arisDatasetAnalysisDF['Working Set Size'] == iWsSize) &
                        (arisDatasetAnalysisDF['Number of Nodes'] == iNumNodes)
                )
                toPlot = arisDatasetAnalysisDF.loc[iCond, ['Communication Time']].values[0][0]

                fig.add_trace(go.Box(
                        y=toPlot, marker_size=3, line_width=1.5, whiskerwidth=1,
                        name=iWsSize,
                        boxpoints='all',  # represent all points
                        boxmean='sd',  # represent mean and standard deviation
                        marker_color=px.colors.qualitative.Vivid[7], showlegend=False
                ), row=numNodesIdx + 1, col=1, )
            fig.update_yaxes(tickmode="array", tickvals=np.arange(0, 3, 0.5), range=[0, 2.5], row=numNodesIdx + 1,
                             col=1)

            # fig.add_trace(go.Scatter(
            #         x=[1],
            #         y=[2],
            #         mode="markers+text",
            #         name="Markers and Text",
            #         text=[f'Message Size = {iMul} * \nWorking Set Size, {iNumberOfMessages} Messages'],
            #         textposition="bottom center"
            # ), col=msgIdx + 1, row=mulIdx + 1)

        fig.update_layout(
                uirevision=True,
                autosize=False,
                width=1000,
                height=500, template="ggplot2",
                title_text=f"20 PpN",
                # title={'text': r'$\text{4 Nodes,  20 Processors per Node, 8 Messages,  }\sqrt{\text{Working Set Size }}\text{ Message Size}$', },
        )
        fig.update_yaxes(title_text="Communication Time (seconds)", row=2, col=1)
        fig.update_xaxes(title_text="Working Set Size per Process", row=2, col=1)
        fig.update_layout(
                font_family="CMU Serif",
                font=dict(size=19),
                uirevision=True,
                autosize=False,
        )
        fig.write_image(mediaFolder + f"64and4Nodes_BoxPlot.pdf")
        time.sleep(4)
        fig.write_image(mediaFolder + f"64and4Nodes_BoxPlot.pdf")

        return fig

    def generatePpNBoxChart():
        subplot_titles = []
        x = [2, 8, 32, 128, 256, 512]
        for ppnIdx, iPpN in enumerate(processesPerNode):
            subplot_titles.append(f'{iPpN} PpN, {numberOfNodes[ppnIdx]} Nodes')

        fig = make_subplots(rows=len(processesPerNode), cols=1,
                            subplot_titles=subplot_titles,
                            shared_xaxes=True,
                            vertical_spacing=0.06)

        for ppnIdx, iPpN in enumerate(processesPerNode):
            for numMsgIdx, iNumberOfMessages in enumerate(numberOfMessages):
                y = []
                yLower = []
                yUpper = []
                for idx, iWsSize in enumerate(workingSetSize):
                    iCond = (
                            (arisDatasetAnalysisDF['Working Set Size'] == iWsSize) &
                            (arisDatasetAnalysisDF['Processes per Node'] == iPpN) &
                            (arisDatasetAnalysisDF['Total Processes'] == iPpN * numberOfNodes[ppnIdx]) &
                            (arisDatasetAnalysisDF['Number of Messages'] == iNumberOfMessages)
                    )
                    toPlot = arisDatasetAnalysisDF.loc[iCond, ['Communication Time']].values[0][0]

                    fig.add_trace(
                            # go.Scatter(
                            #         x=x,
                            #         y=y,
                            #         line=dict(color=px.colors.qualitative.Vivid[ppnIdx]),
                            #         name=f'{iPpN} PpN',
                            #         mode='lines+markers'
                            # )
                            go.Box(
                                    y=toPlot, marker_size=3, line_width=1.5, whiskerwidth=1,
                                    name=iWsSize,
                                    boxpoints='all',  # represent all points
                                    boxmean='sd',  # represent mean and standard deviation
                                    marker_color=px.colors.qualitative.Vivid[7], showlegend=False
                            )
                            , row=ppnIdx + 1, col=1
                    )
                fig.update_xaxes(
                        tickmode='array',
                        tickvals=x, row=1, col=1
                )
            if iPpN < 16:
                fig.update_yaxes(tickmode="array", tickvals=np.arange(0, 0.25, 0.05), range=[0, 0.2], row=ppnIdx + 1,
                                 col=1)
        fig.update_layout(
                legend=dict(traceorder='normal',
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="left",
                            x=0.27)
                ,
                xaxis=dict(
                        tickmode='array',
                        tickvals=x,
                        ticktext=workingSetSize,
                )
        )
        fig.update_layout(
                uirevision=True,
                autosize=False,
                width=1000,
                height=len(processesPerNode) * 250, template="ggplot2",
                title_text=f"128 Total processes",
                title={
                        'y'      : 0.99,
                        'x'      : 0.5,
                        'xanchor': 'center',
                        'yanchor': 'top'
                }
                # title={'text': r'$\text{4 Nodes,  20 Processors per Node, 8 Messages,  }\sqrt{\text{Working Set Size }}\text{ Message Size}$', },
        )
        # for ppnIdx, iPpN in enumerate(processesPerNode):
        #     fig.update_xaxes(type="log", dtick=0.30102999566, row=ppnIdx + 1, col=1)
        fig.update_yaxes(title_text="Communication Time (seconds)", row=1, col=1)
        fig.update_xaxes(title_text="Working Set Size per Process", row=len(processesPerNode), col=1)

        fig.update_layout(
                font_family="CMU Serif",
                font=dict(size=16),
                uirevision=True,
                autosize=False,
        )
        fig.write_image(mediaFolder + f"smallMessages128ProcsBox.pdf")
        time.sleep(4)
        fig.write_image(mediaFolder + f"smallMessages128ProcsBox.pdf")
        return fig

    return app
