import hashlib
import math
import re


def deterministic_embedding(text: str, dimensions: int = 384) -> list[float]:
    """Create a stable local feature-hash vector without models or network access."""
    vector = [0.0] * dimensions
    tokens = re.findall(r"[\w\u4e00-\u9fff]+", text.lower())
    for token in tokens:
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
        index = int.from_bytes(digest[:4], "big") % dimensions
        sign = 1.0 if digest[4] & 1 else -1.0
        vector[index] += sign
    magnitude = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / magnitude for value in vector]

