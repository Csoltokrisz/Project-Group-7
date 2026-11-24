#%%
#This is where we will combine the panels for the dashboard
from dash import Dash, dcc, html

#from Panel1 import buildfig1
from Panel2 import buildfig2
#from Panel3 import buildfig3
#from Panel4 import buildfig4


#Test ------------------------- delete
#buildfig2().show()


app = Dash()

grid_style = {
    "display": "grid",
    "gridTemplateColumns": "1fr 1fr",
    "gap": "10px",
    "padding": "10px",
}

app.layout = html.Div([
    html.H2("Economic Dashboard about the US Cost of Living Crisis", 
            style={"paddingLeft": "20px"}),
    html.Div(style=grid_style,
             children=[
                 dcc.Graph(id="graph-1", figure=buildfig2()),
                 dcc.Graph(id="Correlation Heatmap", figure=buildfig2()),
                 dcc.Graph(id="graph-3", figure=buildfig2()),
                 dcc.Graph(id="graph-4", figure=buildfig2()),
             ],),
])

if __name__ == "__main__":
    app.run(debug=True)
