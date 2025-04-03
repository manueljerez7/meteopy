import threading
import time
import pandas as pd
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import os
import random
from datetime import datetime

# Archivos de almacenamiento
numero_dia = datetime.today().strftime('%j')
DATA_FILE = f"meteo_{numero_dia}.txt"
CONFIG_FILE = "config.txt"
DEVICES_FILE = "devices.txt"

# Cargar nombres de dispositivos desde un fichero
def load_device_names():
    if os.path.exists(DEVICES_FILE):
        with open(DEVICES_FILE, "r") as f:
            names = [line.strip() for line in f.readlines()]
        return names[:18] if len(names) >= 18 else names + [f"Canal_{i}" for i in range(len(names), 18)]
    else:
        return [f"Canal_{i}" for i in range(18)]

# Cargar multiplicadores desde un fichero de texto
def load_multiplicadores():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            valores = f.readlines()
        return [float(v.strip()) for v in valores]
    else:
        return [1.0] * 18

# Guardar multiplicadores en un fichero de texto
def save_multiplicadores(multiplicadores):
    with open(CONFIG_FILE, "w") as f:
        for val in multiplicadores:
            f.write(f"{val}\n")

# Variables compartidas
multiplicadores = load_multiplicadores()
dispositivo_nombres = load_device_names()

def read_datalogger():
    while True:
        valores = [random.uniform(-10, 10) for _ in range(18)]  # Simulación de datos
        # valores deberian ser los datos leidos del datalogger
        valores_multiplicados = [valores[i] * multiplicadores[i] for i in range(18)]
        timestamp = time.strftime("%H:%M:%S")
        
        with open(DATA_FILE, "a") as f:
            f.write(timestamp + "\t" + "\t".join(map(str, valores_multiplicados)) + "\n")
        
        time.sleep(5)  # Intervalo de adquisición

# Hilo de adquisición
datalogger_thread = threading.Thread(target=read_datalogger, daemon=True)
datalogger_thread.start()

# Iniciar Dash
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Estación Meteorológica", style={"textAlign": "center", "color": "#2c3e50", "fontFamily": "Arial, sans-serif"}),
    
    html.Div([
        dcc.Graph(id="live-graph", style={"height": "700px", "width": "100%", "borderRadius": "10px", "boxShadow": "0 4px 8px rgba(0, 0, 0, 0.1)"}),
    ], style={"display": "flex", "justifyContent": "center", "padding": "20px"}),
    
    dcc.Interval(id="interval-update", interval=2000, n_intervals=0),  
    
    html.Div([
        html.Label("Seleccionar dispositivos a mostrar:", style={"fontWeight": "bold", "color": "#34495e"}),
        dcc.Checklist(
            id="channel-selector",
            options=[{"label": dispositivo_nombres[i], "value": dispositivo_nombres[i]} for i in range(12)],
            value=[dispositivo_nombres[i] for i in range(12)],
            inline=True,
            style={"display": "grid", "gridTemplateColumns": "repeat(3, 1fr)", "gap": "10px", "padding": "10px"}
        ),
    ], style={"margin": "20px", "padding": "15px", "backgroundColor": "#ecf0f1", "borderRadius": "10px"}),
    
    html.Div([
        html.Div([
            html.Label(dispositivo_nombres[i], style={"fontWeight": "bold", "color": "#2c3e50", "marginRight": "10px"}),
            dcc.Input(id=f"multiplicador-{i}", type="number", value=multiplicadores[i], step=0.1, style={"width": "80px", "marginRight": "10px", "borderRadius": "5px", "border": "1px solid #bdc3c7"}),
            html.Span(id=f"ultimo-valor-{i}", style={"fontSize": "14px", "color": "#2980b9"})
        ], style={"display": "flex", "alignItems": "center", "marginBottom": "8px", "backgroundColor": "#f8f9fa", "padding": "8px", "borderRadius": "5px"})
        for i in range(18)
    ], style={"display": "grid", "gridTemplateColumns": "repeat(3, 1fr)", "gap": "10px", "padding": "20px"})
])

@app.callback(
    Output("live-graph", "figure"),
    [Input("interval-update", "n_intervals"), Input("channel-selector", "value")]
)
def update_graph(_, selected_channels):
    if not os.path.exists(DATA_FILE):
        return go.Figure()
    
    df = pd.read_csv(DATA_FILE, sep="\t", header=None, names=["Tiempo"] + dispositivo_nombres)
    
    fig = go.Figure()
    for col in selected_channels:
        fig.add_trace(go.Scatter(x=df["Tiempo"], y=df[col], mode="lines", name=col))
    
    return fig

@app.callback(
    [Output(f"multiplicador-{i}", "value") for i in range(18)] +
    [Output(f"ultimo-valor-{i}", "children") for i in range(18)],
    [Input(f"multiplicador-{i}", "value") for i in range(18)] +
    [Input("interval-update", "n_intervals")]
)

def update_multipliers(*values):
    global multiplicadores
    multiplicadores = list(values[:18])
    save_multiplicadores(multiplicadores)
    
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE, sep="\t", header=None, names=["Tiempo"] + dispositivo_nombres)
        ultimo_valor = df.iloc[-1, 1:].tolist() if not df.empty else ["N/A"] * 18
    else:
        ultimo_valor = ["N/A"] * 18
    
    return multiplicadores + ultimo_valor

if __name__ == "__main__":
    app.run(debug=True)
