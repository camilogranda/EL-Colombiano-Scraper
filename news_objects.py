from bs4 import BeautifulSoup
import requests
import json
from common2 import config

class NewsPage:

    def __init__(self, news_site_uid, url):
        self._config = config()['news_sites'][news_site_uid]
        self._queries = self._config['queries']
        self._html = None
        self._url = url

        self._visit(url)

    def _select(self, query_string):
        return self._html.select(query_string)
    
    def _find(self, query_string, attrs):
        return self._html.find(query_string, attrs=attrs)

    def _visit(self, url):
        response = requests.get(url)
        response.raise_for_status()
        self._html = BeautifulSoup(response.content.decode('utf-8', 'ignore'), 'lxml')


class HomePage(NewsPage):

    def __init__(self, news_site_uid, url):
        super().__init__(news_site_uid, url)

    @property
    def sec_links(self):

        try:
            sections = self._select(self._queries['sections_link'])
            section_links = [section['href'] for section in sections][:-2]

            return section_links
        except Exception as e:
            print('Error:', e)

    @property
    def subsec_links(self):
        
        try:
            subsections = self._select(self._queries['sub_sect_links'])
            subsection_links = [subsec['href'] for subsec in subsections]
    
            return subsection_links

        except Exception as e:
            print('Error', e)

    @property
    def article_links(self):
        link_list = []

        try:
            for link in self._select(self._queries['homepage_article_links']):
                if link and link.has_attr('href'):
                    link_list.append(link)
        except Exception as e:
            print('Error:', e)
        
        return set(link['href'] for link in link_list)


class ArticlePage(NewsPage):
    
    def __init__(self, news_site_uid, url):
        super().__init__(news_site_uid, url)
    
    @property
    def get_article(self):
        
        article_dict = {}
        try:
            date = str(self._find(self._queries['article_date'][0], self._queries['article_date'][1]))
            if date:
                date_soup = BeautifulSoup(date, 'lxml')
                script_tag = date_soup.find('script')
                json_obj = json.loads(script_tag.contents[0])
                art_date = json_obj.get('datePublished')
            else:
                art_date = None

            title = self._select(self._queries['article_title'])
            if title:
                article_dict['title'] = title[0].text
            else:
                article_dict['title'] = None
            
            summary = self._find(self._queries['article_summary']['summary_find'][0], self._queries['article_summary']['summary_find'][1]).find_all(self._queries['article_summary']['summary_findall'])[0]
            if summary:
                article_dict['summary'] = summary.text
            else:
                article_dict['summary'] = None

            body = self._select(self._queries['article_body'])
            body_text = [p for p in body]

            body = ""
            if len(body_text) > 0:
                for p in body_text:
                    body += ' ' + p.text
                if body:
                    article_dict['body'] = body
                else:
                    article_dict['body'] = None

            article_dict['url'] = self._url

        except Exception as e:
            print('Error:', e)

        return article_dict