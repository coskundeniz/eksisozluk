from typing import Optional

from eksisozluk.author import Author


class Entry:
    """Entry class contains entry content with author and timestamp information

    :type entry_id: str
    :param entry_id: Unique entry id
    :type content: str
    :param content: Entry text content
    :type author: Author
    :param author: Author of the entry
    :type title: str
    :param title: Title which entry belongs
    :type timestamp: str
    :param timestamp: Timestamp of entry
    :type is_edited: bool
    :param is_edited: Whether entry is edited
    """

    def __init__(
        self,
        entry_id: str,
        content: str,
        author: Author,
        title: str,
        timestamp: str,
        is_edited: Optional[bool] = False,
    ) -> None:

        self.entry_id = entry_id
        self.content = content
        self.author = author
        self.title = title
        self.timestamp = timestamp
        self.is_edited = is_edited

    def get_db_data(self) -> dict[str, str]:
        """Return dictionary object to save to the database

        :rtype: dict
        :returns: Dictionary with entry_id, title and content keys
        """

        return {
            "entry_id": self.entry_id,
            "title": self.title,
            "content": str(self),
        }

    def __str__(self) -> str:

        return f"{self.content} [timestamp]|{self.timestamp}|[/] {self.author}"
