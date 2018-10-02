eksisozluk
==========

A command line program to get popular topics from http://eksisozluk.com

Information
-----------

This script parses popular topics from eksisozluk.com, gets selected topics from user, and
prints entries for selected topics. Topics can be saved as favourite and entries from this
topics can be read later. Also selected entries can be saved.
If "e" is entered, program ends. It was written with Python3.

Requirements
------------

* pip install -r requirements.txt 

Usage
-----
* `python eksisozluk.py`
* `python eksisozluk.py -c number_of_entries_per_topic`
* Save selected topics as favourite
    * `python eksisozluk.py -sf`
* Get entries from favourite topics saved
    * `python eksisozluk.py -gf`
* Save selected entries
    * `python eksisozluk.py -se`
