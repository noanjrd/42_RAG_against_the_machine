"""Answer generation from retrieved sources."""
from ..models.student_search import MinimalAnswer
from ..llm.LLM import LLM
import json
from tqdm import tqdm
import os
from ..utils import remove_touching
from typing import Any



def make_prompt(query: str, sources: list[Any]) -> str:
    """Build the prompt from a question and its retrieved sources.

    Args:
        query: The question.
        sources: Retrieved sources (mappings with file_path,
            first_character_index and last_character_index).

    Returns:
        The prompt with the documentation followed by the question.
    """
    sources = [dict(s) for s in sources]
    prompt = "Documentation: \n"
    sources.sort(key=lambda x: (x["file_path"], x["first_character_index"]))
    sources = remove_touching(sources)
    for source in sources:
        with open(source["file_path"], "r", encoding='utf-8') as f:
            content = f.read()
            content = content[source["first_character_index"]:
                              source["last_character_index"]]
            prompt += content
            prompt += "\n\n"
    prompt += f"Question: {query}\n"
    prompt += ("Only answer from the documentation and say so when "
               "the documentation is insufficient.")
    return prompt


def start_answering_dataset(
        llm: LLM,
        student_search_results_path: str,
        save_directory: str) -> None:
    """Answer every question of a saved search-results file.

    The answers are saved as JSON in save_directory, under the name of
    the input file.

    Args:
        llm: LLM used to answer.
        student_search_results_path: Path to the search results JSON.
        save_directory: Directory where the answers are written.

    Returns:
        None.
    """
    with open(student_search_results_path, "r", encoding='utf-8') as f:
        file = json.load(f)
    file_name = os.path.basename(student_search_results_path)
    output = {"k": file["k"], "search_results": []}
    file = file["search_results"]
    for q in tqdm(file, desc="Answering"):
        prompt = make_prompt(q["question"], q["retrieved_sources"])
        answer = llm.answer(prompt)
        MiniAns = MinimalAnswer(
            answer=answer,
            question_id=q["question_id"],
            question=q["question"],
            retrieved_sources=q["retrieved_sources"])
        output["search_results"].append(MiniAns.model_dump())

    os.makedirs(save_directory, exist_ok=True)
    path = os.path.join(save_directory, file_name)
    with open(path, "w", encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    return


def start_answering(llm: LLM, query: str,
                    search_results: dict[str, Any]) -> None:
    """Answer one query from its retrieved sources and print it.

    Args:
        llm: LLM used to answer.
        query: The question.
        search_results: Output of start_searching, with "retrieved_sources".

    Returns:
        None.
    """
    prompt = "Documentation: \n"
    for source in search_results["retrieved_sources"]:
        with open(source["file_path"], "r", encoding='utf-8') as f:
            content = f.read()
            content = content[source["first_character_index"]:
                              source["last_character_index"]]
            prompt += content
            prompt += "\n\n"
    prompt += f"Question: {query}"
    # print(prompt)
    answer = llm.answer(prompt)
    print("Answer:", answer)
    return
