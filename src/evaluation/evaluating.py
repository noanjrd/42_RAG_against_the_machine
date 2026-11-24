import json
from pydantic import ValidationError
from ..models.student_search import MinimalSearchResults


def calc_percentage_overlap(dataset_first_c: int, dataset_last_c: int,
                            source_first_c: int,
                            source_last_c: int) -> float:
    """Compute the IoU (intersection over union) of two character spans.

    The intersection is the number of characters shared by the expected
    and the retrieved source. The union counts every character covered by
    either span once: len(expected) + len(retrieved) - intersection.

    Args:
        dataset_first_c: First character index of the expected source.
        dataset_last_c: Last character index of the expected source.
        source_first_c: First character index of the retrieved source.
        source_last_c: Last character index of the retrieved source.

    Returns:
        The IoU as a ratio between 0.0 (no overlap) and 1.0 (identical
        spans).
    """
    start = max(source_first_c, dataset_first_c)
    end = min(source_last_c, dataset_last_c)
    inter = end - start
    if inter <= 0:
        return 0.0
    union = ((dataset_last_c - dataset_first_c)
             + (source_last_c - source_first_c) - inter)
    return inter / union


def start_evaluating(student_search_results_path: str,
                     dataset_path: str) -> None:
    """Print the recall score of a saved search-results file.

    A question counts as found at rank k when one of its first k retrieved
    sources comes from the expected file and has an IoU of at least 0.05
    with the expected span. Recall@1, @3, @5 and @10 are the share of
    questions found at each rank. Results that fail validation count as
    not found, and an empty dataset is reported as an error.

    Args:
        student_search_results_path: File written by search_dataset.
        dataset_path: Matching answered-questions dataset file.
    """
    try:
        with open(dataset_path, encoding='utf-8') as f:
            dataset_answered_q = json.load(f)
        dataset_answered_q = dataset_answered_q["rag_questions"]

        with open(student_search_results_path, encoding='utf-8') as f:
            search_answered_q = json.load(f)
        search_answered_q = search_answered_q["search_results"]

        len_questions = len(search_answered_q)
        assert len_questions > 0, "Empty dataset"
        right_chunks = [0] * 4
        for index_q, dataset_q in enumerate(dataset_answered_q):
            search_q = search_answered_q[index_q]
            dataset_file_path = dataset_q["sources"][0]["file_path"]
            dataset_first_c = dataset_q["sources"][0]["first_character_index"]
            dataset_last_c = dataset_q["sources"][0]["last_character_index"]

            try:
                MinimalSearchResults.model_validate(search_q)
                sources = search_q["retrieved_sources"]
                for index_s, source in enumerate(sources):
                    source_first_c = source["first_character_index"]
                    source_last_c = source["last_character_index"]
                    overlapping_percentage = calc_percentage_overlap(
                        dataset_first_c, dataset_last_c,
                        source_first_c, source_last_c)
                    if (source["file_path"] == dataset_file_path
                            and overlapping_percentage >= 0.05):
                        right_chunks[3] += 1
                        if index_s == 0:
                            right_chunks[0] += 1
                        if index_s <= 2:
                            right_chunks[1] += 1
                        if index_s <= 4:
                            right_chunks[2] += 1
                        break

            except ValidationError:
                print("Student data is valid: False")
                continue
            except Exception as e:
                print(e)

        recall = [chunk/len_questions for chunk in right_chunks]
        print("Student data is valid: True")
        print("Evaluation Results")
        print("===========================")
        print(f"Recall@1: {recall[0]:.2}  Recall@3: {recall[1]:.2} "
              f"Recall@5: {recall[2]:.2} Recall@10: {recall[3]:.2}")
    except AssertionError as e:
        print("Error:", e)
