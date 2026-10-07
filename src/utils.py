import re

STOPWORDS = {
    # articles, prepositions, conjunctions
    "a", "an", "the", "of", "to", "in", "on", "at", "by", "for", "with", "from",
    "as", "into", "about", "and", "or", "but", "if", "than", "then", "so",
    # verbs "be/do/have" and modals
    "is", "are", "was", "were", "be", "been", "being", "am",
    "do", "does", "did", "have", "has", "had",
    "can", "could", "will", "would", "should", "may", "might", "must",
    # pronouns and determiners
    "i", "you", "he", "she", "it", "we", "they", "me", "my", "your", "its",
    "this", "that", "these", "those", "there", "here", "some", "any",
    # question words
    "what", "which", "who", "whom", "where", "when", "why", "how"
}

def remove_stopwords(tokens: list[str]) -> list[str]:
    result = []
    for token in tokens:
        word = token.lstrip("Ġ")
        if word  and word not in STOPWORDS:
            result.append(word)
    return result


def add_identifiers(content):
    identifiers = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", content)
    # identifiers = [t for t in identifiers if not keyword.iskeyword(t)]
    new = []
    for identifier in identifiers:
        identifier = identifier.lower()
        new.append(identifier)
        splitted = identifier.split('_')
        new += [el for el in splitted if len(el) > 0]
    return new
