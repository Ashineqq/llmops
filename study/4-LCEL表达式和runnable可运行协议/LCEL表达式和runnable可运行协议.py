import dotenv
from langchain_core.prompts import PromptTemplate
from langchain_deepseek import ChatDeepSeek
from langchain_core.output_parsers import StrOutputParser

dotenv.load_dotenv()

prompt_template = PromptTemplate.from_template("{query}") 
llm = ChatDeepSeek(model="deepseek-v4-flash")
parse = StrOutputParser()

chain = prompt_template | llm | parse

print(chain.invoke({"query": "请讲一个程序员的冷笑话"}))
