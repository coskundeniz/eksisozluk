from abc import ABC, abstractmethod
from typing import Optional

from rich.console import Console

from eksisozluk.theme_config import THEMES, ThemeIndex


class InputReader(ABC):
    """Base input interface"""

    @abstractmethod
    def get_input(self, prompt: Optional[str] = "") -> str:
        """Read input value"""


class ConsoleInputReader(InputReader):
    """Interface for reading user input from console"""

    def __init__(self) -> None:

        self.console = Console(theme=THEMES[ThemeIndex.DEFAULT])

    def get_input(self, prompt: Optional[str] = "") -> str:
        """Get input value from user

        :type prompt: str
        :param prompt: Prompt to show user
        :rtype: str
        :returns: User input
        """

        return self.console.input(prompt)

    def set_theme(self, theme_index: ThemeIndex) -> None:
        """Set console theme

        :type theme_index: ThemeIndex
        :param theme_index: Theme index to set
        """

        new_theme = THEMES.get(theme_index, THEMES[ThemeIndex.DEFAULT])
        self.console = Console(theme=new_theme)


reader = ConsoleInputReader()
