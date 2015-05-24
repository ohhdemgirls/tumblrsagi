#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      User
#
# Created:     20/04/2015
# Copyright:   (c) User 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import sqlalchemy
from sqlalchemy import update

from multiprocessing.dummy import Pool as ThreadPool

import custom_exceptions
from utils import * # General utility functions
import sql_functions# Database interaction
from media_handlers import *# Media finding, extractiong, ect
import config # Settings and configuration
#from tables import *# Table definitions
import twkr_sql_functions



def check_if_there_are_new_posts_to_do_media_for(session):
    """Return true if one or more rows in raw_posts has "null" as the value
    for the processed_post_json column.
    Otherwise return False"""
    posts_query = sqlalchemy.select([RawPosts]).where(RawPosts.processed_post_json == "null")
    post_rows = session.execute(posts_query)
    post_row = post_rows.fetchone()
    logging.debug("post_row: "+repr(post_row))
    return False


def process_one_new_posts_media(post_row):
    """Return True if everything was fine.
    Return False if no more posts should be tried"""
    try:
        session = sql_functions.connect_to_db()
        post_primary_key = post_row["primary_key"]
        logging.debug("Processing post with primary_key: "+repr(post_primary_key))
    ##    #session = sql_functions.connect_to_db()
    ##    # Select the new post from RawPosts table by it's primary key
    ##    post_query = sqlalchemy.select([RawPosts]).where(RawPosts.primary_key == post_primary_key)
    ##    post_result = session.execute(post_query)
    ##    post_row = post_result.fetchone()


        logging.debug("post_row"": "+repr(post_row))
        raw_post_dict = json.loads(post_row["raw_post_json"])
        blog_url = post_row["blog_domain"]
        username = post_row["poster_username"]


        # Handle links for the post
        try:
            processed_post_dict = save_media(session,raw_post_dict)
        except custom_exceptions.MediaGrabberFailed, err:
            logging.error("Post media download failed!")
            logging.exception(err)
            return False
        logging.debug("processed_post_dict"": "+repr(processed_post_dict))

        # Insert row to posts table
        # Insert post into the DB
##        sql_functions.add_post_to_db(
##            session=session,
##            raw_post_dict=raw_post_dict,
##            processed_post_dict=processed_post_dict,
##            info_dict=None,
##            blog_url=blog_url,
##            username=username
##            )
        session.commit()

        media_hashes = []
        for media_hash_key in processed_post_dict["link_to_hash_dict"].keys():
            media_hashes.append(processed_post_dict["link_to_hash_dict"][media_hash_key])

        twkr_sql_functions.insert_one_post(
                session = session,
                post_dict = processed_post_dict,
                blog_id = 1,
                media_hash_list = media_hashes
                )
        session.commit()

        logging.debug("About to update RawPosts")
        # Modify origin row
        processed_post_json = json.dumps(processed_post_dict)
        update_statement = update(RawPosts).where(RawPosts.primary_key==post_primary_key).\
            values(processed_post_json=processed_post_json)
        update_statement.execute()
        session.commit()

        logging.debug("Finished processing new post media")
    except Exception, e:# Log exceptions and pass them on
        logging.critical("Unhandled exception in save_blog()!")
        logging.exception(e)
        raise
    return


##def list_new_post_primary_keys(session,max_rows):
##    # Select new posts
##    # New posts don't have a processed JSON
##    posts_query = sqlalchemy.select([RawPosts]).where(RawPosts.processed_post_json == "null")# I expected "== None" to work, but apparently a string of "null" is the thing to do?
##    logging.debug("posts_query"": "+repr(posts_query))
##    post_rows = session.execute(posts_query)
##    logging.debug("post_rows"": "+repr(post_rows))
##
##    # List rows to grab
##    logging.debug("Getting list of primary keys")
##    post_primary_keys = []
##    row_list_counter = 0
##    for post_row in post_rows:
##        row_list_counter += 1
##        if row_list_counter > max_rows:
##            break
##        post_primary_key = post_row["primary_key"]
##        post_primary_keys.append(post_primary_key)
##        continue
##    logging.debug("post_primary_keys: "+repr(post_primary_keys))
##    return post_primary_keys


def list_new_posts(session,max_rows):
    logging.debug("Getting list of new posts")
    # Select new posts
    # New posts don't have a processed JSON
    posts_query = sqlalchemy.select([RawPosts]).where(RawPosts.processed_post_json == "null").limit(max_rows)# I expected "== None" to work, but apparently a string of "null" is the thing to do?
    logging.debug("posts_query"": "+repr(posts_query))
    post_rows = session.execute(posts_query)
    logging.debug("post_rows"": "+repr(post_rows))

    # List rows to grab
    logging.debug("Getting list of rows")
    post_dicts = []
    row_list_counter = 0
    for post_row in post_rows:
        row_list_counter += 1
        if row_list_counter > max_rows:
            break
        if post_row:
            logging.debug("post_row: "+repr(post_row))
            post_dicts.append(post_row)
        continue
    logging.debug("post_dicts: "+repr(post_dicts))
    return post_dicts


def process_all_posts_media(session,max_rows=1000):
    # Get primary keys for some new posts
    #post_primary_keys = list_new_post_primary_keys(session,max_rows=max_rows)
    post_dicts = list_new_posts(session,max_rows)

    # Process posts
    logging.debug("Processing posts")

    # http://stackoverflow.com/questions/2846653/python-multithreading-for-dummies
    # Make the Pool of workers
    pool = ThreadPool(1)# Set to one for debugging

    results = pool.map(process_one_new_posts_media, post_dicts)
    #close the pool and wait for the work to finish
    pool.close()
    pool.join()

    logging.debug("Finished processing posts for media")


def main():
    try:
        setup_logging(
            log_file_path=os.path.join("debug","tumblr-media-grabber-log.txt"),
            concise_log_file_path=os.path.join("debug","short-tumblr-media-grabber-log.txt")
            )
        # Program
        # Connect to DB
        session = sql_functions.connect_to_db()
        process_all_posts_media(session)
        # /Program
        logging.info("Finished, exiting.")
        return

    except Exception, e:# Log fatal exceptions
        logging.critical("Unhandled exception!")
        logging.exception(e)
    return

if __name__ == '__main__':
    main()
