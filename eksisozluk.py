import sys
import random
from os import path
from argparse import ArgumentParser
from collections import defaultdict, namedtuple

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Please run 'pipenv install' or 'pip install -r requirements.txt'")
    sys.exit(1)


PAGE_URL = 'https://www.eksisozluk.com'
entry_index_map = {}

USER_AGENT_LIST = [
    #Chrome
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36",
    "Mozilla/5.0 (Windows NT 5.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36",
    #Firefox
    "Mozilla/4.0 (compatible; MSIE 9.0; Windows NT 6.1)",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko",
    "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0)",
    "Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko",
    "Mozilla/5.0 (Windows NT 6.2; WOW64; Trident/7.0; rv:11.0) like Gecko",
    "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko",
    "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.0; Trident/5.0)",
    "Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; rv:11.0) like Gecko",
    "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64; Trident/7.0; rv:11.0) like Gecko",
    "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)",
    "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)",
    "Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729)",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0"
]

def parse_page(url):
    """Open and parse page content

    :type url: str
    :param url: url of the page to be parsed
    :rtype: BeautifulSoup
    :returns: BeautifulSoup object
    """

    # pick a random user agent
    user_agent = random.choice(USER_AGENT_LIST)
    headers = {"User-Agent": user_agent}

    response = requests.get(url, headers=headers)

    parsed_page = BeautifulSoup(response.content, "html.parser")

    return parsed_page


def get_topics(url=None):
    """Get list of popular topics

    :type url: string
    :param url: url of the page to be parsed. If called without url
    main url is opened.
    :rtype: list
    :returns: list of extracted results that contains a tuple for each topic
    """

    Topic = namedtuple('Topic', 'index, link, name, entry_count')
    results = []

    parsed_page = parse_page(PAGE_URL) if url is None else parse_page(url)

    if url:
        topic_list = parsed_page.select('section#content-body ul.topic-list')[0]
    else:
        topic_list = parsed_page.find('ul', 'topic-list partial')

    links = topic_list('a')

    for index, link in enumerate(links):

        try:
            topic_link = link['href']
            topic_name = link.contents[0]

            if len(link.contents) == 2:  # [topic_name, entry_count]
                if "," in link.contents[1].string:
                    splitted_count = link.contents[1].string.split(",")
                    topic_entry_count = int(splitted_count[0]) * 1000 + int(splitted_count[1][0]) * 100
                else:
                    topic_entry_count = int(link.contents[1].string)

                topic = Topic(index=index+1,
                            link=topic_link,
                            name=topic_name,
                            entry_count=topic_entry_count)
                results.append(topic)
            else:  # [topic_name]
                topic = Topic(index=index+1,
                            link=topic_link,
                            name=topic_name,
                            entry_count=0)

                results.append(topic)

        except KeyError:
            pass

    return results


def get_entries_for_topic(topic_link, entry_count_per_topic=10):
    """Get last entries for a topic. Number of entries is ten by default, or
       less than ten as requested count per topic.

    :type topic_link: string
    :param topic_link: link of topic
    :type entry_count_per_topic: integer
    :param entry_count_per_topic: number of entries requested per topic
    :rtype: list
    :returns: list of entries for a topic
    """

    # open and parse page for given topic_link
    topic_page_content = parse_page(PAGE_URL + topic_link)
    entry_list_container = topic_page_content.find('ul', {'id': 'entry-item-list'})
    entries_for_topic = entry_list_container.findAll('div', 'content')[:entry_count_per_topic]
    authors = entry_list_container.findAll('a', {'class', 'entry-author'})[:entry_count_per_topic]

    return [(entry[0].text, entry[1].text) for entry in zip(entries_for_topic, authors)]


def get_topics_sorted_by_entry_count(results):
    """Get first ten topics according to entry count

    :type results: list
    :param results: list of topic results
    :rtype: list
    :returns: list of topics sorted by entry count
    """

    return sorted(results, key=lambda x: x.entry_count, reverse=True)[:10]


def get_selected_indexes():
    """Get selected indexes from user

    :rtype: list
    :returns: list of indexes
    """

    topic_indexes = input("\nEnter requested indexes: ")

    selected_topic_indexes = [int(index) for index in topic_indexes.split()
                                            if index.isdigit()]

    if not selected_topic_indexes:
        print("\nNo index selected!")
        sys.exit(1)

    return selected_topic_indexes


def get_entries_for_selected_topics(results, selected_topic_indexes, entry_count_per_topic):
    """Get entries for selected topics

    :type results: list
    :param results: list of topic results
    :type selected_topic_indexes: list
    :param selected_topic_indexes: list of selected indexes
    :type entry_count_per_topic: integer
    :param entry_count_per_topic: number of entries requested per topic (default=10)
    :rtype: dictionary
    :returns: entries for selected topics as name: entry_list pairs
    """

    selected_topic_entries = defaultdict(list)

    for topic_index in selected_topic_indexes:
        for topic in results:
            if topic_index == topic.index:
                topic_entries = get_entries_for_topic(topic.link, entry_count_per_topic)
                selected_topic_entries[topic.name] = topic_entries

    return selected_topic_entries


def add_to_favourite_topics(topic_links):
    """Add selected topics to favourites

    :type topic_links: list
    :param topic_links: list of selected topics
    """

    filename = "favourite_topics.txt"

    existing_topics = read_favourite_topics(filename)

    with open(filename, "a") as favs:

        for topic_link, topic_name in topic_links:
            line = topic_link + "," + topic_name + "\n"
            if line not in existing_topics:
                favs.write(line)


def read_favourite_topics(filename):
    """Read favourite topics from file

    :type filename: string
    :param filename: File name
    :rtype: generator
    :returns: List of favourite topics saved
    """

    if path.exists(filename):
        with open(filename, "r") as fav_topics_file:
            for topic in fav_topics_file.readlines():
                yield (topic.split(",")[0], topic.split(",")[1])
    else:
        print("There is no topic saved to favourites!")


def add_to_favourite_entries(entry_indexes):
    """Save selected entries to a file

    :type entry_indexes: list
    :param entry_indexes: list of selected entry indexes
    """

    filename = "favourite_entries.txt"

    with open(filename, "a") as favourite_entries:

        for index in entry_indexes:
            favourite_entries.write("::: %s ::: %s << %s >>\n%s\n\n" % (entry_index_map[str(index)][2],
                                                                        entry_index_map[str(index)][0],
                                                                        entry_index_map[str(index)][1],
                                                                        "-"*100))

    print("Selected entries were added to %s" % filename)


def list_topics(topic_results, print_top_ten=False):
    """Print currently popular topics

    :type topic_results: list
    :param topic_results: List of topics
    :type print_top_ten: bool
    :param print_top_ten: If True, print top ten entries according to entry count
    """

    if print_top_ten:
        most_entry_topics = get_topics_sorted_by_entry_count(topic_results)

        for index, top_topic in enumerate(most_entry_topics):
            print(index+1, top_topic.name, top_topic.entry_count)

    print()
    for result in topic_results:
        print(result.index, result.name)


def update_entry_index_map(entry_index, entry_content, entry_author, entry_topic):
    """Update entry index map with the following item format

    index: (entry_content, entry_author, entry_topic)

    :type entry_index: integer
    :param entry_index: Index of entry
    :type entry_content: string
    :param entry_content: Text content of entry
    :type entry_author: string
    :param entry_author: Author of entry
    :type entry_topic: string
    :param entry_topic: Topic of entry
    """

    global entry_index_map

    entry_index_map.update({str(entry_index): (entry_content, entry_author, entry_topic)})


def get_all_titles():
    """Get all titles

    :rtype: dictionary
    :returns: titles as index: link pairs
    """

    parsed_page = parse_page(PAGE_URL)

    titles = parsed_page.select('a[href^="/basliklar/kanal"]')

    indexed_titles = {index+1: (title.getText(), title.get("href"))
                                for index, title in enumerate(titles)}

    return indexed_titles


def get_selected_title(titles):
    """List titles, and get the selected title link

    :type titles: dictionary
    :param titles: indexed titles
    :rtype: string
    :returns: relative link of selected title
    """

    for index, title_info in titles.items():
        print("{:2} - {:13}".format(index, title_info[0]), end=' ')
        if index % 4 == 0:
            print()

    try:
        selected = int(input("\nSelect a title: "))

        if selected <= 0 or selected > len(titles):
            raise ValueError
    except ValueError:
        print("Invalid index!")
        sys.exit(1)

    title_link = titles[selected][1]

    return title_link


def print_results(results, save_favourite_entries=False):
    """Print entries for selected topics

    :type results: dictionary
    :param results: entries for selected topics as name: entry_list dict
    :type save_favourite_entries: bool
    :param save_favourite_entries: Whether selected entries will be saved or not
    """

    if save_favourite_entries:
        num_of_total_entries = 0
        for name, t_entries in results.items():
            num_of_total_entries += len(t_entries)

        entry_counter = (n+1 for n in range(num_of_total_entries))

    for topic_name, topic_entries in results.items():

        print("#" * len(topic_name))
        print(topic_name.rstrip())
        print("#" * len(topic_name))

        for index, entry in enumerate(topic_entries):
            entry_content = entry[0].strip()
            entry_author = entry[1]

            if save_favourite_entries:
                entry_index = next(entry_counter)
                update_entry_index_map(entry_index, entry_content, entry_author, topic_name.rstrip())

                print("\n%2s - %s << %s >> [%s]" % (index+1, entry_content, entry_author, entry_index))
            else:
                print("\n%2s - %s << %s >>" % (index+1, entry_content, entry_author))

            print("-" * 80)


def get_arg_parser():
    """Get argument parser

    :rtype: ArgumentParser
    :returns: ArgumentParser object
    """

    arg_parser = ArgumentParser()
    arg_parser.add_argument("-c", "--count", default=10, type=int, dest="entry_count_per_topic",
                            help="Number of entries for a topic to extract")
    arg_parser.add_argument("-sf", "--fav", action='store_true',
                            help="Add selected topics to favourites")
    arg_parser.add_argument("-gf", "--getfavs", action='store_true',
                            help="Get entries from favourite topics")
    arg_parser.add_argument("-se", "--faventry", action='store_true',
                            help="Add selected entries to favourites")
    arg_parser.add_argument("-t", "--titles", action='store_true',
                            help="Get topics from other titles")

    return arg_parser


if __name__ == '__main__':

    arg_parser = get_arg_parser()
    args = arg_parser.parse_args()

    if args.titles:
        titles = get_all_titles()
        selected_title = get_selected_title(titles)
        title_url = PAGE_URL + selected_title

        topic_results = get_topics(url=title_url)
    else:
        topic_results = get_topics()

    if args.fav:

        list_topics(topic_results)

        favourite_topic_indexes = get_selected_indexes()

        topics_selected = [(topic_results[index-1].name, topic_results[index-1].link)
                            for index in favourite_topic_indexes]
        add_to_favourite_topics(topics_selected)

    elif args.getfavs:

        favourite_topic_entries = defaultdict(list)

        favourite_topics = read_favourite_topics("favourite_topics.txt")

        for topic_name, topic_link in favourite_topics:
            favourite_topic_entries[topic_name] = get_entries_for_topic(topic_link)

        print_results(favourite_topic_entries)

    else:

        list_topics(topic_results, print_top_ten=True)

        requested_topic_indexes = get_selected_indexes()
        requested_topic_entries = get_entries_for_selected_topics(topic_results,
                                                                  requested_topic_indexes,
                                                                  args.entry_count_per_topic)

        if args.faventry:

            print_results(requested_topic_entries, save_favourite_entries=True)
            entry_indexes_to_save = get_selected_indexes()
            add_to_favourite_entries(entry_indexes_to_save)

        else:
            print_results(requested_topic_entries)
