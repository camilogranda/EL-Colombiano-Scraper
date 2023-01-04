from common2 import config
from requests.exceptions import HTTPError
from urllib3.exceptions import MaxRetryError
import argparse
import datetime
import logging
import csv
import re
import news_objects as news


logger = logging.getLogger(__name__)
is_well_formed_link = re.compile(r'^https?://.+/.+$')
is_root_path = re.compile(r'^/[^/].+$')
no_protocol_path = re.compile(r'^[//].+')
is_other_host = re.compile(r'^https?://.+/$')


def  _news_scraper(news_site_uid):
    host = config()['news_sites'][news_site_uid]['url']
    logging.info('Beginning scraper for {}'.format(host))
    
    subsection_links = _subsection_links(news_site_uid, host)
    subsec_homepages = [news.HomePage(news_site_uid, link) for link in subsection_links]
    homepage_links = [homepage.article_links for homepage in subsec_homepages[:2]]

    # join all subsection sets
    links_set = homepage_links[0]
    for s in homepage_links:
        links_set.update(s)

    articles = []
    
    for link in links_set:
        article = _fetch_article(news_site_uid, host, link)

        if article:
            logger.info(' Article fetched!')
            articles.append(article)

    _save_articles(news_site_uid, articles)

def _save_articles(news_site_uid, articles):
    field_names = articles[0].keys()
    now = datetime.datetime.now().strftime('%Y-%m-%d')
    out_file_name = '{news_site_uid}_{datetime}_articles.csv'.format(news_site_uid=news_site_uid, datetime=now)
    with open(out_file_name, 'w') as f:
        writer = csv.DictWriter(f, fieldnames=field_names)
        writer.writeheader()
        writer.writerows(articles)


def _fetch_article(news_site_uid, host, link):
    logger.info('Start fetching article at {}'.format(link))
    articlepage = news.ArticlePage(news_site_uid, _build_link(host, link))
    article = None
    try:
        article = articlepage.get_article
    except (HTTPError, MaxRetryError) as e:
        logger.warning('Error while fetching the article.', exc_info=False)
    
    return article


def _subsection_links(news_site_uid, host):
    # Get all sections
    homepage = news.HomePage(news_site_uid, host)
    section_links = [_build_link(host, sec) for sec in homepage.sec_links]
    sections_homepage = [news.HomePage(news_site_uid, sec) for sec in section_links]

    # Get all subsections
    subsection_list = []
    for section in sections_homepage:
        for subsection in section.subsec_links:
            subsection_list.append(_build_link(host, subsection))

    return subsection_list

    # one liner of this for-loop:
    # [subsection_list.extend([_build_link(host, subsection) for subsection in sec.subsec_links]) for sec in secciones]


def _build_link(host, link):
    if is_well_formed_link.match(link):
        return link
    elif is_other_host.match(link):
        return link
    elif is_root_path.match(link):
        return '{}{}'.format(host, link)
    elif no_protocol_path.match(link):
        return 'https:' + link
    else:
        return '{host}/{uri}'.format(host=host, uri=link)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    news_site_choices = list(config()['news_sites'].keys())
    parser.add_argument('news_site',
                        help='The news site that you want to scrape',
                        type=str,
                        choices=news_site_choices)

    args = parser.parse_args()
    _news_scraper(args.news_site)