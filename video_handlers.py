#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
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
from yt_dl_common import *
from utils import *
#from sql_functions import Media
from tables import *# This module only has the table classes
import sql_functions
import config # User settings
import link_handlers
from image_handlers import download_image_link

def crop_youtube_id(url):
    video_id_regex ="""youtube.com/(?:embed/)?(?:watch\?v=)?([a-zA-Z0-9]+)"""
    video_id_search = re.search(video_id_regex, url, re.IGNORECASE|re.DOTALL)
    if video_id_search:
        video_id = video_id_search.group(1)
        logging.debug("Extracted id: "+repr(video_id)+" from url: "+repr(url))
        return video_id
    else:
        return


def handle_youtube_video(session,post_dict):# NEW TABLES
    """Download youtube videos from video posts
    https://github.com/rg3/youtube-dl/blob/master/docs/supportedsites.md
    https://github.com/rg3/youtube-dl/"""
    assert(post_dict["type"] == u"video")# Ensure calling code isn't broken
    assert(post_dict["video_type"] == u"youtube")# Ensure calling code isn't broken
    video_dicts = []# Init early so skipped videos can still return results
    logging.debug("Processing youtube video")
    video_page = post_dict["post_url"]
    media_id_list = []
    logging.debug("video_page: "+repr(video_page))

    # Extract youtube links from video field
    # ex. https://www.youtube.com/embed/lGIEmH3BoyA
    video_items = post_dict["player"]
    youtube_urls = []
    for video_item in video_items:
        # Get a youtube URL
        embed_code = video_item["embed_code"]
        # Skip if no embed code to process (Known to happen) "u'player': [{u'embed_code': False, u'width': 250},"
        if embed_code:
            logging.debug("embed_code: "+repr(embed_code))
            embed_url_regex ="""src=["']([^?"']+)\?"""
            embed_url_search = re.search(embed_url_regex, embed_code, re.IGNORECASE|re.DOTALL)
            if embed_url_search:
                embed_url = embed_url_search.group(1)
                youtube_urls.append(embed_url)
        continue

    # Check if videos are already saved
    download_urls = []
    for youtube_url in youtube_urls:
        video_id = crop_youtube_id(youtube_url)
        # Look up ID in DB
        video_page_query = sqlalchemy.select([Media]).where(Media.video_id == video_id)
        video_page_rows = session.execute(video_page_query)
        video_page_row = video_page_rows.fetchone()
        if video_page_row:
            logging.debug("Skipping previously saved video: "+repr(video_page_row))
            media_id_list += [video_page_row["media_id"]]
        else:
            download_urls.append(youtube_url)
        continue

    # Download videos if there are any

    for download_url in download_urls:
        media_id = run_yt_dl_single(
            session,
            download_url = download_url,
            extractor_used="video_handlers.handle_youtube_video()",
            video_id = crop_youtube_id(download_url),
            )
        media_id_list+=media_id
        continue

    return media_id_list


def handle_vimeo_videos(session,post_dict):# New table
    """Handle downloading of vimeo videos
    https://github.com/rg3/youtube-dl/blob/master/docs/supportedsites.md"""
    logging.debug("Processing vimeo videos")
    # Extract video links from post dict
    video_items = post_dict["player"]
    vimeo_urls = []
    for video_item in video_items:
        embed_code = video_item["embed_code"]
        # u'<iframe src="https://player.vimeo.com/video/118912193?title=0&byline=0&portrait=0" width="250" height="156" frameborder="0" title="Hyperfast Preview - Mai (Patreon Process Videos)" webkitallowfullscreen mozallowfullscreen allowfullscreen></iframe>'
        # https://player.vimeo.com/video/118912193?
        if embed_code:
            # Process links so YT-DL can understand them
            logging.debug("embed_code: "+repr(embed_code))
            embed_url_regex ="""src=["']([^?"']+)"""
            embed_url_search = re.search(embed_url_regex, embed_code, re.IGNORECASE|re.DOTALL)
            if embed_url_search:
                embed_url = embed_url_search.group(1)
                vimeo_urls.append(embed_url)
        continue
    logging.debug("vimeo_urls: "+repr(vimeo_urls))

    # Download videos if there are any
    media_id_list = run_yt_dl_multiple(
        session = session,
        download_urls = vimeo_urls,
        extractor_used="video_handlers.handle_vimeo_videos()",
        )
    logging.debug("Finished downloading vimeo embeds")
    return media_id_list


def handle_imgur_videos(session,post_dict):# NEW TABLES
    """This is where I plan to put code for imgur videos"""
    logging.debug("Processing imgur videos")
    # Extract video links from post dict
    imgur_urls = []
    video_items = post_dict["player"]
    for video_item in video_items:
        embed_code = video_item["embed_code"]
        # u'<iframe class="imgur-embed" width="100%" height="720" frameborder="0" src="http://i.imgur.com/wSBlRyv.gifv#embed"></iframe>'
        # http://i.imgur.com/wSBlRyv.gifv
        if embed_code:
            # Process links so YT-DL can understand them
            logging.debug("embed_code: "+repr(embed_code))
            embed_url_regex ="""src=["']([^?"'#]+)"""
            embed_url_search = re.search(embed_url_regex, embed_code, re.IGNORECASE|re.DOTALL)
            if embed_url_search:
                embed_url = embed_url_search.group(1)
                imgur_urls.append(embed_url)
        continue

    logging.debug("imgur_urls: "+repr(imgur_urls))

    # Download videos if there are any
    media_id_list = run_yt_dl_multiple(
        session = session,
        download_urls = imgur_urls,
        extractor_used="video_handlers.handle_imgur_videos()",
        )
    logging.debug("Finished downloading imgur_video embeds")
    return media_id_list


def handle_vine_videos(session,post_dict):# New table
    """Handle downloading of vine videos
    https://github.com/rg3/youtube-dl/blob/master/docs/supportedsites.md"""
    logging.debug("Processing vine videos")
    # Extract video links from post dict
    video_items = post_dict["player"]
    vine_urls = []
    for video_item in video_items:
        embed_code = video_item["embed_code"]
        # u'<iframe class="vine-embed" src="https://vine.co/v/hjWIUFOYD31/embed/simple"width="500" height="500" frameborder="0"></iframe><script async src="//platform.vine.co/static/scripts/embed.js" charset="utf-8"></script>'
        # https://vine.co/v/hjWIUFOYD31
        if embed_code:
            # Process links so YT-DL can understand them
            logging.debug("embed_code: "+repr(embed_code))
            embed_url_regex ="""src=["']([^?"']+)"""
            embed_url_search = re.search(embed_url_regex, embed_code, re.IGNORECASE|re.DOTALL)
            if embed_url_search:
                embed_url = embed_url_search.group(1)
                vine_urls.append(embed_url)
        continue

    # Deduplicate links
    vine_urls = uniquify(vine_urls)
    logging.debug("vine_urls: "+repr(vine_urls))

    # Skip URLs that have already been done
    download_urls = []
    for vine_url in vine_urls:
        # Extract video ID
        # https://vine.co/v/hjWIUFOYD31/embed/simple -> hjWIUFOYD31
        id_regex ="""vine.co/v/([a-zA-Z0-9]+)/?"""
        id_search = re.search(id_regex, vine_url, re.IGNORECASE|re.DOTALL)
        if id_search:
            # Look up ID in media DB
            video_id = id_search.group(1)
            logging.debug("video_id: "+repr(video_id))
            video_id_row = None# TODO FIXME
            if video_id_row:
                logging.debug("Skipping previously saved video: "+repr(video_page_row))
                continue
        download_urls.append(vine_url)
        continue
    logging.debug("download_urls: "+repr(download_urls))

    # Download videos if there are any
    media_id_list = run_yt_dl_multiple(
        session = session,
        download_urls = download_urls,
        extractor_used="video_handlers.handle_vine_videos()",
        )
    logging.debug("Finished downloading Vine embeds")
    return media_id_list


def handle_tumblr_videos(session,post_dict):
    """Download tumblr-hosted videos from video posts
    https://github.com/rg3/youtube-dl/blob/master/docs/supportedsites.md
    https://github.com/rg3/youtube-dl/"""
    logging.debug("Processing tumblr video")
    video_page = post_dict["post_url"]
    logging.debug("video_page: "+repr(video_page))

    download_urls = [video_page]
    # Download videos if there are any
    media_id_list = run_yt_dl_multiple(
        session = session,
        download_urls = download_urls,
        extractor_used="video_handlers.handle_tumblr_videos()",
        )
    logging.debug("Finished downloading Tumblr embeds")
    return media_id_list


def handle_livestream_videos(session,post_dict):
    """This is where I plan to put code for imgur videos"""
    logging.debug("Processing livestream video")
    # Extract video links from post dict
    livestream_urls = []
    video_items = post_dict["player"]
    for video_item in video_items:
        embed_code = video_item["embed_code"]
        # u'<iframe src="http://new.livestream.com/accounts/1249127/events/3464519/player?width=560&height=315&autoPlay=true&mute=false" width="250" height="140" frameborder="0" scrolling="no"> </iframe>'
        # http://new.livestream.com/accounts/1249127/events/3464519/player?
        if embed_code:
            # Process links so YT-DL can understand them
            logging.debug("embed_code: "+repr(embed_code))
            embed_url_regex ="""src=["']([^?"'#]+)"""
            embed_url_search = re.search(embed_url_regex, embed_code, re.IGNORECASE|re.DOTALL)
            if embed_url_search:
                embed_url = embed_url_search.group(1)
                livestream_urls.append(embed_url)
        continue
    logging.debug("livestream_urls: "+repr(livestream_urls))

    # Download videos if there are any
    media_id_list = run_yt_dl_multiple(
        session = session,
        download_urls = livestream_urls,
        extractor_used="video_handlers.handle_livestream_videos()",
        )

    logging.debug("Finished downloading livestream embeds")
    return media_id_list


def handle_yahoo_videos(session,post_dict):
    """Download yahoo videos given by the videos section fo the API"""
    logging.debug("Processing yahoo video")
    # Extract video links from post dict
    yahoo_urls = []
    video_items = post_dict["player"]
    for video_item in video_items:
        embed_code = video_item["embed_code"]
        # u'<iframe src="http://new.livestream.com/accounts/1249127/events/3464519/player?width=560&height=315&autoPlay=true&mute=false" width="250" height="140" frameborder="0" scrolling="no"> </iframe>'
        # http://new.livestream.com/accounts/1249127/events/3464519/player?
        if embed_code:
            # Process links so YT-DL can understand them
            logging.debug("embed_code: "+repr(embed_code))
            embed_url_regex ="""src=["']([^?"'#]+)"""
            embed_url_search = re.search(embed_url_regex, embed_code, re.IGNORECASE|re.DOTALL)
            if embed_url_search:
                embed_url = embed_url_search.group(1)
                yahoo_urls.append(embed_url)
        continue
    logging.debug("yahoo_urls: "+repr(yahoo_urls))

    # Download videos if there are any
    media_id_list = run_yt_dl_multiple(
        session = session,
        download_urls = yahoo_urls,
        extractor_used="video_handlers.handle_yahoo_videos()",
        )

    logging.debug("Finished downloading yahoo embeds")
    return media_id_list


def handle_dailymotion_videos(session,post_dict):
    """Download dailymotion videos given by the videos section fo the API"""
    logging.debug("Processing dailymotion video")
    # Extract video links from post dict
    video_urls = []
    video_items = post_dict["player"]
    for video_item in video_items:
        embed_code = video_item["embed_code"]
        # u'embed_code': u'<iframe src="https://www.dailymotion.com/embed/video/x2msryd" width="250" height="139" frameborder="0" allowfullscreen></iframe>'
        # https://www.dailymotion.com/embed/video/x2msryd
        if embed_code:
            # Process links so YT-DL can understand them
            logging.debug("embed_code: "+repr(embed_code))
            embed_url_regex ="""src=["']([^?"'#]+)"""
            embed_url_search = re.search(embed_url_regex, embed_code, re.IGNORECASE|re.DOTALL)
            if embed_url_search:
                embed_url = embed_url_search.group(1)
                video_urls.append(embed_url)
        continue
    logging.debug("video_urls: "+repr(video_urls))

    # Download videos if there are any
    media_id_list = run_yt_dl_multiple(
        session = session,
        download_urls = video_urls,
        extractor_used="video_handlers.handle_dailymotion_videos()",
        )

    logging.debug("Finished downloading dailymotion embeds")
    return media_id_list


def handle_instagram_videos(session,post_dict):
    """Download instagram videos given by the videos section fo the API"""
    logging.debug("Processing instagram video")
    # Extract video links from post dict
    if "instagram.com" in post_dict["permalink_url"]:
        video_urls = [ post_dict["permalink_url"] ]
    else:
        logging.error("Assumption of permalink always being video link was false, recode handler!")
        assert(False)

    # Download videos if there are any
    media_id_list = run_yt_dl_multiple(
        session = session,
        download_urls = video_urls,
        extractor_used="video_handlers.handle_instagram_videos()",
        )

    logging.debug("Finished downloading instagram embeds")
    return media_id_list


def handle_kickstarter_videos(session,post_dict):
    """Download kickstarter videos given by the videos section fo the API"""
    logging.debug("Processing kickstarter video")
    # Extract video links from post dict
    video_urls = []
    video_items = post_dict["player"]
    for video_item in video_items:
        embed_code = video_item["embed_code"]
        # u'embed_code': u'<iframe frameborder="0" height="375" scrolling="no" src="https://www.kickstarter.com/projects/1420158244/power-drive-2000/widget/video.html" width="500"></iframe>'
        # https://www.kickstarter.com/projects/1420158244/power-drive-2000/widget/video.html
        if embed_code:
            # Process links so YT-DL can understand them
            logging.debug("embed_code: "+repr(embed_code))
            embed_url_regex ="""src=["']([^?"'#]+)"""
            embed_url_search = re.search(embed_url_regex, embed_code, re.IGNORECASE|re.DOTALL)
            if embed_url_search:
                embed_url = embed_url_search.group(1)
                video_urls.append(embed_url)
        continue
    logging.debug("video_urls: "+repr(video_urls))

    # Download videos if there are any
    media_id_list = run_yt_dl_multiple(
        session = session,
        download_urls = video_urls,
        extractor_used="video_handlers.handle_kickstarter_videos()",
        )
    logging.debug("Finished downloading kickstarter embeds")
    return media_id_list


def handle_dropbox_embed(session,post_dict):
    # Grab links
    player_string = repr(post_dict["player"])
    links = link_handlers.find_links(player_string)
    logging.debug("handle_dropbox_embed() links:"+repr(links))
    for link in links:
        # Process the first matching link and return what the handler gives
        if "dl.dropboxusercontent.com" in link:
            return link_handlers.handle_dropbox_link(session,link)
    # If no links match return empty list
    return []


def handle_blip_videos(session,post_dict):
    """Download blip videos given by the videos section fo the API"""
    logging.debug("Processing blip video")
    # Extract video links from post dict
    video_urls = []
    video_items = post_dict["player"]
    for video_item in video_items:
        embed_code = video_item["embed_code"]
        # u'embed_code': u'<iframe src="https://blip.tv/play/iIEHgv_aSAI.html?p=1" width="250" height="203" frameborder="0" allowfullscreen></iframe><embed type="application/x-shockwave-flash" src="http://a.blip.tv/api.swf#iIEHgv_aSAI" style="display:none"></embed>',
        # https://blip.tv/play/iIEHgv_aSAI.html
        if embed_code:
            # Process links so YT-DL can understand them
            logging.debug("handle_blip_videos() embed_code: "+repr(embed_code))
            embed_url_regex ="""(https:?//blip.tv/play/\w+.html)"""
            embed_url_search = re.search(embed_url_regex, embed_code, re.IGNORECASE|re.DOTALL)
            if embed_url_search:
                embed_url = embed_url_search.group(1)
                video_urls.append(embed_url)
        continue
    logging.debug("handle_blip_videos() video_urls: "+repr(video_urls))

    # Download videos if there are any
    media_id_list = run_yt_dl_multiple(
        session = session,
        download_urls = video_urls,
        extractor_used="video_handlers.handle_blip_videos()",
        )
    logging.debug("Finished downloading blip embeds")
    return media_id_list


def handle_coub_videos(session,post_dict):
    """Download coub videos given by the videos section fo the API"""
    logging.debug("Processing coub video")
    # Extract video links from post dict
    video_urls = []
    video_items = post_dict["player"]
    for video_item in video_items:
        embed_code = video_item["embed_code"]
        # u'embed_code': u'<iframe src="//coub.com/embed/3rj9f?autoplay=true&maxheight=720&maxwidth=540&muted=true" allowfullscreen="true" frameborder="0" autoplay="true" width="250" height="140"></iframe>',
        # //coub.com/embed/3rj9f
        # http://coub.com/view/3rj9f
        if embed_code:
            # Process links so YT-DL can understand them
            logging.debug("handle_coub_videos() embed_code: "+repr(embed_code))
            embed_url_regex ="""coub.com/embed/(\w+)"""
            embed_url_search = re.search(embed_url_regex, embed_code, re.IGNORECASE|re.DOTALL)
            if embed_url_search:
                video_id = embed_url_search.group(1)
                video_url = "http://coub.com/view/"+video_id
                video_urls.append(video_url)
        continue
    logging.debug("handle_coub_videos() video_urls: "+repr(video_urls))

    # Download videos if there are any
    media_id_list = run_yt_dl_multiple(
        session = session,
        download_urls = video_urls,
        extractor_used="video_handlers.handle_coub_videos()",
        )
    logging.debug("Finished downloading coub embeds")
    return media_id_list


def handle_liveleak_videos(session,post_dict):
    """Download liveleak videos given by the videos section fo the API"""
    logging.debug("Processing liveleak video")
    # Extract video links from post dict
    video_urls = []
    video_items = post_dict["player"]
    for video_item in video_items:
        embed_code = video_item["embed_code"]
        # u'embed_code': u'<iframe width="250" height="140" src="http://www.liveleak.com/ll_embed?f=01b03505a8a6" frameborder="0" allowfullscreen></iframe>',
        # http://www.liveleak.com/ll_embed?f=01b03505a8a6
        if embed_code:
            # Process links so YT-DL can understand them
            logging.debug("handle_liveleak_videos() embed_code: "+repr(embed_code))
            embed_url_regex ="""liveleak.com/ll_embed\?f=(\w+)"""
            embed_url_search = re.search(embed_url_regex, embed_code, re.IGNORECASE|re.DOTALL)
            if embed_url_search:
                video_id = embed_url_search.group(1)
                video_url = "http://www.liveleak.com/ll_embed?f="+video_id
                video_urls.append(video_url)
        continue
    logging.debug("handle_liveleak_videos() video_urls: "+repr(video_urls))

    # Download videos if there are any
    media_id_list = run_yt_dl_multiple(
        session = session,
        download_urls = video_urls,
        extractor_used="video_handlers.handle_liveleak_videos()",
        )
    logging.debug("Finished downloading liveleak embeds")
    return media_id_list


def handle_vidme_videos(session,post_dict):
    """Download vidme videos given by the videos section fo the API"""
    logging.debug("Processing vidme video")
    # Extract video links from post dict
    video_urls = []
    video_items = post_dict["player"]
    for video_item in video_items:
        embed_code = video_item["embed_code"]
        # u'embed_code': u'<iframe src="https://vid.me/e/JPd9" frameborder="0" allowfullscreen webkitallowfullscreen mozallowfullscreen scrolling="no" height="140" width="250"></iframe>',
        # https://vid.me/e/JPd9
        if embed_code:
            # Process links so YT-DL can understand them
            logging.debug("handle_vidme_videos() embed_code: "+repr(embed_code))
            embed_url_regex ="""vid.me/\w/([a-zA-Z0-9]+)"""
            embed_url_search = re.search(embed_url_regex, embed_code, re.IGNORECASE|re.DOTALL)
            if embed_url_search:
                video_id = embed_url_search.group(1)
                video_url = "https://vid.me/e/"+video_id
                video_urls.append(video_url)
        continue
    logging.debug("handle_vidme_videos() video_urls: "+repr(video_urls))

    # Download videos if there are any
    media_id_list = run_yt_dl_multiple(
        session = session,
        download_urls = video_urls,
        extractor_used="video_handlers.handle_vidme_videos()",
        )
    logging.debug("Finished downloading vidme embeds")
    return media_id_list


def handle_xhamster_videos(session,post_dict):#TODO FIXME
    """Download xhamster videos given by the videos section fo the API"""
    logging.debug("Processing xhamster video")
    logging.warning("handle_xhamster_videos() is not finished yet due to youtube-dl issues. FIX IT!")#TODO FIXME
    return []#TODO FIXME
    # Extract video links from post dict
    video_urls = []
    video_items = post_dict["player"]
    for video_item in video_items:
        embed_code = video_item["embed_code"]
        # u'embed_code': u'<iframe width="250" height="187" src="http://xhamster.com/xembed.php?video=3328539" frameborder="0" scrolling="no"></iframe>',
        # http://xhamster.com/xembed.php?video=3328539
        if embed_code:
            # Process links so YT-DL can understand them
            logging.debug("handle_xhamster_videos() embed_code: "+repr(embed_code))
            embed_url_regex ="""vid.me/\w/([a-zA-Z0-9]+)"""#TODO FIXME
            embed_url_search = re.search(embed_url_regex, embed_code, re.IGNORECASE|re.DOTALL)
            if embed_url_search:
                video_id = embed_url_search.group(1)
                video_url = "https://vid.me/e/"+video_id#TODO FIXME
                video_urls.append(video_url)
        continue
    logging.debug("handle_xhamster_videos() video_urls: "+repr(video_urls))

    # Download videos if there are any
    media_id_list = run_yt_dl_multiple(
        session = session,
        download_urls = video_urls,
        extractor_used="video_handlers.handle_xhamster_videos()",
        )
    logging.debug("Finished downloading xhamster embeds")
    return media_id_list


def handle_flash_embed(session,post_dict):#TODO FIXME
    """Download xhamster videos given by the videos section fo the API"""
    logging.debug("Processing flash embed")
    logging.warning("handle_flash_embed() is not finished yet. FIX IT!")#TODO FIXME
    """ u'player': [{u'embed_code': u'<embed width="250" height="291" align="middle" pluginspage="http://www.adobe.com/go/getflashplayer" type="application/x-shockwave-flash" allowfullscreen="false" allowscriptaccess="sameDomain" name="xdft" bgcolor="#000000" scale="noscale" quality="high" menu="false" src="http://www.najle.com/idaft/idaft/xdft.swf">',
              u'width': 250},
             {u'embed_code': u'<embed width="400" height="466" align="middle" pluginspage="http://www.adobe.com/go/getflashplayer" type="application/x-shockwave-flash" allowfullscreen="false" allowscriptaccess="sameDomain" name="xdft" bgcolor="#000000" scale="noscale" quality="high" menu="false" src="http://www.najle.com/idaft/idaft/xdft.swf">',
              u'width': 400},
             {u'embed_code': u'<embed width="500" height="582" align="middle" pluginspage="http://www.adobe.com/go/getflashplayer" type="application/x-shockwave-flash" allowfullscreen="false" allowscriptaccess="sameDomain" name="xdft" bgcolor="#000000" scale="noscale" quality="high" menu="false" src="http://www.najle.com/idaft/idaft/xdft.swf">',
              u'width': 500}],"""
    # Extract video links from post dict
    found_links = []
    video_items = post_dict["player"]
    for video_item in video_items:
        embed_code = video_item["embed_code"]
        #
        if embed_code:
            # Find links in the field
            field_links = link_handlers.find_links(embed_code)
            found_links += field_links
        continue
    logging.debug("handle_flash_embed() found_links: "+repr(found_links))

    # Remove duplicate links
    links = uniquify(found_links)

    media_id_list = []
    # Choose which links to save
    for link in links:
        # If link ends in .swf
        if ".swf" in link[-4:]:
            media_id_list += download_image_link(session,link)
            continue
        # If link ends in .flv
        elif ".flv" in link[-4:]:
            media_id_list += download_image_link(session,link)
            continue
        continue

    return media_id_list



def handle_video_posts(session,post_dict):
    """Decide which video functions to run and pass back what they return"""
    # Check if post is a video post
    if post_dict["type"] != u"video":
        return {}
    logging.debug("Post is video")
    # Youtube
    if post_dict["video_type"] == u"youtube":
        logging.debug("Post is youtube")
        return handle_youtube_video(session,post_dict)
    # Tumblr
    elif post_dict["video_type"] == u"tumblr":
        logging.debug("Post is tumblr video")
        return handle_tumblr_videos(session,post_dict)
    # Vine
    elif post_dict["video_type"] == u"vine":
        logging.debug("Post is vine video")
        return handle_vine_videos(session,post_dict)
    # vimeo
    elif post_dict["video_type"] == u"vimeo":
        logging.debug("Post is vimeo video")
        return handle_vimeo_videos(session,post_dict)
    # Yahoo
    elif post_dict["video_type"] == u"yahoo":
        logging.debug("Post is yahoo video")
        return handle_yahoo_videos(session,post_dict)
    # dailymotion
    elif post_dict["video_type"] == u"dailymotion":
        logging.debug("Post is dailymotion video")
        return handle_dailymotion_videos(session,post_dict)
    # instagram
    elif post_dict["video_type"] == u"instagram":
        logging.debug("Post is instagram video")
        return handle_instagram_videos(session,post_dict)
    # kickstarter
    elif post_dict["video_type"] == u"kickstarter":
        logging.debug("Post is kickstarter video")
        return handle_kickstarter_videos(session,post_dict)
    # collegehumor
    elif post_dict["video_type"] == u"collegehumor":
        logging.debug("Post is collegehumor video, not saving video.")
        return []
    # blip
    elif post_dict["video_type"] == u"blip":
        logging.debug("Post is blip video")
        return handle_blip_videos(session,post_dict)
    # coub
    elif post_dict["video_type"] == u"coub":
        logging.debug("Post is coub looping service video, not saving video.")
        return []
    # "unknown" - special cases?
    elif (post_dict["video_type"] == u"unknown"):
        logging.warning("API reports video type as unknown, handlers may be inappropriate or absent.")
        # imgur
        if "imgur-embed" in repr(post_dict["player"]):
            logging.debug("Post is imgur video")
            return handle_imgur_videos(session,post_dict)
        # Livestream
        elif "livestream.com" in repr(post_dict["player"]):
            logging.debug("Post is livestream video")
            return handle_livestream_videos(session,post_dict)
        # sembeo? - Skip this ad
        elif "http://www.sembeo.com" in repr(post_dict["player"]):
            logging.debug("Post looks like an ad for sembeo? skipping video DL")
            return []
        # ?dead? youtube?
        elif "youtube.com" in repr(post_dict["player"]):
            logging.debug("Post looks like a dead youtube video? skipping video DL")
            return []
        # creativity-online.com - Ads
        elif "creativity-online.com" in repr(post_dict["player"]):
            logging.debug("Post looks like a flash advertisment, fuck coding for that bullshit. skipping.")
            return []
        # Bandcamp? WHY
        elif "bandcamp.com/EmbeddedPlayer" in repr(post_dict["player"]):
            logging.debug("Post looks like a bandcamp gizmo that we can't easily code for. skipping.")
            return []
        # Dropbox flash? possibly other dropbox?
        elif "https://dl.dropboxusercontent.com/s/" in repr(post_dict["player"]):
            logging.debug("Post looks like a dropbox thing? Sending to dropbox link handler.")
            return handle_dropbox_embed(session,post_dict)
        # Bandcamp? WHY
        elif "www.jest.com" in repr(post_dict["player"]):
            logging.debug("Post looks like a jest.com thing, skipping.")
            return []
        # Liveleak
        elif "liveleak.com" in repr(post_dict["player"]):
            logging.debug("Post looks like a liveleak embed..")
            return handle_liveleak_videos(session,post_dict)
        # broken dailymotion
        elif "dailymotion.com" in repr(post_dict["player"]):
            logging.debug("Post looks like a broken dailymotion video, skipping.")
            return []
        # vid.me
        elif "vid.me" in repr(post_dict["player"]):
            logging.debug("Post looks like a vid.me embed..")
            return handle_vidme_videos(session,post_dict)
        # xhamster.com
        elif "xhamster.com/xembed.php?" in repr(post_dict["player"]):
            logging.debug("Post looks like a xhamster embed..")
            return handle_xhamster_videos(session,post_dict)
        # xvideos.com - porn *tube
        elif ".xvideos.com" in repr(post_dict["player"]):
            logging.debug("Post looks like a xvideos video, skipping.")
            return []
        # ign
        elif ".ign.com/video" in repr(post_dict["player"]):
            logging.debug("Post looks like a ign video, skipping.")
            return []
        # naturesoundsfor.me
        elif "naturesoundsfor.me" in repr(post_dict["player"]):
            logging.debug("Post looks like naturesoundsfor.me, skipping.")
            return []

        # This should be last so we don't accidentally pick up other media types
        # Flash embed
        elif """="application/x-shockwave-flash""" in repr(post_dict["player"]):
            logging.debug("Post looks like a Flash embed")
            return handle_flash_embed(session,post_dict)

    # If no handler is applicable, stop for fixing
    logging.error("Unknown video type!")
    logging.error("locals(): "+repr(locals()))
    logging.error("""post_dict: """+repr(post_dict))
    assert(False)# Not implimented
    return {}


def debug():
    """For WIP, debug, ect function calls"""
    session = sql_functions.connect_to_db()

    # Youtube
    youtube_dict_1 = {u'reblog_key': u'HfjckfH7', u'short_url': u'http://tmblr.co/ZUGffq1cfuHuJ', u'thumbnail_width': 480, u'player': [{u'width': 250, u'embed_code': u'<iframe width="250" height="140" id="youtube_iframe" src="https://www.youtube.com/embed/lGIEmH3BoyA?feature=oembed&amp;enablejsapi=1&amp;origin=http://safe.txmblr.com&amp;wmode=opaque" frameborder="0" allowfullscreen></iframe>'}, {u'width': 400, u'embed_code': u'<iframe width="400" height="225" id="youtube_iframe" src="https://www.youtube.com/embed/lGIEmH3BoyA?feature=oembed&amp;enablejsapi=1&amp;origin=http://safe.txmblr.com&amp;wmode=opaque" frameborder="0" allowfullscreen></iframe>'}, {u'width': 500, u'embed_code': u'<iframe width="500" height="281" id="youtube_iframe" src="https://www.youtube.com/embed/lGIEmH3BoyA?feature=oembed&amp;enablejsapi=1&amp;origin=http://safe.txmblr.com&amp;wmode=opaque" frameborder="0" allowfullscreen></iframe>'}], u'id': 110224285203L, u'post_url': u'http://askbuttonsmom.tumblr.com/post/110224285203/throwback-can-you-believe-its-been-almost-2yrs', u'tags': [u"button's mom", u'hardcopy', u'song', u'shadyvox'], u'highlighted': [], u'state': u'published', u'html5_capable': True, u'type': u'video', u'format': u'html', u'timestamp': 1423197599, u'note_count': 145, u'video_type': u'youtube', u'date': u'2015-02-06 04:39:59 GMT', u'thumbnail_height': 360, u'permalink_url': u'https://www.youtube.com/watch?v=lGIEmH3BoyA', u'slug': u'throwback-can-you-believe-its-been-almost-2yrs', u'blog_name': u'askbuttonsmom', u'caption': u'<p>Throwback! Can you believe it&#8217;s been almost 2yrs since this came out? Mommy&#8217;s getting old&#8230;</p>', u'thumbnail_url': u'https://i.ytimg.com/vi/lGIEmH3BoyA/hqdefault.jpg'}
    youtube_dict_2 = {u'highlighted': [], u'reblog_key': u'qO3JnfS7', u'player': [{u'width': 250, u'embed_code': False}, {u'width': 400, u'embed_code': False}, {u'width': 500, u'embed_code': False}], u'format': u'html', u'timestamp': 1390412461, u'note_count': 4282, u'tags': [], u'video_type': u'youtube', u'id': 74184911379L, u'post_url': u'http://askbuttonsmom.tumblr.com/post/74184911379/ask-thecrusaders-bar-buddies-dont-worry', u'caption': u'<p><a class="tumblr_blog" href="http://ask-thecrusaders.tumblr.com/post/74162414750/bar-buddies-dont-worry-neon-you-will-have-your">ask-thecrusaders</a>:</p>\n<blockquote>\n<p><strong>"Bar Buddies"</strong><br/><br/>Dont\u2019 worry Neon, you will have your music video soon enough.</p>\n</blockquote>\n<p>Honestly, that Neon Lights is a TERRIBLE influence!! No son of mine will grow up to be a drunken drug-shooting bass dropping hipster! :C</p>', u'state': u'published', u'html5_capable': False, u'reblog': {u'comment': u'<p>Honestly, that Neon Lights is a TERRIBLE influence!! No son of mine will grow up to be a drunken drug-shooting bass dropping hipster! :C</p>', u'tree_html': u'<p><a class="tumblr_blog" href="http://ask-thecrusaders.tumblr.com/post/74162414750/bar-buddies-dont-worry-neon-you-will-have-your">ask-thecrusaders</a>:</p><blockquote>\n<p><strong>"Bar Buddies"</strong><br/><br/>Dont\u2019 worry Neon, you will have your music video soon enough.</p>\n</blockquote>', u'trail': [{u'blog': {u'theme': {u'title_font_weight': u'bold', u'title_color': u'#444444', u'header_bounds': 0, u'title_font': u'Helvetica Neue', u'link_color': u'#529ECC', u'header_image_focused': u'http://assets.tumblr.com/images/default_header/optica_pattern_04.png?_v=7c4e5e82cf797042596e2e64af1c383f', u'show_description': True, u'show_header_image': True, u'header_stretch': True, u'body_font': u'Helvetica Neue', u'show_title': True, u'header_image_scaled': u'http://assets.tumblr.com/images/default_header/optica_pattern_04.png?_v=7c4e5e82cf797042596e2e64af1c383f', u'avatar_shape': u'circle', u'show_avatar': True, u'background_color': u'#F6F6F6', u'header_image': u'http://assets.tumblr.com/images/default_header/optica_pattern_04.png?_v=7c4e5e82cf797042596e2e64af1c383f'}, u'name': u'ask-thecrusaders'}, u'comment': u'<p><strong>"Bar Buddies"</strong><br><br>Dont\u2019 worry Neon, you will have your music video soon enough.</p>', u'post': {u'id': u'74162414750'}}]}, u'short_url': u'http://tmblr.co/ZUGffq155m_eJ', u'date': u'2014-01-22 17:41:01 GMT', u'type': u'video', u'slug': u'ask-thecrusaders-bar-buddies-dont-worry', u'blog_name': u'askbuttonsmom'}
    #youtube_result_1 = handle_video_posts(session,youtube_dict_1)
    #youtube_result_2 = handle_video_posts(session,youtube_dict_2)

    # Vimeo
    vimeo_dict_1 = {u'reblog_key': u'3BuzwM1q', u'reblog': {u'comment': u'', u'tree_html': u'<p><a href="http://robscorner.tumblr.com/post/110250942998/a-hyperfast-preview-video-for-the-kind-of-content" class="tumblr_blog">robscorner</a>:</p><blockquote><p>A hyperfast preview video for the kind of content I\u2019m featuring on Patreon (patreon.com/robaato)! Slower version will be available for my supporters!<br/>MUSIC: The End (T.E.I.N. Pt. 2) | 12th Planet<br/></p><p>Support for high-resolution art, PSDs, process videos, tutorials, character requests, and more!<br/></p></blockquote>', u'trail': [{u'blog': {u'theme': {u'title_font_weight': u'bold', u'header_full_height': 1071, u'title_color': u'#FFFFFF', u'header_bounds': u'92,1581,978,3', u'title_font': u'Gibson', u'link_color': u'#529ECC', u'header_image_focused': u'http://static.tumblr.com/a5a733e78671519e8eb9cf3700ccfb70/ybimlef/1eon5zyi0/tumblr_static_tumblr_static_2df9bnxrqh1c4c8sgk8448s80_focused_v3.jpg', u'show_description': False, u'header_full_width': 1600, u'header_focus_width': 1578, u'header_stretch': True, u'show_header_image': True, u'body_font': u'Helvetica Neue', u'show_title': True, u'header_image_scaled': u'http://static.tumblr.com/cfa3addece89b58093ea0a8a87082653/ybimlef/FWyn5zyhv/tumblr_static_2df9bnxrqh1c4c8sgk8448s80_2048_v2.png', u'avatar_shape': u'square', u'show_avatar': True, u'header_focus_height': 886, u'background_color': u'#337db1', u'header_image': u'http://static.tumblr.com/cfa3addece89b58093ea0a8a87082653/ybimlef/FWyn5zyhv/tumblr_static_2df9bnxrqh1c4c8sgk8448s80.png'}, u'name': u'robscorner'}, u'comment': u'<p>A hyperfast preview video for the kind of content I\u2019m featuring on Patreon (patreon.com/robaato)! Slower version will be available for my supporters!<br>MUSIC: The End (T.E.I.N. Pt. 2) | 12th Planet<br></p><p>Support for high-resolution art, PSDs, process videos, tutorials, character requests, and more!<br></p>', u'post': {u'id': u'110250942998'}}]}, u'thumbnail_width': 295, u'player': [{u'width': 250, u'embed_code': u'<iframe src="https://player.vimeo.com/video/118912193?title=0&byline=0&portrait=0" width="250" height="156" frameborder="0" title="Hyperfast Preview - Mai (Patreon Process Videos)" webkitallowfullscreen mozallowfullscreen allowfullscreen></iframe>'}, {u'width': 400, u'embed_code': u'<iframe src="https://player.vimeo.com/video/118912193?title=0&byline=0&portrait=0" width="400" height="250" frameborder="0" title="Hyperfast Preview - Mai (Patreon Process Videos)" webkitallowfullscreen mozallowfullscreen allowfullscreen></iframe>'}, {u'width': 500, u'embed_code': u'<iframe src="https://player.vimeo.com/video/118912193?title=0&byline=0&portrait=0" width="500" height="312" frameborder="0" title="Hyperfast Preview - Mai (Patreon Process Videos)" webkitallowfullscreen mozallowfullscreen allowfullscreen></iframe>'}], u'id': 110255840681, u'post_url': u'http://nsfw.kevinsano.com/post/110255840681/robscorner-a-hyperfast-preview-video-for-the-kind', u'source_title': u'robscorner', u'tags': [u'reblog', u'erohua'], u'highlighted': [], u'state': u'published', u'short_url': u'http://tmblr.co/Zo9zBq1chmfsf', u'html5_capable': True, u'type': u'video', u'format': u'html', u'timestamp': 1423238010, u'note_count': 415, u'video_type': u'vimeo', u'source_url': u'http://robscorner.tumblr.com/post/110250942998/a-hyperfast-preview-video-for-the-kind-of-content', u'date': u'2015-02-06 15:53:30 GMT', u'thumbnail_height': 184, u'permalink_url': u'https://vimeo.com/118912193', u'slug': u'robscorner-a-hyperfast-preview-video-for-the-kind', u'blog_name': u'nsfwkevinsano', u'caption': u'<p><a href="http://robscorner.tumblr.com/post/110250942998/a-hyperfast-preview-video-for-the-kind-of-content" class="tumblr_blog">robscorner</a>:</p><blockquote><p>A hyperfast preview video for the kind of content I\u2019m featuring on Patreon (patreon.com/robaato)! Slower version will be available for my supporters!<br/>MUSIC: The End (T.E.I.N. Pt. 2) | 12th Planet<br/></p><p>Support for high-resolution art, PSDs, process videos, tutorials, character requests, and more!<br/></p></blockquote>', u'thumbnail_url': u'https://i.vimeocdn.com/video/506047324_295x166.jpg'}
    #vimeo_result_1 = handle_video_posts(session,vimeo_dict_1)

    # Imgur
    imgur_post_dict = {u'highlighted': [], u'reblog_key': u'qX0EtplN', u'player': [{u'width': 250, u'embed_code': u'<iframe class="imgur-embed" width="100%" height="720" frameborder="0" src="http://i.imgur.com/wSBlRyv.gifv#embed"></iframe>'}, {u'width': 400, u'embed_code': u'<iframe class="imgur-embed" width="100%" height="720" frameborder="0" src="http://i.imgur.com/wSBlRyv.gifv#embed"></iframe>'}, {u'width': 500, u'embed_code': u'<iframe class="imgur-embed" width="100%" height="720" frameborder="0" src="http://i.imgur.com/wSBlRyv.gifv#embed"></iframe>'}], u'format': u'html', u'timestamp': 1415466120, u'note_count': 109, u'tags': [], u'thumbnail_width': 0, u'id': 102102282191, u'post_url': u'http://jessicaanner.tumblr.com/post/102102282191/front-view-clothed-large-version-gif-back', u'caption': u'<p><em><strong><a href="http://jessicaanner.tumblr.com/post/101601852991/front-view-clothed-large-version-gif-back">Front View (Clothed)</a> <a href="http://i.imgur.com/fDixfAC.gifv"><span class="auto_link" title="">(Large version)</span></a><a href="http://d.facdn.net/art/benezia/1414952655.benezia_front_armored_optimized.gif"><span class="auto_link" title=""> (GIF)</span></a></strong></em><br/><em><strong><a href="http://jessicaanner.tumblr.com/post/101666148721/front-view-clothed-large-version-gif-back">Back View (Clothed)</a> <a href="http://i.imgur.com/QYfRNeQ.gifv" title="">(Large version)</a> <a href="http://d.facdn.net/art/benezia/1415012804.benezia_back_armored_optimized.gif">(GIF)</a></strong></em><br/><em><strong><a href="http://jessicaanner.tumblr.com/post/101768307896/front-view-clothed-large-version-gif-back">Front View (Nude)</a> <a href="http://i.imgur.com/0N7ir7o.gifv">(Large version)</a> <a href="http://d.facdn.net/art/benezia/1415120393.benezia_front_nude_optimized.gif" title="">(GIF)</a></strong></em><br/><em><strong><a href="http://jessicaanner.tumblr.com/post/101852253284/front-view-clothed-large-version-gif-back">Back View (Nude)</a> <a href="http://i.imgur.com/sP5h9ux.gifv" title="">(Large version)</a> <a href="http://d.facdn.net/art/benezia/1415120590.benezia_back_nude_optimized.gif" title="">(GIF)</a></strong></em><br/><strong><em><a href="http://jessicaanner.tumblr.com/post/101934955336/front-view-clothed-large-version-gif-back">Buttocks Closeup View</a> <a href="http://i.imgur.com/BXMYuxk.gifv" title="">(Large version)</a> <a href="http://i.imgur.com/3bhzRP2.gif">(GIF)</a></em></strong><br/><em><strong><a href="http://jessicaanner.tumblr.com/post/102102282191/front-view-clothed-large-version-gif-back">Crotch Closeup View</a> <a href="http://i.imgur.com/wSBlRyv.gifv">(Large version)</a> <a href="http://i.imgur.com/UiDU1XB.gif">(GIF)</a></strong></em><br/><em><strong><a href="http://jessicaanner.tumblr.com/post/102017653601/front-view-clothed-large-version-gif-back">Bust Closeup View</a> <a href="http://i.imgur.com/S5M6PID.gifv">(Large version)</a> <a href="http://i.imgur.com/BlMYohP.gif">(GIF)</a></strong></em></p>', u'state': u'published', u'html5_capable': False, u'video_type': u'unknown', u'short_url': u'http://tmblr.co/ZLO7Om1V5nI-F', u'date': u'2014-11-08 17:02:00 GMT', u'thumbnail_height': 0, u'thumbnail_url': u'', u'type': u'video', u'slug': u'front-view-clothed-large-version-gif-back', u'blog_name': u'jessicaanner'}
    #imgur_result = handle_video_posts(session,imgur_post_dict)

    # Vine
    vine_dict = {u'reblog_key': u'A5DhHt28', u'reblog': {u'comment': u'<p>Have a nice weekend, Tumblr.&nbsp;</p>', u'tree_html': u'', u'trail': []}, u'placement_id': u'{"i":"mF4avY6GyshXjaQmfk0v","v":4,"t":1427193020,"c":{"p":"113540981790","b":"staff"},"d":{"v":{"e":"hjWIUFOYD31"}},"h":"3291f1aa07"}', u'thumbnail_width': 480, u'player': [{u'width': 250, u'embed_code': u'<iframe class="vine-embed" src="https://vine.co/v/hjWIUFOYD31/embed/simple"width="250" height="250" frameborder="0"></iframe><script async src="//platform.vine.co/static/scripts/embed.js" charset="utf-8"></script>'}, {u'width': 400, u'embed_code': u'<iframe class="vine-embed" src="https://vine.co/v/hjWIUFOYD31/embed/simple"width="400" height="400" frameborder="0"></iframe><script async src="//platform.vine.co/static/scripts/embed.js" charset="utf-8"></script>'}, {u'width': 500, u'embed_code': u'<iframe class="vine-embed" src="https://vine.co/v/hjWIUFOYD31/embed/simple"width="500" height="500" frameborder="0"></iframe><script async src="//platform.vine.co/static/scripts/embed.js" charset="utf-8"></script>'}], u'id': 113540981790L, u'post_url': u'http://staff.tumblr.com/post/113540981790/have-a-nice-weekend-tumblr', u'source_title': u'weloveshortvideos.com', u'tags': [], u'highlighted': [], u'state': u'published', u'short_url': u'http://tmblr.co/ZE5Fby1flaUGU', u'html5_capable': True, u'type': u'video', u'format': u'html', u'timestamp': 1426282797, u'note_count': 48309, u'video_type': u'vine', u'source_url': u'http://weloveshortvideos.com', u'date': u'2015-03-13 21:39:57 GMT', u'thumbnail_height': 480, u'permalink_url': u'https://vine.co/v/hjWIUFOYD31', u'slug': u'have-a-nice-weekend-tumblr', u'blog_name': u'staff', u'caption': u'<p>Have a nice weekend, Tumblr.\xa0</p>', u'thumbnail_url': u'http://v.cdn.vine.co/r/thumbs/FE4C8DC8781008139866036658176_1c16044fdd3.3.4.mp4_l_pAXVyCckNVnk2OzdadqNB_6bq4mYoBHpBFRIF8Hi3OdOW1vmjP1TR075G1ZegT.jpg?versionId=abawWSw4Y_QFv2TKPWz6j8N5y7.6LOGq'}
    #vine_restult = handle_video_posts(session,vine_dict)

    # Tumblr
    tumblr_video_post_dict = {u'reblog_key': u'3bqfxHgy', u'short_url': u'http://tmblr.co/Z_sLQw1eYTSqS', u'thumbnail_width': 480, u'player': [{u'width': 250, u'embed_code': u'<iframe width="250" height="140" id="youtube_iframe" src="https://www.youtube.com/embed/tT5pifkZzEk?feature=oembed&amp;enablejsapi=1&amp;origin=http://safe.txmblr.com&amp;wmode=opaque" frameborder="0" allowfullscreen></iframe>'}, {u'width': 400, u'embed_code': u'<iframe width="400" height="225" id="youtube_iframe" src="https://www.youtube.com/embed/tT5pifkZzEk?feature=oembed&amp;enablejsapi=1&amp;origin=http://safe.txmblr.com&amp;wmode=opaque" frameborder="0" allowfullscreen></iframe>'}, {u'width': 500, u'embed_code': u'<iframe width="500" height="281" id="youtube_iframe" src="https://www.youtube.com/embed/tT5pifkZzEk?feature=oembed&amp;enablejsapi=1&amp;origin=http://safe.txmblr.com&amp;wmode=opaque" frameborder="0" allowfullscreen></iframe>'}], u'id': 112247295260L, u'post_url': u'http://tsitra360.tumblr.com/post/112247295260/my-latest-art-timelapse-is-up-see-how-i-drew', u'tags': [], u'highlighted': [], u'state': u'published', u'html5_capable': True, u'type': u'video', u'format': u'html', u'timestamp': 1425068852, u'note_count': 79, u'video_type': u'youtube', u'date': u'2015-02-27 20:27:32 GMT', u'thumbnail_height': 360, u'permalink_url': u'https://www.youtube.com/watch?v=tT5pifkZzEk', u'slug': u'my-latest-art-timelapse-is-up-see-how-i-drew', u'blog_name': u'tsitra360', u'caption': u'<p>My latest art timelapse is up! See how I drew Berry Swirl on my youtube channel.</p>', u'thumbnail_url': u'https://i.ytimg.com/vi/tT5pifkZzEk/hqdefault.jpg'}
    #tumblr_Result = handle_video_posts(session,tumblr_video_post_dict)

    # Yahoo video
    yahoo_post_dict = {u'reblog_key': u'GGWw7A77', u'reblog': {u'comment': u'<p>It&rsquo;s really happening!</p>', u'tree_html': u'<p><a class="tumblr_blog" href="http://whitehouse.tumblr.com/post/88396016693/obamairl">whitehouse</a>:</p><blockquote>\n<p>President Obama is answering your questions on education and college affordability in his first-ever Tumblr Q&amp;A today.</p>\n<p>Tune in right here at 4 p.m. ET, and make sure to follow us @<a class="tumblelog" href="http://tmblr.co/mWgXp6TEB4GEsC_jKXfrSvw">whitehouse</a>.</p>\n</blockquote>', u'trail': [{u'blog': {u'theme': {u'title_font_weight': u'bold', u'header_full_height': 1056, u'title_color': u'#444444', u'header_bounds': u'43,1500,887,0', u'title_font': u'Gibson', u'link_color': u'#529ECC', u'header_image_focused': u'http://static.tumblr.com/861cd9f032b93a7ace681b4fcb7d05e4/mjqkjev/pEEn56435/tumblr_static_tumblr_static_17trsnvc8xes0og8kgk88coc0_focused_v3.jpg', u'show_description': True, u'header_full_width': 1500, u'header_focus_width': 1500, u'header_stretch': True, u'show_header_image': True, u'body_font': u'Helvetica Neue', u'show_title': True, u'header_image_scaled': u'http://static.tumblr.com/861cd9f032b93a7ace681b4fcb7d05e4/mjqkjev/sgln56432/tumblr_static_17trsnvc8xes0og8kgk88coc0_2048_v2.jpg', u'avatar_shape': u'square', u'show_avatar': True, u'header_focus_height': 844, u'background_color': u'#FAFAFA', u'header_image': u'http://static.tumblr.com/861cd9f032b93a7ace681b4fcb7d05e4/mjqkjev/sgln56432/tumblr_static_17trsnvc8xes0og8kgk88coc0.jpg'}, u'name': u'whitehouse'}, u'comment': u'<p>President Obama is answering your questions on education and college affordability in his first-ever Tumblr Q&A today.</p>\n<p>Tune in right here at 4 p.m. ET, and make sure to follow us @<a class="tumblelog" href="http://tmblr.co/mWgXp6TEB4GEsC_jKXfrSvw">whitehouse</a>.</p>', u'post': {u'id': u'88396016693'}}]}, u'thumbnail_width': 320, u'player': [{u'width': 250, u'embed_code': u'<iframe width="250" height="140" src="https://news.yahoo.com/video/tumblr-goes-white-house-190000218.html?format=embed" frameborder="0" allowfullscreen></iframe>'}, {u'width': 400, u'embed_code': u'<iframe width="400" height="225" src="https://news.yahoo.com/video/tumblr-goes-white-house-190000218.html?format=embed" frameborder="0" allowfullscreen></iframe>'}, {u'width': 500, u'embed_code': u'<iframe width="500" height="281" src="https://news.yahoo.com/video/tumblr-goes-white-house-190000218.html?format=embed" frameborder="0" allowfullscreen></iframe>'}], u'id': 88400573880, u'post_url': u'http://staff.tumblr.com/post/88400573880/whitehouse-president-obama-is-answering-your', u'tags': [u'ObamaIRL'], u'highlighted': [], u'state': u'published', u'short_url': u'http://tmblr.co/ZE5Fby1IL5RMu', u'html5_capable': True, u'type': u'video', u'format': u'html', u'timestamp': 1402430040, u'note_count': 9899, u'video_type': u'yahoo', u'date': u'2014-06-10 19:54:00 GMT', u'thumbnail_height': 180, u'permalink_url': u'https://news.yahoo.com/video/tumblr-goes-white-house-190000218.html', u'slug': u'whitehouse-president-obama-is-answering-your', u'blog_name': u'staff', u'caption': u'<p><a class="tumblr_blog" href="http://whitehouse.tumblr.com/post/88396016693/obamairl">whitehouse</a>:</p>\n<blockquote>\n<p>President Obama is answering your questions on education and college affordability in his first-ever Tumblr Q&amp;A today.</p>\n<p>Tune in right here at 4 p.m. ET, and make sure to follow us @<a class="tumblelog" href="http://tmblr.co/mWgXp6TEB4GEsC_jKXfrSvw">whitehouse</a>.</p>\n</blockquote>\n<p>It\u2019s really happening!</p>', u'thumbnail_url': u'https://s1.yimg.com/uu/api/res/1.2/JW58D_.UFfRLkBOrIemIXw--/dz0zMjA7c209MTtmaT1maWxsO3B5b2ZmPTA7aD0xODA7YXBwaWQ9eXRhY2h5b24-/http://l.yimg.com/os/publish-images/ivy/2014-06-10/912811c0-f0c6-11e3-bb53-bd3ad1c7b3ec_06102014_tumblr_white_house.jpg'}
    #yahoo_result = handle_video_posts(session,yahoo_post_dict)

    # Livestream
    livestream_post_dict_1 ={u'reblog_key': u'oapXWQlr', u'reblog': {u'comment': u'<p><span>To reiterate: this an&nbsp;</span><strong>only</strong><span>&nbsp;and an&nbsp;</span><strong>exclusive&nbsp;</strong><span>and it&nbsp;</span><strong>starts in just a few minutes</strong><span>. Hurry on over. &nbsp;</span></p>', u'tree_html': u'<p><a class="tumblr_blog" href="http://92y.tumblr.com/post/101031505431/watch-the-92y-livestream-of-game-of-thrones">92y</a>:</p><blockquote>\n<p>Watch the 92Y Livestream of <strong>Game of Thrones</strong> creator <strong>George R.R. Martin, TONIGHT at 8\xa0pm ET</strong>, in his <strong>only</strong> public U.S. appearance for the release of <a href="http://www.amazon.com/gp/product/B00EGMGGVK/ref=as_li_tl?ie=UTF8&amp;camp=1789&amp;creative=390957&amp;creativeASIN=B00EGMGGVK&amp;linkCode=as2&amp;tag=92y-20&amp;linkId=V3MMY57QIQ7QVFNK"><em>The World of Ice and Fire: The Untold History of Westeros and the Game of Thrones</em></a>. Exclusively on Tumblr!</p>\n</blockquote>', u'trail': [{u'blog': {u'theme': {u'title_font_weight': u'bold', u'title_color': u'#444444', u'header_bounds': u'', u'title_font': u'Gibson', u'link_color': u'#529ECC', u'header_image_focused': u'http://assets.tumblr.com/images/default_header/optica_pattern_13_focused_v3.png?_v=2f4063be1dd2ee91e4eca54332e25191', u'show_description': True, u'show_header_image': True, u'header_stretch': True, u'body_font': u'Helvetica Neue', u'show_title': True, u'header_image_scaled': u'http://assets.tumblr.com/images/default_header/optica_pattern_13_focused_v3.png?_v=2f4063be1dd2ee91e4eca54332e25191', u'avatar_shape': u'square', u'show_avatar': True, u'background_color': u'#FAFAFA', u'header_image': u'http://assets.tumblr.com/images/default_header/optica_pattern_13.png?_v=2f4063be1dd2ee91e4eca54332e25191'}, u'name': u'92y'}, u'comment': u'<p>Watch the 92Y Livestream of <strong>Game of Thrones</strong> creator <strong>George R.R. Martin, TONIGHT at 8\xa0pm ET</strong>, in his <strong>only</strong> public U.S. appearance for the release of <a href="http://www.amazon.com/gp/product/B00EGMGGVK/ref=as_li_tl?ie=UTF8&camp=1789&creative=390957&creativeASIN=B00EGMGGVK&linkCode=as2&tag=92y-20&linkId=V3MMY57QIQ7QVFNK"><em>The World of Ice and Fire: The Untold History of Westeros and the Game of Thrones</em></a>. Exclusively on Tumblr!</p>', u'post': {u'id': u'101031505431'}}]}, u'thumbnail_width': 0, u'player': [{u'width': 250, u'embed_code': u'<iframe src="http://new.livestream.com/accounts/1249127/events/3464519/player?width=560&height=315&autoPlay=true&mute=false" width="250" height="140" frameborder="0" scrolling="no"> </iframe>'}, {u'width': 400, u'embed_code': u'<iframe src="http://new.livestream.com/accounts/1249127/events/3464519/player?width=560&height=315&autoPlay=true&mute=false" width="400" height="225" frameborder="0" scrolling="no"> </iframe>'}, {u'width': 500, u'embed_code': u'<iframe src="http://new.livestream.com/accounts/1249127/events/3464519/player?width=560&height=315&autoPlay=true&mute=false" width="500" height="281" frameborder="0" scrolling="no"> </iframe>'}], u'id': 101038462325, u'post_url': u'http://staff.tumblr.com/post/101038462325/92y-watch-the-92y-livestream-of-game-of-thrones', u'tags': [], u'highlighted': [], u'state': u'published', u'short_url': u'http://tmblr.co/ZE5Fby1U6N9Lr', u'html5_capable': False, u'type': u'video', u'format': u'html', u'timestamp': 1414366397, u'note_count': 917, u'video_type': u'unknown', u'date': u'2014-10-26 23:33:17 GMT', u'thumbnail_height': 0, u'slug': u'92y-watch-the-92y-livestream-of-game-of-thrones', u'blog_name': u'staff', u'caption': u'<p><a class="tumblr_blog" href="http://92y.tumblr.com/post/101031505431/watch-the-92y-livestream-of-game-of-thrones">92y</a>:</p>\n<blockquote>\n<p>Watch the 92Y Livestream of <strong>Game of Thrones</strong> creator <strong>George R.R. Martin, TONIGHT at 8\xa0pm ET</strong>, in his <strong>only</strong> public U.S. appearance for the release of <a href="http://www.amazon.com/gp/product/B00EGMGGVK/ref=as_li_tl?ie=UTF8&amp;camp=1789&amp;creative=390957&amp;creativeASIN=B00EGMGGVK&amp;linkCode=as2&amp;tag=92y-20&amp;linkId=V3MMY57QIQ7QVFNK"><em>The World of Ice and Fire: The Untold History of Westeros and the Game of Thrones</em></a>. Exclusively on Tumblr!</p>\n</blockquote>\n<p><span>To reiterate: this an\xa0</span><strong>only</strong><span>\xa0and an\xa0</span><strong>exclusive\xa0</strong><span>and it\xa0</span><strong>starts in just a few minutes</strong><span>. Hurry on over. \xa0</span></p>', u'thumbnail_url': u''}
    #livestream_result_1 = handle_video_posts(session,livestream_post_dict_1)
    livestream_post_dict_2 = {u'reblog_key': u'oapXWQlr', u'reblog': {u'comment': u'<p><span>To reiterate: this an&nbsp;</span><strong>only</strong><span>&nbsp;and an&nbsp;</span><strong>exclusive&nbsp;</strong><span>and it&nbsp;</span><strong>starts in just a few minutes</strong><span>. Hurry on over. &nbsp;</span></p>', u'tree_html': u'<p><a class="tumblr_blog" href="http://92y.tumblr.com/post/101031505431/watch-the-92y-livestream-of-game-of-thrones">92y</a>:</p><blockquote>\n<p>Watch the 92Y Livestream of <strong>Game of Thrones</strong> creator <strong>George R.R. Martin, TONIGHT at 8\xa0pm ET</strong>, in his <strong>only</strong> public U.S. appearance for the release of <a href="http://www.amazon.com/gp/product/B00EGMGGVK/ref=as_li_tl?ie=UTF8&amp;camp=1789&amp;creative=390957&amp;creativeASIN=B00EGMGGVK&amp;linkCode=as2&amp;tag=92y-20&amp;linkId=V3MMY57QIQ7QVFNK"><em>The World of Ice and Fire: The Untold History of Westeros and the Game of Thrones</em></a>. Exclusively on Tumblr!</p>\n</blockquote>'}, u'thumbnail_width': 0, u'player': [{u'width': 250, u'embed_code': u'<iframe src="http://new.livestream.com/accounts/1249127/events/3464519/player?width=560&height=315&autoPlay=true&mute=false" width="250" height="140" frameborder="0" scrolling="no"> </iframe>'}, {u'width': 400, u'embed_code': u'<iframe src="http://new.livestream.com/accounts/1249127/events/3464519/player?width=560&height=315&autoPlay=true&mute=false" width="400" height="225" frameborder="0" scrolling="no"> </iframe>'}, {u'width': 500, u'embed_code': u'<iframe src="http://new.livestream.com/accounts/1249127/events/3464519/player?width=560&height=315&autoPlay=true&mute=false" width="500" height="281" frameborder="0" scrolling="no"> </iframe>'}], u'id': 101038462325L, u'post_url': u'http://staff.tumblr.com/post/101038462325/92y-watch-the-92y-livestream-of-game-of-thrones', u'tags': [], u'highlighted': [], u'state': u'published', u'short_url': u'http://tmblr.co/ZE5Fby1U6N9Lr', u'html5_capable': False, u'type': u'video', u'format': u'html', u'timestamp': 1414366397, u'note_count': 916, u'video_type': u'unknown', u'trail': [{u'blog': {u'theme': {u'title_font_weight': u'bold', u'title_color': u'#444444', u'header_bounds': 0, u'title_font': u'Gibson', u'link_color': u'#003da8', u'header_image_focused': u'http://static.tumblr.com/53cb545b9361dbb26c47bbe5baef4ba5/rdt1unh/Knvnmtmf2/tumblr_static_dlaci2b0vi804ow8wkswkoc8c_2048_v2.png', u'show_description': True, u'show_header_image': True, u'header_stretch': True, u'body_font': u'Helvetica Neue', u'show_title': True, u'header_image_scaled': u'http://static.tumblr.com/53cb545b9361dbb26c47bbe5baef4ba5/rdt1unh/Knvnmtmf2/tumblr_static_dlaci2b0vi804ow8wkswkoc8c_2048_v2.png', u'avatar_shape': u'square', u'show_avatar': True, u'background_color': u'#fafafa', u'header_image': u'http://static.tumblr.com/53cb545b9361dbb26c47bbe5baef4ba5/rdt1unh/Knvnmtmf2/tumblr_static_dlaci2b0vi804ow8wkswkoc8c.png'}, u'name': u'92y'}, u'content': u'<p>Watch the 92Y Livestream of <strong>Game of Thrones</strong> creator <strong>George R.R. Martin, TONIGHT at 8\xa0pm ET</strong>, in his <strong>only</strong> public U.S. appearance for the release of <a href="http://www.amazon.com/gp/product/B00EGMGGVK/ref=as_li_tl?ie=UTF8&camp=1789&creative=390957&creativeASIN=B00EGMGGVK&linkCode=as2&tag=92y-20&linkId=V3MMY57QIQ7QVFNK"><em>The World of Ice and Fire: The Untold History of Westeros and the Game of Thrones</em></a>. Exclusively on Tumblr!</p>', u'post': {u'id': u'101031505431'}, u'is_root_item': True}, {u'blog': {u'theme': {u'title_font_weight': u'bold', u'title_color': u'#FFFFFF', u'header_bounds': 0, u'title_font': u'Gibson', u'link_color': u'#56BC8A', u'header_image_focused': u'http://static.tumblr.com/10e607f9b9b4c588d1cbd6c9f8b564d9/3hpyv0p/nFBnlgttl/tumblr_static_1sssiwavcjs0gs4cggwsok040_2048_v2.gif', u'show_description': True, u'show_header_image': True, u'header_stretch': True, u'body_font': u'Helvetica Neue', u'show_title': True, u'header_image_scaled': u'http://static.tumblr.com/10e607f9b9b4c588d1cbd6c9f8b564d9/3hpyv0p/nFBnlgttl/tumblr_static_1sssiwavcjs0gs4cggwsok040_2048_v2.gif', u'avatar_shape': u'square', u'show_avatar': False, u'background_color': u'#37475c', u'header_image': u'http://static.tumblr.com/10e607f9b9b4c588d1cbd6c9f8b564d9/3hpyv0p/nFBnlgttl/tumblr_static_1sssiwavcjs0gs4cggwsok040.gif'}, u'name': u'staff'}, u'content': u'<p><span>To reiterate: this an\xa0</span><strong>only</strong><span>\xa0and an\xa0</span><strong>exclusive\xa0</strong><span>and it\xa0</span><strong>starts in just a few minutes</strong><span>. Hurry on over. \xa0</span></p>', u'post': {u'id': u'101038462325'}, u'content_raw': u'<p><span>To reiterate: this an&nbsp;</span><strong>only</strong><span>&nbsp;and an&nbsp;</span><strong>exclusive&nbsp;</strong><span>and it&nbsp;</span><strong>starts in just a few minutes</strong><span>. Hurry on over. &nbsp;</span></p>', u'is_current_item': True}], u'date': u'2014-10-26 23:33:17 GMT', u'thumbnail_height': 0, u'slug': u'92y-watch-the-92y-livestream-of-game-of-thrones', u'blog_name': u'staff', u'caption': u'<p><a class="tumblr_blog" href="http://92y.tumblr.com/post/101031505431/watch-the-92y-livestream-of-game-of-thrones">92y</a>:</p>\n<blockquote>\n<p>Watch the 92Y Livestream of <strong>Game of Thrones</strong> creator <strong>George R.R. Martin, TONIGHT at 8\xa0pm ET</strong>, in his <strong>only</strong> public U.S. appearance for the release of <a href="http://www.amazon.com/gp/product/B00EGMGGVK/ref=as_li_tl?ie=UTF8&amp;camp=1789&amp;creative=390957&amp;creativeASIN=B00EGMGGVK&amp;linkCode=as2&amp;tag=92y-20&amp;linkId=V3MMY57QIQ7QVFNK"><em>The World of Ice and Fire: The Untold History of Westeros and the Game of Thrones</em></a>. Exclusively on Tumblr!</p>\n</blockquote>\n<p><span>To reiterate: this an\xa0</span><strong>only</strong><span>\xa0and an\xa0</span><strong>exclusive\xa0</strong><span>and it\xa0</span><strong>starts in just a few minutes</strong><span>. Hurry on over. \xa0</span></p>', u'thumbnail_url': u''}
    #livestream_result_2 = handle_video_posts(session,livestream_post_dict_2)
    #logging.info("livestream_result_2:"+repr(livestream_result_2))

    # dailymotion
    dailymotion_post_dict = {u'reblog_key': u'itw5H3n3', u'reblog': {u'comment': u'<p>Dat ending</p>', u'tree_html': u'<p><a href="http://orcasnack-garth.tumblr.com/post/116512570927/i-made-a-video-a-silly-video-with-vore-of-my" class="tumblr_blog" target="_blank">orcasnack-garth</a>:</p><blockquote><p>I made a video! A silly video with vore of my favorite Disney Princess Mermaid and her pet killer whale who may or may not be canon. Enjoy the silliness!\n\n</p><p><a href="http://orcasnack-garth.tumblr.com/post/116512570927/i-made-a-video-a-silly-video-with-vore-of-my" target="_blank">Read More</a></p></blockquote>', u'trail': [{u'blog': {u'theme': {u'title_font_weight': u'bold', u'title_color': u'#444444', u'header_bounds': u'', u'title_font': u'Gibson', u'link_color': u'#529ECC', u'header_image_focused': u'http://assets.tumblr.com/images/default_header/optica_pattern_05.png?_v=671444c5f47705cce40d8aefd23df3b1', u'show_description': True, u'show_header_image': True, u'header_stretch': True, u'body_font': u'Helvetica Neue', u'show_title': True, u'header_image_scaled': u'http://assets.tumblr.com/images/default_header/optica_pattern_05.png?_v=671444c5f47705cce40d8aefd23df3b1', u'avatar_shape': u'square', u'show_avatar': True, u'background_color': u'#FAFAFA', u'header_image': u'http://assets.tumblr.com/images/default_header/optica_pattern_05.png?_v=671444c5f47705cce40d8aefd23df3b1'}, u'name': u'orcasnack-garth'}, u'comment': u'<p>I made a video! A silly video with vore of my favorite Disney Princess Mermaid and her pet killer whale who may or may not be canon. Enjoy the silliness!\n\n</p><p><a href="http://orcasnack-garth.tumblr.com/post/116512570927/i-made-a-video-a-silly-video-with-vore-of-my" target="_blank">Read More</a></p>', u'post': {u'id': u'116512570927'}}]}, u'thumbnail_width': 430, u'player': [{u'width': 250, u'embed_code': u'<iframe src="https://www.dailymotion.com/embed/video/x2msryd" width="250" height="139" frameborder="0" allowfullscreen></iframe>'}, {u'width': 400, u'embed_code': u'<iframe src="https://www.dailymotion.com/embed/video/x2msryd" width="400" height="222" frameborder="0" allowfullscreen></iframe>'}, {u'width': 500, u'embed_code': u'<iframe src="https://www.dailymotion.com/embed/video/x2msryd" width="500" height="278" frameborder="0" allowfullscreen></iframe>'}], u'id': 116527639439, u'post_url': u'http://ponyoptica.tumblr.com/post/116527639439/orcasnack-garth-i-made-a-video-a-silly-video', u'tags': [], u'highlighted': [], u'state': u'published', u'short_url': u'http://tmblr.co/Z0KBot1iXbgkF', u'html5_capable': True, u'type': u'video', u'format': u'html', u'timestamp': 1429155957, u'note_count': 5, u'video_type': u'dailymotion', u'date': u'2015-04-16 03:45:57 GMT', u'thumbnail_height': 240, u'permalink_url': u'http://www.dailymotion.com/video/x2msryd', u'slug': u'orcasnack-garth-i-made-a-video-a-silly-video', u'blog_name': u'ponyoptica', u'caption': u'<p><a href="http://orcasnack-garth.tumblr.com/post/116512570927/i-made-a-video-a-silly-video-with-vore-of-my" class="tumblr_blog" target="_blank">orcasnack-garth</a>:</p>\n\n<blockquote><p>I made a video! A silly video with vore of my favorite Disney Princess Mermaid and her pet killer whale who may or may not be canon. Enjoy the silliness!\n\n</p><p><a href="http://orcasnack-garth.tumblr.com/post/116512570927/i-made-a-video-a-silly-video-with-vore-of-my" target="_blank">Read More</a></p></blockquote>\n\n<p>Dat ending</p>', u'thumbnail_url': u'https://s2-ssl.dmcdn.net/J8u2z/x240-zHV.jpg'}
    #dailymotion_result = handle_video_posts(session,dailymotion_post_dict)

    # instagram
    instagram_post_dict = {u'reblog_key': u'rEWRmG6V', u'reblog': {u'comment': u'<p>Must be fun to have a horse~.&nbsp;</p>', u'tree_html': u'<p><a class="tumblr_blog" href="http://askrainestallion.tumblr.com/post/69426515274/raine-and-may-walking-together-mini-horses">askrainestallion</a>:</p><blockquote>\n<p>Raine and May walking together #mini #horses #walking #sunny #snow #raine #may #backyard #grass #cold #cloudy #country #outside #oregon #playing</p>\n</blockquote>', u'trail': [{u'blog': {u'theme': {u'title_font_weight': u'bold', u'title_color': u'#444444', u'header_bounds': u'', u'title_font': u'Gibson', u'link_color': u'#529ECC', u'header_image_focused': u'http://assets.tumblr.com/images/default_header/optica_pattern_09_focused_v3.png?_v=abe6f565397f54e880c2b76e6fc2022e', u'show_description': True, u'show_header_image': True, u'header_stretch': True, u'body_font': u'Helvetica Neue', u'show_title': True, u'header_image_scaled': u'http://assets.tumblr.com/images/default_header/optica_pattern_09_focused_v3.png?_v=abe6f565397f54e880c2b76e6fc2022e', u'avatar_shape': u'square', u'show_avatar': True, u'background_color': u'#FAFAFA', u'header_image': u'http://assets.tumblr.com/images/default_header/optica_pattern_09.png?_v=abe6f565397f54e880c2b76e6fc2022e'}, u'name': u'askrainestallion'}, u'comment': u'<p>Raine and May walking together #mini #horses #walking #sunny #snow #raine #may #backyard #grass #cold #cloudy #country #outside #oregon #playing</p>', u'post': {u'id': u'69426515274'}}]}, u'thumbnail_width': 306, u'player': [{u'width': 250, u'embed_code': u'<blockquote class="instagram-media" data-instgrm-version="4" style=" background:#FFF; border:0; border-radius:3px; box-shadow:0 0 1px 0 rgba(0,0,0,0.5),0 1px 10px 0 rgba(0,0,0,0.15); margin: 1px; max-width: 250px; padding:0; width:99.375%; width:-webkit-calc(100% - 2px); width:calc(100% - 2px);"><div style="padding:8px;"> <div style=" background:#F8F8F8; line-height:0; margin-top:40px; padding:50% 0; text-align:center; width:100%;"> <div style=" background:url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACwAAAAsCAMAAAApWqozAAAAGFBMVEUiIiI9PT0eHh4gIB4hIBkcHBwcHBwcHBydr+JQAAAACHRSTlMABA4YHyQsM5jtaMwAAADfSURBVDjL7ZVBEgMhCAQBAf//42xcNbpAqakcM0ftUmFAAIBE81IqBJdS3lS6zs3bIpB9WED3YYXFPmHRfT8sgyrCP1x8uEUxLMzNWElFOYCV6mHWWwMzdPEKHlhLw7NWJqkHc4uIZphavDzA2JPzUDsBZziNae2S6owH8xPmX8G7zzgKEOPUoYHvGz1TBCxMkd3kwNVbU0gKHkx+iZILf77IofhrY1nYFnB/lQPb79drWOyJVa/DAvg9B/rLB4cC+Nqgdz/TvBbBnr6GBReqn/nRmDgaQEej7WhonozjF+Y2I/fZou/qAAAAAElFTkSuQmCC); display:block; height:44px; margin:0 auto -44px; position:relative; top:-22px; width:44px;"></div></div><p style=" color:#c9c8cd; font-family:Arial,sans-serif; font-size:14px; line-height:17px; margin-bottom:0; margin-top:8px; overflow:hidden; padding:8px 0 7px; text-align:center; text-overflow:ellipsis; white-space:nowrap;"><a href="https://instagram.com/p/hrekk_DDnp/" style=" color:#c9c8cd; font-family:Arial,sans-serif; font-size:14px; font-style:normal; font-weight:normal; line-height:17px; text-decoration:none;" target="_top">A video posted by Dustin (@rainesfarm)</a> on <time style=" font-family:Arial,sans-serif; font-size:14px; line-height:17px;" datetime="2013-12-08T23:37:30+00:00">Dec 8, 2013 at 3:37pm PST</time></p></div></blockquote>\n<script async defer src="//platform.instagram.com/en_US/embeds.js"></script>'}, {u'width': 400, u'embed_code': u'<blockquote class="instagram-media" data-instgrm-version="4" style=" background:#FFF; border:0; border-radius:3px; box-shadow:0 0 1px 0 rgba(0,0,0,0.5),0 1px 10px 0 rgba(0,0,0,0.15); margin: 1px; max-width: 400px; padding:0; width:99.375%; width:-webkit-calc(100% - 2px); width:calc(100% - 2px);"><div style="padding:8px;"> <div style=" background:#F8F8F8; line-height:0; margin-top:40px; padding:50% 0; text-align:center; width:100%;"> <div style=" background:url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACwAAAAsCAMAAAApWqozAAAAGFBMVEUiIiI9PT0eHh4gIB4hIBkcHBwcHBwcHBydr+JQAAAACHRSTlMABA4YHyQsM5jtaMwAAADfSURBVDjL7ZVBEgMhCAQBAf//42xcNbpAqakcM0ftUmFAAIBE81IqBJdS3lS6zs3bIpB9WED3YYXFPmHRfT8sgyrCP1x8uEUxLMzNWElFOYCV6mHWWwMzdPEKHlhLw7NWJqkHc4uIZphavDzA2JPzUDsBZziNae2S6owH8xPmX8G7zzgKEOPUoYHvGz1TBCxMkd3kwNVbU0gKHkx+iZILf77IofhrY1nYFnB/lQPb79drWOyJVa/DAvg9B/rLB4cC+Nqgdz/TvBbBnr6GBReqn/nRmDgaQEej7WhonozjF+Y2I/fZou/qAAAAAElFTkSuQmCC); display:block; height:44px; margin:0 auto -44px; position:relative; top:-22px; width:44px;"></div></div><p style=" color:#c9c8cd; font-family:Arial,sans-serif; font-size:14px; line-height:17px; margin-bottom:0; margin-top:8px; overflow:hidden; padding:8px 0 7px; text-align:center; text-overflow:ellipsis; white-space:nowrap;"><a href="https://instagram.com/p/hrekk_DDnp/" style=" color:#c9c8cd; font-family:Arial,sans-serif; font-size:14px; font-style:normal; font-weight:normal; line-height:17px; text-decoration:none;" target="_top">A video posted by Dustin (@rainesfarm)</a> on <time style=" font-family:Arial,sans-serif; font-size:14px; line-height:17px;" datetime="2013-12-08T23:37:30+00:00">Dec 8, 2013 at 3:37pm PST</time></p></div></blockquote>\n<script async defer src="//platform.instagram.com/en_US/embeds.js"></script>'}, {u'width': 500, u'embed_code': u'<blockquote class="instagram-media" data-instgrm-version="4" style=" background:#FFF; border:0; border-radius:3px; box-shadow:0 0 1px 0 rgba(0,0,0,0.5),0 1px 10px 0 rgba(0,0,0,0.15); margin: 1px; max-width: 500px; padding:0; width:99.375%; width:-webkit-calc(100% - 2px); width:calc(100% - 2px);"><div style="padding:8px;"> <div style=" background:#F8F8F8; line-height:0; margin-top:40px; padding:50% 0; text-align:center; width:100%;"> <div style=" background:url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACwAAAAsCAMAAAApWqozAAAAGFBMVEUiIiI9PT0eHh4gIB4hIBkcHBwcHBwcHBydr+JQAAAACHRSTlMABA4YHyQsM5jtaMwAAADfSURBVDjL7ZVBEgMhCAQBAf//42xcNbpAqakcM0ftUmFAAIBE81IqBJdS3lS6zs3bIpB9WED3YYXFPmHRfT8sgyrCP1x8uEUxLMzNWElFOYCV6mHWWwMzdPEKHlhLw7NWJqkHc4uIZphavDzA2JPzUDsBZziNae2S6owH8xPmX8G7zzgKEOPUoYHvGz1TBCxMkd3kwNVbU0gKHkx+iZILf77IofhrY1nYFnB/lQPb79drWOyJVa/DAvg9B/rLB4cC+Nqgdz/TvBbBnr6GBReqn/nRmDgaQEej7WhonozjF+Y2I/fZou/qAAAAAElFTkSuQmCC); display:block; height:44px; margin:0 auto -44px; position:relative; top:-22px; width:44px;"></div></div><p style=" color:#c9c8cd; font-family:Arial,sans-serif; font-size:14px; line-height:17px; margin-bottom:0; margin-top:8px; overflow:hidden; padding:8px 0 7px; text-align:center; text-overflow:ellipsis; white-space:nowrap;"><a href="https://instagram.com/p/hrekk_DDnp/" style=" color:#c9c8cd; font-family:Arial,sans-serif; font-size:14px; font-style:normal; font-weight:normal; line-height:17px; text-decoration:none;" target="_top">A video posted by Dustin (@rainesfarm)</a> on <time style=" font-family:Arial,sans-serif; font-size:14px; line-height:17px;" datetime="2013-12-08T23:37:30+00:00">Dec 8, 2013 at 3:37pm PST</time></p></div></blockquote>\n<script async defer src="//platform.instagram.com/en_US/embeds.js"></script>'}], u'id': 69426891231, u'post_url': u'http://snivydaleaf.tumblr.com/post/69426891231/askrainestallion-raine-and-may-walking-together', u'tags': [], u'highlighted': [], u'state': u'published', u'short_url': u'http://tmblr.co/ZVKTlv10gAadV', u'html5_capable': True, u'type': u'video', u'format': u'html', u'timestamp': 1386546205, u'note_count': 3, u'video_type': u'instagram', u'date': u'2013-12-08 23:43:25 GMT', u'thumbnail_height': 306, u'permalink_url': u'https://instagram.com/p/hrekk_DDnp', u'slug': u'askrainestallion-raine-and-may-walking-together', u'blog_name': u'snivydaleaf', u'caption': u'<p><a class="tumblr_blog" href="http://askrainestallion.tumblr.com/post/69426515274/raine-and-may-walking-together-mini-horses">askrainestallion</a>:</p>\n<blockquote>\n<p>Raine and May walking together #mini #horses #walking #sunny #snow #raine #may #backyard #grass #cold #cloudy #country #outside #oregon #playing</p>\n</blockquote>\n<p>Must be fun to have a horse~.\xa0</p>', u'thumbnail_url': u'https://igcdn-photos-c-a.akamaihd.net/hphotos-ak-xpa1/t51.2885-15/1389689_553115131437290_481275793_a.jpg'}
    #instagram_result = handle_video_posts(session,instagram_post_dict)

    # sembeo? looks like an ad
    sembeo_post_dict = {u'reblog_key': u'NpsXvI0e', u'reblog': {u'comment': u'', u'tree_html': u'<p><a class="tumblr_blog" href="http://ask-wolfofsadness.tumblr.com/post/46160407321/tylersthings-bahdumbahdumbombombom">ask-wolfofsadness</a>:</p><blockquote>\n<p><a class="tumblr_blog" href="http://tylersthings.tumblr.com/post/46141661903/bahdumbahdumbombombom-stillnotdavid">tylersthings</a>:</p>\n<blockquote>\n<p><a class="tumblr_blog" href="http://bahdumbahdumbombombom.tumblr.com/post/45945978418/stillnotdavid-incrediblyfree-random-nexus">bahdumbahdumbombombom</a>:</p>\n<blockquote>\n<p><a class="tumblr_blog" href="http://stillnotdavid.tumblr.com/post/41765817778/incrediblyfree-random-nexus-missingone123">stillnotdavid</a>:</p>\n<blockquote>\n<p><a class="tumblr_blog" href="http://incrediblyfree.tumblr.com/post/41763743730/random-nexus-missingone123-technogecho">incrediblyfree</a>:</p>\n<blockquote>\n<p><a class="tumblr_blog" href="http://random-nexus.tumblr.com/post/26899864973/missingone123-technogecho-click-the">random-nexus</a>:</p>\n<blockquote>\n<p><a class="tumblr_blog" href="http://missingone123.tumblr.com/post/18820975157/technogecho-click-the-squares-the-whole">missingone123</a>:</p>\n<blockquote>\n<p><a class="tumblr_blog" href="http://technogecho.tumblr.com/post/18818924591/click-the-squares-the-whole-world-needs-to">technogecho</a>:</p>\n<blockquote>\n<blockquote>\n<p><strong><big><big>CLICK THE SQUARES.</big></big></strong></p>\n<p><img alt="image" height="158" src="http://media.tumblr.com/tumblr_lcsdx6ogB51qbnni6.jpg" width="206"/></p>\n<p><strong><big>THE WHOLE WORLD NEEDS TO KNOW ABOUT THIS.</big></strong></p>\n<p>THIS THIS THIS THIS!</p>\n<p><strong>ALWAYS</strong> REBLOG MUSICAL SQUARES</p>\n<p>YOU HAVE NOT LIVED IF YOU HAVEN\u2019T SEEN THIS YET</p>\n</blockquote>\n<p>these squares are magical</p>\n</blockquote>\n<p>This is amazing.</p>\n</blockquote>\n<p>This! Do It!</p>\n</blockquote>\n<p>aw that was delightful ;3</p>\n</blockquote>\n<p>I made a sick song with this tho.</p>\n</blockquote>\n<p>spent way too long playing with this..</p>\n</blockquote>\n<p>It\u2019s back. IT\u2019S BACK.\xa0<em><strong>IT\u2019S BAAAAACK</strong></em></p>\n</blockquote>\n<p>&lt;3</p>\n</blockquote>', u'trail': [{u'blog': {u'theme': {u'title_font_weight': u'bold', u'title_color': u'#444444', u'header_bounds': u'', u'title_font': u'Gibson', u'link_color': u'#529ECC', u'header_image_focused': u'http://assets.tumblr.com/images/default_header/optica_pattern_01.png?_v=f67ca5ac5d1c4a0526964674cb5a0605', u'show_description': True, u'show_header_image': True, u'header_stretch': True, u'body_font': u'Helvetica Neue', u'show_title': True, u'header_image_scaled': u'http://assets.tumblr.com/images/default_header/optica_pattern_01.png?_v=f67ca5ac5d1c4a0526964674cb5a0605', u'avatar_shape': u'square', u'show_avatar': True, u'background_color': u'#FAFAFA', u'header_image': u'http://assets.tumblr.com/images/default_header/optica_pattern_01.png?_v=f67ca5ac5d1c4a0526964674cb5a0605'}, u'name': u'ask-wolfofsadness'}, u'comment': u'<p><3</p>', u'post': {u'id': u'46160407321'}}, {u'blog': {u'theme': {u'title_font_weight': u'bold', u'header_full_height': 865, u'title_color': u'#444444', u'header_bounds': u'292,1191,865,173', u'title_font': u'Helvetica Neue', u'link_color': u'#529ECC', u'header_image_focused': u'http://static.tumblr.com/819b3dab5176802210eb6b918d1c8eba/ancrs0a/q7vn56dtm/tumblr_static_tumblr_static_82ap7v3vng4csgos48wwwc8o0_focused_v3.png', u'show_description': True, u'header_full_width': 1280, u'header_focus_width': 1018, u'header_stretch': True, u'show_header_image': True, u'body_font': u'Helvetica Neue', u'show_title': True, u'header_image_scaled': u'http://static.tumblr.com/819b3dab5176802210eb6b918d1c8eba/ancrs0a/S7In56dti/tumblr_static_82ap7v3vng4csgos48wwwc8o0_2048_v2.png', u'avatar_shape': u'square', u'show_avatar': True, u'header_focus_height': 573, u'background_color': u'#BFE4A8', u'header_image': u'http://static.tumblr.com/819b3dab5176802210eb6b918d1c8eba/ancrs0a/S7In56dti/tumblr_static_82ap7v3vng4csgos48wwwc8o0.png'}, u'name': u'tylersthings'}, u'comment': u'<p>It\u2019s back. IT\u2019S BACK.\xa0<em><strong>IT\u2019S BAAAAACK</strong></em></p>', u'post': {u'id': u'46141661903'}}, {u'blog': {u'theme': [], u'name': u'bahdumbahdumbombombom'}, u'comment': u'<p>spent way too long playing with this..</p>', u'post': {u'id': u'45945978418'}}, {u'blog': {u'theme': {u'title_font_weight': u'bold', u'title_color': u'#444444', u'header_bounds': 0, u'title_font': u'Gibson', u'link_color': u'#529ECC', u'header_image_focused': u'http://assets.tumblr.com/images/default_header/optica_pattern_14.png?_v=8c2d3b00544b7efbc4ac06dc3f80e374', u'show_description': True, u'show_header_image': True, u'header_stretch': True, u'body_font': u'Helvetica Neue', u'show_title': True, u'header_image_scaled': u'http://assets.tumblr.com/images/default_header/optica_pattern_14.png?_v=8c2d3b00544b7efbc4ac06dc3f80e374', u'avatar_shape': u'square', u'show_avatar': True, u'background_color': u'#FAFAFA', u'header_image': u'http://assets.tumblr.com/images/default_header/optica_pattern_14.png?_v=8c2d3b00544b7efbc4ac06dc3f80e374'}, u'name': u'stillnotdavid'}, u'comment': u'<p>I made a sick song with this tho.</p>', u'post': {u'id': u'41765817778'}}, {u'blog': {u'theme': {u'title_font_weight': u'bold', u'title_color': u'#444444', u'header_bounds': u'', u'title_font': u'Gibson', u'link_color': u'#529ECC', u'header_image_focused': u'http://assets.tumblr.com/images/default_header/optica_pattern_03_focused_v3.png?_v=a0f20b51ed40eb5a930ab86effe42a40', u'show_description': True, u'show_header_image': True, u'header_stretch': True, u'body_font': u'Helvetica Neue', u'show_title': True, u'header_image_scaled': u'http://assets.tumblr.com/images/default_header/optica_pattern_03_focused_v3.png?_v=a0f20b51ed40eb5a930ab86effe42a40', u'avatar_shape': u'square', u'show_avatar': True, u'background_color': u'#FAFAFA', u'header_image': u'http://assets.tumblr.com/images/default_header/optica_pattern_03.png?_v=a0f20b51ed40eb5a930ab86effe42a40'}, u'name': u'incrediblyfree'}, u'comment': u'<p>aw that was delightful ;3</p>', u'post': {u'id': u'41763743730'}}, {u'blog': {u'theme': {u'title_font_weight': u'bold', u'header_full_height': 327, u'title_color': u'#dcecf5', u'header_bounds': u'0,400,225,0', u'title_font': u'Streetscript', u'link_color': u'#2da4ee', u'header_image_focused': u'http://static.tumblr.com/c55ca5ec4f6b6f042563f005cbf332a4/ixzdrhr/uHwnedykl/tumblr_static_tumblr_static_8qgrsom8x0cg0wwkgcw0gwsso_focused_v3.jpg', u'show_description': True, u'header_full_width': 400, u'header_focus_width': 400, u'header_stretch': True, u'show_header_image': True, u'body_font': u'Helvetica Neue', u'show_title': True, u'header_image_scaled': u'http://static.tumblr.com/c55ca5ec4f6b6f042563f005cbf332a4/ixzdrhr/3nSnedykk/tumblr_static_8qgrsom8x0cg0wwkgcw0gwsso_2048_v2.jpg', u'avatar_shape': u'square', u'show_avatar': True, u'header_focus_height': 225, u'background_color': u'#213758', u'header_image': u'http://static.tumblr.com/c55ca5ec4f6b6f042563f005cbf332a4/ixzdrhr/3nSnedykk/tumblr_static_8qgrsom8x0cg0wwkgcw0gwsso.jpg'}, u'name': u'random-nexus'}, u'comment': u'<p>This! Do It!</p>', u'post': {u'id': u'26899864973'}}, {u'blog': {u'theme': {u'title_font_weight': u'bold', u'title_color': u'#444444', u'header_bounds': u'', u'title_font': u'Gibson', u'link_color': u'#529ECC', u'header_image_focused': u'http://assets.tumblr.com/images/default_header/optica_pattern_02_focused_v3.png?_v=b976ee00195b1b7806c94ae285ca46a7', u'show_description': True, u'show_header_image': True, u'header_stretch': True, u'body_font': u'Helvetica Neue', u'show_title': True, u'header_image_scaled': u'http://assets.tumblr.com/images/default_header/optica_pattern_02_focused_v3.png?_v=b976ee00195b1b7806c94ae285ca46a7', u'avatar_shape': u'square', u'show_avatar': True, u'background_color': u'#FAFAFA', u'header_image': u'http://assets.tumblr.com/images/default_header/optica_pattern_02.png?_v=b976ee00195b1b7806c94ae285ca46a7'}, u'name': u'missingone123'}, u'comment': u'<p>This is amazing.</p>', u'post': {u'id': u'18820975157'}}, {u'blog': {u'theme': {u'title_font_weight': u'bold', u'title_color': u'#444444', u'header_bounds': u'', u'title_font': u'Gibson', u'link_color': u'#529ECC', u'header_image_focused': u'http://assets.tumblr.com/images/default_header/optica_pattern_06_focused_v3.png?_v=c5e9c9bdca5f67be80d91514a36509cc', u'show_description': True, u'show_header_image': True, u'header_stretch': True, u'body_font': u'Helvetica Neue', u'show_title': True, u'header_image_scaled': u'http://assets.tumblr.com/images/default_header/optica_pattern_06_focused_v3.png?_v=c5e9c9bdca5f67be80d91514a36509cc', u'avatar_shape': u'square', u'show_avatar': True, u'background_color': u'#FAFAFA', u'header_image': u'http://assets.tumblr.com/images/default_header/optica_pattern_06.png?_v=c5e9c9bdca5f67be80d91514a36509cc'}, u'name': u'technogecho'}, u'comment': u'<blockquote>\n<p><strong><big><big>CLICK THE SQUARES.</big></big></strong></p>\n<p><img alt="image" height="158" src="http://media.tumblr.com/tumblr_lcsdx6ogB51qbnni6.jpg" width="206"></p>\n<p><strong><big>THE WHOLE WORLD NEEDS TO KNOW ABOUT THIS.</big></strong></p>\n<p>THIS THIS THIS THIS!</p>\n<p><strong>ALWAYS</strong> REBLOG MUSICAL SQUARES</p>\n<p>YOU HAVE NOT LIVED IF YOU HAVEN\u2019T SEEN THIS YET</p>', u'post': {u'id': u'18818924591'}}]}, u'thumbnail_width': 0, u'player': [{u'width': 250, u'embed_code': u'</p>\r\n<div align="center"><object width="250" height="250" codebase="http://download.macromedia.com/pub/shockwave/cabs/flash/swflash.cab#version=5,0,0,0" classid="clsid:D27CDB6E-AE6D-11cf-96B8-444553540000"><param value="http://www.sembeo.com/media/Matrix.swf" name="movie"><param value="high" name="quality"><embed width="250" height="250" type="application/x-shockwave-flash" pluginspage="http://www.macromedia.com/shockwave/download/index.cgi?P1_Prod_Version=ShockwaveFlash" quality="high" src="http://www.sembeo.com/media/Matrix.swf"></object><br/><a href="http://www.sembeo.com/">Insurance</a></div>\r\n<p>'}, {u'width': 400, u'embed_code': u'</p>\r\n<div align="center"><object width="400" height="400" codebase="http://download.macromedia.com/pub/shockwave/cabs/flash/swflash.cab#version=5,0,0,0" classid="clsid:D27CDB6E-AE6D-11cf-96B8-444553540000"><param value="http://www.sembeo.com/media/Matrix.swf" name="movie"><param value="high" name="quality"><embed width="400" height="400" type="application/x-shockwave-flash" pluginspage="http://www.macromedia.com/shockwave/download/index.cgi?P1_Prod_Version=ShockwaveFlash" quality="high" src="http://www.sembeo.com/media/Matrix.swf"></object><br/><a href="http://www.sembeo.com/">Insurance</a></div>\r\n<p>'}, {u'width': 500, u'embed_code': u'</p>\r\n<div align="center"><object width="500" height="500" codebase="http://download.macromedia.com/pub/shockwave/cabs/flash/swflash.cab#version=5,0,0,0" classid="clsid:D27CDB6E-AE6D-11cf-96B8-444553540000"><param value="http://www.sembeo.com/media/Matrix.swf" name="movie"><param value="high" name="quality"><embed width="500" height="500" type="application/x-shockwave-flash" pluginspage="http://www.macromedia.com/shockwave/download/index.cgi?P1_Prod_Version=ShockwaveFlash" quality="high" src="http://www.sembeo.com/media/Matrix.swf"></object><br/><a href="http://www.sembeo.com/">Insurance</a></div>\r\n<p>'}], u'id': 46302035274, u'post_url': u'http://snivydaleaf.tumblr.com/post/46302035274/ask-wolfofsadness-tylersthings', u'source_title': u'mandaflewaway', u'tags': [], u'highlighted': [], u'state': u'published', u'short_url': u'http://tmblr.co/ZVKTlvh7qFrA', u'html5_capable': False, u'type': u'video', u'format': u'html', u'timestamp': 1364262118, u'note_count': 964900, u'video_type': u'unknown', u'source_url': u'http://mandaflewaway.tumblr.com/post/2057242738', u'date': u'2013-03-26 01:41:58 GMT', u'thumbnail_height': 0, u'slug': u'ask-wolfofsadness-tylersthings', u'blog_name': u'snivydaleaf', u'caption': u'<p><a class="tumblr_blog" href="http://ask-wolfofsadness.tumblr.com/post/46160407321/tylersthings-bahdumbahdumbombombom">ask-wolfofsadness</a>:</p>\n<blockquote>\n<p><a class="tumblr_blog" href="http://tylersthings.tumblr.com/post/46141661903/bahdumbahdumbombombom-stillnotdavid">tylersthings</a>:</p>\n<blockquote>\n<p><a class="tumblr_blog" href="http://bahdumbahdumbombombom.tumblr.com/post/45945978418/stillnotdavid-incrediblyfree-random-nexus">bahdumbahdumbombombom</a>:</p>\n<blockquote>\n<p><a class="tumblr_blog" href="http://stillnotdavid.tumblr.com/post/41765817778/incrediblyfree-random-nexus-missingone123">stillnotdavid</a>:</p>\n<blockquote>\n<p><a class="tumblr_blog" href="http://incrediblyfree.tumblr.com/post/41763743730/random-nexus-missingone123-technogecho">incrediblyfree</a>:</p>\n<blockquote>\n<p><a class="tumblr_blog" href="http://random-nexus.tumblr.com/post/26899864973/missingone123-technogecho-click-the">random-nexus</a>:</p>\n<blockquote>\n<p><a class="tumblr_blog" href="http://missingone123.tumblr.com/post/18820975157/technogecho-click-the-squares-the-whole">missingone123</a>:</p>\n<blockquote>\n<p><a class="tumblr_blog" href="http://technogecho.tumblr.com/post/18818924591/click-the-squares-the-whole-world-needs-to">technogecho</a>:</p>\n<blockquote>\n<blockquote>\n<p><strong><big><big>CLICK THE SQUARES.</big></big></strong></p>\n<p><img alt="image" height="158" src="http://media.tumblr.com/tumblr_lcsdx6ogB51qbnni6.jpg" width="206"/></p>\n<p><strong><big>THE WHOLE WORLD NEEDS TO KNOW ABOUT THIS.</big></strong></p>\n<p>THIS THIS THIS THIS!</p>\n<p><strong>ALWAYS</strong> REBLOG MUSICAL SQUARES</p>\n<p>YOU HAVE NOT LIVED IF YOU HAVEN\u2019T SEEN THIS YET</p>\n</blockquote>\n<p>these squares are magical</p>\n</blockquote>\n<p>This is amazing.</p>\n</blockquote>\n<p>This! Do It!</p>\n</blockquote>\n<p>aw that was delightful ;3</p>\n</blockquote>\n<p>I made a sick song with this tho.</p>\n</blockquote>\n<p>spent way too long playing with this..</p>\n</blockquote>\n<p>It\u2019s back. IT\u2019S BACK.\xa0<em><strong>IT\u2019S BAAAAACK</strong></em></p>\n</blockquote>\n<p>&lt;3</p>\n</blockquote>', u'thumbnail_url': u''}
    #sembeo_result = handle_video_posts(session,sembeo_post_dict)

    # Kickstarter video
    kickstarter_post_dict = {u'reblog_key': u'cbhGyHmc', u'reblog': {u'comment': u'', u'tree_html': u'<p><a href="http://xopachi.tumblr.com/post/119722564480/im-sad-this-wont-reach-its-goal" class="tumblr_blog">xopachi</a>:</p><blockquote><p>I\u2019m sad this won\u2019t reach it\u2019s goal.</p></blockquote>'}, u'thumbnail_width': 540, u'player': [{u'width': 250, u'embed_code': u'<iframe frameborder="0" height="187" scrolling="no" src="https://www.kickstarter.com/projects/1420158244/power-drive-2000/widget/video.html" width="250"></iframe>'}, {u'width': 400, u'embed_code': u'<iframe frameborder="0" height="300" scrolling="no" src="https://www.kickstarter.com/projects/1420158244/power-drive-2000/widget/video.html" width="400"></iframe>'}, {u'width': 500, u'embed_code': u'<iframe frameborder="0" height="375" scrolling="no" src="https://www.kickstarter.com/projects/1420158244/power-drive-2000/widget/video.html" width="500"></iframe>'}], u'id': 119722994086L, u'highlighted': [], u'format': u'html', u'post_url': u'http://nsfw.kevinsano.com/post/119722994086/xopachi-im-sad-this-wont-reach-its-goal', u'state': u'published', u'short_url': u'http://tmblr.co/Zo9zBq1lW2_cc', u'html5_capable': True, u'type': u'video', u'tags': [u'reblog', u'xopachi'], u'timestamp': 1432428705, u'note_count': 145, u'video_type': u'kickstarter', u'trail': [{u'blog': {u'theme': {u'title_font_weight': u'regular', u'header_full_height': 1600, u'title_color': u'#ffffff', u'header_bounds': u'224,1359,988,0', u'background_color': u'#9d9393', u'link_color': u'#3e3e3e', u'header_image_focused': u'http://static.tumblr.com/b2456b6ff202ae5712771f1b4bd241fe/hpnekee/prHnhl413/tumblr_static_tumblr_static_4fjroqeve6m80gwsk8w084k44_focused_v3.jpg', u'show_description': True, u'header_full_width': 1359, u'header_focus_width': 1359, u'show_header_image': True, u'body_font': u'Helvetica Neue', u'show_title': True, u'header_stretch': True, u'avatar_shape': u'square', u'show_avatar': True, u'header_focus_height': 764, u'title_font': u'Avalon', u'header_image': u'http://static.tumblr.com/b2456b6ff202ae5712771f1b4bd241fe/hpnekee/zXlnhl40z/tumblr_static_4fjroqeve6m80gwsk8w084k44.jpg', u'header_image_scaled': u'http://static.tumblr.com/b2456b6ff202ae5712771f1b4bd241fe/hpnekee/zXlnhl40z/tumblr_static_4fjroqeve6m80gwsk8w084k44_2048_v2.jpg'}, u'name': u'xopachi'}, u'content': u'<p>I\u2019m sad this won\u2019t reach it\u2019s goal.</p>', u'post': {u'id': u'119722564480'}, u'is_root_item': True}], u'date': u'2015-05-24 00:51:45 GMT', u'thumbnail_height': 405, u'permalink_url': u'https://www.kickstarter.com/projects/1420158244/power-drive-2000', u'slug': u'xopachi-im-sad-this-wont-reach-its-goal', u'blog_name': u'nsfwkevinsano', u'caption': u'<p><a href="http://xopachi.tumblr.com/post/119722564480/im-sad-this-wont-reach-its-goal" class="tumblr_blog">xopachi</a>:</p>\n\n<blockquote><p>I\u2019m sad this won\u2019t reach it\u2019s goal.</p></blockquote>', u'thumbnail_url': u'https://ksr-ugc.imgix.net/projects/1784048/photo-original.png?v=1432592842&w=560&h=420&fit=crop&auto=format&q=92&s=749617ab68487a3ee4c88e9e60bfe298'}
    #kickstarter_result = handle_video_posts(session,kickstarter_post_dict)

    # Dropbox flash embeds
    dropbox_flash_post_dict = {u'reblog_key': u'217zx1Ox', u'reblog': {u'comment': u'<p>Silly. (It&rsquo;s a game, Go to the post to play it)</p>', u'tree_html': u'<p><a class="tumblr_blog" href="http://stoicfive.tumblr.com/post/95173128374/a-little-game-prototype-based-off-this-one-mock-up" target="_blank">stoicfive</a>:</p><blockquote>\n<p>A little game prototype based off <a href="http://archive.heinessen.com/boards/mlp/img/0193/11/1408317408319.webm" target="_blank">this</a> one mock-up I keep seeing too often.</p>\n<p>Like the reference material you can only boop and have a slugfest with the enemy npcs in this version. (But it\u2019s ready to be expanded on)</p>\n<p>As there\u2019s nothing else to build off, winning just advances you by 1 level, losing sets you back to level 5.</p>\n<p>I took a guess at how the mock-up\u2019s system might have worked. It seems like as your captcha meter fills, you get extra commands to execute before the reload timer ticks down and begins posting all the commands in queue. That would allow for combining or combos.</p>\n<p>Music is <a href="https://www.youtube.com/watch?v=CsG9HiKcPM0" target="_blank">Boop</a><br/>Sounds effects fudged in sfxr<br/>Victory fanfare is from MaL:SS? Ran through GXSCC</p>\n</blockquote>'}, u'thumbnail_width': 0, u'player': [{u'width': 250, u'embed_code': u'<object width="250" height="250"><param name="movie" value="https://dl.dropboxusercontent.com/s/cdxam7r5iwv3ax6/test.swf" /><param name="allowFullScreen" value="true" /><param name="allowscriptaccess" value="always" /><embed src="https://dl.dropboxusercontent.com/s/cdxam7r5iwv3ax6/test.swf" width="250" height="250"></embed></object>'}, {u'width': 400, u'embed_code': u'<object width="400" height="400"><param name="movie" value="https://dl.dropboxusercontent.com/s/cdxam7r5iwv3ax6/test.swf" /><param name="allowFullScreen" value="true" /><param name="allowscriptaccess" value="always" /><embed src="https://dl.dropboxusercontent.com/s/cdxam7r5iwv3ax6/test.swf" width="400" height="400"></embed></object>'}, {u'width': 500, u'embed_code': u'<object width="500" height="500"><param name="movie" value="https://dl.dropboxusercontent.com/s/cdxam7r5iwv3ax6/test.swf" /><param name="allowFullScreen" value="true" /><param name="allowscriptaccess" value="always" /><embed src="https://dl.dropboxusercontent.com/s/cdxam7r5iwv3ax6/test.swf" width="500" height="500"></embed></object>'}], u'id': 95175094419L, u'highlighted': [], u'format': u'html', u'post_url': u'http://zippysqrl.tumblr.com/post/95175094419/stoicfive-a-little-game-prototype-based-off', u'state': u'published', u'short_url': u'http://tmblr.co/ZSpV2v1OeuB2J', u'html5_capable': False, u'type': u'video', u'tags': [u'MLPGame', u'reblog'], u'timestamp': 1408435680, u'note_count': 91, u'video_type': u'unknown', u'trail': [{u'blog': {u'theme': {u'title_font_weight': u'bold', u'title_color': u'#444444', u'header_bounds': 0, u'background_color': u'#FAFAFA', u'link_color': u'#529ECC', u'header_image_focused': u'http://assets.tumblr.com/images/default_header/optica_pattern_01.png?_v=f67ca5ac5d1c4a0526964674cb5a0605', u'show_description': True, u'show_header_image': True, u'body_font': u'Helvetica Neue', u'show_title': True, u'header_stretch': True, u'avatar_shape': u'square', u'show_avatar': True, u'title_font': u'Gibson', u'header_image': u'http://assets.tumblr.com/images/default_header/optica_pattern_01.png?_v=f67ca5ac5d1c4a0526964674cb5a0605', u'header_image_scaled': u'http://assets.tumblr.com/images/default_header/optica_pattern_01.png?_v=f67ca5ac5d1c4a0526964674cb5a0605'}, u'name': u'stoicfive'}, u'content': u'<p>A little game prototype based off <a href="http://archive.heinessen.com/boards/mlp/img/0193/11/1408317408319.webm" target="_blank">this</a> one mock-up I keep seeing too often.</p>\n<p>Like the reference material you can only boop and have a slugfest with the enemy npcs in this version. (But it\u2019s ready to be expanded on)</p>\n<p>As there\u2019s nothing else to build off, winning just advances you by 1 level, losing sets you back to level 5.</p>\n<p>I took a guess at how the mock-up\u2019s system might have worked. It seems like as your captcha meter fills, you get extra commands to execute before the reload timer ticks down and begins posting all the commands in queue. That would allow for combining or combos.</p>\n<p>Music is <a href="https://www.youtube.com/watch?v=CsG9HiKcPM0" target="_blank">Boop</a><br>Sounds effects fudged in sfxr<br>Victory fanfare is from MaL:SS? Ran through GXSCC</p>', u'post': {u'id': u'95173128374'}, u'is_root_item': True}, {u'blog': {u'theme': {u'title_font_weight': u'bold', u'header_full_height': 810, u'title_color': u'#444444', u'header_bounds': u'72,1183,737,0', u'background_color': u'#F6F6F6', u'link_color': u'#529ECC', u'header_image_focused': u'http://static.tumblr.com/310beb53e5f385bc79d5017c31fd655a/3uessne/SeCn65nho/tumblr_static_tumblr_static_80gai8e3d7s484cko0sos4s40_focused_v3.png', u'show_description': True, u'header_full_width': 1183, u'header_focus_width': 1183, u'show_header_image': True, u'body_font': u'Helvetica Neue', u'show_title': True, u'header_stretch': True, u'avatar_shape': u'circle', u'show_avatar': True, u'header_focus_height': 665, u'title_font': u'Helvetica Neue', u'header_image': u'http://static.tumblr.com/310beb53e5f385bc79d5017c31fd655a/3uessne/SGLn65nhm/tumblr_static_80gai8e3d7s484cko0sos4s40.png', u'header_image_scaled': u'http://static.tumblr.com/310beb53e5f385bc79d5017c31fd655a/3uessne/SGLn65nhm/tumblr_static_80gai8e3d7s484cko0sos4s40_2048_v2.png'}, u'name': u'zippysqrl'}, u'content': u'<p>Silly. (It\u2019s a game, Go to the post to play it)</p>', u'post': {u'id': u'95175094419'}, u'content_raw': u"<p>Silly. (It's a game, Go to the post to play it)</p>", u'is_current_item': True}], u'date': u'2014-08-19 08:08:00 GMT', u'thumbnail_height': 0, u'slug': u'stoicfive-a-little-game-prototype-based-off', u'blog_name': u'zippysqrl', u'caption': u'<p><a class="tumblr_blog" href="http://stoicfive.tumblr.com/post/95173128374/a-little-game-prototype-based-off-this-one-mock-up" target="_blank">stoicfive</a>:</p>\n<blockquote>\n<p>A little game prototype based off <a href="http://archive.heinessen.com/boards/mlp/img/0193/11/1408317408319.webm" target="_blank">this</a> one mock-up I keep seeing too often.</p>\n<p>Like the reference material you can only boop and have a slugfest with the enemy npcs in this version. (But it\u2019s ready to be expanded on)</p>\n<p>As there\u2019s nothing else to build off, winning just advances you by 1 level, losing sets you back to level 5.</p>\n<p>I took a guess at how the mock-up\u2019s system might have worked. It seems like as your captcha meter fills, you get extra commands to execute before the reload timer ticks down and begins posting all the commands in queue. That would allow for combining or combos.</p>\n<p>Music is <a href="https://www.youtube.com/watch?v=CsG9HiKcPM0" target="_blank">Boop</a><br/>Sounds effects fudged in sfxr<br/>Victory fanfare is from MaL:SS? Ran through GXSCC</p>\n</blockquote>\n<p>Silly. (It&rsquo;s a game, Go to the post to play it)</p>', u'thumbnail_url': u''}
    #dropbox_flash_result = handle_video_posts(session,dropbox_flash_post_dict)
    #logging.info("dropbox_flash_result:"+repr(dropbox_flash_result))

    # blip
    blip_post_dict = {u'reblog_key': u'2AdxssOH', u'reblog': {u'comment': u'<p>Retsupurae - The Most Shameful Thing in the World - The Retsupurae Archive on Blip</p>\n<p>LIFE IS SUFFERING</p>', u'tree_html': u''}, u'thumbnail_width': 480, u'player': [{u'width': 250, u'embed_code': u'<iframe src="https://blip.tv/play/iIEHgv_aSAI.html?p=1" width="250" height="203" frameborder="0" allowfullscreen></iframe><embed type="application/x-shockwave-flash" src="http://a.blip.tv/api.swf#iIEHgv_aSAI" style="display:none"></embed>'}, {u'width': 400, u'embed_code': u'<iframe src="https://blip.tv/play/iIEHgv_aSAI.html?p=1" width="400" height="325" frameborder="0" allowfullscreen></iframe><embed type="application/x-shockwave-flash" src="http://a.blip.tv/api.swf#iIEHgv_aSAI" style="display:none"></embed>'}, {u'width': 500, u'embed_code': u'<iframe src="https://blip.tv/play/iIEHgv_aSAI.html?p=1" width="500" height="406" frameborder="0" allowfullscreen></iframe><embed type="application/x-shockwave-flash" src="http://a.blip.tv/api.swf#iIEHgv_aSAI" style="display:none"></embed>'}], u'id': 29958821420L, u'highlighted': [], u'source_title': u'blip.tv', u'format': u'html', u'post_url': u'http://rapidstrike.tumblr.com/post/29958821420/retsupurae-the-most-shameful-thing-in-the-world', u'state': u'published', u'short_url': u'http://tmblr.co/Zf2prwRvhrOi', u'html5_capable': True, u'type': u'video', u'tags': [], u'timestamp': 1345630795, u'note_count': 0, u'video_type': u'blip', u'source_url': u'http://blip.tv/players/episode/iIEHgv_aSAI', u'trail': [{u'content': u'<p>Retsupurae - The Most Shameful Thing in the World - The Retsupurae Archive on Blip</p>\n<p>LIFE IS SUFFERING</p>', u'content_raw': u'<p>Retsupurae - The Most Shameful Thing in the World - The Retsupurae Archive on Blip</p>\r\n<p>LIFE IS SUFFERING</p>', u'is_current_item': True, u'blog': {u'theme': {u'title_font_weight': u'bold', u'header_full_height': 2000, u'title_color': u'#444444', u'header_bounds': u'644,2000,1769,0', u'background_color': u'#FAFAFA', u'link_color': u'#529ECC', u'header_image_focused': u'http://static.tumblr.com/f422cfd10f999ee477482cb90bbd268d/9kxvsrn/N1Mn8uarc/tumblr_static_tumblr_static_1nejsfhjccpww444c4wo8sk8c_focused_v3.jpg', u'show_description': True, u'header_full_width': 2000, u'header_focus_width': 2000, u'show_header_image': True, u'body_font': u'Helvetica Neue', u'show_title': True, u'header_stretch': True, u'avatar_shape': u'square', u'show_avatar': True, u'header_focus_height': 1125, u'title_font': u'Gibson', u'header_image': u'http://static.tumblr.com/22ebfa39543f2494741f8a0b626fb5a4/9kxvsrn/XbGn8uar6/tumblr_static_1nejsfhjccpww444c4wo8sk8c.png', u'header_image_scaled': u'http://static.tumblr.com/22ebfa39543f2494741f8a0b626fb5a4/9kxvsrn/XbGn8uar6/tumblr_static_1nejsfhjccpww444c4wo8sk8c_2048_v2.png'}, u'name': u'rapidstrike'}, u'is_root_item': True, u'post': {u'id': u'29958821420'}}], u'date': u'2012-08-22 10:19:55 GMT', u'thumbnail_height': 390, u'permalink_url': u'https://blip.tv/file/iIEHgv_aSAI', u'slug': u'retsupurae-the-most-shameful-thing-in-the-world', u'blog_name': u'rapidstrike', u'caption': u'<p>Retsupurae - The Most Shameful Thing in the World - The Retsupurae Archive on Blip</p>\n<p>LIFE IS SUFFERING</p>', u'thumbnail_url': u'http://a.images.blip.tv/TheRPArchive-RetsupuraeTheMostShamefulThingInTheWorld911-998.jpg', u'bookmarklet': True}
    #blip_result = handle_video_posts(session,blip_post_dict)
    #logging.debug("blip_result:"+repr(blip_result))

    # jest?
    jest_post_dict = {u'reblog_key': u'l7ejKyzq', u'reblog': {u'comment': u'<p><strong>THIS CAN&rsquo;T BE ANYMORE PERFECT</strong></p>', u'tree_html': u'<p><a class="tumblr_blog" href="http://adriofthedead.tumblr.com/post/24666481447/carouselcarouser-robotverve-toastradamus">adriofthedead</a>:</p><blockquote>\n<p><a class="tumblr_blog" href="http://carouselcarouser.tumblr.com/post/24666356229/robotverve-toastradamus-weeaboo-chan">carouselcarouser</a>:</p>\n<blockquote>\n<p><a class="tumblr_blog" href="http://robotverve.tumblr.com/post/24666273081">robotverve</a>:</p>\n<blockquote>\n<p><a class="tumblr_blog" href="http://toastradamus.tumblr.com/post/24666262031">toastradamus</a>:</p>\n<blockquote>\n<p><a class="tumblr_blog" href="http://weeaboo-chan.tumblr.com/post/24666214535/laughingalonewithklingon-acelebritysbodypart">weeaboo-chan</a>:</p>\n<blockquote>\n<p><a class="tumblr_blog" href="http://laughingalonewithklingon.tumblr.com/post/24664749456/acelebritysbodypart-alilyinhighgarden">laughingalonewithklingon</a>:</p>\n<blockquote>\n<p><a class="tumblr_blog" href="http://acelebritysbodypart.tumblr.com/post/24631241634">acelebritysbodypart</a>:</p>\n<blockquote>\n<p><a class="tumblr_blog" href="http://alilyinhighgarden.tumblr.com/post/24613138091/gilbert-gottfried-reads-fifty-shades-of-grey">alilyinhighgarden</a>:</p>\n<blockquote>\n<p>Gilbert Gottfried reads Fifty Shades of Grey</p>\n</blockquote>\n<p>This is hilarious omfg</p>\n</blockquote>\n<p>I A&lt;M LITERALLY SCREAMING HOLY \xa0SHIT</p>\n</blockquote>\n<p>hyoly FUKC</p>\n</blockquote>\n<p>IM FUCKING DEAD</p>\n</blockquote>\n<p>HYPERVENTILATING</p>\n</blockquote>\n<p>OH MY GOD THEIR FACES</p>\n</blockquote>\n<p>CLI-<em>TOR</em>-US</p>\n</blockquote>'}, u'thumbnail_width': 0, u'player': [{u'width': 250, u'embed_code': u'<iframe src="http://www.jest.com/e/174214" width="250" height="156" frameborder="0" webkitAllowFullScreen allowFullScreen></iframe>'}, {u'width': 400, u'embed_code': u'<iframe src="http://www.jest.com/e/174214" width="400" height="250" frameborder="0" webkitAllowFullScreen allowFullScreen></iframe>'}, {u'width': 500, u'embed_code': u'<iframe src="http://www.jest.com/e/174214" width="500" height="312" frameborder="0" webkitAllowFullScreen allowFullScreen></iframe>'}], u'id': 24669327568L, u'highlighted': [], u'source_title': u'holycityfangirl', u'format': u'html', u'post_url': u'http://rapidstrike.tumblr.com/post/24669327568/adriofthedead-carouselcarouser-robotverve', u'state': u'published', u'short_url': u'http://tmblr.co/Zf2prwM_Q13G', u'html5_capable': False, u'type': u'video', u'tags': [], u'timestamp': 1339144326, u'note_count': 25082, u'video_type': u'unknown', u'source_url': u'http://holycityfangirl.tumblr.com/post/24613138091/gilbert-gottfried-reads-fifty-shades-of-grey', u'trail': [{u'blog': {u'theme': {u'title_font_weight': u'bold', u'title_color': u'#444444', u'header_bounds': u'', u'background_color': u'#FAFAFA', u'link_color': u'#529ECC', u'header_image_focused': u'http://assets.tumblr.com/images/default_header/optica_pattern_10_focused_v3.png?_v=eafbfb1726b334d86841955ae7b9221c', u'show_description': True, u'show_header_image': True, u'body_font': u'Helvetica Neue', u'show_title': True, u'header_stretch': True, u'avatar_shape': u'square', u'show_avatar': True, u'title_font': u'Gibson', u'header_image': u'http://assets.tumblr.com/images/default_header/optica_pattern_10.png?_v=eafbfb1726b334d86841955ae7b9221c', u'header_image_scaled': u'http://assets.tumblr.com/images/default_header/optica_pattern_10_focused_v3.png?_v=eafbfb1726b334d86841955ae7b9221c'}, u'name': u'alilyinhighgarden'}, u'content': u'<p>Gilbert Gottfried reads Fifty Shades of Grey</p>', u'post': {u'id': u'24613138091'}, u'is_root_item': True}, {u'blog': {u'theme': [], u'name': u'acelebritysbodypart'}, u'content': u'<p>This is hilarious omfg</p>', u'post': {u'id': u'24631241634'}}, {u'blog': {u'theme': {u'title_font_weight': u'bold', u'title_color': u'#444444', u'header_bounds': u'', u'background_color': u'#FAFAFA', u'link_color': u'#529ECC', u'header_image_focused': u'http://assets.tumblr.com/images/default_header/optica_pattern_04_focused_v3.png?_v=7c4e5e82cf797042596e2e64af1c383f', u'show_description': True, u'show_header_image': True, u'body_font': u'Helvetica Neue', u'show_title': True, u'header_stretch': True, u'avatar_shape': u'square', u'show_avatar': True, u'title_font': u'Gibson', u'header_image': u'http://assets.tumblr.com/images/default_header/optica_pattern_04.png?_v=7c4e5e82cf797042596e2e64af1c383f', u'header_image_scaled': u'http://assets.tumblr.com/images/default_header/optica_pattern_04_focused_v3.png?_v=7c4e5e82cf797042596e2e64af1c383f'}, u'name': u'laughingalonewithklingon'}, u'content': u'<p>I A<M LITERALLY SCREAMING HOLY \xa0SHIT</p>', u'post': {u'id': u'24664749456'}}, {u'blog': {u'theme': {u'title_font_weight': u'bold', u'title_color': u'#444444', u'header_bounds': 0, u'background_color': u'#FAFAFA', u'link_color': u'#529ECC', u'header_image_focused': u'http://assets.tumblr.com/images/default_header/optica_pattern_03.png?_v=a0f20b51ed40eb5a930ab86effe42a40', u'show_description': True, u'show_header_image': True, u'body_font': u'Helvetica Neue', u'show_title': True, u'header_stretch': True, u'avatar_shape': u'square', u'show_avatar': True, u'title_font': u'Gibson', u'header_image': u'http://assets.tumblr.com/images/default_header/optica_pattern_03.png?_v=a0f20b51ed40eb5a930ab86effe42a40', u'header_image_scaled': u'http://assets.tumblr.com/images/default_header/optica_pattern_03.png?_v=a0f20b51ed40eb5a930ab86effe42a40'}, u'name': u'weeaboo-chan'}, u'content': u'<p>hyoly FUKC</p>', u'post': {u'id': u'24666214535'}}, {u'blog': {u'theme': {u'title_font_weight': u'bold', u'header_full_height': 366, u'title_color': u'#000000', u'header_bounds': u'5,500,286,0', u'background_color': u'#ffc2ee', u'link_color': u'#560977', u'header_image_focused': u'http://static.tumblr.com/3a9976189420de03d821124b0dc569e4/o9rh1fb/EEUnjdd0h/tumblr_static_tumblr_static_2c8yg59dh0lcw0cog00wg0gsg_focused_v3.jpg', u'show_description': True, u'header_full_width': 500, u'header_focus_width': 500, u'show_header_image': True, u'body_font': u'Helvetica Neue', u'show_title': True, u'header_stretch': True, u'avatar_shape': u'circle', u'show_avatar': True, u'header_focus_height': 281, u'title_font': u'Grumpy Black 48', u'header_image': u'http://static.tumblr.com/3a9976189420de03d821124b0dc569e4/o9rh1fb/Crenjdd0g/tumblr_static_2c8yg59dh0lcw0cog00wg0gsg.jpg', u'header_image_scaled': u'http://static.tumblr.com/3a9976189420de03d821124b0dc569e4/o9rh1fb/Crenjdd0g/tumblr_static_2c8yg59dh0lcw0cog00wg0gsg_2048_v2.jpg'}, u'name': u'toastradamus'}, u'content': u'<p>IM FUCKING DEAD</p>', u'post': {u'id': u'24666262031'}}, {u'blog': {u'theme': {u'title_font_weight': u'bold', u'header_full_height': 429, u'title_color': u'#A77DC2', u'header_bounds': u'64,574,354,58', u'background_color': u'#e77b9f', u'link_color': u'#fff55a', u'header_image_focused': u'http://static.tumblr.com/d89656dd02c85b62db02d327f1e83de6/j3pcffn/I4sn5gxb5/tumblr_static_tumblr_static__focused_v3.png', u'show_description': True, u'header_full_width': 620, u'header_focus_width': 516, u'show_header_image': True, u'body_font': u'Helvetica Neue', u'show_title': True, u'header_stretch': True, u'avatar_shape': u'circle', u'show_avatar': True, u'header_focus_height': 290, u'title_font': u'Arquitecta', u'header_image': u'http://static.tumblr.com/d89656dd02c85b62db02d327f1e83de6/j3pcffn/2b0n5gxb3/tumblr_static_.png', u'header_image_scaled': u'http://static.tumblr.com/d89656dd02c85b62db02d327f1e83de6/j3pcffn/2b0n5gxb3/tumblr_static__2048_v2.png'}, u'name': u'robotverve'}, u'content': u'<p>HYPERVENTILATING</p>', u'post': {u'id': u'24666273081'}}, {u'blog': {u'theme': {u'title_font_weight': u'bold', u'title_color': u'#444444', u'header_bounds': u'', u'background_color': u'#FAFAFA', u'link_color': u'#529ECC', u'header_image_focused': u'http://assets.tumblr.com/images/default_header/optica_pattern_13_focused_v3.png?_v=2f4063be1dd2ee91e4eca54332e25191', u'show_description': True, u'show_header_image': True, u'body_font': u'Helvetica Neue', u'show_title': True, u'header_stretch': True, u'avatar_shape': u'square', u'show_avatar': True, u'title_font': u'Gibson', u'header_image': u'http://assets.tumblr.com/images/default_header/optica_pattern_13.png?_v=2f4063be1dd2ee91e4eca54332e25191', u'header_image_scaled': u'http://assets.tumblr.com/images/default_header/optica_pattern_13_focused_v3.png?_v=2f4063be1dd2ee91e4eca54332e25191'}, u'name': u'carouselcarouser'}, u'content': u'<p>OH MY GOD THEIR FACES</p>', u'post': {u'id': u'24666356229'}}, {u'blog': {u'theme': {u'title_font_weight': u'bold', u'header_full_height': 297, u'title_color': u'#5AC9E1', u'header_bounds': u'7,500,289,0', u'background_color': u'#FFFFFF', u'link_color': u'#444444', u'header_image_focused': u'http://static.tumblr.com/a59c7c206b1614b4ccf80311e457d0d0/jrsr7vt/VaUn7actq/tumblr_static_tumblr_static_cfca7jdqcyog0ccsgcog4sow4_focused_v3.png', u'show_description': True, u'header_full_width': 500, u'header_focus_width': 500, u'show_header_image': True, u'body_font': u'Helvetica Neue', u'show_title': True, u'header_stretch': True, u'avatar_shape': u'square', u'show_avatar': True, u'header_focus_height': 282, u'title_font': u'Helvetica Neue', u'header_image': u'http://static.tumblr.com/a59c7c206b1614b4ccf80311e457d0d0/jrsr7vt/DIKn7actp/tumblr_static_cfca7jdqcyog0ccsgcog4sow4.png', u'header_image_scaled': u'http://static.tumblr.com/a59c7c206b1614b4ccf80311e457d0d0/jrsr7vt/DIKn7actp/tumblr_static_cfca7jdqcyog0ccsgcog4sow4_2048_v2.png'}, u'name': u'adriofthedead'}, u'content': u'<p>CLI-<em>TOR</em>-US</p>', u'post': {u'id': u'24666481447'}}, {u'blog': {u'theme': {u'title_font_weight': u'bold', u'header_full_height': 2000, u'title_color': u'#444444', u'header_bounds': u'644,2000,1769,0', u'background_color': u'#FAFAFA', u'link_color': u'#529ECC', u'header_image_focused': u'http://static.tumblr.com/f422cfd10f999ee477482cb90bbd268d/9kxvsrn/N1Mn8uarc/tumblr_static_tumblr_static_1nejsfhjccpww444c4wo8sk8c_focused_v3.jpg', u'show_description': True, u'header_full_width': 2000, u'header_focus_width': 2000, u'show_header_image': True, u'body_font': u'Helvetica Neue', u'show_title': True, u'header_stretch': True, u'avatar_shape': u'square', u'show_avatar': True, u'header_focus_height': 1125, u'title_font': u'Gibson', u'header_image': u'http://static.tumblr.com/22ebfa39543f2494741f8a0b626fb5a4/9kxvsrn/XbGn8uar6/tumblr_static_1nejsfhjccpww444c4wo8sk8c.png', u'header_image_scaled': u'http://static.tumblr.com/22ebfa39543f2494741f8a0b626fb5a4/9kxvsrn/XbGn8uar6/tumblr_static_1nejsfhjccpww444c4wo8sk8c_2048_v2.png'}, u'name': u'rapidstrike'}, u'content': u'<p><strong>THIS CAN\u2019T BE ANYMORE PERFECT</strong></p>', u'post': {u'id': u'24669327568'}, u'content_raw': u"<p><strong>THIS CAN'T BE ANYMORE PERFECT</strong></p>", u'is_current_item': True}], u'date': u'2012-06-08 08:32:06 GMT', u'thumbnail_height': 0, u'slug': u'adriofthedead-carouselcarouser-robotverve', u'blog_name': u'rapidstrike', u'caption': u'<p><a class="tumblr_blog" href="http://adriofthedead.tumblr.com/post/24666481447/carouselcarouser-robotverve-toastradamus">adriofthedead</a>:</p>\n<blockquote>\n<p><a class="tumblr_blog" href="http://carouselcarouser.tumblr.com/post/24666356229/robotverve-toastradamus-weeaboo-chan">carouselcarouser</a>:</p>\n<blockquote>\n<p><a class="tumblr_blog" href="http://robotverve.tumblr.com/post/24666273081">robotverve</a>:</p>\n<blockquote>\n<p><a class="tumblr_blog" href="http://toastradamus.tumblr.com/post/24666262031">toastradamus</a>:</p>\n<blockquote>\n<p><a class="tumblr_blog" href="http://weeaboo-chan.tumblr.com/post/24666214535/laughingalonewithklingon-acelebritysbodypart">weeaboo-chan</a>:</p>\n<blockquote>\n<p><a class="tumblr_blog" href="http://laughingalonewithklingon.tumblr.com/post/24664749456/acelebritysbodypart-alilyinhighgarden">laughingalonewithklingon</a>:</p>\n<blockquote>\n<p><a class="tumblr_blog" href="http://acelebritysbodypart.tumblr.com/post/24631241634">acelebritysbodypart</a>:</p>\n<blockquote>\n<p><a class="tumblr_blog" href="http://alilyinhighgarden.tumblr.com/post/24613138091/gilbert-gottfried-reads-fifty-shades-of-grey">alilyinhighgarden</a>:</p>\n<blockquote>\n<p>Gilbert Gottfried reads Fifty Shades of Grey</p>\n</blockquote>\n<p>This is hilarious omfg</p>\n</blockquote>\n<p>I A&lt;M LITERALLY SCREAMING HOLY \xa0SHIT</p>\n</blockquote>\n<p>hyoly FUKC</p>\n</blockquote>\n<p>IM FUCKING DEAD</p>\n</blockquote>\n<p>HYPERVENTILATING</p>\n</blockquote>\n<p>OH MY GOD THEIR FACES</p>\n</blockquote>\n<p>CLI-<em>TOR</em>-US</p>\n</blockquote>\n<p><strong>THIS CAN&rsquo;T BE ANYMORE PERFECT</strong></p>', u'thumbnail_url': u''}
    #jest_result = handle_video_posts(session,jest_post_dict)
    #logging.debug("jest_result:"+repr(jest_result))

    # coub loop service
    coub_post_dict = {u'reblog_key': u'q3pdA63K', u'reblog': {u'comment': u'<blockquote>\n<p><em>Artorias Bowling</em></p>\n</blockquote>', u'tree_html': u''}, u'thumbnail_width': 540, u'player': [{u'width': 250, u'embed_code': u'<iframe src="//coub.com/embed/3rj9f?autoplay=true&maxheight=720&maxwidth=540&muted=true" allowfullscreen="true" frameborder="0" autoplay="true" width="250" height="140"></iframe>'}, {u'width': 400, u'embed_code': u'<iframe src="//coub.com/embed/3rj9f?autoplay=true&maxheight=720&maxwidth=540&muted=true" allowfullscreen="true" frameborder="0" autoplay="true" width="400" height="224"></iframe>'}, {u'width': 500, u'embed_code': u'<iframe src="//coub.com/embed/3rj9f?autoplay=true&maxheight=720&maxwidth=540&muted=true" allowfullscreen="true" frameborder="0" autoplay="true" width="500" height="280"></iframe>'}], u'id': 101082217532L, u'highlighted': [], u'source_title': u'lordranandbeyond', u'format': u'html', u'post_url': u'http://eissypone.tumblr.com/post/101082217532/artorias-bowling', u'state': u'published', u'short_url': u'http://tmblr.co/ZHhs0n1U8_3my', u'html5_capable': False, u'type': u'video', u'tags': [], u'timestamp': 1414412701, u'note_count': 196, u'video_type': u'coub', u'source_url': u'http://lordranandbeyond.tumblr.com/post/101061834450/artorias-bowling', u'trail': [{u'blog': {u'theme': {u'title_font_weight': u'bold', u'title_color': u'#444444', u'header_bounds': 0, u'background_color': u'#FAFAFA', u'link_color': u'#529ECC', u'header_image_focused': u'http://assets.tumblr.com/images/default_header/optica_pattern_11.png?_v=4275fa0865b78225d79970023dde05a1', u'show_description': True, u'show_header_image': True, u'body_font': u'Helvetica Neue', u'show_title': True, u'header_stretch': True, u'avatar_shape': u'square', u'show_avatar': True, u'title_font': u'Gibson', u'header_image': u'http://assets.tumblr.com/images/default_header/optica_pattern_11.png?_v=4275fa0865b78225d79970023dde05a1', u'header_image_scaled': u'http://assets.tumblr.com/images/default_header/optica_pattern_11.png?_v=4275fa0865b78225d79970023dde05a1'}, u'name': u'eissypone'}, u'content': u'<blockquote>\n<p><em>Artorias Bowling</em></p>\n</blockquote>', u'post': {u'id': u'101082217532'}, u'content_raw': u'<blockquote>\r\n<p><em>Artorias Bowling</em></p>\r\n</blockquote>\r\n<p></p>', u'is_current_item': True}], u'date': u'2014-10-27 12:25:01 GMT', u'thumbnail_height': 303, u'permalink_url': u'http://coub.com/view/3rj9f', u'slug': u'artorias-bowling', u'blog_name': u'eissypone', u'caption': u'<blockquote>\n<p><em>Artorias Bowling</em></p>\n</blockquote>', u'thumbnail_url': u'https://coub.com/assets-proxy?url=http://ell.akamai.coub.com/get/b13/p/coub/simple/cw_tumblr_pic/3bc739152fe/ef8972d4689eae22aebda/1413989827_62qolm_tumblr-img-generator-res.jpg'}
    #coub_result = handle_video_posts(session,coub_post_dict)
    #logging.debug("coub_result:"+repr(coub_result))

    # liveleak
    liveleak_post_dict = {u'reblog_key': u'AmAhWGkj', u'reblog': {u'comment': u'<p>&#65288;*&acute;&#9661;&#65344;*&#65289;</p>', u'tree_html': u''}, u'thumbnail_width': 0, u'player': [{u'width': 250, u'embed_code': u'<iframe width="250" height="140" src="http://www.liveleak.com/ll_embed?f=01b03505a8a6" frameborder="0" allowfullscreen></iframe>'}, {u'width': 400, u'embed_code': u'<iframe width="400" height="225" src="http://www.liveleak.com/ll_embed?f=01b03505a8a6" frameborder="0" allowfullscreen></iframe>'}, {u'width': 500, u'embed_code': u'<iframe width="500" height="281" src="http://www.liveleak.com/ll_embed?f=01b03505a8a6" frameborder="0" allowfullscreen></iframe>'}], u'id': 22162041589L, u'highlighted': [], u'format': u'html', u'post_url': u'http://sukebepanda.tumblr.com/post/22162041589', u'state': u'published', u'short_url': u'http://tmblr.co/ZHmWxvKezUhr', u'html5_capable': False, u'type': u'video', u'tags': [], u'timestamp': 1335834624, u'note_count': 1, u'video_type': u'unknown', u'trail': [{u'content': u'<p>\uff08*\xb4\u25bd\uff40*\uff09</p>', u'content_raw': u'<p>&#65288;*&acute;&#9661;&#65344;*&#65289;</p>', u'is_current_item': True, u'blog': {u'theme': {u'title_font_weight': u'bold', u'title_color': u'#444444', u'header_bounds': 0, u'background_color': u'#F6F6F6', u'link_color': u'#529ECC', u'header_image_focused': u'http://assets.tumblr.com/images/default_header/optica_pattern_02.png?_v=b976ee00195b1b7806c94ae285ca46a7', u'show_description': True, u'show_header_image': True, u'body_font': u'Helvetica Neue', u'show_title': True, u'header_stretch': True, u'avatar_shape': u'square', u'show_avatar': True, u'title_font': u'Helvetica Neue', u'header_image': u'http://assets.tumblr.com/images/default_header/optica_pattern_02.png?_v=b976ee00195b1b7806c94ae285ca46a7', u'header_image_scaled': u'http://assets.tumblr.com/images/default_header/optica_pattern_02.png?_v=b976ee00195b1b7806c94ae285ca46a7'}, u'name': u'sukebepanda'}, u'is_root_item': True, u'post': {u'id': u'22162041589'}}], u'date': u'2012-05-01 01:10:24 GMT', u'thumbnail_height': 0, u'slug': u'', u'blog_name': u'sukebepanda', u'caption': u'<p>\uff08*\xb4\u25bd\uff40*\uff09</p>', u'thumbnail_url': u''}
    #liveleak_result = handle_video_posts(session,liveleak_post_dict)
    #logging.debug("liveleak_result:"+repr(liveleak_result))

    # Broken dailymotion
    broken_dailymotion_post_dict = {u'reblog_key': u'wx5UKzeA', u'reblog': {u'comment': u'<p>Deadpool is one of my favorite superheroes, next to Nightwing, Starfire and Spider-Man. I hope this actually becomes a thing someday.</p>', u'tree_html': u'<p><a class="tumblr_blog" href="http://www.herochan.com/post/93248161765/ryan-reynolds-as-deadpool-in-hd-if-we-add-the" target="_blank">herochan</a>:</p><blockquote>\n<p><strong>Ryan Reynolds as Deadpool\u2026 in HD</strong></p>\n<p>If we add the word \u201cleaked\u201d to this will it make it more exciting? If \u201cleaked\u201d means \u201cuploaded by the animation studio\u201d then this is even more \u201cleaked\u201d than when \u201cleaked\u201d meant \u201cshown to 1000\u2019s of people at Comic-Con\u201d.\xa0</p>\n</blockquote>'}, u'thumbnail_width': 0, u'player': [{u'width': 250, u'embed_code': u'<iframe frameborder="0" width="250" height="140" src="//www.dailymotion.com/embed/video/x22eged" allowfullscreen></iframe><br /><a href="http://www.dailymotion.com/video/x22eged_deadpool-test-footage-in-hd_videogames">Deadpool Test Footage in HD</a> <i>by <a href="http://www.dailymotion.com/itsartmag">itsartmag</a></i>'}, {u'width': 400, u'embed_code': u'<iframe frameborder="0" width="400" height="225" src="//www.dailymotion.com/embed/video/x22eged" allowfullscreen></iframe><br /><a href="http://www.dailymotion.com/video/x22eged_deadpool-test-footage-in-hd_videogames">Deadpool Test Footage in HD</a> <i>by <a href="http://www.dailymotion.com/itsartmag">itsartmag</a></i>'}, {u'width': 500, u'embed_code': u'<iframe frameborder="0" width="500" height="281" src="//www.dailymotion.com/embed/video/x22eged" allowfullscreen></iframe><br /><a href="http://www.dailymotion.com/video/x22eged_deadpool-test-footage-in-hd_videogames">Deadpool Test Footage in HD</a> <i>by <a href="http://www.dailymotion.com/itsartmag">itsartmag</a></i>'}], u'id': 93309838435L, u'highlighted': [], u'source_title': u'herochan', u'format': u'html', u'post_url': u'http://marikazemus34.tumblr.com/post/93309838435/herochan-ryan-reynolds-as-deadpool-in-hd-if', u'recommended_source': None, u'state': u'published', u'short_url': u'http://tmblr.co/Z8Vcaq1MvioHZ', u'html5_capable': False, u'type': u'video', u'tags': [], u'timestamp': 1406730599, u'note_count': 23121, u'video_type': u'unknown', u'source_url': u'http://herochan.tumblr.com/post/93248161765/ryan-reynolds-as-deadpool-in-hd', u'trail': [{u'blog': {u'theme': {u'title_font_weight': u'bold', u'header_full_height': 200, u'title_color': u'#444444', u'header_bounds': u'0,385,200,30', u'background_color': u'#dcecf5', u'link_color': u'#fe2d08', u'header_image_focused': u'http://static.tumblr.com/9a3b8a29899ed13fde172f0ca0c46561/oqk1mwg/Uxhne9i6c/tumblr_static_tumblr_static_e1tjpmansvwc4cwskcwow44gw_focused_v3.gif', u'show_description': True, u'header_full_width': 400, u'header_focus_width': 355, u'show_header_image': True, u'body_font': u'Helvetica Neue', u'show_title': True, u'header_stretch': True, u'avatar_shape': u'square', u'show_avatar': True, u'header_focus_height': 200, u'title_font': u'Helvetica Neue', u'header_image': u'http://static.tumblr.com/9a3b8a29899ed13fde172f0ca0c46561/oqk1mwg/gNcne9i6b/tumblr_static_e1tjpmansvwc4cwskcwow44gw.gif', u'header_image_scaled': u'http://static.tumblr.com/9a3b8a29899ed13fde172f0ca0c46561/oqk1mwg/gNcne9i6b/tumblr_static_e1tjpmansvwc4cwskcwow44gw_2048_v2.gif'}, u'name': u'herochan'}, u'content': u'<p><strong>Ryan Reynolds as Deadpool\u2026 in HD</strong></p>\n<p>If we add the word \u201cleaked\u201d to this will it make it more exciting? If \u201cleaked\u201d means \u201cuploaded by the animation studio\u201d then this is even more \u201cleaked\u201d than when \u201cleaked\u201d meant \u201cshown to 1000\u2019s of people at Comic-Con\u201d.\xa0</p>', u'post': {u'id': u'93248161765'}, u'is_root_item': True}, {u'blog': {u'theme': {u'title_font_weight': u'bold', u'title_color': u'#ffffff', u'header_bounds': 0, u'background_color': u'#000000', u'link_color': u'#c1bfc7', u'header_image_focused': u'http://static.tumblr.com/2b01c129791f195feccc7e2be2bc963a/72onzl6/Jv2nmo180/tumblr_static_6ct1neicb2g4k4gg4o0s0480o_2048_v2.png', u'show_description': True, u'show_header_image': True, u'body_font': u'Helvetica Neue', u'show_title': True, u'header_stretch': True, u'avatar_shape': u'square', u'show_avatar': True, u'title_font': u'Alternate Gothic', u'header_image': u'http://static.tumblr.com/2b01c129791f195feccc7e2be2bc963a/72onzl6/Jv2nmo180/tumblr_static_6ct1neicb2g4k4gg4o0s0480o.png', u'header_image_scaled': u'http://static.tumblr.com/2b01c129791f195feccc7e2be2bc963a/72onzl6/Jv2nmo180/tumblr_static_6ct1neicb2g4k4gg4o0s0480o_2048_v2.png'}, u'name': u'marikazemus34'}, u'content': u'<p>Deadpool is one of my favorite superheroes, next to Nightwing, Starfire and Spider-Man. I hope this actually becomes a thing someday.</p>', u'post': {u'id': u'93309838435'}, u'content_raw': u'<p>Deadpool is one of my favorite superheroes, next to Nightwing, Starfire and Spider-Man. I hope this actually becomes a thing someday.</p>', u'is_current_item': True}], u'date': u'2014-07-30 14:29:59 GMT', u'thumbnail_height': 0, u'slug': u'herochan-ryan-reynolds-as-deadpool-in-hd-if', u'blog_name': u'marikazemus34', u'caption': u'<p><a class="tumblr_blog" href="http://www.herochan.com/post/93248161765/ryan-reynolds-as-deadpool-in-hd-if-we-add-the" target="_blank">herochan</a>:</p>\n<blockquote>\n<p><strong>Ryan Reynolds as Deadpool\u2026 in HD</strong></p>\n<p>If we add the word \u201cleaked\u201d to this will it make it more exciting? If \u201cleaked\u201d means \u201cuploaded by the animation studio\u201d then this is even more \u201cleaked\u201d than when \u201cleaked\u201d meant \u201cshown to 1000\u2019s of people at Comic-Con\u201d.\xa0</p>\n</blockquote>\n<p>Deadpool is one of my favorite superheroes, next to Nightwing, Starfire and Spider-Man. I hope this actually becomes a thing someday.</p>', u'thumbnail_url': u''}
    #broken_dailymotion_result = handle_video_posts(session,broken_dailymotion_post_dict)
    #logging.debug("broken_dailymotion_result:"+repr(broken_dailymotion_result))


    # vid.me
    vidme_post_dict = {u'reblog_key': u'p8Mr5KUO', u'reblog': {u'comment': u'<p>proud patron =D</p>', u'tree_html': u'<p><a href="http://saltyicecream.tumblr.com/post/120791148304/supported-by-patreon-miyuki-the-android-was" class="tumblr_blog">saltyicecream</a>:</p><blockquote><h2>Supported by <b><a href="https://www.patreon.com/SaltyIceCream">Patreon</a></b></h2><p>Miyuki (the android) was voiced by <b><a href="http://megamoeka.tumblr.com/">MegaMoeka</a>.</b>\xa0</p><p><i>please don\u2019t be a creepo 8). It\u2019s called voice acting for a reason.</i></p><p>I found her through <a href="http://hentaiwriter.tumblr.com/">HentaiWriter</a>.\xa0Megamoeka is an awesome voice actress. I think she is still doing commissions for criminally low rates. I\u2019d hop on that if you need voice acting done.\xa0</p><p>I know it\u2019s short, I just wanted to see if I could actually do something like this. I think it turned out ok. The sound was a headache tho.</p><h2>Here is a <b><a href="http://webmup.com/7cb40/">WebM Link</a>.</b>\xa0Just better quality.</h2><p>On a side note, if you are interested in voice acting in future stuff, shoot me a voice demo (male or female, just be 18 or over). I don\u2019t need to hear moaning or anything like that, actual voice acting is way better for me.</p></blockquote>'}, u'thumbnail_width': 0, u'player': [{u'width': 250, u'embed_code': u'<iframe src="https://vid.me/e/JPd9" frameborder="0" allowfullscreen webkitallowfullscreen mozallowfullscreen scrolling="no" height="140" width="250"></iframe>'}, {u'width': 400, u'embed_code': u'<iframe src="https://vid.me/e/JPd9" frameborder="0" allowfullscreen webkitallowfullscreen mozallowfullscreen scrolling="no" height="225" width="400"></iframe>'}, {u'width': 500, u'embed_code': u'<iframe src="https://vid.me/e/JPd9" frameborder="0" allowfullscreen webkitallowfullscreen mozallowfullscreen scrolling="no" height="281" width="500"></iframe>'}], u'id': 120800817969L, u'highlighted': [], u'format': u'html', u'post_url': u'http://tenkaboutthebutts.tumblr.com/post/120800817969/saltyicecream-supported-by-patreon-miyuki-the', u'recommended_source': None, u'state': u'published', u'short_url': u'http://tmblr.co/Ze4Tbv1mWIZCn', u'html5_capable': False, u'type': u'video', u'tags': [], u'timestamp': 1433537926, u'note_count': 1060, u'video_type': u'unknown', u'trail': [{u'blog': {u'theme': {u'title_font_weight': u'bold', u'header_full_height': 500, u'title_color': u'#444444', u'header_bounds': u'109,500,390,0', u'background_color': u'#F6F6F6', u'link_color': u'#529ECC', u'header_image_focused': u'http://static.tumblr.com/9d05d0626ceede201b6fb625392530ec/qwzs2zp/K41nakmsx/tumblr_static_tumblr_static_1t3xub3jop8g4ogskkosgs0k8_focused_v3.gif', u'show_description': True, u'header_full_width': 500, u'header_focus_width': 500, u'show_header_image': True, u'body_font': u'Helvetica Neue', u'show_title': True, u'header_stretch': True, u'avatar_shape': u'circle', u'show_avatar': True, u'header_focus_height': 281, u'title_font': u'Helvetica Neue', u'header_image': u'http://static.tumblr.com/9d05d0626ceede201b6fb625392530ec/qwzs2zp/7punakmsw/tumblr_static_1t3xub3jop8g4ogskkosgs0k8.gif', u'header_image_scaled': u'http://static.tumblr.com/9d05d0626ceede201b6fb625392530ec/qwzs2zp/7punakmsw/tumblr_static_1t3xub3jop8g4ogskkosgs0k8_2048_v2.gif'}, u'name': u'saltyicecream'}, u'content': u'<h2>Supported by <b><a href="https://www.patreon.com/SaltyIceCream">Patreon</a></b></h2><p>Miyuki (the android) was voiced by <b><a href="http://megamoeka.tumblr.com/">MegaMoeka</a>.</b>\xa0</p><p><i>please don\u2019t be a creepo 8). It\u2019s called voice acting for a reason.</i></p><p>I found her through <a href="http://hentaiwriter.tumblr.com/">HentaiWriter</a>.\xa0Megamoeka is an awesome voice actress. I think she is still doing commissions for criminally low rates. I\u2019d hop on that if you need voice acting done.\xa0</p><p>I know it\u2019s short, I just wanted to see if I could actually do something like this. I think it turned out ok. The sound was a headache tho.</p><h2>Here is a <b><a href="http://webmup.com/7cb40/">WebM Link</a>.</b>\xa0Just better quality.</h2><p>On a side note, if you are interested in voice acting in future stuff, shoot me a voice demo (male or female, just be 18 or over). I don\u2019t need to hear moaning or anything like that, actual voice acting is way better for me.</p>', u'post': {u'id': u'120791148304'}, u'is_root_item': True}, {u'blog': {u'theme': {u'title_font_weight': u'bold', u'header_full_height': 333, u'title_color': u'#444444', u'header_bounds': u'25,500,307,0', u'background_color': u'#dccbe7', u'link_color': u'#529ECC', u'header_image_focused': u'http://static.tumblr.com/75bc2eab3cb07b368cfbaf7947fcd61b/soqnzor/er7n68k2k/tumblr_static_tumblr_static_63hqr5ymqvkssc04cw4s0skoo_focused_v3.gif', u'show_description': True, u'header_full_width': 500, u'header_focus_width': 500, u'show_header_image': True, u'body_font': u'Helvetica Neue', u'show_title': True, u'header_stretch': True, u'avatar_shape': u'square', u'show_avatar': True, u'header_focus_height': 282, u'title_font': u'Gibson', u'header_image': u'http://static.tumblr.com/75bc2eab3cb07b368cfbaf7947fcd61b/soqnzor/H8Mn68k2i/tumblr_static_63hqr5ymqvkssc04cw4s0skoo.gif', u'header_image_scaled': u'http://static.tumblr.com/75bc2eab3cb07b368cfbaf7947fcd61b/soqnzor/H8Mn68k2i/tumblr_static_63hqr5ymqvkssc04cw4s0skoo_2048_v2.gif'}, u'name': u'tenkaboutthebutts'}, u'content': u'<p>proud patron =D</p>', u'post': {u'id': u'120800817969'}, u'content_raw': u'<p>proud patron =D</p>', u'is_current_item': True}], u'date': u'2015-06-05 20:58:46 GMT', u'thumbnail_height': 0, u'slug': u'saltyicecream-supported-by-patreon-miyuki-the', u'blog_name': u'tenkaboutthebutts', u'caption': u'<p><a href="http://saltyicecream.tumblr.com/post/120791148304/supported-by-patreon-miyuki-the-android-was" class="tumblr_blog">saltyicecream</a>:</p>\n\n<blockquote><h2>Supported by <b><a href="https://www.patreon.com/SaltyIceCream">Patreon</a></b></h2><p>Miyuki (the android) was voiced by <b><a href="http://megamoeka.tumblr.com/">MegaMoeka</a>.</b>\xa0</p><p><i>please don\u2019t be a creepo 8). It\u2019s called voice acting for a reason.</i></p><p>I found her through <a href="http://hentaiwriter.tumblr.com/">HentaiWriter</a>.\xa0Megamoeka is an awesome voice actress. I think she is still doing commissions for criminally low rates. I\u2019d hop on that if you need voice acting done.\xa0</p><p>I know it\u2019s short, I just wanted to see if I could actually do something like this. I think it turned out ok. The sound was a headache tho.</p><h2>Here is a <b><a href="http://webmup.com/7cb40/">WebM Link</a>.</b>\xa0Just better quality.</h2><p>On a side note, if you are interested in voice acting in future stuff, shoot me a voice demo (male or female, just be 18 or over). I don\u2019t need to hear moaning or anything like that, actual voice acting is way better for me.</p></blockquote>\n\n<p>proud patron =D</p>', u'thumbnail_url': u''}
    #vidme_result = handle_video_posts(session,vidme_post_dict)
    #logging.debug("vidme_result:"+repr(vidme_result))


    # xhamster.com
    xhamster_post_dict = {u'reblog_key': u'oJcaTUkA', u'reblog': {u'comment': u'<p>Quick video animation featuring <a href="http://littlemissbrex.tumblr.com/" target="_blank">LittleMissBrex</a>&rsquo;s voice.</p>\n<p>(During the previous audition, this submitted voice clip really inspired me to make an animation of it)</p>', u'tree_html': u''}, u'thumbnail_width': 0, u'player': [{u'width': 250, u'embed_code': u'<iframe width="250" height="187" src="http://xhamster.com/xembed.php?video=3328539" frameborder="0" scrolling="no"></iframe>'}, {u'width': 400, u'embed_code': u'<iframe width="400" height="300" src="http://xhamster.com/xembed.php?video=3328539" frameborder="0" scrolling="no"></iframe>'}, {u'width': 500, u'embed_code': u'<iframe width="500" height="375" src="http://xhamster.com/xembed.php?video=3328539" frameborder="0" scrolling="no"></iframe>'}], u'id': 93184782392L, u'highlighted': [], u'format': u'html', u'post_url': u'http://manyakisart.tumblr.com/post/93184782392/quick-video-animation-featuring-littlemissbrexs', u'recommended_source': None, u'state': u'published', u'short_url': u'http://tmblr.co/ZwXS0t1MoFl0u', u'html5_capable': False, u'type': u'video', u'tags': [u'Animation', u'LittleMissBrex', u'Pen', u'Masturbation'], u'timestamp': 1406611200, u'note_count': 507, u'video_type': u'unknown', u'trail': [{u'content': u'<p>Quick video animation featuring <a href="http://littlemissbrex.tumblr.com/" target="_blank">LittleMissBrex</a>\u2019s voice.</p>\n<p>(During the previous audition, this submitted voice clip really inspired me to make an animation of it)</p>', u'content_raw': u'<p>Quick video animation featuring <a href="http://littlemissbrex.tumblr.com/" target="_blank">LittleMissBrex</a>\'s voice.</p>\r\n<p>(During the previous audition, this submitted voice clip really inspired me to make an animation of it)</p>', u'is_current_item': True, u'blog': {u'theme': {u'title_font_weight': u'bold', u'title_color': u'#444444', u'header_bounds': u'', u'background_color': u'#FAFAFA', u'link_color': u'#529ECC', u'header_image_focused': u'http://static.tumblr.com/ee1543326d0dda96845ae39319176d21/wfewwet/BFRn5jwvr/tumblr_static_bvzexobv6nwcso844gks8ook8_2048_v2.jpg', u'show_description': True, u'show_header_image': True, u'body_font': u'Helvetica Neue', u'show_title': True, u'header_stretch': True, u'avatar_shape': u'circle', u'show_avatar': True, u'title_font': u'Gibson', u'header_image': u'http://static.tumblr.com/ee1543326d0dda96845ae39319176d21/wfewwet/BFRn5jwvr/tumblr_static_bvzexobv6nwcso844gks8ook8.jpg', u'header_image_scaled': u'http://static.tumblr.com/ee1543326d0dda96845ae39319176d21/wfewwet/BFRn5jwvr/tumblr_static_bvzexobv6nwcso844gks8ook8_2048_v2.jpg'}, u'name': u'manyakisart'}, u'is_root_item': True, u'post': {u'id': u'93184782392'}}], u'date': u'2014-07-29 05:20:00 GMT', u'thumbnail_height': 0, u'post_author': u'mikeinelart', u'slug': u'quick-video-animation-featuring-littlemissbrexs', u'blog_name': u'manyakisart', u'caption': u'<p>Quick video animation featuring <a href="http://littlemissbrex.tumblr.com/" target="_blank">LittleMissBrex</a>&rsquo;s voice.</p>\n<p>(During the previous audition, this submitted voice clip really inspired me to make an animation of it)</p>', u'thumbnail_url': u''}
    xhamster_result = handle_video_posts(session,xhamster_post_dict)
    logging.debug("xhamster_result:"+repr(xhamster_result))

    # xvideos.com
    xvideos_post_dict = {u'reblog_key': u'dwlUshzs', u'reblog': {u'comment': u'<p>thats it</p>\n<p>everyone in the porn industry go home</p>\n<p>this is the pinnacle of porn so there is no point in continuing</p>', u'tree_html': u''}, u'thumbnail_width': 0, u'player': [{u'width': 250, u'embed_code': u'<iframe src="http://flashservice.xvideos.com/embedframe/6114991" frameborder=0 width=510 height=400 scrolling=no></iframe>'}, {u'width': 400, u'embed_code': u'<iframe src="http://flashservice.xvideos.com/embedframe/6114991" frameborder=0 width=510 height=400 scrolling=no></iframe>'}, {u'width': 500, u'embed_code': u'<iframe src="http://flashservice.xvideos.com/embedframe/6114991" frameborder=0 width=510 height=400 scrolling=no></iframe>'}], u'id': 76968398547L, u'highlighted': [], u'format': u'html', u'post_url': u'http://atrolux.tumblr.com/post/76968398547/thats-it-everyone-in-the-porn-industry-go-home', u'recommended_source': None, u'state': u'published', u'short_url': u'http://tmblr.co/ZiXWFq17hh8xJ', u'html5_capable': False, u'type': u'video', u'tags': [u'nsfw', u'real porn'], u'timestamp': 1392657025, u'note_count': 81, u'video_type': u'unknown', u'trail': [{u'content': u'<p>thats it</p>\n<p>everyone in the porn industry go home</p>\n<p>this is the pinnacle of porn so there is no point in continuing</p>', u'content_raw': u'<p>thats it</p>\r\n<p>everyone in the porn industry go home</p>\r\n<p>this is the pinnacle of porn so there is no point in continuing</p>', u'is_current_item': True, u'blog': {u'theme': {u'title_font_weight': u'bold', u'title_color': u'#444444', u'header_bounds': u'', u'background_color': u'#89826C', u'link_color': u'#D4C69D', u'header_image_focused': u'http://static.tumblr.com/a6412cbeac7cba9cf282bce2dbe379bc/jo4xovz/cbRnn2cuf/tumblr_static_filename_2048_v2.jpg', u'show_description': True, u'show_header_image': True, u'body_font': u'Helvetica Neue', u'show_title': True, u'header_stretch': True, u'avatar_shape': u'square', u'show_avatar': True, u'title_font': u'Helvetica Neue', u'header_image': u'http://static.tumblr.com/a6412cbeac7cba9cf282bce2dbe379bc/jo4xovz/cbRnn2cuf/tumblr_static_filename.jpg', u'header_image_scaled': u'http://static.tumblr.com/a6412cbeac7cba9cf282bce2dbe379bc/jo4xovz/cbRnn2cuf/tumblr_static_filename_2048_v2.jpg'}, u'name': u'atrolux'}, u'is_root_item': True, u'post': {u'id': u'76968398547'}}], u'date': u'2014-02-17 17:10:25 GMT', u'thumbnail_height': 0, u'slug': u'thats-it-everyone-in-the-porn-industry-go-home', u'blog_name': u'atrolux', u'caption': u'<p>thats it</p>\n<p>everyone in the porn industry go home</p>\n<p>this is the pinnacle of porn so there is no point in continuing</p>', u'thumbnail_url': u''}
    #xvideos_result = handle_video_posts(session,xvideos_post_dict)
    #logging.debug("xvideos_result:"+repr(xvideos_result))

    # ign
    ign_post_dict = {u'reblog_key': u'A11AOxZ4', u'reblog': {u'comment': u'', u'tree_html': u'<p><a class="tumblr_blog" href="http://heckyeahratchetandclank.tumblr.com/post/55131168661/ratchet-and-clank-into-the-nexus-preview">heckyeahratchetandclank</a>:</p><blockquote>\n<p>Ratchet and Clank: Into the Nexus preview.</p>\n</blockquote>'}, u'thumbnail_width': 0, u'player': [{u'width': 250, u'embed_code': u'<iframe src="http://widgets.ign.com/video/embed/content.html?url=http://www.ign.com/videos/2013/07/10/ratchet-clank-into-the-nexus-video-preview" width="250" height="140" scrolling="no" frameborder="0" allowfullscreen></iframe>'}, {u'width': 400, u'embed_code': u'<iframe src="http://widgets.ign.com/video/embed/content.html?url=http://www.ign.com/videos/2013/07/10/ratchet-clank-into-the-nexus-video-preview" width="400" height="224" scrolling="no" frameborder="0" allowfullscreen></iframe>'}, {u'width': 500, u'embed_code': u'<iframe src="http://widgets.ign.com/video/embed/content.html?url=http://www.ign.com/videos/2013/07/10/ratchet-clank-into-the-nexus-video-preview" width="500" height="280" scrolling="no" frameborder="0" allowfullscreen></iframe>'}], u'id': 55132376273L, u'highlighted': [], u'source_title': u'heckyeahratchetandclank', u'format': u'html', u'post_url': u'http://blinkpen.tumblr.com/post/55132376273/heckyeahratchetandclank-ratchet-and-clank-into', u'recommended_source': None, u'state': u'published', u'short_url': u'http://tmblr.co/ZEPS1xpM9KpH', u'html5_capable': False, u'type': u'video', u'tags': [u'EXCITEMENT', u'AAAAAAAAAA', u'fuck i dont have a ps3', u';m;'], u'timestamp': 1373505842, u'note_count': 40, u'video_type': u'unknown', u'source_url': u'http://heckyeahratchetandclank.tumblr.com/post/55131168661/ratchet-and-clank-into-the-nexus-preview', u'trail': [{u'blog': {u'theme': {u'title_font_weight': u'bold', u'header_full_height': 768, u'title_color': u'#444444', u'header_bounds': u'108,1002,659,21', u'background_color': u'#FAFAFA', u'link_color': u'#529ECC', u'header_image_focused': u'http://static.tumblr.com/3b2881d95516e7eba16f0390b48d346a/6p5tmgy/vrTn5d3jx/tumblr_static_tumblr_static_am4rkfgq38gk0cwcocgsws84k_focused_v3.jpg', u'show_description': True, u'header_full_width': 1024, u'header_focus_width': 981, u'show_header_image': True, u'body_font': u'Helvetica Neue', u'show_title': True, u'header_stretch': True, u'avatar_shape': u'square', u'show_avatar': True, u'header_focus_height': 551, u'title_font': u'Gibson', u'header_image': u'http://static.tumblr.com/ae7c84944d965516123c8dca6fe4093c/6p5tmgy/DBkn5d3ju/tumblr_static_am4rkfgq38gk0cwcocgsws84k.png', u'header_image_scaled': u'http://static.tumblr.com/ae7c84944d965516123c8dca6fe4093c/6p5tmgy/DBkn5d3ju/tumblr_static_am4rkfgq38gk0cwcocgsws84k_2048_v2.png'}, u'name': u'heckyeahratchetandclank'}, u'content': u'<p>Ratchet and Clank: Into the Nexus preview.</p>', u'post': {u'id': u'55131168661'}, u'is_root_item': True}], u'date': u'2013-07-11 01:24:02 GMT', u'thumbnail_height': 0, u'slug': u'heckyeahratchetandclank-ratchet-and-clank-into', u'blog_name': u'blinkpen', u'caption': u'<p><a class="tumblr_blog" href="http://heckyeahratchetandclank.tumblr.com/post/55131168661/ratchet-and-clank-into-the-nexus-preview">heckyeahratchetandclank</a>:</p>\n<blockquote>\n<p>Ratchet and Clank: Into the Nexus preview.</p>\n</blockquote>', u'thumbnail_url': u''}
    #ign_result = handle_video_posts(session,ign_post_dict)
    #logging.debug("ign_result:"+repr(ign_result))

    # naturesoundsfor.me REALLY TUMBLR FUCKING REALLY?
    naturesoundsforme_post_dict = {u'reblog_key': u'A11AOxZ4', u'reblog': {u'comment': u'', u'tree_html': u'<p><a class="tumblr_blog" href="http://heckyeahratchetandclank.tumblr.com/post/55131168661/ratchet-and-clank-into-the-nexus-preview">heckyeahratchetandclank</a>:</p><blockquote>\n<p>Ratchet and Clank: Into the Nexus preview.</p>\n</blockquote>'}, u'thumbnail_width': 0, u'player': [{u'width': 250, u'embed_code': u'<iframe src="http://widgets.ign.com/video/embed/content.html?url=http://www.ign.com/videos/2013/07/10/ratchet-clank-into-the-nexus-video-preview" width="250" height="140" scrolling="no" frameborder="0" allowfullscreen></iframe>'}, {u'width': 400, u'embed_code': u'<iframe src="http://widgets.ign.com/video/embed/content.html?url=http://www.ign.com/videos/2013/07/10/ratchet-clank-into-the-nexus-video-preview" width="400" height="224" scrolling="no" frameborder="0" allowfullscreen></iframe>'}, {u'width': 500, u'embed_code': u'<iframe src="http://widgets.ign.com/video/embed/content.html?url=http://www.ign.com/videos/2013/07/10/ratchet-clank-into-the-nexus-video-preview" width="500" height="280" scrolling="no" frameborder="0" allowfullscreen></iframe>'}], u'id': 55132376273L, u'highlighted': [], u'source_title': u'heckyeahratchetandclank', u'format': u'html', u'post_url': u'http://blinkpen.tumblr.com/post/55132376273/heckyeahratchetandclank-ratchet-and-clank-into', u'recommended_source': None, u'state': u'published', u'short_url': u'http://tmblr.co/ZEPS1xpM9KpH', u'html5_capable': False, u'type': u'video', u'tags': [u'EXCITEMENT', u'AAAAAAAAAA', u'fuck i dont have a ps3', u';m;'], u'timestamp': 1373505842, u'note_count': 40, u'video_type': u'unknown', u'source_url': u'http://heckyeahratchetandclank.tumblr.com/post/55131168661/ratchet-and-clank-into-the-nexus-preview', u'trail': [{u'blog': {u'theme': {u'title_font_weight': u'bold', u'header_full_height': 768, u'title_color': u'#444444', u'header_bounds': u'108,1002,659,21', u'background_color': u'#FAFAFA', u'link_color': u'#529ECC', u'header_image_focused': u'http://static.tumblr.com/3b2881d95516e7eba16f0390b48d346a/6p5tmgy/vrTn5d3jx/tumblr_static_tumblr_static_am4rkfgq38gk0cwcocgsws84k_focused_v3.jpg', u'show_description': True, u'header_full_width': 1024, u'header_focus_width': 981, u'show_header_image': True, u'body_font': u'Helvetica Neue', u'show_title': True, u'header_stretch': True, u'avatar_shape': u'square', u'show_avatar': True, u'header_focus_height': 551, u'title_font': u'Gibson', u'header_image': u'http://static.tumblr.com/ae7c84944d965516123c8dca6fe4093c/6p5tmgy/DBkn5d3ju/tumblr_static_am4rkfgq38gk0cwcocgsws84k.png', u'header_image_scaled': u'http://static.tumblr.com/ae7c84944d965516123c8dca6fe4093c/6p5tmgy/DBkn5d3ju/tumblr_static_am4rkfgq38gk0cwcocgsws84k_2048_v2.png'}, u'name': u'heckyeahratchetandclank'}, u'content': u'<p>Ratchet and Clank: Into the Nexus preview.</p>', u'post': {u'id': u'55131168661'}, u'is_root_item': True}], u'date': u'2013-07-11 01:24:02 GMT', u'thumbnail_height': 0, u'slug': u'heckyeahratchetandclank-ratchet-and-clank-into', u'blog_name': u'blinkpen', u'caption': u'<p><a class="tumblr_blog" href="http://heckyeahratchetandclank.tumblr.com/post/55131168661/ratchet-and-clank-into-the-nexus-preview">heckyeahratchetandclank</a>:</p>\n<blockquote>\n<p>Ratchet and Clank: Into the Nexus preview.</p>\n</blockquote>', u'thumbnail_url': u''}
    #naturesoundsforme_result = handle_video_posts(session,naturesoundsforme_post_dict)
    #logging.debug("naturesoundsforme_result:"+repr(naturesoundsforme_result))

    # Flash embed
    flash_embed_1_post_dict = {u'reblog_key': u'yR1QXDvG', u'reblog': {u'comment': u'<p><em><strong>WHO IS BEHIND THIS MARVELOUS GADGET&hellip;.</strong></em></p>', u'tree_html': u'<p><a class="tumblr_blog" href="http://i-like-pigeons.tumblr.com/post/25713502874/your-keyboard-is-now-daft-punk-this-is-not-a">i-like-pigeons</a>:</p><blockquote>\n<p>Your keyboard is now Daft Punk\u2026</p>\n<p><small>this is not a video, click on it</small></p>\n<p><img src="http://media.tumblr.com/tumblr_lwqf46RRAN1r4w28f.png"/></p>\n<p><img src="http://media.tumblr.com/tumblr_m61cysdQfk1qgtjf8.gif"/></p>\n</blockquote>'}, u'thumbnail_width': 0, u'player': [{u'width': 250, u'embed_code': u'<embed width="250" height="291" align="middle" pluginspage="http://www.adobe.com/go/getflashplayer" type="application/x-shockwave-flash" allowfullscreen="false" allowscriptaccess="sameDomain" name="xdft" bgcolor="#000000" scale="noscale" quality="high" menu="false" src="http://www.najle.com/idaft/idaft/xdft.swf">'}, {u'width': 400, u'embed_code': u'<embed width="400" height="466" align="middle" pluginspage="http://www.adobe.com/go/getflashplayer" type="application/x-shockwave-flash" allowfullscreen="false" allowscriptaccess="sameDomain" name="xdft" bgcolor="#000000" scale="noscale" quality="high" menu="false" src="http://www.najle.com/idaft/idaft/xdft.swf">'}, {u'width': 500, u'embed_code': u'<embed width="500" height="582" align="middle" pluginspage="http://www.adobe.com/go/getflashplayer" type="application/x-shockwave-flash" allowfullscreen="false" allowscriptaccess="sameDomain" name="xdft" bgcolor="#000000" scale="noscale" quality="high" menu="false" src="http://www.najle.com/idaft/idaft/xdft.swf">'}], u'id': 25777675314L, u'highlighted': [], u'source_title': u'rossocrama', u'format': u'html', u'post_url': u'http://blinkpen.tumblr.com/post/25777675314/i-like-pigeons-your-keyboard-is-now-daft-punk', u'recommended_source': None, u'state': u'published', u'short_url': u'http://tmblr.co/ZEPS1xO0U1mo', u'html5_capable': False, u'type': u'video', u'tags': [u'daft punk', u'idaft', u'EVERYTHING IS FUN'], u'timestamp': 1340540254, u'note_count': 362383, u'video_type': u'unknown', u'source_url': u'http://rossocrama.tumblr.com/post/3683251435/your-keyboard-is-now-daft-punk-this-is-not-a', u'trail': [{u'blog': {u'theme': {u'title_font_weight': u'bold', u'header_full_height': 340, u'title_color': u'#444444', u'header_bounds': u'70,382,281,8', u'background_color': u'#F6F6F6', u'link_color': u'#529ECC', u'header_image_focused': u'http://static.tumblr.com/c06a92a7f8e0e067da8ba177f4dad940/yebyu3h/ISena682w/tumblr_static_tumblr_static_7vzgahntmccgk8480gc80ww88_focused_v3.gif', u'show_description': False, u'header_full_width': 385, u'header_focus_width': 374, u'show_header_image': True, u'body_font': u'Helvetica Neue', u'show_title': True, u'header_stretch': True, u'avatar_shape': u'circle', u'show_avatar': True, u'header_focus_height': 211, u'title_font': u'Helvetica Neue', u'header_image': u'http://static.tumblr.com/c06a92a7f8e0e067da8ba177f4dad940/yebyu3h/S4Yna67yv/tumblr_static_7vzgahntmccgk8480gc80ww88.gif', u'header_image_scaled': u'http://static.tumblr.com/c06a92a7f8e0e067da8ba177f4dad940/yebyu3h/S4Yna67yv/tumblr_static_7vzgahntmccgk8480gc80ww88_2048_v2.gif'}, u'name': u'i-like-pigeons'}, u'content': u'<p>Your keyboard is now Daft Punk\u2026</p>\n<p><small>this is not a video, click on it</small></p>\n<p><img src="http://media.tumblr.com/tumblr_lwqf46RRAN1r4w28f.png"></p>\n<p><img src="http://media.tumblr.com/tumblr_m61cysdQfk1qgtjf8.gif"></p>', u'post': {u'id': u'25713502874'}}, {u'blog': {u'theme': {u'title_font_weight': u'bold', u'header_full_height': 500, u'title_color': u'#444444', u'header_bounds': u'109,500,390,0', u'background_color': u'#FAFAFA', u'link_color': u'#529ECC', u'header_image_focused': u'http://static.tumblr.com/fd9046a4b64f963fdbdc19006aacd73c/0zjbon4/jYUni1cq9/tumblr_static_tumblr_static_cljm29atew0kgsgcw4kkkscc0_focused_v3.png', u'show_description': True, u'header_full_width': 500, u'header_focus_width': 500, u'show_header_image': True, u'body_font': u'Helvetica Neue', u'show_title': True, u'header_stretch': True, u'avatar_shape': u'circle', u'show_avatar': True, u'header_focus_height': 281, u'title_font': u'Gibson', u'header_image': u'http://static.tumblr.com/fd9046a4b64f963fdbdc19006aacd73c/0zjbon4/Qx7ni1cq8/tumblr_static_cljm29atew0kgsgcw4kkkscc0.png', u'header_image_scaled': u'http://static.tumblr.com/fd9046a4b64f963fdbdc19006aacd73c/0zjbon4/Qx7ni1cq8/tumblr_static_cljm29atew0kgsgcw4kkkscc0_2048_v2.png'}, u'name': u'blinkpen'}, u'content': u'<p><em><strong>WHO IS BEHIND THIS MARVELOUS GADGET\u2026.</strong></em></p>', u'post': {u'id': u'25777675314'}, u'content_raw': u'<p><em><strong>WHO IS BEHIND THIS MARVELOUS GADGET....</strong></em></p>', u'is_current_item': True}], u'date': u'2012-06-24 12:17:34 GMT', u'thumbnail_height': 0, u'slug': u'i-like-pigeons-your-keyboard-is-now-daft-punk', u'blog_name': u'blinkpen', u'caption': u'<p><a class="tumblr_blog" href="http://i-like-pigeons.tumblr.com/post/25713502874/your-keyboard-is-now-daft-punk-this-is-not-a">i-like-pigeons</a>:</p>\n<blockquote>\n<p>Your keyboard is now Daft Punk\u2026</p>\n<p><small>this is not a video, click on it</small></p>\n<p><img src="http://media.tumblr.com/tumblr_lwqf46RRAN1r4w28f.png"/></p>\n<p><img src="http://media.tumblr.com/tumblr_m61cysdQfk1qgtjf8.gif"/></p>\n</blockquote>\n\n<p><em><strong>WHO IS BEHIND THIS MARVELOUS GADGET&hellip;.</strong></em></p>', u'thumbnail_url': u''}
    flash_embed_1_result = handle_video_posts(session,flash_embed_1_post_dict)
    logging.debug("flash_embed_1_result:"+repr(flash_embed_1_result))

    # Broken different flash embed (401 error from dropbox is expected)
    flash_embed_2_post_dict = {u'reblog_key': u'SdXFvyFH', u'reblog': {u'comment': u'<p>Derpy: And it is awesome.</p>', u'tree_html': u''}, u'thumbnail_width': 0, u'player': [{u'width': 250, u'embed_code': u'<EMBED src="https://dl.dropbox.com/s/q8vz5tn8frgxgql/DailyFlash.swf" quality=high width="250" height="78" NAME="Yourfilename" ALIGN="" TYPE="application/x-shockwave-flash"></EMBED> '}, {u'width': 400, u'embed_code': u'<EMBED src="https://dl.dropbox.com/s/q8vz5tn8frgxgql/DailyFlash.swf" quality=high width="400" height="126" NAME="Yourfilename" ALIGN="" TYPE="application/x-shockwave-flash"></EMBED> '}, {u'width': 500, u'embed_code': u'<EMBED src="https://dl.dropbox.com/s/q8vz5tn8frgxgql/DailyFlash.swf" quality=high width="500" height="157" NAME="Yourfilename" ALIGN="" TYPE="application/x-shockwave-flash"></EMBED> '}], u'id': 36452349354L, u'highlighted': [], u'format': u'html', u'post_url': u'http://dailyderp.tumblr.com/post/36452349354/derpy-and-it-is-awesome', u'recommended_source': None, u'state': u'published', u'short_url': u'http://tmblr.co/ZZ3wevXykhMg', u'html5_capable': False, u'type': u'video', u'tags': [u'week28'], u'timestamp': 1353790223, u'note_count': 30, u'video_type': u'unknown', u'trail': [{u'content': u'<p>Derpy: And it is awesome.</p>', u'content_raw': u'<p>Derpy: And it is awesome.</p>', u'is_current_item': True, u'blog': {u'theme': {u'title_font_weight': u'bold', u'title_color': u'#444444', u'header_bounds': u'', u'background_color': u'#FAFAFA', u'link_color': u'#529ECC', u'header_image_focused': u'http://assets.tumblr.com/images/default_header/optica_pattern_08_focused_v3.png?_v=f0f055039bb6136b9661cf2227b535c2', u'show_description': True, u'show_header_image': True, u'body_font': u'Helvetica Neue', u'show_title': True, u'header_stretch': True, u'avatar_shape': u'square', u'show_avatar': True, u'title_font': u'Gibson', u'header_image': u'http://assets.tumblr.com/images/default_header/optica_pattern_08.png?_v=f0f055039bb6136b9661cf2227b535c2', u'header_image_scaled': u'http://assets.tumblr.com/images/default_header/optica_pattern_08_focused_v3.png?_v=f0f055039bb6136b9661cf2227b535c2'}, u'name': u'dailyderp'}, u'is_root_item': True, u'post': {u'id': u'36452349354'}}], u'date': u'2012-11-24 20:50:23 GMT', u'thumbnail_height': 0, u'slug': u'derpy-and-it-is-awesome', u'blog_name': u'dailyderp', u'caption': u'<p>Derpy: And it is awesome.</p>', u'thumbnail_url': u''}
    flash_embed_2_result = handle_video_posts(session,flash_embed_2_post_dict)
    logging.debug("flash_embed_2_result:"+repr(flash_embed_2_result))

    return


def main():
    try:
        setup_logging(log_file_path=os.path.join("debug","video-handlers-log.txt"))
        debug()
    except Exception, e:# Log fatal exceptions
        logging.critical("Unhandled exception!")
        logging.exception(e)
    return


if __name__ == '__main__':
    main()
