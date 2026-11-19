#%%
#This is where we will combine the panels for the dashboard

import gradio as gr
from Panel2 import panel2fig

Panel2launch = panel2fig()

with gr.Blocks() as main:
    gr.Markdown("# Group 7 Dashboard")

Panel2launch.render()

main.launch()

# %%
