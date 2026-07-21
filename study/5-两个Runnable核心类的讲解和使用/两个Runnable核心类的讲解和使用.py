import dotenv
from langchain_core.prompts import PromptTemplate
from langchain_deepseek import ChatDeepSeek
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableParallel

dotenv.load_dotenv()

# RunnableParallel：从上游拿到数据，并行执行多个表达式，封装成字典传递给下游
# RunnablePassthrouth：从上游拿到数据，直接传递给下游（RunnablePassthrough.assign可以在字典中新增键）


def retrival(query: str) -> str:
    print(f"执行了retrival方法 {query}")
    return "我是lws"


prompt_template = PromptTemplate.from_template("""请根据下面提供的上下文，来回答用户的问题
                                               <context>{context}</context>
                                               用户的提问是：{query}""")
llm = ChatDeepSeek(model="deepseek-v4-flash")
parser = StrOutputParser()

chain = (
    RunnableParallel(
        context=lambda x: retrival(x["query"]),
        query=lambda x: x["query"],
    )
    | prompt_template
    | llm
    | parser
)

print(chain.invoke({"query": "我叫什么名字"}))
