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
import daq_control

# Versión que utiliza dash en 2º plano y el datalogger en 1º plano

# Archivos de almacenamiento
numero_dia = datetime.today().strftime('%j')
año = datetime.today().strftime('%Y')
DATA_FILE = f"meteo_{año}_{numero_dia}.txt"
CONFIG_FILE = "config.txt"
DEVICES_FILE = "devices.txt"

def load_device_names():
    if os.path.exists(DEVICES_FILE):
        with open(DEVICES_FILE, "r") as f:
            names = [line.strip() for line in f.readlines()]
        return names[:17] if len(names) >= 17 else names + [f"Canal_{i}" for i in range(len(names), 17)]
    else:
        return [f"Canal_{i}" for i in range(17)]

def load_multiplicadores():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            valores = f.readlines()
        return [float(v.strip()) for v in valores]
    else:
        return [1.0] * 17

def save_multiplicadores(multiplicadores):
    with open(CONFIG_FILE, "w") as f:
        for val in multiplicadores:
            f.write(f"{val}\n")

multiplicadores = load_multiplicadores()
dispositivo_nombres = load_device_names()

txt_multiplicadores = "(W/m^2)/V"
txt_multiplicadores_list = ["(ºC)/V", "(m/s)/V", "(º)/V", "(bar)/V", "(%)/V"]

txt_units = ["W/m^2"] * 12 + ["ºC", "m/s", "º", "bar", "%"]

units_multiplicadores = [txt_multiplicadores] * 12 + txt_multiplicadores_list

def read_datalogger():
    while True:
        valores = [random.uniform(0, 1) for _ in range(17)]
        valores_multiplicados = [valores[i] * multiplicadores[i] for i in range(17)]
        valores_multiplicados = [round(val, 3) for val in valores_multiplicados]
        timestamp = time.strftime("%H:%M:%S")
        
        with open(DATA_FILE, "a") as f:
            f.write(timestamp + "\t" + "\t".join(map(str, valores_multiplicados)) + "\n")
        
        time.sleep(5)

def run_dash_server():
    app = dash.Dash(__name__)

    app.layout = html.Div(style={"backgroundColor": "#f4f6f9", "fontFamily": "Arial, sans-serif","padding":"10px"}, children=[
        html.H1("Estación Meteorológica", style={
            "textAlign": "center",
            "color": "#2c3e50",
            "paddingTop": "20px",
            "marginBottom": "30px",
        }),

        html.Div([
            dcc.Graph(
                id="live-graph",
                style={
                    "height": "600px",
                    "width": "100%",
                    "borderRadius": "10px",
                    "boxShadow": "0 8px 16px rgba(0, 0, 0, 0.1)",
                    "backgroundColor": "#ffffff"
                }
            ),
        ], style={"padding": "0 40px", "marginBottom": "30px"}),

        dcc.Interval(id="interval-update", interval=2000, n_intervals=0),

        html.Div([
            html.Label("Seleccionar dispositivos a mostrar:", style={
                "fontWeight": "bold",
                "color": "#34495e",
                "fontSize": "16px",
                "marginBottom": "10px"
            }),
            dcc.Checklist(
                id="channel-selector",
                options=[{"label": dispositivo_nombres[i], "value": dispositivo_nombres[i]} for i in range(12)],
                value=[dispositivo_nombres[i] for i in range(12)],
                inline=True,
                style={
                    "display": "grid",
                    "gridTemplateColumns": "repeat(3, 1fr)",
                    "gap": "10px",
                    "padding": "10px"
                }
            ),
        ], style={
            "margin": "0 40px 30px 40px",
            "padding": "20px",
            "backgroundColor": "#ffffff",
            "borderRadius": "10px",
            "boxShadow": "0 4px 8px rgba(0,0,0,0.05)"
        }),

        html.Div([
            html.H2("Radiación", style={
                "textAlign": "center",
                "color": "#2c3e50",
                "marginBottom": "20px"
            }),
            html.Div([
                html.Div([
                    html.Label(dispositivo_nombres[i], style={"fontWeight": "bold", "color": "#2c3e50"}),
                    dcc.Input(
                        id=f"multiplicador-{i}",
                        type="number",
                        value=multiplicadores[i],
                        step=0.001,
                        style={
                            "width": "100px",
                            "marginLeft": "10px",
                            "marginRight": "10px",
                            "borderRadius": "5px",
                            "border": "1px solid #bdc3c7"
                        }
                    ),
                    html.Label(units_multiplicadores[i], style={"color": "red", "marginRight": "30px"}),
                    html.Span(id=f"ultimo-valor-{i}", style={"fontWeight": "bold", "fontSize": "15px", "color": "#2980b9"}),
                    html.Label(txt_units[i], style={"color": "#2980b9", "marginLeft": "2px", "marginRight": "10px"})
                ], style={
                    "display": "flex",
                    "alignItems": "center",
                    "padding": "10px",
                    "backgroundColor": "#fdfefe",
                    "borderRadius": "6px",
                    "boxShadow": "0 2px 4px rgba(0, 0, 0, 0.05)"
                })
                for i in range(12)
            ], style={
                "display": "grid",
                "gridTemplateColumns": "repeat(3, 1fr)",
                "gap": "15px",
                "padding": "0 40px"
            })
        ], style={"marginBottom": "40px"}),

        html.Div([
    html.H2("Meteorología", style={
        "textAlign": "center",
        "color": "#2c3e50",
        "marginBottom": "20px"
    }),
    html.Div([
        html.Div([
            html.Label(dispositivo_nombres[i], style={
                "fontWeight": "bold",
                "color": "#2c3e50"
            }),
            dcc.Input(
                id=f"multiplicador-{i}",
                type="number",
                value=multiplicadores[i],
                step=0.5,
                style={
                    "width": "80px",
                    "marginLeft": "10px",
                    "marginRight": "10px",
                    "borderRadius": "5px",
                    "border": "1px solid #bdc3c7",
                    "display": "none"
                }
            ),
            html.Span(id=f"ultimo-valor-{i}", style={
                "fontWeight": "bold",
                "fontSize": "15px",
                "color": "#2980b9",
                "marginLeft": "10px",

            }),
            html.Label(txt_units[i], style={"color": "#2980b9", "marginLeft": "2px", "marginRight": "10px"})

        ], style={
            "display": "flex",
            "alignItems": "center",
            "padding": "10px",
            "backgroundColor": "#fdfefe",
            "borderRadius": "6px",
            "boxShadow": "0 2px 4px rgba(0, 0, 0, 0.05)"
        })
        for i in range(12, 17)
    ], style={
        "display": "grid",
        "gridTemplateColumns": "repeat(3, 1fr)",
        "gap": "15px",
        "padding": "0 40px"
    })
], style={
    "margin": "0 40px 30px 40px",
    "padding": "20px",
    "backgroundColor": "#ffffff",
    "borderRadius": "10px",
    "boxShadow": "0 4px 8px rgba(0,0,0,0.05)"
}),
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

        fig.update_layout(
            margin={"l": 40, "r": 20, "t": 40, "b": 40},
            paper_bgcolor="#ffffff",
            plot_bgcolor="#ffffff",
            font=dict(color="#2c3e50"),
        )

        return fig
    @app.callback(
        [Output(f"multiplicador-{i}", "value") for i in range(17)] +
        [Output(f"ultimo-valor-{i}", "children") for i in range(17)],
        [Input(f"multiplicador-{i}", "value") for i in range(17)] +
        [Input("interval-update", "n_intervals")]
    )
    def update_multipliers(*values):
        global multiplicadores
        multiplicadores = list(values[:17])
        save_multiplicadores(list(values[:17]))
        
        if os.path.exists(DATA_FILE):
            df = pd.read_csv(DATA_FILE, sep="\t", header=None, names=["Tiempo"] + dispositivo_nombres)
            ultimo_valor = df.iloc[-1, 1:].tolist() if not df.empty else ["N/A"] * 17
        else:
            ultimo_valor = ["N/A"] * 17
        
        return multiplicadores + ultimo_valor
    
    app.run(debug=True, use_reloader=False)

dash_thread = threading.Thread(target=run_dash_server, daemon=True)
dash_thread.start()

if __name__ == "__main__":
    
    #read_datalogger()
    
    daq_control.daq_control()
