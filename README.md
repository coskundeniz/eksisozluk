eksisozluk
==========

A command line program to get topics from http://eksisozluk.com

Information
-----------

This script parses topics from eksisozluk.com, gets selected topics from user, and
prints entries for selected topics. Topics can be saved as favourite and entries from this
topics can be read later. Also selected entries can be saved. It was written with Python3.

Requirements
------------

Run one of the followings

* pipenv install
* pip install -r requirements.txt 

Usage
-----
* `python3 eksisozluk.py`
* `python3 eksisozluk.py -c number_of_entries_per_topic`
* Save selected topics as favourite
    * `python3 eksisozluk.py -sf`
* Get entries from favourite topics saved
    * `python3 eksisozluk.py -gf`
* Save selected entries
    * `python3 eksisozluk.py -se`
* Get topics from other titles
    * `python3 eksisozluk.py -t`
