from abc import ABC, abstractmethod
from typing import Optional

from rich.console import Console

from eksisozluk.theme_config import THEMES, ThemeIndex


class Writer(ABC):
    """Base output interface"""

    @abstractmethod
    def print(self, message: Optional[str] = "", *args, **kwargs) -> None:
        """Print the given message"""


class ConsoleWriter(Writer):
    """Interface for printing to the console"""

    def __init__(self) -> None:

        self.console = Console(theme=THEMES[ThemeIndex.DEFAULT])

    def print(self, message: Optional[str] = "", *args, **kwargs) -> None:
        """Print the given message

        :type message: str
        :param message: Message to print
        """

        self.console.print(message, *args, **kwargs)

    def set_theme(self, theme_index: ThemeIndex) -> None:
        """Set console theme

        :type theme_index: ThemeIndex
        :param theme_index: Theme index to select
        """

        new_theme = THEMES.get(theme_index, THEMES[ThemeIndex.DEFAULT])
        self.console = Console(theme=new_theme)


writer = ConsoleWriter()
