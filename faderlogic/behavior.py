"""Library-only title comparison. Never changes track metadata or set order."""
import re
import unicodedata
from PyQt6.QtWidgets import QTableWidgetItem


def title_sort_key(title, punctuation=False, numbers=False):
    value = str(title).casefold()
    if punctuation:
        value = value.lstrip()
        while value and unicodedata.category(value[0])[0] in ('P', 'S'):
            value = value[1:].lstrip()
    if numbers:
        # Zero-padded counters, or short numbers with explicit separators.
        # Bare 2 Unlimited / 99 Luftballons / 1999 remain meaningful titles.
        value = re.sub(r'^(?:0\d{1,2}(?:\s*[-._)]\s*|\s+)|\d{1,3}\s*[-._)]\s*)(?=\S)', '', value)
        if punctuation:
            value = value.lstrip()
            while value and unicodedata.category(value[0])[0] in ('P', 'S'):
                value = value[1:].lstrip()
    return value


class TitleItem(QTableWidgetItem):
    def __lt__(self, other):
        table = self.tableWidget()
        options = table.property('title_sort_options') or {}
        if not any(options.values()):
            return super().__lt__(other)
        return title_sort_key(self.text(), **options) < title_sort_key(other.text(), **options)
