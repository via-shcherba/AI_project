import json
import logging


class JsonFormatter(logging.Formatter):       
    
    def format(self, record):
        timestamp = self.formatTime(record, self.datefmt)
        log_entry = {
            "timestamp": timestamp,
            "chat_id": record.chat_id if 'chat_id' in record.__dict__ else None,
            "level": record.levelname,
            "message": record.getMessage(),
        }
        if 'message_id' in record.__dict__:
            log_entry.update({"message_id": record.message_id}) 
        if 'json_body' in record.__dict__:
            log_entry.update({"json_body": record.json_body})           
        return json.dumps(log_entry, ensure_ascii=False)