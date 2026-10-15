from ..models.student_search import  MinimalSearchResults, MinimalAnswer
from ..llm.LLM import LLM
import json
from tqdm import tqdm
import os

def remove_touching(sources):
    n = len(sources)
    i = 0
    while i < n-1:
        first = sources[i]["last_character_index"]
        last = sources[i+1]["first_character_index"]
        if first <= last and first + 10 >= last and sources[i]["file_path"] == sources[i+1]["file_path"]:
            sources[i]["last_character_index"] = sources[i+1]["last_character_index"]
            sources.pop(i+1)
            n -= 1
            continue
        i+=1
    return sources

def make_prompt(query, sources):
    sources = [dict(s) for s in sources]
    prompt = "Documentation: \n"
    sources.sort(key=lambda x: (x["file_path"], x["first_character_index"]))
    sources = remove_touching(sources)
    for source in sources:
        with open(source["file_path"], "r", encoding='utf-8') as f:
            content = f.read()
            content = content[source["first_character_index"] : source["last_character_index"]]
            prompt += content
            prompt += "\n\n"
    prompt += f"Question: {query}\n"
    prompt += f"Only answer from the documentation and say so when the documentation is insufficient."
    return prompt


def start_answering_dataset(llm: LLM, student_search_results_path: str, save_directory: str):
    with open(student_search_results_path, "r", encoding='utf-8') as f:
        file = json.load(f)
    file_name = os.path.basename(student_search_results_path)
    output = {"k": file["k"], "search_results": []}
    file = file["search_results"]
    for q in tqdm(file, desc="Answering"):
        prompt = make_prompt(q["question"], q["retrieved_sources"])
        answer = llm.answer(prompt)
        MiniAns = MinimalAnswer(answer=answer, question_id=q["question_id"], question=q["question"], retrieved_sources=q["retrieved_sources"])
        output["search_results"].append(MiniAns.model_dump())

    os.makedirs(save_directory, exist_ok=True)
    path = os.path.join(save_directory, file_name)
    with open(path, "w", encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    return

def start_answering(llm: LLM, query, search_results):
    prompt = "Documentation: \n"
    for source  in search_results["retrieved_sources"]:
        with open(source["file_path"], "r", encoding='utf-8') as f:
            content = f.read()
            content = content[source["first_character_index"] : source["last_character_index"]]
            prompt += content
            prompt += "\n\n"
    prompt += f"Question: {query}"
    print(prompt)
    answer = llm.answer(prompt)
    print("Answer:",answer)
    return