from langchain_core.prompts import PromptTemplate, ChatPromptTemplate

prompt = PromptTemplate.from_template("Hello {name}, welcome to {platform}!") 
print(prompt.format(name="Alice", platform="LangChain"))  # 输出: Hello Alice, welcome to LangChain!
print(prompt.invoke({"name": "Bob", "platform": "LangChain"}))  # 输出: Hello Bob, welcome to LangChain! 