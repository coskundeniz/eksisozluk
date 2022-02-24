from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Union, Generator

from pymongo import MongoClient
from pymongo.errors import PyMongoError, ServerSelectionTimeoutError
import sqlite3

from eksisozluk.constants import DB_NAME, DB_ADDR, DB_PORT
from eksisozluk.exceptions import EksiReaderDatabaseError
from eksisozluk.entry import Entry
from eksisozluk.title import Title
from eksisozluk.writer import writer


Entries = list[Entry]
Titles = list[Title]
EntryGenerator = Generator[Entry, None, None]
TitleGenerator = Generator[Title, None, None]
DBRecordGenerator = Generator[dict[str, str], None, None]
DBCursor = sqlite3.Connection.cursor


class Database(ABC):
    """Base db class"""

    def save(self, item) -> None:
        """Save item to the database

        :type item: dict
        :param item: Item to save into database
        """

        if "name" in item.keys():
            self.save_title(item)

        elif "entry_id" in item.keys():
            self.save_entry(item)

    @abstractmethod
    def save_title(self, item) -> None:
        """Save the given item to the titles database"""

    @abstractmethod
    def save_entry(self, item) -> None:
        """Save the given item to the entries database"""

    @abstractmethod
    def get_titles(self) -> DBRecordGenerator:
        """Return all titles from database"""

    @abstractmethod
    def get_entries(self) -> DBRecordGenerator:
        """Return all entries from database"""


class MongoDatabase(Database):
    """MongoDB database

    Raises EksiReaderDatabaseError if database connection
    is not established in 2 seconds.
    """

    def __init__(self):

        try:
            self.db_client = MongoClient(
                DB_ADDR, DB_PORT, serverSelectionTimeoutMS=2000
            )
            self.db_client.server_info()

        except ServerSelectionTimeoutError as exp:
            raise EksiReaderDatabaseError(
                "Failed to connect to database! Please check if database server is running."
            ) from exp

        self.db = self.db_client[DB_NAME]
        self.titles_db = self.db["favourite_titles"]
        self.entries_db = self.db["favourite_entries"]

    def save_title(self, item) -> None:
        """Save the given item to the titles database

        :type item: dict
        :param item: Title data to save into database
        """

        if not self.titles_db.find_one({"name": item["name"]}):
            self.titles_db.insert_one(item)
        else:
            writer.print(
                f"[error]Title '{item['name']}' already exists. Skipping...[/]"
            )

    def save_entry(self, item) -> None:
        """Save the given item to the entries database

        :type item: dict
        :param item: Entry data to save into database
        """

        if not self.entries_db.find_one({"entry_id": item["entry_id"]}):
            self.entries_db.insert_one(item)
        else:
            entry_id = item["entry_id"]
            writer.print(f"[error]Entry {entry_id} already exists. Skipping...[/]")

    def get_titles(self) -> DBRecordGenerator:
        """Return all titles from database

        :rtype: Generator
        :returns: All titles from database
        """

        titles = self.titles_db.find()
        for title in titles:
            yield title

    def get_entries(self) -> DBRecordGenerator:
        """Return all entries from database in reverse order

        :rtype: Generator
        :returns: All entries from database
        """

        entries = self.entries_db.find(sort=[("_id", -1)])
        for entry in entries:
            yield entry


class SQLiteDatabase(Database):
    """SQLite database

    Raises EksiReaderDatabaseError if database connection
    is not established.
    """

    def __init__(self):

        self._create_db_tables()

    def save_title(self, item) -> None:
        """Save the given item to the titles database

        :type item: dict
        :param item: Title data to save into database
        """

        with self._titles_db() as titledb_cursor:
            titledb_cursor.execute(
                "SELECT name FROM titles WHERE name=?", (item["name"],)
            )
            found = titledb_cursor.fetchone()

            if not found:
                titledb_cursor.execute(
                    "INSERT INTO titles (name, link) VALUES (?, ?)",
                    (item["name"], item["link"]),
                )
            else:
                writer.print(
                    f"[error]Title '{item['name']}' already exists. Skipping...[/]"
                )

    def save_entry(self, item) -> None:
        """Save the given item to the entries database

        :type item: dict
        :param item: Entry data to save into database
        """

        with self._entries_db() as entrydb_cursor:
            entrydb_cursor.execute(
                "SELECT entry_id FROM entries WHERE entry_id=?", (item["entry_id"],)
            )
            found = entrydb_cursor.fetchone()

            if not found:
                entrydb_cursor.execute(
                    "INSERT INTO entries (entry_id, title, content) VALUES (?, ?, ?)",
                    (item["entry_id"], item["title"], item["content"]),
                )
            else:
                entry_id = item["entry_id"]
                writer.print(f"[error]Entry {entry_id} already exists. Skipping...[/]")

    def get_titles(self) -> DBRecordGenerator:
        """Return all titles from database

        :rtype: Generator
        :returns: All titles from database
        """

        with self._titles_db() as titledb_cursor:
            titles = titledb_cursor.execute("SELECT * FROM titles;")

            for title in titles:
                yield {"name": title[1], "link": title[2]}

    def get_entries(self) -> DBRecordGenerator:
        """Return all entries from database in reverse order

        :rtype: Generator
        :returns: All entries from database
        """

        with self._entries_db() as entrydb_cursor:
            entries = entrydb_cursor.execute("SELECT * FROM entries ORDER BY id DESC;")

            for entry in entries:
                yield {
                    "entry_id": entry[1],
                    "title": entry[2],
                    "content": entry[3],
                }

    def _create_db_tables(self) -> None:
        """Create titles and entries database tables"""

        with self._titles_db() as titledb_cursor:
            titledb_cursor.execute(
                """CREATE TABLE IF NOT EXISTS titles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    link TEXT NOT NULL
                );"""
            )

        with self._entries_db() as entrydb_cursor:
            entrydb_cursor.execute(
                """CREATE TABLE IF NOT EXISTS entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entry_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL
                );"""
            )

    @contextmanager
    def _titles_db(self) -> DBCursor:
        """Context manager that returns titles db cursor

        :rtype: sqlite3.Connection.cursor
        :returns: Database connection cursor
        """

        titles_db = sqlite3.connect("favourite_titles.db")
        try:
            yield titles_db.cursor()

        except sqlite3.Error as exp:
            raise EksiReaderDatabaseError(
                "Failed to connect to titles database!"
            ) from exp

        finally:
            titles_db.commit()
            titles_db.close()

    @contextmanager
    def _entries_db(self) -> DBCursor:
        """Context manager that returns entries db cursor

        :rtype: sqlite3.Connection.cursor
        :returns: Database connection cursor
        """

        entries_db = sqlite3.connect("favourite_entries.db")
        try:
            yield entries_db.cursor()

        except sqlite3.Error as exp:
            raise EksiReaderDatabaseError(
                "Failed to connect to entries database!"
            ) from exp

        finally:
            entries_db.commit()
            entries_db.close()


class Storage(ABC):
    """Base storage class for favourite item persistence"""

    def __init__(self, database: Database):
        self.database = database

    @abstractmethod
    def save(self, items: list[Union[Entry, Title]]) -> None:
        """Save items to the database"""


class TitleStorage(Storage):
    """Storage class for favourite titles"""

    def __init__(self, database: Database):

        super().__init__(database)

    def save(self, titles: Titles) -> None:
        """Save selected titles to the database

        Raises EksiReaderDatabaseError if an error occurs
        during the save operation.

        :type titles: list
        :param titles: List of selected titles
        """

        try:
            for title in titles:
                self.database.save(title.get_db_data())

        except PyMongoError as exp:
            raise EksiReaderDatabaseError(exp) from exp

        writer.print("[favsuccess]Saved selected titles to the database[/] :thumbs_up:")

    def get_titles(self) -> DBRecordGenerator:
        """Get saved titles

        :rtype: Generator
        :returns: Titles saved as favourite
        """

        yield from self.database.get_titles()


class EntryStorage(Storage):
    """Storage class for favourite entries"""

    def __init__(self, database: Database):

        super().__init__(database)

    def save(self, entries: Entries) -> None:
        """Save selected entries to the database

        Raises EksiReaderDatabaseError if an error occurs
        during the save operation.

        :type entries: list
        :param entries: List of selected entries
        """

        try:
            for entry in entries:
                self.database.save(entry.get_db_data())

        except PyMongoError as exp:
            raise EksiReaderDatabaseError(exp) from exp

        writer.print(
            "[favsuccess]Saved selected entries to the database[/] :thumbs_up:"
        )

    def get_entries(self) -> DBRecordGenerator:
        """Get saved entries in reverse order

        :rtype: Generator
        :returns: Entries saved as favourite
        """

        yield from self.database.get_entries()


try:
    database = MongoDatabase()
except EksiReaderDatabaseError:
    database = SQLiteDatabase()


title_storage = TitleStorage(database=database)
entry_storage = EntryStorage(database=database)
