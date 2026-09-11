def is_palindrome(value):
    """Return True if the given value reads the same forwards and backwards.

    Accepts strings or numbers. Non-alphanumeric characters are ignored
    (stripped) so that phrases like 'A man, a plan, a canal: Panama' are
    treated as palindromes. Case is ignored.
    """
    # Normalise: keep only alphanumeric characters, lowercased
    cleaned = [ch.lower() for ch in str(value) if ch.isalnum()]
    cleaned_str = "".join(cleaned)
    return cleaned_str == cleaned_str[::-1]


if __name__ == "__main__":
    test_cases = [
        ("racecar", True),
        ("RaceCar", True),
        ("A man, a plan, a canal: Panama", True),
        ("Was it a car or a cat I saw?", True),
        ("hello", False),
        ("12321", True),
        ("12345", False),
        ("", True),
        ("   ", True),
        ("No 'x' in Nixon", True),
    ]

    for text, expected in test_cases:
        result = is_palindrome(text)
        status = "PASS" if result == expected else "FAIL"
        print(f"[{status}] is_palindrome({text!r}) = {result} (expected {expected})")