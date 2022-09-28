from typing import Any


def word_pos_to_list_item(word_pos: str, items: list[Any]) -> Any:
    """
    Provided a list, convert word_pos to an index integer and return the element in the list at that position:

    e.g.

    >>> x = [0, 1, 2 ,3, 4, 5]
    >>> word_pos_to_list_item("1st", x)
    0
    >>> word_pos_to_list_item("4th", x)
    3
    >>> word_pos_to_list_item("10th", x)
    IndexError: list index out of range
    """
    return items[int(word_pos[:-2]) - 1]
