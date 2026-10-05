from pydantic import BaseModel


class Token():
    def __init__(self, token):
        self.token = token
        self.document_frequency = 0

    