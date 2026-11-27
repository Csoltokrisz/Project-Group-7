from dash import Dash, dcc, html
#from panel_1_revised import get_panel_map
from Panel2 import buildfig2
from panel_3_copy import get_panel_3
from Panel4_2 import get_panel_4


#Test ------------------------- delete
#buildfig2().show()


app = Dash()

grid_style = {
    "display": "grid",
    "gridTemplateColumns": "minmax(0, 1fr) minmax(0, 1fr)",
    "gap": "10px",
    "padding": "10px",
}

app.layout = html.Div([
    html.H2("Economic Dashboard about the US Cost of Living Crisis", 
            style={"paddingLeft": "20px"}),
    html.Div(style=grid_style,
             children=[
                 dcc.Graph(id="asd", figure=buildfig2(), responsive=True, style={"width": "100%", "height": "100%"}),
                 dcc.Graph(id="heatmap", figure=buildfig2(), responsive=True, style={"width": "100%", "height": "100%"}),
                 dcc.Graph(id="asdf", figure=buildfig2(), responsive=True, style={"width": "100%", "height": "100%"}),
                 get_panel_4(),
             ],),
])

if __name__ == "__main__":
    app.run(debug=True)
