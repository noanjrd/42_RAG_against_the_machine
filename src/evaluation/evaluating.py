import json
from pydantic import ValidationError
from ..models.student_search import MinimalSearchResults
from ..utils import remove_touching

def start_evaluating(student_search_results_path, dataset_path):
    with open(dataset_path, encoding='utf-8') as f:
        dataset_answered_q = json.load(f)
    dataset_answered_q =  dataset_answered_q["rag_questions"]

    with open(student_search_results_path, encoding='utf-8') as f:
        search_answered_q = json.load(f)
    search_answered_q =  search_answered_q["search_results"]

    right_chunks = 0
    for index, dataset_q in enumerate(dataset_answered_q):
        search_q = search_answered_q[index]
        dataset_file_path = dataset_q["sources"][0]["file_path"]
        dataset_first_c = dataset_q["sources"][0]["first_character_index"]
        dataset_last_c = dataset_q["sources"][0]["last_character_index"]
        
        try:
            MinimalSearchResults.model_validate(search_q)
            sources = search_q["retrieved_sources"]
            sources.sort(key=lambda x: (x["file_path"] ,x["first_character_index"]))
            sources = remove_touching(sources)
            for source in sources:
                source_first_c = source["first_character_index"]
                source_last_c = source["last_character_index"]
                if source["file_path"] == dataset_file_path and   dataset_first_c >= source_first_c and dataset_last_c <= source_last_c:
                    right_chunks += 1
                    break
            
        except ValidationError:
            print("Error")
            continue
        except Exception as e:
            print(e)
        
        # print(question)
    print(right_chunks / len(dataset_answered_q))
    return