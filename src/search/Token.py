"""Query token with its document frequency."""


class Token():
    """A query token used by the BM25 search.

    Attributes:
        token: The token text.
        document_frequency: Number of chunks containing the token.
    """
    def __init__(self, token: str) -> None:
        self.token = token
        self.document_frequency = 0
