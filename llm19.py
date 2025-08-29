# github mcp собран по MR - https://github.com/github/github-mcp-server/pull/888
# GITHUB_PERSONAL_ACCESS_TOKEN="token"  ./github-mcp-server http --port 8081


from mcp import ClientSession
from mcp.client.sse import sse_client
import asyncio
import ollama
import json
import re
import os
from dotenv import load_dotenv
import httpx
import requests
import json

class BasicActionLLM:
    def __init__(self):
        self.model = ""
        self.conversation_history = []
        self.system_prompt = ""
        self.finish_prompt = ""
        self.think_delete = False

    def add_to_context(self, role: str, content: str):
        self.conversation_history.append({"role": role, "content": content})

    def clear_context(self):
        self.conversation_history = []

    def get_llm_response(self, prompt: str, role='user', tools=True):
        if tools:
            tools = [GeneralInformation.mcp_think]
        else:
            tools = []
        final_response = False
        self.add_to_context(role, prompt)
        try:
            client = ollama.Client(host=os.getenv('HOST_PORT_OLLAMA'))
            response = client.chat(
                model=self.model,
                messages=self.conversation_history,
                stream=False,
                tools=tools,
                
            )
            llm_response = response["message"]["content"].strip()
            self.add_to_context("assistant", llm_response)
            available_functions = {
                'mcp_think': GeneralInformation.mcp_think,
            }
            for tool in response.message.tool_calls or []:
                function_to_call = available_functions.get(tool.function.name)
                if function_to_call:
                    bra =  function_to_call(**tool.function.arguments)
                    print(bra) 
                    # self.clear_context()
                    
                    # self.add_to_context('system', f'Список веток: "{bra}" , представлены ветки репозитория {tool.function.arguments.get('repo')} пользователя GitHub {tool.function.arguments.get('owner')}. размышляй и отвечай только на Русском языке')
                    # final_response, llm_response = self.get_llm_response('необходимо посчитать количество веток в представленном списке, вернуть список веток и общие их количество. В ответе нужно обязательно указать репозиторий и автора, список  веток нужно оформить в список')
                else:
                    print('Function not found:', tool.function.name)
            return final_response, llm_response
        except Exception as e:
            print(f"Ошибка при обращении к LLM: {str(e)}")
            return final_response, ""

    def clean_response(self, llm_response: str):
        return re.sub(r"<think>.*?</think>", "", llm_response, flags=re.DOTALL).strip()

class GeneralInformation(BasicActionLLM):
    def __init__(self):
        self.model = os.getenv('OLLAMA_MODEL')
        self.conversation_history = []
        self.system_prompt = """
            размышляй и пиши только на Русском языке
            Ты система для работы с Github.
            Нужно запросить список веток в репозитории llm1 пользователя danilvoe
        """
        self.sending_prompt = ""
        self.think_delete = True
        
    
    def get_gamedev_tz_info(self):
        self.add_to_context("system", self.system_prompt)
        final_response, response = self.get_llm_response('устрой мозговой штурм на тему 1+1')
        # final_response, response = self.get_llm_response('нужно решить задачу трех тел. Нужно устроить мозговой штурм')
        print(f"Бот: {response}")
        # user_input = input("\nВы: ").strip()
        # final, response = self.get_llm_response(user_input)
        # print(response)
        

    @staticmethod
    def mcp_think(think:str):
        """
        Используйте инструмент, чтобы подумать о чем -то. Он не получит новую информацию и не внесет никаких изменений в хранилище, а просто войдите в систему мысли. 
        Используйте его, когда необходимы сложные рассуждения или мозговой штурм.

        Args:
            thought: Ваши мысли

        Returns:
            str: результат
        """
        return asyncio.run( GeneralInformation._mcp_list_branches(think))
        
    @staticmethod
    async def _mcp_list_branches(think:str):
        headers = {
            "KEY": os.getenv('MCP_KEY',''), 
            }

        async with sse_client(url=os.getenv('HOST_PORT_MCP',''),headers=headers) as streams:
            async with ClientSession(*streams) as session:
                await session.initialize()

                tools_response = await session.list_tools()
                available_tools = tools_response.tools
                print(available_tools)

                result = await session.call_tool(
                    name="Think",
                    arguments={"thought": think}
                )
                print(result.content)
        
def main():
    if os.path.exists('.env'):
        load_dotenv('.env')
    bot_info = GeneralInformation()
    bot_info.clear_context()
    s = bot_info.get_gamedev_tz_info()


if __name__ == "__main__":
    main()