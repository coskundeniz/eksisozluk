from abc import ABC, abstractmethod
from typing import Any, Generator

from pymongo import MongoClient
from pymongo.errors import PyMongoError, ServerSelectionTimeoutError

from eksisozluk.constants import DB_NAME, DB_ADDR, DB_PORT
from eksisozluk.exceptions import EksiReaderDatabaseError
from eksisozluk.entry import Entry
from eksisozluk.title import Title
from eksisozluk.writer import writer


Entries = list[Entry]
Titles = list[Title]
EntryGenerator = Generator[Entry, None, None]
TitleGenerator = Generator[Title, None, None]


class MongoDatabase:
    """MongoDB database

    Raises EksiReaderDatabaseError if database connection
    is not established in 3 seconds.
    """

    def __init__(self):

        try:
            self.db_client = MongoClient(
                DB_ADDR, DB_PORT, serverSelectionTimeoutMS=3000
            )
            self.db_client.server_info()

        except ServerSelectionTimeoutError as exp:
            raise EksiReaderDatabaseError(
                "Failed to connect to database! Please check if database server is running."
            ) from exp

        self.db = self.db_client[DB_NAME]


class Storage(ABC):
    """Base storage class for favourite item persistence"""

    def __init__(self, database: MongoDatabase):
        self.eksidb = database.db

    @abstractmethod
    def save(self, items: list[Any]):
        """Save items to the database"""


class TitleStorage(Storage):
    """Storage class for favourite titles"""

    def __init__(self, database: MongoDatabase):

        super().__init__(database)
        self.titles_db = self.eksidb["favourite_titles"]

    def save(self, titles: Titles) -> None:
        """Save selected titles to the database

        :type titles: list
        :param titles: List of selected titles
        """

        try:
            for title in titles:
                if not self.titles_db.find_one({"name": title.name}):
                    self.titles_db.insert_one(title.get_db_data())
                else:
                    writer.print(
                        f"[error]Title '{title.name}' already exists. Skipping...[/]"
                    )

        except PyMongoError as exp:
            raise EksiReaderDatabaseError(exp) from exp

        writer.print("[favsuccess]Saved selected titles to the database[/] :thumbs_up:")

    def get_titles(self) -> TitleGenerator:
        """Get saved titles

        :rtype: Generator
        :returns: List of titles saved as favourite
        """

        titles = self.titles_db.find()
        for title in titles:
            yield title


class EntryStorage(Storage):
    """Storage class for favourite entries"""

    def __init__(self, database: MongoDatabase):

        super().__init__(database)
        self.entries_db = self.eksidb["favourite_entries"]

    def save(self, entries: Entries) -> None:
        """Save selected entries to the database

        :type entries: list
        :param entries: List of selected entries
        """

        try:
            for entry in entries:
                if not self.entries_db.find_one({"entry_id": entry.entry_id}):
                    self.entries_db.insert_one(entry.get_db_data())
                else:
                    entry_id = entry.entry_id
                    author = entry.author.nickname
                    writer.print(
                        f"[error]Entry {entry_id} by {author} already exists. Skipping...[/]"
                    )

        except PyMongoError as exp:
            raise EksiReaderDatabaseError(exp) from exp

        writer.print(
            "[favsuccess]Saved selected entries to the database[/] :thumbs_up:"
        )

    def get_entries(self) -> EntryGenerator:
        """Get saved entries in reverse order

        :rtype: Generator
        :returns: List of entries saved as favourite
        """

        entries = self.entries_db.find(sort=[("_id", -1)])
        for entry in entries:
            yield entry


try:
    mongo_database = MongoDatabase()

except EksiReaderDatabaseError as exp:
    writer.print(f"[error]{exp}[/]")
    raise SystemExit() from exp


title_storage = TitleStorage(database=mongo_database)
entry_storage = EntryStorage(database=mongo_database)
