class LanguageTranslator:
    
    def __init__(self, gpt, json_translator_system, text_translator_system):
        self.gpt = gpt
        self.text_translator_system = text_translator_system
        self.json_translator_system = json_translator_system
                

    async def translate_text(self, text, language, model, temp):
        if not text:
            return text
        messages = [
            {"role": "system", "content": self.text_translator_system},
            {"role": "user", "content": "Translate to English this text: Как вязать носки?"},
            {"role": "assistant", "content": "How to knit socks?"},
            {"role": "user", "content": f"Translate to {language} this text: {text}"}
        ]
        try:
            return await self.gpt.call_gpt_async(messages, model, temp)
        except:
            return text
        
        
    async def translate_json(self, json_str, language, model, temp):
        messages = [
            {"role": "system", "content": self.json_translator_system},
            {"role": "user", "content": 'Translate to Russian values of json: {"CHAT_MSG": "Chat"}'},
            {"role": "assistant", "content": '{"CHAT_MSG": "Чат"}'},
            {"role": "user", "content": f"Translate to {language} values of json: {json_str}"}
        ]
        try:
            return await self.gpt.call_gpt_async(messages, model, temp)
        except:
            return json_str