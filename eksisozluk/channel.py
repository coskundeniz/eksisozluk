from typing import Generator, Optional

from eksisozluk.constants import PAGE_URL
from eksisozluk.parsing_utils import (
    parse_page,
    find_element_with_id,
    select_first_element,
    get_elements_with_css_selector,
)
from eksisozluk.input_reader import reader
from eksisozluk.title import Title


Titles = list[Title]
Indexes = list[int]
TitleGenerator = Generator[Title, None, None]


class Channel:
    """Channel class represents a main topic like news, music etc.

    :type name: str
    :param name: Name of the channel
    :type link: str
    :param link: Link of the channel
    """

    def __init__(self, name: str, link: str) -> None:

        self.name = name
        self.link = link
        self._titles: Optional[Titles] = []

    def get_titles(self) -> TitleGenerator:
        """Get all titles

        :rtype: Generator
        :returns: All titles under the channel
        """

        channels_page = parse_page(f"{PAGE_URL}/{self.link}")
        content_element = find_element_with_id("content", channels_page)
        description = select_first_element("topic-list-description", content_element)
        if description:
            total_titles = int(description.text.split()[0])
        else:
            total_titles = 1

        page_number = 1

        while len(self) < total_titles:

            yield from self._get_titles_on_page(page_number)

            load_more = reader.get_input(
                f"\n[loadmore](Showing {len(self)}/{total_titles}) "
                f"Load more titles [ Enter | q ] [/]"
            )
            if not load_more:
                page_number += 1
            else:
                break

    def get_selected_titles(self, selected_indexes: Indexes) -> Titles:
        """Get titles for the given indexes

        :type selected_indexes: list
        :param selected_indexes: List of indexes
        :rtype: list
        :returns: List of selected titles
        """

        return [self._titles[index - 1] for index in selected_indexes]

    def _get_titles_on_page(self, page_number: int) -> TitleGenerator:
        """Get titles for the given page

        :type page_number: int
        :param page_number: Page number for the request
        :rtype: Generator
        :returns: All titles for the given page
        """

        channels_page = parse_page(f"{PAGE_URL}/{self.link}?p={page_number}")
        content_element = find_element_with_id("content", channels_page)
        title_elements = get_elements_with_css_selector("li > a", content_element)

        for element in title_elements:

            if element.select("small"):
                # remove the today's entry count from the title text
                splitted_title_text = element.text.strip().split()
                name = " ".join(splitted_title_text[:-1])

                entry_count_text = splitted_title_text[-1]
                if "," in entry_count_text:
                    splitted_count = entry_count_text.split(",")
                    entry_count = (
                        int(splitted_count[0]) * 1000 + int(splitted_count[1][0]) * 100
                    )
                else:
                    entry_count = int(entry_count_text)
            else:
                name = element.text.strip()
                entry_count = 0

            link = element["href"].split("?")[0]
            title = Title(name, link, entry_count)
            self._titles.append(title)

            yield title

    def __len__(self) -> int:

        return len(self._titles)

    def __str__(self) -> str:

        return f"[channelname]{self.name:13}[/]"
