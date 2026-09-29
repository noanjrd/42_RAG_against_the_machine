import fire
from .chunk.chunking import going_through_data

class Rag:
    def __init__(self, k=5) -> None:
        pass
    
    def test(self):
        print("hey")
        
    def index(self, max_chunk_size=2000):
        going_through_data(max_chunk_size)
        print("hey")
    
    
def main():
    fire.Fire(Rag)

if __name__ == "__main__":
    main()