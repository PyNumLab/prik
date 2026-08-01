from prik.contracts import Int32


class item:
    value: Int32


state: item


def make_item(initial: Int32) -> item: ...
