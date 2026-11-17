#%%
#This is where we will combine the panels for the dashboard

import gradio as gr
from Panel2 import makepanel2

makepanel2()

with gr.Blocks() as main:
    gr.Markdown("# Group 7 Dashboard")



#main.launch()

# %%
