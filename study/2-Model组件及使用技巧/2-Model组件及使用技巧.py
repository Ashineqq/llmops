import dotenv
from langchain_core.prompts import ChatPromptTemplate
from datetime import datetime
from langchain_deepseek import ChatDeepSeek

dotenv.load_dotenv()

#  编排prompt
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a helpful assistant.The current time is {current_time}."),
        ("user", "{query}"),
    ]
).partial(current_time=datetime.now())

# 创建 DeepSeek模型
llm = ChatDeepSeek(
    model="deepseek-v4-flash",
)

ai_message = llm.invoke(prompt.invoke({"query": "现在是几点，请讲一个程序员的冷笑话"}))
print(ai_message.content)  # 输出: 现在是几点，请讲一个程序员的冷笑话
