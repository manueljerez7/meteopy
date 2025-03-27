import threading
import time
import pandas as pd
import pyvisa
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import os

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
    rm = pyvisa.ResourceManager()
    instrument = rm.open_resource("DATALOGGER_ADDRESS")
    
    while True:
        valores = [float(instrument.query(f"MEAS:CHAN{i}?")) for i in range(18)]
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
    dcc.Graph(id="live-graph"),
    dcc.Interval(id="interval-update", interval=5000, n_intervals=0),  # Actualización cada 5 segundos
    
    html.Div([
        html.Label(f"Multiplicador Canal {i}"),
        dcc.Input(id=f"multiplicador-{i}", type="number", value=multiplicadores[i], step=0.1)
    ]) for i in range(18)
])

@app.callback(
    Output("live-graph", "figure"),
    [Input("interval-update", "n_intervals")]
)
def update_graph(_):
    if not os.path.exists(DATA_FILE):
        return go.Figure()
    
    df = pd.read_csv(DATA_FILE, sep="\t", header=None, names=["Tiempo"] + [f"Canal_{i}" for i in range(18)])
    df = df.tail(100)  # Últimos 100 registros
    
    fig = go.Figure()
    for col in df.columns[1:]:
        fig.add_trace(go.Scatter(x=df["Tiempo"], y=df[col], mode="lines", name=col))
    
    return fig

@app.callback(
    [Output(f"multiplicador-{i}", "value") for i in range(18)],
    [Input(f"multiplicador-{i}", "value") for i in range(18)]
)
def update_multipliers(*values):
    global multiplicadores
    multiplicadores = list(values)
    save_multiplicadores(multiplicadores)
    return values

if __name__ == "__main__":
    app.run_server(debug=True)
