from argparse import ArgumentParser

from eksisozluk.eksireader import EksiReader
from eksisozluk.exceptions import (
    EksiReaderException,
    EksiReaderInvalidInputError,
    EksiReaderMissingInputError,
    EksiReaderNoChannelError,
    EksiReaderDatabaseError,
)
from eksisozluk.writer import writer
from eksisozluk.input_reader import reader


def handle_exception(exp: EksiReaderException) -> None:
    """Print the error message and exit

    :type exp: EksiReaderException
    :param exp: Exception raised by the reader
    """

    writer.print(f"[error]{exp}[/]")
    raise SystemExit() from exp


def get_arg_parser() -> ArgumentParser:
    """Get argument parser

    :rtype: ArgumentParser
    :returns: ArgumentParser object
    """

    arg_parser = ArgumentParser()
    arg_parser.add_argument(
        "-ch", "--channels", action="store_true", help="Get titles from other channels"
    )
    arg_parser.add_argument(
        "-ae", "--author_entries", action="store_true", help="Get author entries"
    )
    arg_parser.add_argument(
        "-ft",
        "--favtitle",
        action="store_true",
        help="Add selected titles to favourites",
    )
    arg_parser.add_argument(
        "-lfte",
        "--listfavtitleentry",
        action="store_true",
        help="Get today's entries from favourite titles",
    )
    arg_parser.add_argument(
        "-fe",
        "--faventry",
        action="store_true",
        help="Add selected entries to favourites",
    )
    arg_parser.add_argument(
        "-lfe",
        "--listfaventry",
        action="store_true",
        help="Show entries saved as favourite",
    )
    arg_parser.add_argument(
        "-th",
        "--theme",
        default=1,
        type=int,
        help="Change theme",
    )

    return arg_parser


def main():
    """Main entry point for the eksisozluk reader"""

    arg_parser = get_arg_parser()
    args = arg_parser.parse_args()

    if args.theme:
        writer.set_theme(args.theme)
        reader.set_theme(args.theme)

    eksireader = EksiReader()

    faventry_enabled = True if args.faventry else False

    channels = eksireader.get_channels()

    try:
        if args.listfaventry:
            eksireader.show_saved_entries()

        elif args.listfavtitleentry:
            eksireader.get_favourite_title_entries(faventry_enabled)

        else:
            if args.author_entries:
                eksireader.get_author_entries()

            else:
                if args.channels:
                    selected_channel = eksireader.get_selected_channel(channels)
                else:
                    # get entries from default channel
                    selected_channel = eksireader.get_channel_by_name("gundem")

                titles = eksireader.get_channel_titles(selected_channel)
                selected_title_indexes = eksireader.get_selected_titles(titles)
                eksireader.get_selected_title_entries(
                    selected_channel, selected_title_indexes, faventry_enabled
                )

                if args.favtitle:
                    eksireader.save_favourite_titles(selected_channel)

    except (
        EksiReaderInvalidInputError,
        EksiReaderMissingInputError,
        EksiReaderNoChannelError,
        EksiReaderDatabaseError,
    ) as exp:
        handle_exception(exp)

    except EksiReaderException as exp:
        handle_exception(exp)


if __name__ == "__main__":

    main()
