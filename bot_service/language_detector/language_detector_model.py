class LanguageDetector:
    
    def __init__(self, gpt, system):
        self.gpt = gpt
        self.system = system
        

    async def get_language(self, request, model, temp):
        if not request:
            return 'English'
        messages = [
            {"role": "system", "content": self.system},
            {"role": "user", "content": "Text: привет"},
            {"role": "assistant", "content": "Russian"},
            {"role": "user", "content": f"Text: {request}"}
        ]
        try:
            return await self.gpt.call_gpt_async(messages, model, temp)
        except:
            return 'English'