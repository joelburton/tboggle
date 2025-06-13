from typing import List, TypeVar

T = TypeVar('T')

def fill(words: List[T], col_pp: int, rows_pp: int) -> List[List[List[T]]]:
    """
    Arranges a list of items into pages with specified column and row layout.
    Items are filled column-wise and returned as a list of pages, where each
    page contains rows of items arranged in columns.

    Args:
        words: List of items to arrange
        col_pp: Maximum number of columns per page
        rows_pp: Number of rows per page

    Returns:
        List of pages, where each page is a list of rows containing items

    Example:
        >>> w = list("abcdefghijklmnopqrstuvwxyz")
        >>> b = fill(w, 2, 3)
        >>> b == [
        ...    [['a', 'd'], ['b', 'e'], ['c', 'f']],
        ...    [['g', 'j'], ['h', 'k'], ['i', 'l']],
        ...    [['m', 'p'], ['n', 'q'], ['o', 'r']],
        ...    [['s', 'v'], ['t', 'w'], ['u', 'x']],
        ...    [['y'], ['z']]
        ... ]
        True
    """
    def create_columns(page_words: List[T], num_cols: int) -> List[List[T]]:
        columns = []
        for col in range(num_cols):
            column_items = [
                page_words[col * rows_pp + row]
                for row in range(rows_pp)
                if col * rows_pp + row < len(page_words)
            ]
            columns.append(column_items)
        return columns

    def transpose_to_rows(columns: List[List[T]]) -> List[List[T]]:
        rows = []
        for row_idx in range(rows_pp):
            row_items = [
                col[row_idx] for col in columns
                if row_idx < len(col)
            ]
            if row_items:
                rows.append(row_items)
        return rows

    def pad_rows(rows: List[List[T]]) -> None:
        if not rows:
            return
        target_length = len(rows[0])
        for row in rows:
            row.extend([''] * (target_length - len(row)))

    pages = []
    pos = 0
    items_per_page = col_pp * rows_pp

    while pos < len(words):
        page_words = words[pos:pos + items_per_page]

        # Calculate actual columns needed for this page
        actual_cols = min(col_pp, (len(page_words) + rows_pp - 1))

        # Process page layout
        columns = create_columns(page_words, actual_cols)
        rows = transpose_to_rows(columns)
        pad_rows(rows)
        pages.append(rows)

        pos += items_per_page

    return pages
