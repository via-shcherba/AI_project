class BanDetector:
        
    def __init__(self, gpt, system):
        self.gpt = gpt
        self.system = system
                

    async def get_result(self, request, model, temp):
        messages = [
            {"role": "system", "content": self.system},
            {"role": "user", "content": "User request: Какие у вас торговые условия?"},
            {"role": "assistant", "content": ""},
            {"role": "user", "content": f"User request: {request}"}
        ]
        try:
            return await self.gpt.call_gpt_async(messages, model, temp)
        except:
            return ''