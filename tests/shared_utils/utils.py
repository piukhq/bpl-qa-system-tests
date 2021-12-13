from typing import Any


def _sort_key(element: Any) -> list:
    return sorted(element)


def compare_unordered_complex_data(data_1: Any, data_2: Any, /) -> bool:
    if isinstance(data_1, list):
        return all(
            compare_unordered_complex_data(a, b)
            for a, b in zip(sorted(data_1, key=_sort_key), sorted(data_2, key=_sort_key))
        )
    elif isinstance(data_1, dict):
        return all(
            a == b and compare_unordered_complex_data(data_1[a], data_2[b])
            for a, b in zip(sorted(data_1), sorted(data_2))
        )
    else:
        return data_1 == data_2
