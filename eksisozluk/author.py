from typing import Generator, Optional, TYPE_CHECKING

import bs4

from eksisozluk.constants import PAGE_URL
from eksisozluk.exceptions import EksiReaderPageRequestError
from eksisozluk.parsing_utils import (
    parse_page,
    find_element_with_id,
    select_all_elements,
    select_first_element,
    handle_a_tag,
    handle_br_tag,
    get_element_attribute,
    create_driver,
    wait_for_element_to_load,
    click_load_more,
    close_cookie_dialog,
)
from eksisozluk.input_reader import reader
from eksisozluk.writer import writer


if TYPE_CHECKING:
    import selenium
    from eksisozluk.entry import Entry

EntryGenerator = Generator["Entry", None, None]


class Author:
    """Author representation consists of author id and nickname

    :type author_id: str
    :param author_id: Unique id of the author
    ::type nickname: str
    :param nickname: Nickname of the author
    """

    def __init__(self, author_id: str, nickname: str) -> None:

        self.author_id = author_id
        self.nickname = nickname
        self.link = f"/biri/{self.nickname.strip().replace(' ', '-')}"
        self._entries: list[Entry] = []
        self._driver: Optional["selenium.webdriver"] = None

    def get_entries(self) -> EntryGenerator:
        """Get all entries for author

        :rtype: Generator
        :returns: List of entries
        """

        author_page_link = f"{PAGE_URL}{self.link}"

        # check if author exists
        try:
            author_page = parse_page(author_page_link)
        except EksiReaderPageRequestError as exp:
            raise SystemExit(
                f"Couldn't found an author with nickname: {self.nickname}"
            ) from exp

        total_author_entries = int(
            find_element_with_id("entry-count-total", author_page).text
        )

        with writer.console.status(
            f"[waitspinner]Getting entries for {self.nickname}..."
        ):
            self._load_author_page(author_page_link)
            close_cookie_dialog(self._driver)

        while len(self._entries) < total_author_entries:

            yield from self._get_entries_partial()

            load_more = reader.get_input(
                "\n[loadmore]Load more entries [ Enter | q ] [/]"
            )
            if not load_more:
                click_load_more(self._driver)
            else:
                break

        self._driver.quit()

    def _get_entries_partial(self) -> EntryGenerator:
        """Get entries from the current page

        :rtype: Generator
        :returns: List of entries
        """

        from eksisozluk.entry import Entry

        entries_container = wait_for_element_to_load(self._driver, selector="#topic")
        items = select_all_elements("topic-item", entries_container)[-10:]

        for item in items:

            title_element = find_element_with_id("title", item)
            title = get_element_attribute("data-title", title_element)
            entry_container = find_element_with_id("entry-item-list", item)
            content_element = select_first_element("content", entry_container)

            content = ""
            for element in content_element.contents:

                if isinstance(element, bs4.element.NavigableString):
                    content += element.string.strip()
                elif isinstance(element, bs4.element.Tag):
                    content += handle_a_tag(element)
                    content += handle_br_tag(element)

            timestamp = select_first_element("entry-date", entry_container).text
            is_edited = "~" in timestamp

            entry = Entry(
                entry_id="",
                content=content,
                author=self,
                title=title,
                timestamp=timestamp,
                is_edited=is_edited,
            )
            self._entries.append(entry)

            yield entry

    def _load_author_page(self, link):
        """Load author main page

        :type link: str
        :param link: Author page link
        :rtype: Generator
        :returns: List of entries
        """

        self._driver = create_driver()
        self._driver.get(link)

        wait_for_element_to_load(self._driver, selector="#topic")

    def __str__(self) -> str:

        return f"[author]<< {self.nickname} >>[/]"
