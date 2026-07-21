from langchain_core.output_parsers import JsonOutputParser
from langchain_core.utils.pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_deepseek import ChatDeepSeek
import dotenv

dotenv.load_dotenv()

llm = ChatDeepSeek(
    model="deepseek-v4-flash",
)


class JokeModel(BaseModel):
    """定义一个笑话模型"""

    joke: str = Field(description="一个程序员的冷笑话")
    punchline: str = Field(description="冷笑话的点")


parser = JsonOutputParser(pydantic_object=JokeModel)

prompt_template = ChatPromptTemplate.from_template(
    "请根据用户的提问进行回答。\n {formate_instructions}\n 用户提问：{query}"
).partial(formate_instructions=parser.get_format_instructions())

prompt = prompt_template.invoke({"query": "请讲一个程序员的冷笑话"}).to_messages()
llm_response = llm.invoke(prompt)
parsed_output = parser.parse(llm_response.content)
print(parsed_output['joke'])  # 输出: 一个程序员的冷笑话