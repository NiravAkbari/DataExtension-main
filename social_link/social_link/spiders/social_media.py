import os
import glob
import scrapy
import pandas as pd
import datetime

folder_path = "./input_folder"

files = glob.glob(os.path.join(folder_path, "*"))
files.sort(key=os.path.getmtime, reverse=True)

if files:
    input_folder_path = files[0]
    today = datetime.datetime.now()
    file_name = input_folder_path.split("\\")[1].split(".")[0]
    output_folder_path = f'./output_folder/{file_name}_output_{today.strftime("%Y_%m_%dT%H_%M_%S")}.xlsx'

    class SocialMediaSpider(scrapy.Spider):
        name = "social_media"
        def __init__(self):
            self.df = pd.read_excel(input_folder_path)
            print(self.df)

            self.html_snippets = self.df['Contact_Page']

            self.headers = {
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
                }

        def start_requests(self):
            for index, row in self.df.iterrows():
                snippet = row['Contact_Page']  
                yield scrapy.Request(url=snippet, headers=self.headers, callback=self.parse, meta={"index": index}, errback=self.error_handler,dont_filter=True)     
                break
        def parse(self, response):
            social_media_links = set(response.xpath(
                '//a[contains(@href, "twitter.com") or contains(@href, "facebook.com") or contains(@href, "tiktok.com") or contains(@href, "linkedin.com") or contains(@href, "mailto:") or contains(@href, "instagram.com") or contains(@href, "pinterest.com") or contains(@href, "youtube.com")][@target]/@href').extract())

            social_columns = {
                'Twitter Links': [],
                'Facebook Links': [],
                'TikTok Links': [],
                'LinkedIn Links': [],
                'Mail Links': [],
                'Instagram Links': [],
                'Pinterest Links': [],
                'YouTube Links': [],
            }

            index = response.meta["index"]

            for link in social_media_links:
                if 'twitter.com' in link:
                    social_columns['Twitter Links'].append(link)
                elif 'facebook.com' in link:
                    social_columns['Facebook Links'].append(link)
                elif 'tiktok.com' in link:
                    social_columns['TikTok Links'].append(link)
                elif 'linkedin.com' in link:
                    social_columns['LinkedIn Links'].append(link)
                elif 'mailto:' in link:
                    social_columns['Mail Links'].append(link)
                elif 'instagram.com' in link:
                    social_columns['Instagram Links'].append(link)
                elif 'pinterest.com' in link:
                    social_columns['Pinterest Links'].append(link)
                elif 'youtube.com' in link:
                    social_columns['YouTube Links'].append(link)

            for column, links in social_columns.items():
                self.df.at[index, column] = ', '.join(links)  

            self.df.to_excel(output_folder_path, index=False)    

        def error_handler(self, failure):
            request = failure.request
            response = failure.value.response

            if response is not None:
                if response.status == 301:
                    new_location = response.headers.get('Location')
                    self.logger.warning(f"Following 301 redirect to: {new_location}")
                    yield scrapy.Request(url=new_location, callback=self.parse, errback=self.error_handler)

                elif response.status == 404:
                    self.logger.error(f"404 Not Found for URL: {request.url}")

            elif 'DNSLookupError' in str(failure):
                self.logger.warning(f"Retrying DNS lookup failed request: {request.url}")
                yield request
            
            else:
                pass
else:
    print("The folder is empty. >>>>>>>>>>>>>>>>>>>>>>>")