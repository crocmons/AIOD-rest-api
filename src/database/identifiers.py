import random
import string
from typing import Callable


def generate_id_with_prefix(prefix: str = "temp") -> Callable[[], str]:
    if len(prefix) > 4:
        raise ValueError(f"Provided prefix {prefix!r} must contain 4 or fewer characters.")
    alpha_numeric = string.ascii_letters + string.digits

    def generate():
        random_string = ''.join(random.choices(alpha_numeric, k=24))
        return f"{prefix}_{random_string}"

    return generate
