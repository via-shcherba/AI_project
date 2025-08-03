class NeedDetector:
        
    def __init__(self, gpt, system):
        self.gpt = gpt
        self.system = system
                
    
    async def get_need(self, text, model, temp):  
        messages = [
            {"role": "system", "content": self.system},
            {"role": "user", "content": text}
        ]
        return await self.gpt.call_gpt_async(messages, model, temp)