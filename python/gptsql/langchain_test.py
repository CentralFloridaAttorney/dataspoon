from langchain import PromptTemplate, LLMBashChain
from langchain.llms import OpenAI

from python.gptsql.gpttool import GptTool

llm = OpenAI(openai_api_key="OPENAI_API_KEY")
llm = OpenAI(temperature=0.9)
text = "What would be a good company name for a company that makes colorful socks?"
print(llm(text))
prompt = PromptTemplate(
    input_variables=["product"],
    template="What is a good name for a company that makes {product}?",
)
from langchain.chains import LLMChain
chain = LLMChain(llm=llm, prompt=prompt)
chain.run("colorful socks")
# -> '\n\nSocktastic!'

from langchain.utilities.bash import BashProcess


persistent_process = BashProcess(persistent=True)
bash_chain = LLMBashChain.from_llm(llm, bash_process=persistent_process, verbose=True)
dbtool = GptTool("gptsql")
# text = """DBTool("gptsql").put("asdf", "asdf", "qwer")"""
text = """python DBTool("gptsql").get("asdf", "asdf")"""
bash_chain.run(text)