from datetime import datetime
from typing import Generator, Optional, TYPE_CHECKING

from eksisozluk.constants import PAGE_URL
from eksisozluk.channel import Channel
from eksisozluk.exceptions import (
    EksiReaderInvalidInputError,
    EksiReaderMissingInputError,
    EksiReaderNoChannelError,
)
from eksisozluk.parsing_utils import (
    parse_page,
    select_all_elements,
    get_element_text_content,
    find_element_with_id,
    get_element_attribute,
    create_driver,
)
from eksisozluk.storage import entry_storage, title_storage

from eksisozluk.author import Author
from eksisozluk.entry import Entry
from eksisozluk.title import Title
from eksisozluk.input_reader import reader
from eksisozluk.writer import writer


if TYPE_CHECKING:
    from selenium import webdriver


Channels = list[Channel]
Indexes = list[int]
TitleGenerator = Generator[Title, None, None]
EntryGenerator = Generator[Entry, None, None]


class EksiReader:
    """Main control point of the reader script"""

    def __init__(self) -> None:

        self.channels: Channels = []

    def get_channels(self) -> Channels:
        """Get all channels

        :rtype: list
        :returns: List of channels
        """

        unlisted_channels = (
            "/basliklar/gundem",
            "/debe",
            "/basliklar/sorunsal",
            "/basliklar/basiboslar",
            "/basliklar/tarihte-bugun",
        )

        for channel_link in unlisted_channels:
            channel_name = channel_link.rsplit("/", maxsplit=1)[-1]
            self.channels.append(Channel(channel_name, channel_link))

        channels_page = parse_page(PAGE_URL + "/kanallar")
        channels_container = find_element_with_id("channel-follow-list", channels_page)
        channel_elements = select_all_elements("index-link", channels_container)

        for channel in channel_elements:
            channel_name = get_element_text_content(channel)[1:]
            channel_link = get_element_attribute("href", channel)

            self.channels.append(Channel(channel_name, channel_link))

        return self.channels

    def get_selected_channel(self, channels: Channels) -> Channel:
        """List channels and get the selected channel

        Raises EksiReaderInvalidInputError if the given index is
        out of bounds, or invalid such as a character.

        :type channels: list
        :param channels: List of channels
        :rtype: Channel
        :returns: Selected channel
        """

        for index, channel in enumerate(channels, start=1):
            writer.print(
                f"[indexbracket][[/]{index:2}[indexbracket]][/] {channel}",
                end=" ",
            )
            if index % 5 == 0:
                writer.print()

        try:
            selected = int(reader.get_input("\n\n[userprompt]Enter channel index: [/]"))

            if not 0 < selected <= len(channels):
                raise EksiReaderInvalidInputError("Invalid index!")

        except ValueError as exp:
            raise EksiReaderInvalidInputError("Invalid input!") from exp

        return channels[selected - 1]

    def get_channel_by_name(self, channel_name: str) -> Channel:
        """Find and return channel by name

        If there is no channel with the given name,
        EksiReaderNoChannelError is raised.

        :type channel_name: str
        :param channel_name: Name of the channel
        :rtype: Channel
        :returns: Channel found
        """

        for channel in self.channels:
            if channel.name == channel_name:
                return channel

        raise EksiReaderNoChannelError(f"Could not found channel with name: {channel_name}")

    def get_channel_titles(self, channel: Channel) -> TitleGenerator:
        """Get all titles for the given channel

        :type channel: Channel
        :param channel: Channel object
        :rtype: Generator
        :returns: List of titles under the given channel
        """

        return channel.get_titles()

    def get_selected_titles(self, titles: TitleGenerator) -> Indexes:
        """List titles and get the selected indexes

        :type titles: Generator
        :param titles: List of titles
        :rtype: list
        :returns: Selected title indexes
        """

        for index, title in enumerate(titles, start=1):
            writer.print(
                f"[indexbracket][[/]{index:3}[indexbracket]][/] [titletext]{title.name}[/]"
            )

        return self.get_selected_indexes(prompt="Enter requested indexes")

    def get_selected_title_entries(
        self, channel: Channel, indexes: Indexes, faventry_enabled: bool
    ) -> None:
        """Get entries from the selected titles under a channel

        :type channel: Channel
        :param channel: Channel object
        :type indexes: list
        :param indexes: Selected title indexes
        :type faventry_enabled: bool
        :param faventry_enabled: True if faventry option is passed, False otherwise
        """

        titles = channel.get_selected_titles(indexes)

        for title in titles:
            self._get_title_entries(title, faventry_enabled)

    def get_selected_entries(self, title: Title, entry_indexes: Indexes) -> EntryGenerator:
        """Get selected entries from title to add as favourites

        :type title: Title
        :param title: Title object
        :type entry_indexes: list
        :param entry_indexes: Selected entry indexes to add as favourite
        :rtype: Generator
        :returns: List of selected entries of the given title
        """

        yield from title.get_selected_entries(entry_indexes)

    def show_saved_entries(self) -> None:
        """Show entries saved as favourite"""

        entries = entry_storage.get_entries()

        writer.console.rule(f"{' ⭐ ' * 7}")
        for entry in entries:
            writer.print(f"[authorentrytitle]>>> {entry['title']}[/]")
            writer.print(f"[entrytext]{entry['content']}[/]")
            writer.console.rule()

    def get_favourite_title_entries(self, faventry_enabled) -> None:
        """Show entries from favourite titles

        :type faventry_enabled: bool
        :param faventry_enabled: True if faventry option is passed, False otherwise
        """

        with writer.console.status("[waitspinner]Getting entries from favourite titles..."):
            driver = create_driver()

        for item in title_storage.get_titles():
            today = datetime.today().strftime("%Y-%m-%d")
            link = f"{item['link']}?day={today}"
            title = Title(item["name"], link)

            self._get_title_entries(title, faventry_enabled, entries_for_today=True, driver=driver)

    def _get_title_entries(
        self,
        title: Title,
        faventry_enabled: bool,
        entries_for_today: Optional[bool] = False,
        driver: Optional["webdriver"] = None,
    ) -> None:
        """Show title entries

        If faventry option is passed, entry indexes are asked from
        user to save to the database as favourite.

        :type title: Title
        :param title: Title object
        :type faventry_enabled: bool
        :param faventry_enabled: True if faventry option is passed, False otherwise
        :type entries_for_today: bool
        :param entries_for_today: Whether only today's entries requested
        :type driver: selenium.webdriver
        :param driver: Selenium webdriver instance
        """

        writer.print(f"[titlebanner]{title}[/]")

        entries = title.get_entries(entries_for_today, driver)

        for index, entry in enumerate(entries, start=1):

            entry_index_str = self._prepare_index_str(index, faventry_enabled)
            writer.print(f"{entry_index_str}[entrytext]{entry}[/]")
            writer.console.rule()

        if faventry_enabled:
            try:
                selected_entry_indexes = self.get_selected_indexes(
                    prompt="⭐ Enter entry indexes to favourite"
                )
                selected_entries = self.get_selected_entries(title, selected_entry_indexes)
                entry_storage.save(selected_entries)

            except EksiReaderMissingInputError:
                pass

    def save_favourite_titles(self, channel: Channel) -> None:
        """Save selected titles to database as favourite

        :type channel: Channel
        :param channel: Channel object
        """

        indexes = self.get_selected_indexes(prompt="⭐ Enter title indexes to favourite")
        titles = channel.get_selected_titles(indexes)
        title_storage.save(titles)

    @staticmethod
    def get_author_entries() -> None:
        """Show entries for author"""

        nickname = reader.get_input("\n[userprompt]Enter author nickname: [/]")

        author = Author("", nickname)

        entries = author.get_entries()

        writer.print()
        for entry in entries:
            writer.print(f"[authorentrytitle]>>> {entry.title}[/]")
            writer.print(f"[entrytext]{entry}[/]")
            writer.console.rule()

    @staticmethod
    def get_selected_indexes(*, prompt) -> Indexes:
        """Get selected indexes from user

        Raises EksiReaderMissingInputError if no input is given.

        :rtype: list
        :returns: List of indexes
        """

        indexes = reader.get_input(f"\n[userprompt]{prompt}: [/]")

        selected_indexes = [int(index) for index in indexes.split() if index.isdigit()]

        if not selected_indexes:
            raise EksiReaderMissingInputError("No index selected!")

        return selected_indexes

    @staticmethod
    def _prepare_index_str(index, faventry_enabled):
        """Prepare the representation string for the index

        :type faventry_enabled: bool
        :param faventry_enabled: True if faventry option is passed, False otherwise
        """

        digit_len = len(str(index))
        entry_index_str = (
            f"[indexbracket][[/]{index:{digit_len}}[indexbracket]][/] " if faventry_enabled else ""
        )

        return entry_index_str
