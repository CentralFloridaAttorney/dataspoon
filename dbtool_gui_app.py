import gradio as gr

from python.dataspoon.dbtool import DBTool


def put_data(database_name, table_name, unique_id, key, value):
    db_tool = DBTool(database_name, table_name)
    db_tool.put(unique_id, key, value)
    return "Data inserted successfully!"

def get_data(database_name, table_name, unique_id, key):
    db_tool = DBTool(database_name, table_name)
    value = db_tool.get(unique_id, key)
    return value

def switch_interface(interface_to_show):
    if interface_to_show == "put":
        put_interface.launch(share=True, inbrowser=True)
    elif interface_to_show == "get":
        get_interface.launch(share=True, inbrowser=True)

put_interface = gr.Interface(
    fn=put_data,
    inputs=[
        gr.inputs.Textbox(label="Database Name"),
        gr.inputs.Textbox(label="Table Name"),
        gr.inputs.Textbox(label="Unique ID"),
        gr.inputs.Textbox(label="Key"),
        gr.inputs.Textbox(label="Value")
    ],
    outputs=gr.outputs.Textbox(label="Output"),
    title="Insert Data into MySQL Database",
    description="Enter the database name, table name, unique ID, key, and value to insert data into your MySQL database."
)

get_interface = gr.Interface(
    fn=get_data,
    inputs=[
        gr.inputs.Textbox(label="Database Name"),
        gr.inputs.Textbox(label="Table Name"),
        gr.inputs.Textbox(label="Unique ID"),
        gr.inputs.Textbox(label="Key"),
    ],
    outputs=gr.outputs.Textbox(label="Output"),
    title="Retrieve Data from MySQL Database",
    description="Enter the database name, table name, unique ID, and key to retrieve data from your MySQL database."
)

switch_interface_app = gr.Interface(
    fn=switch_interface,
    inputs=gr.inputs.Radio(["put", "get"], label="Select Interface"),
    outputs=None,
    title="DBTool GUI",
    description="Choose the interface to use: put or get."
)

switch_interface_app.launch(share=False, inbrowser=True)
