from transformers import AutoTokenizer

class LLM:
    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen3-0.6B")
        
        return
    
    def tokenize(self, text):
        tokenized = self.tokenizer.tokenize(text)
        return tokenized
        

    