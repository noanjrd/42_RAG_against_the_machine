"""Command line entry point of the RAG pipeline (Fire)."""
import fire
from .index.indexing import start_indexing
from .llm.LLM import LLM
from .search.searching import start_searching, start_searching_dataset
from .answer.answering import start_answering, start_answering_dataset


class Rag:
    """Command line interface of the RAG pipeline.

    Each public method is a sub-command (index, search, search_dataset,
    answer, answer_dataset) exposed by Fire.
    """
    def __init__(self) -> None:
        pass

    def index(self, max_chunk_size: int = 2000) -> None:
        """Chunk, tokenize and index the vLLM sources.

        Args:
            max_chunk_size: Maximum number of characters per chunk (>= 1).

        Returns:
            None. Exits with status 1 on invalid input or interruption.
        """
        try:
            assert max_chunk_size > 0, "max_chunk_size must be at least 1"
            llm = LLM()
            start_indexing(max_chunk_size, llm)
        except AssertionError as e:
            print("Error:", e)
            exit(1)
        except KeyboardInterrupt:
            print("Program interrupted")
            exit(1)
        return

    def search(self, *args: str, k: int = 5) -> None:
        """Retrieve the k most relevant chunks for one query.

        Args:
            *args: Exactly one positional argument, the query.
            k: Number of chunks to retrieve (>= 1).

        Returns:
            None. Prints the retrieved sources; exits with status 1 on error.
        """
        try:
            assert len(args) == 1, "Need one query"
            assert k > 0, "k must be at least 1"
            query = args[0]
            llm = LLM()
            print("Query:", query)
            start_searching(llm, query, k)
        except AssertionError as e:
            print("Error:", e)
            exit(1)
        except KeyboardInterrupt:
            print("Program interrupted")
            exit(1)
        return

    def search_dataset(self, dataset_path: str,
                       save_directory: str = "data/answers",
                       k: int = 5) -> None:
        """Retrieve chunks for every question of a dataset.

        Args:
            dataset_path: Path to the JSON dataset of questions.
            save_directory: Directory where the search results are written.
            k: Number of chunks to retrieve per question (>= 1).

        Returns:
            None. Exits with status 1 on invalid input or interruption.
        """
        try:
            assert k > 0, "k must be at least 1"
            llm = LLM()
            print("k:", k)
            start_searching_dataset(llm, dataset_path, save_directory, k)
        except AssertionError as e:
            print("Error:", e)
            exit(1)
        except KeyboardInterrupt:
            print("Program interrupted")
            exit(1)
        return

    def answer(self, *args: str, k: int = 5) -> None:
        """Retrieve chunks for one query and answer it with the LLM.

        Args:
            *args: Exactly one positional argument, the query.
            k: Number of chunks used as context (>= 1).

        Returns:
            None. Prints the answer; exits with status 1 on error.
        """
        try:
            assert len(args) == 1, "Need one query"
            assert k > 0, "k must be at least 1"
            query = args[0]
            llm = LLM()
            search_result = start_searching(llm, query, k)
            start_answering(llm, query, search_result)
        except AssertionError as e:
            print(e)
            exit(1)
        except KeyboardInterrupt:
            print("Program interrupted")
            exit(1)
        return

    def answer_dataset(self, student_search_results_path: str,
                       save_directory: str) -> None:
        """Answer every question of a saved search-results file.

        Args:
            student_search_results_path: Path to the JSON file produced by
                search_dataset.
            save_directory: Directory where the answers are written.

        Returns:
            None. Exits with status 1 on invalid input or interruption.
        """
        try:
            assert student_search_results_path, \
                "student_search_results_path is empty"
            assert len(save_directory) > 0, "save_directory is empty"
            llm = LLM()
            start_answering_dataset(
                llm, student_search_results_path, save_directory)
        except AssertionError as e:
            print(e)
            exit(1)
        except KeyboardInterrupt:
            print("Program interrupted")
            exit(1)


def main() -> None:
    """Run the Fire command line interface.

    Returns:
        None.
    """
    fire.Fire(Rag)


if __name__ == "__main__":
    main()
