#%%
#This is where we will combine the panels for the dashboard

import gradio as gr
from Panel2 import panel2fig
from Panel4 import panel4fig

Panel2launch = panel2fig()

with gr.Blocks() as main:
    gr.Markdown("# Group 7 Dashboard")
    gr.Plot(value=panel4fig(), label="RPP Change by Presidential Vote Winner")

Panel2launch.render()

main.launch()

# %%
