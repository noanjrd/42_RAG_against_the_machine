import re
import keyword

STOPWORDS = {
    # articles, prepositions, conjunctions
    "a", "an", "the", "of", "to", "in", "on", "at", "by", "for", "with",
    "from",
    "as", "into", "about", "and", "or", "but", "if", "than", "then", "so",
    # verbs "be/do/have" and modals
    "is", "are", "was", "were", "be", "been", "being", "am",
    "do", "does", "did", "have", "has", "had",
    "can", "could", "will", "would", "should", "may", "might", "must",
    # pronouns and determiners
    "i", "you", "he", "she", "it", "we", "they", "me", "my", "your", "its",
    "this", "that", "these", "those", "there", "here", "some", "any",
    # question words
    "what", "which", "who", "whom", "where", "when", "why", "how",
    ",", ":", ".", "!", ";"
}


def split_evey_n_character(max_chunk_size: int, text: str) -> list[str]:
    """Split a text into consecutive pieces of fixed length.

    Args:
        max_chunk_size: Length of each piece (the last one may be shorter).
        text: Text to split.

    Returns:
        The list of pieces, in order.
    """
    n = len(text)
    splitted_text = [text[i: i + max_chunk_size]
                     for i in range(0, n, max_chunk_size)]
    return splitted_text


def remove_stopwords(tokens: list[str]) -> list[str]:
    """Normalize tokens and drop stopwords and punctuation.

    Removes the leading BPE space marker of tokens and replaces accented
    characters (e, e, a with accents) by their ASCII equivalent.

    Args:
        tokens: Tokens produced by the tokenizer.

    Returns:
        The normalized tokens that are not empty nor stopwords.
    """
    result: list[str] = []
    for token in tokens:
        word = token.lstrip("Ġ")
        word = word.replace('é', 'e')
        word = word.replace('è', 'e')
        word = word.replace('à', 'a')
        if word and word not in STOPWORDS:
            result.append(word)
    return result


def add_identifiers(content: str) -> list[str]:
    """Extract lowercase code identifiers from a source text.

    Python keywords are ignored. Each identifier is kept whole and also
    split on underscores (my_var gives my_var, my, var).

    Args:
        content: Source code or text to scan.

    Returns:
        The list of identifiers and identifier parts (duplicates kept).
    """
    identifiers = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", content)
    identifiers = [t for t in identifiers if not keyword.iskeyword(t)]
    new = []
    for identifier in identifiers:
        identifier = identifier.lower()
        new.append(identifier)
        splitted = identifier.split('_')
        new += [el for el in splitted if el]
    return new
