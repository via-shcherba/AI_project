import aiohttp # type: ignore


class GPT_API():
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.url = "https://api.openai.com/v1/chat/completions"


    async def call_gpt_async(self, messages, model, temp=None, tools=None):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": model,
            "messages": messages          
        }
        if tools:
            data.update({"tools": tools})
        else:
            data.update({"temperature": temp})
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.url, headers=headers, json=data) as response:
                if response.status == 200:
                    response_data = await response.json()    
                    if tools:
                        return response_data['choices'][0]['message']['tool_calls']    
                    else:               
                        return response_data['choices'][0]['message']['content']
                else:
                    print(f'OpenAI Status: {response.status}*********************')
                    return None        