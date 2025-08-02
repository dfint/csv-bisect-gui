from __future__ import annotations

import tkinter as tk
from functools import partial
from itertools import islice
from operator import itemgetter
from tkinter import ttk
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from bidict import MutableBidict, bidict
from tkinter_layout_helpers import grid_manager, pack_manager

from csv_bisect_gui.scrollbar_frame import ScrollbarFrame

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

T = TypeVar("T")


class Node(Generic[T]):
    _all_items: list[T]
    start: int
    end: int

    def __init__(self, items: list[T], start: int = 0, end: int | None = None) -> None:
        self._all_items = items
        self.start = start

        if end is None:
            end = len(items) - 1

        self.end = end
        assert self.start >= 0
        assert self.end < len(items)

    @property
    def size(self) -> int:
        return self.end - self.start + 1

    def split(self) -> tuple[Node[T], Node[T]]:
        assert self.size >= 2, f"Not enough items to split: {self.size}"
        mid = (self.start + self.end) // 2
        return Node(self._all_items, self.start, mid), Node(self._all_items, mid + 1, self.end)

    @property
    def tree_text(self) -> str:
        if self.size == 0:
            return "[] (0 strings)"
        if self.size == 1:
            return f"[{self.start} : {self.end}] (1 string)"
        return f"[{self.start} : {self.end}] ({self.size} strings)"

    @property
    def slice(self) -> slice:
        return slice(self.start, self.end + 1)

    @property
    def items(self) -> Iterable[T]:
        s = self.slice
        return islice(self._all_items, s.start, s.stop)

    @property
    def column_text(self) -> str:
        if self.start > self.end:
            return "<empty>"
        if self.start == self.end:
            item = self._all_items[self.start]
            return str(item)
        if self.end - self.start + 1 <= 2:  # One or two strings in the slice: show all strings
            return ",".join(map(str, self.items))
        # More strings: show the first and the last
        return f"{self._all_items[self.start]} ... {self._all_items[self.end]}"

    def __hash__(self) -> int:
        return hash((self.start, self.end))

    def __eq__(self, other: Node[T]) -> bool:
        return self.start == other.start and self.end == other.end

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(..., {self.start}, {self.end})"


class BisectTool(tk.Frame, Generic[T]):
    _strings: list[T] | None
    _nodes_by_item_ids: MutableBidict[str, Node[T]]

    def __init__(self, *args: list[Any], strings: list[T] | None = None, **kwargs: dict[str, Any]) -> None:
        super().__init__(*args, **kwargs)
        with grid_manager(self, sticky=tk.NSEW, pady=2) as grid:
            scrollbar_frame = ScrollbarFrame(widget_factory=ttk.Treeview, show_scrollbars=tk.VERTICAL)

            self.tree = tree = scrollbar_frame.widget
            tree["columns"] = ("strings",)
            tree.heading("#0", text="Tree")
            tree.heading("#1", text="Strings")

            self._nodes_by_item_ids = bidict()
            self.strings = strings

            with grid.new_row() as row:
                row.add(scrollbar_frame).configure(weight=1)

            with (
                grid.new_row() as row,
                pack_manager(tk.Frame(), side=tk.LEFT, expand=True, fill=tk.X, padx=1) as toolbar,
            ):
                toolbar.pack_all(
                    ttk.Button(text="Split", command=self.split_selected_node),
                    ttk.Button(text="Mark as bad", command=partial(self.mark_selected_node, background="orange")),
                    ttk.Button(text="Mark as good", command=partial(self.mark_selected_node, background="lightgreen")),
                    ttk.Button(text="Clear mark", command=partial(self.mark_selected_node, background="white")),
                )

                row.add(toolbar.parent)

            grid.columnconfigure(0, weight=1)

    @property
    def strings(self) -> list[T] | None:
        return self._strings

    @strings.setter
    def strings(self, value: list[T] | None) -> None:
        self._strings = value
        self.tree.delete(*self.tree.get_children())
        self._nodes_by_item_ids = bidict()  # Create new empty bidict to avoid ValueDuplicationError
        if value:
            self.insert_node(Node[T](value))

    def insert_node(self, node: Node[T], parent_node: Node[T] | None = None) -> None:
        parent_item_id = "" if not parent_node else self._nodes_by_item_ids.inverse[parent_node]

        item_id = self.tree.insert(
            parent_item_id,
            tk.END,
            text=node.tree_text,
            values=(node.column_text,),
            open=True,
        )

        self._nodes_by_item_ids[item_id] = node

        # Add an item id as a tag to color the row by that tag
        self.tree.item(item_id, tags=(item_id,))

    def get_item_id_of_node(self, node: Node[T]) -> MutableBidict[Node[T], str]:
        return self._nodes_by_item_ids.inverse[node]

    def get_selected_node(self) -> Node[T] | None:
        tree = self.tree
        selected_ids = tree.selection()
        if selected_ids and not tree.get_children(selected_ids[0]):
            return self._nodes_by_item_ids[selected_ids[0]]
        return None

    def split_selected_node(self) -> None:
        parent = self.get_selected_node()
        if parent and parent.start != parent.end:
            new_nodes = parent.split()

            for node in new_nodes:
                self.insert_node(parent_node=parent, node=node)

            # move selection to the first child
            item_id = self._nodes_by_item_ids.inverse[new_nodes[0]]
            self.tree.selection_set(item_id)

    def mark_selected_node(self, **kwargs: dict[str, Any]) -> None:
        tree = self.tree
        for item in tree.selection():
            tree.tag_configure(item, **kwargs)

    @property
    def selected_nodes(self) -> Iterable[Node[T]]:
        return (self._nodes_by_item_ids[item_id] for item_id in self.tree.selection())

    @property
    def filtered_strings(self) -> Iterator[T]:
        nodes: list[Node[T]] = list(self.selected_nodes)
        if not nodes:
            return self._strings
        if len(nodes) == 1:
            # Only one row selected (optimized case)
            return islice(self._strings, nodes[0].start, nodes[0].end + 1)
        # Merge ranges when multiple rows selected
        enumerated_strings = list(enumerate(self._strings))
        strings = set()
        for node in nodes:
            strings |= set(islice(enumerated_strings, node.start, node.end + 1))

        # Restore original order of the strings
        return map(itemgetter(1), sorted(strings, key=itemgetter(0)))
