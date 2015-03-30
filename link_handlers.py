#-------------------------------------------------------------------------------
# Name:        link_handlers
# Purpose:  code for links in post text and other things not given directly by the tumblr API
#
# Author:      User
#
# Created:     28/03/2015
# Copyright:   (c) User 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------
# Libraries
import sqlalchemy
import subprocess# For video and some audio downloads
import urllib# For encoding audio urls
import re
import logging
# This project
from utils import *
from sql_functions import Media
import sql_functions
import config # User settings
from image_handlers import *





def find_links_src(html):
    """Given string containing '<img src="http://media.tumblr.com/tumblr_m7g6koAnx81r3kwau.jpg"/>'
    return ['http://media.tumblr.com/tumblr_m7g6koAnx81r3kwau.jpg']
    """
    embed_regex = """src=["']([^'"]+)["']/>"""
    links = re.findall(embed_regex,html, re.DOTALL)
    logging.debug("find_links_src() links: "+repr(links))
    return links


def find_url_links(html):
    """Find URLS in a string of text"""
    # Should return list of strings
    # Copied from:
    # http://stackoverflow.com/questions/520031/whats-the-cleanest-way-to-extract-urls-from-a-string-using-python
    # old regex http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+
    url_regex = 'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+~]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    links = re.findall(url_regex,html, re.DOTALL)
    logging.debug("find_url_links() links: "+repr(links))
    assert(type(links) is type([]))# Should be list
    return links


def extract_post_links(post_dict):
    """Run all applicable extractors for a post"""
    links = []
    # Collect links in the post text

    # collect together fields that would have text
    # Assuming anything that exists and is not None will be string
    fields_string = u""
    if u"body" in post_dict.keys():
        fields_string += (post_dict["body"]+u"\n\n")
    if u"title" in post_dict.keys():
        if post_dict["title"]:
            fields_string += (post_dict["title"]+u"\n\n")
    if u"text" in post_dict.keys():
        if post_dict["text"]:
            fields_string += (post_dict["text"]+u"\n\n")
    if u"source" in post_dict.keys():
        if post_dict["source"]:
            fields_string += (post_dict["source"]+u"\n\n")
    if u"description" in post_dict.keys():
        if post_dict["description"]:
            fields_string += (post_dict["description"]+u"\n\n")
    if u"url" in post_dict.keys():
        if post_dict["url"]:
            fields_string += (post_dict["url"]+u"\n\n")
    if u"source" in post_dict.keys():
        if post_dict["source"]:
            fields_string += (post_dict["source"]+u"\n\n")
    if u"caption" in post_dict.keys():
        if post_dict["caption"]:
            fields_string += (post_dict["caption"]+u"\n\n")
    if u"question" in post_dict.keys():
        if post_dict["question"]:
            fields_string += (post_dict["question"]+u"\n\n")
    if u"answer" in post_dict.keys():
        if post_dict["answer"]:
            fields_string += (post_dict["answer"]+u"\n\n")
    if u"source_url" in post_dict.keys():
        if post_dict["source_url"]:
            fields_string += (post_dict["source_url"]+u"\n\n")
    # Search for links in string
    logging.debug("extract_post_links() fields_string: "+repr(fields_string))
    links += find_links_src(fields_string)
    links += find_url_links(fields_string)
    logging.debug("extract_post_links() links: "+repr(links))
    return links


def handle_image_links(session,all_post_links):
    """Check and save images linked to by a post
    return link_hash_dict = {}# {link:hash}"""
    logging.debug("handle_image_links() all_post_links"+repr(all_post_links))
    # Find all links in post dict
    # Select whick links are image links
    link_extentions = [
    "jpg","jpeg",
    "gif",
    "png",
    ]
    image_links = []
    for link in all_post_links:
        # Grab extention if one exists
        after_last_dot = link.split(".")[-1]
        before_first_q_mark = after_last_dot.split("?")[0]
        # Check if extention is one we want
        for extention in link_extentions:
            if extention in before_first_q_mark:
                image_links.append(link)
    logging.debug("handle_image_links() image_links: "+repr(image_links))
    # Save image links
    link_hash_dict = download_image_links(session,image_links)
    return link_hash_dict# {link:hash}





def handle_links(session,post_dict):# TODO FIXME
    """Call other functions to handle non-tumblr API defined links and pass data from them back"""
    logging.debug("Handling external links...")
    logging.warning("External links handling not yet implimented, fix this!")# TODO FIXME

    # Get list of links
    all_post_links = extract_post_links(post_dict)
    logging.debug("handle_links() all_post_links"+repr(all_post_links))
    # Remove links already in DB
    logging.warning("handle_links() Preexisting link check is disabled.")
    preexisting_link_dict = {}# {link:hash}# TODO FIXME
    logging.debug("handle_links() preexisting_link_dict: "+repr(preexisting_link_dict))
    new_links = []
    preexisting_links = preexisting_link_dict.keys()
    for post_link in all_post_links:
        if post_link in preexisting_links:
            continue
        else:
            new_links.append(post_link)
    new_links = uniquify(new_links)
    logging.debug("new_links: "+repr(new_links))

    # Saved linked images
    # TODO FIXME
    remote_images_dict = handle_image_links(session,all_post_links)# {link:hash}

    # Saved linked videos
    # TODO FIXME

    # Saved linked audio
    # TODO FIXME

    # Site handlers

    # gfycat
    #https://gfycat.com/MatureSilkyEwe
    # TODO FIXME

    # e621.net
    # https://e621.net/post/show/599802
    # TODO FIXME



    # Join mapping dicts # {link:hash}
    remote_link_to_hash_dict = merge_dicts(
    preexisting_link_dict,# Links that were already in the DB
    remote_images_dict,
    )
    logging.debug("handle_links() Finished processing external links.")
    logging.debug("handle_links() remote_link_to_hash_dict:"+repr(remote_link_to_hash_dict))
    return remote_link_to_hash_dict# {link:hash}












def main():
    pass

if __name__ == '__main__':
    main()