#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os.path
from collections import defaultdict
from argparse import ArgumentParser
from urllib2 import urlopen
from bs4 import BeautifulSoup


PAGE_URL = 'https://eksisozluk.com'


def parse_page(page_url):
    """Open and parse page content

    :rtype: object
    :returns: parsed page as a BeautifulSoup object
    """

    page = urlopen(page_url)
    parsed_page = BeautifulSoup(page, 'lxml')

    return parsed_page


def get_topics():
    """Get list of popular topics

    :rtype: list
    :returns: list of extracted results that contains a tuple for each topic
    """

    results = []

    parsed_page = parse_page(PAGE_URL)

    topic_list = parsed_page.find('ul', 'topic-list partial')

    links = topic_list('a')

    for index, link in enumerate(links):
        topic_link = link['href'].encode('utf-8')
        topic_name = link.contents[0].encode('utf-8')

        if "," in link.contents[1].string:
            splitted_count = link.contents[1].string.split(",")
            number_of_entries_for_topic = int(splitted_count[0]) * 1000 + int(splitted_count[1][0]) * 100
        else:
            number_of_entries_for_topic = int(link.contents[1].string)

        results.append((index+1, topic_link, topic_name, number_of_entries_for_topic))

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

    return sorted(results, key=lambda x: x[3], reverse=True)[:10]


def get_selected_topic_indexes():
    """Get index of selected topics from user

    :rtype: list
    :returns: list of indexes
    """

    topic_indexes = raw_input("\nEnter requested topic indexes: ")

    if topic_indexes == "e":
        sys.exit(1)

    selected_topic_indexes = [int(index) for index in list(topic_indexes.split())
                                         if index.isdigit()]

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

    selected_topic_links = []
    selected_topic_entries = defaultdict(list)

    for topic_index in selected_topic_indexes:
        for topic_result in results:
            if topic_index == topic_result[0]:
                topic_link = topic_result[1]
                topic_name = topic_result[2]

                selected_topic_links.append(topic_link)
                selected_topic_entries[topic_name] = get_entries_for_topic(topic_link, entry_count_per_topic)

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
    :rtype: list
    :returns: List of favourite topics saved
    """

    favourite_topics = []

    if (os.path.exists(filename)):

        with open(filename, "r") as fav_topics_file:
            for topic in fav_topics_file.readlines():
                favourite_topics.append((topic.split(",")[0], topic.split(",")[1]))

    return favourite_topics


def list_topics(topic_results, print_top_ten=False):
    """Print currently popular topics

    :type topic_results: list
    :param topic_results: List of topics
    :type print_top_ten: bool
    :param print_top_ten: If True, print top ten entries according to entry count
    """

    if print_top_ten:
        most_entry_topics = get_topics_sorted_by_entry_count(topic_results)

        print
        for index, (t_index, t_link, t_name, t_entry_count) in enumerate(most_entry_topics):
            print index+1, t_name, t_entry_count

    print
    for (t_index, t_link, t_name, t_entry_count) in topic_results:
        print t_index, t_name


def print_results(results):
    """Print entries for selected topics

    :type results: dictionary
    :param results: entries for selected topics as name: entry_list dict
    """

    for topic_name, topic_entries in results.iteritems():

        print "#" * len(topic_name)
        print topic_name.rstrip()
        print "#" * len(topic_name)

        for index, entry in enumerate(topic_entries):
            entry_content = entry[0].strip().encode('utf-8')
            entry_author = entry[1].encode('utf-8')

            print "\n%2s - %s << %s >>" % (index+1, entry_content, entry_author)
            print "-" * 80


if __name__ == '__main__':

    arg_parser = ArgumentParser()
    arg_parser.add_argument("-c", "--count", default=10, type=int, dest="entry_count_per_topic",
                            help="Number of entries for a topic to extract")
    arg_parser.add_argument("-sf", "--fav", action='store_true', help="Add selected topics to favourites")
    arg_parser.add_argument("-gf", "--getfavs", action='store_true', help="Get entries from favourite topics")

    args = arg_parser.parse_args()
    topic_results = get_topics()

    if args.fav:

        list_topics(topic_results)

        favourite_topic_indexes = get_selected_topic_indexes()

        topics_selected = [(topic_results[index-1][1], topic_results[index-1][2]) for index in favourite_topic_indexes]
        add_to_favourite_topics(topics_selected)
    
    elif args.getfavs:
        
        favourite_topic_entries = defaultdict(list)

        favourite_topics = read_favourite_topics("favourite_topics.txt")

        for topic_link, topic_name in favourite_topics:
            favourite_topic_entries[topic_name] = get_entries_for_topic(topic_link)
    
        print_results(favourite_topic_entries)

    else:
        list_topics(topic_results, True)

        requested_topic_indexes = get_selected_topic_indexes()
        requested_topic_entries = get_entries_for_selected_topics(topic_results,
                                                                  requested_topic_indexes,
                                                                  args.entry_count_per_topic)

        print_results(requested_topic_entries)
