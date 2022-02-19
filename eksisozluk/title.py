from typing import Generator, Optional, TYPE_CHECKING

import bs4

from eksisozluk.constants import PAGE_URL
from eksisozluk.author import Author
from eksisozluk.entry import Entry
from eksisozluk.parsing_utils import (
    parse_page,
    select_first_element,
    get_element_attribute,
    find_element_with_id,
    find_elements_with_tag,
    handle_a_tag,
    handle_br_tag,
    wait_for_element_to_load,
)
from eksisozluk.input_reader import reader
from eksisozluk.writer import writer

if TYPE_CHECKING:
    from selenium import webdriver

Entries = list[Entry]
Indexes = list[int]
EntryGenerator = Generator[Entry, None, None]


class Title:
    """Title contains entries about a topic

    :type name: str
    :param name: Name of the title
    :type link: str
    :param link: Link of the title
    :type entry_count: int
    :param entry_count: Number of today's entries
    """

    def __init__(self, name: str, link: str, entry_count: Optional[int] = 0) -> None:

        self.name = name
        self.link = link
        self.entry_count = entry_count
        self._num_pages: Optional[int] = 0
        self._entries: Optional[Entries] = []

    def get_entries(
        self,
        entries_for_today: Optional[bool] = False,
        driver: Optional["webdriver"] = None,
    ) -> EntryGenerator:
        """Get entries of title

        :type entries_for_today: bool
        :param entries_for_today: Whether only today's entries requested
        :type driver: selenium.webdriver
        :param driver: Selenium webdriver instance
        :rtype: Generator
        :returns: List of entries under the title
        """

        if entries_for_today:
            driver.get(f"{PAGE_URL}{self.link}")
            page_content = wait_for_element_to_load(driver, selector="#container")
        else:
            page_content = parse_page(f"{PAGE_URL}{self.link}")

        page_count_element = select_first_element("pager", page_content)
        if page_count_element:
            self._num_pages = int(
                get_element_attribute("data-pagecount", page_count_element)
            )
        else:
            self._num_pages = 1

        entry_container = find_element_with_id("entry-item-list", page_content)
        if not entry_container:
            writer.print("[error]No entries found for today[/]\n")
            return

        page_number = 1

        while page_number <= self._num_pages:

            yield from self._get_entries_on_page(page_number, entries_for_today)

            load_more = reader.get_input(
                f"\n[loadmore](Showing page {page_number}/{self._num_pages}) "
                f"Load more entries [ Enter | q ] [/]"
            )
            if not load_more:
                page_number += 1
            else:
                break

    def get_selected_entries(self, selected_indexes: Indexes) -> Entries:
        """Get entries for the given indexes

        :type selected_indexes: list
        :param selected_indexes: List of indexes
        :rtype: list
        :returns: List of selected entries
        """

        return [self._entries[index - 1] for index in selected_indexes]

    def get_db_data(self) -> dict[str, str]:
        """Return dictionary object to save to the database

        :rtype: dict
        :returns: Dictionary with name and link keys
        """

        return {"name": self.name, "link": self.link}

    def _get_entries_on_page(
        self, page_number: int, entries_for_today: Optional[bool] = False
    ) -> EntryGenerator:
        """Get entries from the given page

        If today's entries are requested, adjust the url parameter.

        :type page_number: int
        :param page_number: Page number for the request
        :type entries_for_today: bool
        :param entries_for_today: Whether only today's entries requested
        :rtype: Generator
        :returns: List of entries for the given page
        """

        page_arg = f"&p={page_number}" if entries_for_today else f"?p={page_number}"
        entries_page = parse_page(f"{PAGE_URL}/{self.link}{page_arg}")
        entry_container = find_element_with_id("entry-item-list", entries_page)
        entries = find_elements_with_tag("li", entry_container)

        for entry_element in entries:

            entry_fields = self._extract_entry_fields(entry_element)
            entry = Entry(**entry_fields)
            self._entries.append(entry)

            yield entry

    def _extract_entry_fields(self, entry_element: bs4.element.Tag) -> dict[str, str]:
        """Extract fields to construct an entry

        :type entry_element: bs4.element.Tag
        :param entry_element: Entry element
        :rtype: dict
        :returns: Entry fields as a dictionary
        """

        entry_id = get_element_attribute("data-id", entry_element)

        content_element = select_first_element("content", entry_element)
        content = ""
        for element in content_element.contents:

            if isinstance(element, bs4.element.NavigableString):
                content += element.string.strip()
            elif isinstance(element, bs4.element.Tag):
                content += handle_a_tag(element)
                content += handle_br_tag(element)

        author_nickname = get_element_attribute("data-author", entry_element)
        author_id = get_element_attribute("data-author-id", entry_element)
        author = Author(author_id, author_nickname)

        title = self.name

        timestamp = select_first_element("entry-date", entry_element).text

        is_edited = "~" in timestamp

        return {
            "entry_id": entry_id,
            "content": content,
            "author": author,
            "title": title,
            "timestamp": timestamp,
            "is_edited": is_edited,
        }

    def __str__(self) -> str:

        title_length = len(self.name)

        return f"\n{'=' * title_length}\n{self.name}\n{'=' * title_length}\n"
