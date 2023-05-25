import gradio as gr
from langchain.tools import Tool
from langchain.utilities import PythonREPL

from python.gptsql.gpttool import GptTool


def put_data(database_name, table_name, unique_id, key, value):
    gpt_tool = GptTool(database_name, table_name)
    gpt_tool.put(unique_id, key, value)
    return "Data inserted successfully!"

def get_data(database_name, table_name, unique_id, key):
    gpt_tool = GptTool(database_name, table_name)
    value = gpt_tool.get(unique_id, key)
    return value

def chat_bot(message):
    # Your chatbot logic here
    bot_response = "This is an example response to the message: " + message
    return bot_response

def test_button(message):
    python_repl = PythonREPL()
    link_key = "asdf"
    key = "key"
    value = "value"
    command = "DBTool('gptsql').get('asdf', 'key')"
    python_repl.run(command)
    repl_tool = Tool(
        name="python_repl",
        description="A Python shell. Use this to execute python commands. Input should be a valid python command. If you want to see the output of a value, you should print it out with `print(...)`.",
        func=python_repl.run
    )
    return repl_tool


with gr.Blocks() as demo:
    with gr.Tab("Chat Interface"):
        with gr.Row():
            chat_output = gr.outputs.Textbox(label="Chatbot says:")
        with gr.Row():
            chat_input = gr.inputs.Textbox(lines=2, placeholder='Type your message here...')
        with gr.Row():
            chat_btn = gr.Button(label="Send")
            chat_btn.click(chat_bot, inputs=[chat_input], outputs=[chat_output])
            chat_btn = gr.Button(label="Test")
            chat_btn.click(test_button, inputs=[chat_input], outputs=[chat_output])

    with gr.Tab("Put Data"):
        with gr.Row():
            database_name = gr.inputs.Textbox(label="Database Name")
            table_name = gr.inputs.Textbox(label="Table Name")
            unique_id = gr.inputs.Textbox(label="Unique ID")
            key = gr.inputs.Textbox(label="Key")
            value = gr.inputs.Textbox(label="Value")
        with gr.Row():
            put_output = gr.outputs.Textbox(label="Output")
        with gr.Row():
            btn = gr.Button("Put Data").style(full_width=True)
            btn.click(put_data, inputs=[database_name, table_name, unique_id, key, value], outputs=[put_output])

    with gr.Tab("Get Data"):
        with gr.Row():
            database_name = gr.inputs.Textbox(label="Database Name")
            table_name = gr.inputs.Textbox(label="Table Name")
            unique_id = gr.inputs.Textbox(label="Unique ID")
            key = gr.inputs.Textbox(label="Key")
        with gr.Row():
            get_output = gr.outputs.Textbox(label="Output")
        with gr.Row():
            btn = gr.Button("Get Data").style(full_width=True)
            btn.click(get_data, inputs=[database_name, table_name, unique_id, key], outputs=[get_output])

demo.launch()
