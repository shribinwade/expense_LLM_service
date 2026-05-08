from app.service.llmService import LLMService
from app.utils.messageUtil import MessageUtil

class MessageService:
    def __init__(self):
        self.messageUtil = MessageUtil();
        self.llmService  = LLMService();
    
    def process_message(self,message):
        if self.messageUtil.isBankSms(message):
            return self.llmService.runLLM(message)
        else:
            return None