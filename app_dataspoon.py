import gradio as gr

from python.dataspoon.configtool import ConfigTool
from python.dataspoon.dbtool import DBTool
DEFAULT_DATABASE = "svgobject_database"
DEFAULT_TABLE = "svgobject_table"

def load_db():
    # dbtool = DBTool(configs["dbtool_db"], configs["dbtool_table"])
    dbtool = DBTool(DEFAULT_DATABASE, DEFAULT_TABLE)
    dataframe = dbtool.get_dataframe()
    return dataframe


# configs = ["user", "passwd", "port", "host", "database_name", "onehotdb_table", "words_filename_key"]
configs = ConfigTool('default').get_configs()
config_textbox = []
with gr.Blocks() as dbtool_app:
    with gr.Tab("DBTool"):
        with gr.Row():
            bnt_load_db = gr.Button(value="Load DB")
            db_status = gr.Label("temp label")
        with gr.Row():
            keys = list(configs.keys())
            for row in range(len(keys)-1):
                this_key = keys[row]
                this_value = configs[this_key]
                this_textbox = gr.Textbox(label=this_value, value=this_value, elem_id=this_value)
                config_textbox.append(this_textbox)
        with gr.Row():
            config_frame = gr.DataFrame()
    with gr.Tab("Table"):
        with gr.Row():
            bnt_refresh_tableFrame = gr.Button(value="Refresh Table Frame")
        with gr.Row():
            table_frame = gr.DataFrame()
        bnt_refresh_tableFrame.click(fn=load_db, inputs=[], outputs=[table_frame])
dbtool_app.launch()
