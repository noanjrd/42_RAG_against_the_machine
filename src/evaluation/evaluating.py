import json
from pydantic import ValidationError
from ..models.student_search import MinimalSearchResults
from ..utils import remove_touching


def calc_percentage_overlap(dataset_first_c: int, dataset_last_c: int,
                            source_first_c: int,
                            source_last_c: int) -> float:
    """Compute how much of the expected source a retrieved source covers.

    Args:
        dataset_first_c: First character index of the expected source.
        dataset_last_c: Last character index of the expected source.
        source_first_c: First character index of the retrieved source.
        source_last_c: Last character index of the retrieved source.

    Returns:
        The overlap as a percentage of the expected source length, or 0.0
        when they do not overlap.
    """
    start = max(source_first_c, dataset_first_c)
    end = min(source_last_c, dataset_last_c)
    gt_len = dataset_last_c - dataset_first_c
    if end <= start or gt_len <= 0:
        return 0.0
    return (end - start) / gt_len * 100


def start_evaluating(student_search_results_path: str,
                     dataset_path: str) -> None:
    """Print the recall score of a saved search-results file.

    A question counts as found when a retrieved source comes from the
    expected file and overlaps at least 33% of the expected source. Results
    that fail validation count as not found.

    Args:
        student_search_results_path: File written by search_dataset.
        dataset_path: Matching answered-questions dataset file.
    """
    with open(dataset_path, encoding='utf-8') as f:
        dataset_answered_q = json.load(f)
    dataset_answered_q = dataset_answered_q["rag_questions"]

    with open(student_search_results_path, encoding='utf-8') as f:
        search_answered_q = json.load(f)
    search_answered_q = search_answered_q["search_results"]

    right_chunks = 0
    for index, dataset_q in enumerate(dataset_answered_q):
        search_q = search_answered_q[index]
        dataset_file_path = dataset_q["sources"][0]["file_path"]
        dataset_first_c = dataset_q["sources"][0]["first_character_index"]
        dataset_last_c = dataset_q["sources"][0]["last_character_index"]

        try:
            MinimalSearchResults.model_validate(search_q)
            sources = search_q["retrieved_sources"]
            sources.sort(key=lambda x: (x["file_path"],
                                        x["first_character_index"]))
            sources = remove_touching(sources)
            for source in sources:
                source_first_c = source["first_character_index"]
                source_last_c = source["last_character_index"]
                overlapping_percentage = calc_percentage_overlap(
                    dataset_first_c, dataset_last_c,
                    source_first_c, source_last_c)
                if (source["file_path"] == dataset_file_path
                        and overlapping_percentage >= 33):
                    right_chunks += 1
                    break

        except ValidationError:
            print("Error")
            continue
        except Exception as e:
            print(e)
    recall = right_chunks / len(dataset_answered_q)
    print(f"Here is the recall score: {recall:.2}")
