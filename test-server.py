import threading
import time
import pandas as pd
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import os
import random

#Lee y dibuja los 18 canales. 
#En realidad, solo primeros 12 canales son radiación, los otros 6 son otras magnitudes.


# Archivos de almacenamiento
DATA_FILE = "datos.txt"
CONFIG_FILE = "multiplicadores.txt"

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

def read_datalogger():
    while True:
        valores = [random.uniform(-10, 10) for _ in range(18)]  # Simulación de datos
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
    html.H1("Monitor de Datalogger", style={"textAlign": "center", "color": "#333"}),
    
    html.Div([
        dcc.Graph(id="live-graph", style={"height": "400px", "width": "100%", "backgroundColor": "#f8f9fa", "padding": "10px", "borderRadius": "10px"}),
    ], style={"display": "flex", "justifyContent": "center"}),
    
    dcc.Interval(id="interval-update", interval=5000, n_intervals=0),  # Actualización cada 5 segundos
    
    html.Div([
        html.Label("Seleccionar canales a mostrar:"),
        dcc.Checklist(
            id="channel-selector",
            options=[{"label": f"Canal {i}", "value": f"Canal_{i}"} for i in range(18)],
            value=[f"Canal_{i}" for i in range(18)],  # Mostrar todos por defecto
            inline=True,
            style={"marginBottom": "20px", "display": "grid", "gridTemplateColumns": "repeat(3, 1fr)", "gap": "10px"}
        ),
    ], style={"margin": "20px"}),
    
    html.Div([
        html.Div([
            html.Label(f"Canal {i}", style={"fontWeight": "bold", "width": "100px"}),
            dcc.Input(id=f"multiplicador-{i}", type="number", value=multiplicadores[i], step=0.1, style={"width": "80px", "marginRight": "10px"}),
            html.Span(id=f"ultimo-valor-{i}", style={"fontSize": "16px", "color": "blue", "flexGrow": "1"})
        ], style={"display": "flex", "alignItems": "center", "marginBottom": "5px", "backgroundColor": "#eef", "padding": "5px", "borderRadius": "5px"})
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
    
    df = pd.read_csv(DATA_FILE, sep="\t", header=None, names=["Tiempo"] + [f"Canal_{i}" for i in range(18)])
    
    fig = go.Figure()
    for col in selected_channels:
        fig.add_trace(go.Scatter(x=df["Tiempo"], y=df[col], mode="lines", name=col))
    
    fig.update_layout(
        plot_bgcolor="#f8f9fa", 
        paper_bgcolor="#ffffff",
        margin=dict(l=20, r=20, t=20, b=20),
        font=dict(color="#333")
    )
    
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
    
    # Leer el último valor de cada canal
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE, sep="\t", header=None, names=["Tiempo"] + [f"Canal_{i}" for i in range(18)])
        ultimo_valor = df.iloc[-1, 1:].tolist() if not df.empty else ["N/A"] * 18
    else:
        ultimo_valor = ["N/A"] * 18
    
    return multiplicadores + ultimo_valor

if __name__ == "__main__":
    app.run(debug=True)