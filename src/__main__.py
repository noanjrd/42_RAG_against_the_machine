import fire
from .index.indexing import start_indexing
from .llm.model import LLM
from .search.searching import start_searching

class Rag:
    def __init__(self, k=5) -> None:
        pass
    
    def test(self):
        print("hey")
        
    def index(self, max_chunk_size=2000):
        try:
            assert max_chunk_size > 0, "max_chunk_size must be at least 1"
            llm = LLM()
            start_indexing(max_chunk_size, llm)
            print("hey")
        except AssertionError as e:
            print("Error:", e)
            exit(1)
        except KeyboardInterrupt:
            print("Program interrupted")
            exit(1)
        return
        
    def search(self, *args,  k=5):
        try:
            assert len(args) == 1, "Need one query"
            assert k > 0, "k must be at least 1"
            query = args[0]
            llm = LLM()
            print("Query:", query)
            tokenized_query = llm.tokenize(query)
            start_searching(tokenized_query)
        except AssertionError as e:
            print("Error:", e)
            exit(1)
        return
    
    
def main():
    fire.Fire(Rag)

if __name__ == "__main__":
    main()