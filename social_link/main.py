import os
from scrapy.crawler import CrawlerProcess
from social_link.spiders.social_media import SocialMediaSpider

def social_media_run():
    
    process = CrawlerProcess()
    process.crawl(SocialMediaSpider)
    process.start()

if __name__ == '__main__':
    social_media_run()
