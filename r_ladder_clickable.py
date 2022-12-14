# -*- coding: utf-8 -*-
"""
Created on Tue Dec 13 12:36:09 2022

@author: tostraml
"""

from dash import Dash, dcc, html, Input, Output
import plotly.graph_objects as go
import json, urllib
from dash import callback_context
import pandas as pd
import plotly.express as px
import numpy as np

app = Dash(__name__)
server = app.server

nodes = [("Grondstof",'rgba(127, 127, 127, 0.4)'),
         ("Vooraad Markt",'rgba(188, 189, 34, 0.8)'), 
         ("In gebruik",'rgba(44, 160, 44, 0.8)'), 
         ("Buiten gebruik",'rgba(214, 39, 40, 0.8)'),
         ("Hergebruik",'rgba(140, 86, 75, 0.8)'),
         ("Refurbish<br>Repair",'rgba(31, 119, 180, 0.8)'),
         ("Recycle",'rgba(255, 127, 14, 0.8)'),
         ("Manufacture",'rgba(148, 103, 189, 0.8)'),
         ("Grondstof",'rgba(127, 127, 127, 0.4)'),
         ("Waste",'rgba(27, 27, 27, 0.8)'),
         ("Export",'rgba(150, 150, 150, 0.4)')]

sankey = True
random_ts = 0.2*np.random.randn(len(nodes),8)

def decrease_alpha(color):
    current_alpha = color.split(', ')[-1]
    current_alpha = float(current_alpha[:-1])
    new_alpha = current_alpha/2
    new_color = color.split(', ')[:-1]
    new_color.append('{:.1f})'.format(new_alpha))
    return ', '.join(new_color)




app.layout = html.Div([
    
    dcc.Graph(id="graph"),
    
    html.Div(id='slidediv', children=[
        html.P("Levensduur"),
        dcc.Slider(id='slider_ld', min=0, max=2, 
                   value=1, step=0.1),
        html.P("Prijs"),
        dcc.Slider(id='slider_prijs', min=0, max=2, 
                   value=1, step=0.1),
        ],
    style={'width':'40vw'})
])


@app.callback(
    Output("graph", "figure"), 
    Input("slider_ld", "value"),
    Input("slider_prijs", "value"),
    Input("graph", "clickData"))
def display_sankey(levensduur,prijs,clicky):
    if prijs != 1:
        prijs=2-(0.99*prijs)
    if levensduur !=1:
        levensduur=2-(0.99*levensduur)
    links = [
                ( 0,  1,  243707 ), #https://www.nationaalweeeregister.nl/assets/uploads/PDF/2022/Rapportage%202021_V20220627.pdf
                ( 1,  2,  prijs*(243707 - 96698) ), #WEEE
                ( 2,  3,  prijs*levensduur*(404+200+493+330) ),
                ( 3,  4,  prijs*levensduur*404 ), #WEEE
                ( 3,  5,  prijs*levensduur*200 ),
                ( 3,  6,  prijs*levensduur*493+330 ), #WEEE
                ( 4,  7,  prijs*levensduur*404 ), #WEEE
                ( 5,  7,  prijs*levensduur*200 ),
                ( 6,  8,  prijs*levensduur*330 ), #WEEE
                ( 6,  9,  prijs*levensduur*493 ), #WEEE
                ( 7,  2,  prijs*levensduur*404+200 ), #WEEE + zelf verzonnen 200 3->5
                ( 1,  10, prijs*96698)]  #https://www.nationaalweeeregister.nl/assets/uploads/PDF/2022/Rapportage%202021_V20220627.pdf

    
    links = [(l[0],l[1],l[2],decrease_alpha(nodes[l[1]][1])) for l in links]

    values = {0:243707}

    for node in range(1,len(nodes)):
        values[node] = sum([l[2] for l in links if l[1]==node])
    values[2] = 147009
    
    
    timeseries = [1.1,1.3,1,0.9,0.8,1.1,1.2,1]

    ctx = callback_context
    trigger_id = ctx.triggered[0]["prop_id"].split(".")
    print(trigger_id)
    
    if trigger_id[0] == 'graph':
        global sankey
        sankey= not sankey
    
    if not sankey and clicky is not None and 'points' in clicky.keys():
        print(clicky['points'][0])
        node = clicky['points'][0]['index']
        current_value = values[node]
        
        ts = [(timeseries[i]+random_ts[node,i])*current_value for i in range(len(timeseries))]
        
        years = [2014,2015,2016,2017,2018,2019,2020,2021]
        
        dff = pd.DataFrame()
        dff['Ton/pj'] = ts
        dff['Jaar']= years
        fig = px.scatter(dff, x='Jaar', y='Ton/pj')
        fig.update_traces(mode='lines+markers',line_color=clicky['points'][0]['color'], marker_color=clicky['points'][0]['color'])
        fig = go.Figure(fig)
              
    else:
        sank = go.Sankey(
        valueformat = ".0f",
        valuesuffix = " ton",
        arrangement = "fixed",
        orientation='h',
        node = {
            "label": [node[0] for node in nodes],
            "color": [node[1] for node in nodes],
            'pad':10,
            'customdata':[values[i] for i in range(len(nodes))],
            'hovertemplate':'De vooraad van %{label} is %{customdata} ton<br /><extra></extra>'},  # 10 Pixels
        link = {
            "source": [l[0] for l in links],
            "target": [l[1] for l in links],
            "value":  [l[2]/40 if l[0] in [0,1] else l[2] for l in links],
            'customdata':[l[2] for l in links],
            "color":  [l[3] for l in links],
            'hovertemplate':'Stroom van %{source.label}<br />'+
            'naar %{target.label}<br />is %{customdata} ton<br /><extra></extra>'})
        
        fig = go.Figure(sank)
        
        fig.add_annotation(
        x=0.3,
        y=0.55,
        xref="x domain",
        yref="y domain",
        text="Prijs -",
        showarrow=True,
        font=dict(
            family="Courier New, monospace",
            size=16,
            color="#ffffff"
            ),
        align="center",
        arrowhead=2,
        arrowsize=1,
        arrowwidth=2,
        arrowcolor="#636363",
        ax=0,
        ay=-50,
        bordercolor="#c7c7c7",
        borderwidth=2,
        borderpad=4,
        bgcolor="#ff7f0e",
        opacity=0.8
        )
        
        fig.add_annotation(
        x=0.3,
        y=0.25,
        xref="x domain",
        yref="y domain",
        text="Opbrengst +",
        showarrow=True,
        font=dict(
            family="Courier New, monospace",
            size=16,
            color="#ffffff"
            ),
        align="center",
        arrowhead=2,
        arrowsize=1,
        arrowwidth=2,
        arrowcolor="#636363",
        ax=0,
        ay=50,
        bordercolor="#c7c7c7",
        borderwidth=2,
        borderpad=4,
        bgcolor="#ff7f0e",
        opacity=0.8
        )
        
        fig.add_annotation(
        x=0.5,
        y=0.4,
        xref="x domain",
        yref="y domain",
        text="Levensduur -",
        showarrow=True,
        font=dict(
            family="Courier New, monospace",
            size=16,
            color="#ffffff"
            ),
        align="center",
        arrowhead=2,
        arrowsize=1,
        arrowwidth=2,
        arrowcolor="#636363",
        ax=0,
        ay=-50,
        bordercolor="#c7c7c7",
        borderwidth=2,
        borderpad=4,
        bgcolor="#ff7f0e",
        opacity=0.8
        )
        
        fig.update_layout(title_text="R-ladder Grondstoffen zonnepanelen ton/pj 2021", font_size=10)
    
    return fig
if __name__ == '__main__':
    app.run_server(debug=False)