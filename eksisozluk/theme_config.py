from enum import IntEnum

from rich.theme import Theme


custom_theme_default = Theme(
    {
        "repr.number": "#81C14B",
        "rule.line": "bright_yellow",
        "repr.url": "not underline",
        "repr.call": "not bold",
        "repr.brace": "not bold",
        "indexbracket": "bold dark_green",
        "entrytext": "dark_olive_green3",
        "titletext": "#E0A734",
        "titlebanner": "bold bright_yellow",
        "channelname": "#E0A734",
        "userprompt": "bold #E0A734",
        "loadmore": "#81C14B",
        "timestamp": "not bold dark_orange3",
        "authorentrytitle": "orange1",
        "author": "cyan",
        "favsuccess": "bold bright_green",
        "waitspinner": "bold bright_green",
        "error": "bold bright_red",
    }
)


custom_theme_green_variants = Theme(
    {
        "repr.number": "#81C14B",
        "rule.line": "dark_sea_green4",
        "repr.url": "not underline",
        "repr.call": "not bold",
        "repr.brace": "not bold",
        "indexbracket": "bold dark_green",
        "entrytext": "chartreuse3",
        "titletext": "green3",
        "titlebanner": "bold spring_green3",
        "channelname": "green3",
        "userprompt": "bold green3",
        "loadmore": "#81C14B",
        "timestamp": "not bold dark_green",
        "authorentrytitle": "bold spring_green3",
        "author": "green4",
        "favsuccess": "bold bright_green",
        "waitspinner": "bold bright_green",
        "error": "bold bright_green",
    }
)


class ThemeIndex(IntEnum):

    DEFAULT = 1
    GREEN = 2


THEMES = {
    ThemeIndex.DEFAULT: custom_theme_default,
    ThemeIndex.GREEN: custom_theme_green_variants,
}
