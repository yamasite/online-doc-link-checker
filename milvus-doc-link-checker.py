# encoding utf-8
# using Python 3.5.1
# Crawls all doc pages from the sitemap and check if all links are valid

import urllib.request
from lxml import etree
from pathlib import Path
import os
import requests
from bs4 import BeautifulSoup


class GetURLsFromSitemap(object):


    def __init__(self, url):
        self.url = url


    def get_url_list(self, url):

        file_name = "outputlinks.txt"

        # Gets the sitemap file per the URL
        def get_sitemap(url):

            try:
                response = urllib.request.urlopen(url, data=None)
                xml_code = response.read()
                # print(type(xml_code))
                # Take URLs with the following format: <xhtml:link rel="alternate" hreflang="en" href="https://www.milvus.io/docs/en/aboutmilvus/overview"/>
                xml_root = etree.HTML(xml_code)
                # print(etree.tostring(xml_root))
            except urllib.request.URLError as e:
                xml_root = etree.HTML("")
                print(e)

            return xml_root

        xml_root = get_sitemap(url)
        # Find all links in href attributes
        link_elements = xml_root.findall(".//link[@href]")
        links = []
        for link_element in link_elements:
            # print(type(link_element))
            link_href = link_element.get("href")
            # print(type(link_href))
            links.append(link_href)

        # Find all links in <loc> tags
        link_elements_loc = xml_root.findall(".//loc")
        for link_element_loc in link_elements_loc:
            link_loc = etree.tostring(link_element_loc, method="text")
            # Remove b' prefixes by changing byte literals to strings
            links.append(link_loc.decode('utf-8'))

        #print(links)

        # Writes the URL list to a text file
        text_file = Path(file_name)
        if text_file.is_file():
            os.remove(file_name)

        with open(file_name,'a') as f:
            for link in links:
             f.write(link + "\n")

        return file_name



class CheckLinkStatus(object):

    def __init__(self, file_name):
        self.file_name = file_name

    def check_link_status(self, file_name):

        report_name="link_report.txt"

        with open(file_name,'r',encoding='utf-8') as f:
            links = f.read().splitlines()
            # Abandonded this: links = f.readlines()
            # readlines() is stupid because newline character is added to each element. This
            # will lead to errors in later functions that use the URL. %0A is the URL encoding
            # of a newline

        text_file = Path(report_name)
        if text_file.is_file():
            os.remove(report_name)

        for link in links:
            try:
                print(link)
                # print(type(link))
                r = requests.get(link)
                # header_info = r.raise_for_status()
                status_code = r.status_code

                """
                Informational responses (100–199),
                Successful responses (200–299),
                Redirects (300–399),
                Client errors (400–499),
                and Server errors (500–599).
                """
                # Consider putting this info in a database
                with open(report_name,'a', encoding="utf-8") as f:

                    if status_code is 200:
                        f.write("PASS " + "Status code: " + str(status_code) + " " + str(link) + " has no errors." + "\n")
                    elif status_code in range(300,399):
                        f.write("FAIL " + "Status code: " + str(status_code) + " " + str(link) + " has a redirect." + "\n")
                    elif status_code in range(400,599):
                        f.write("FAIL " + "Status code: " + str(status_code) + " " + str(link) + " has errors." + "\n")


            except requests.ConnectionError:
                print("Failed to connect.")

        # Format the report




class GetURLFromEachPage(object):
    
    def __init__(self, sitemap_link_file):
        self.sitemap_url_list = sitemap_link_file
    
    def extract_url_from_html(self, sitemap_link_file):

        links = []
        full_report_name = "full_link_report.txt"

        with open(sitemap_link_file,'r',encoding='utf-8') as f:
            parse_url_list = f.read().splitlines()


        for parse_url in parse_url_list:

            links.append(parse_url)

            try:
                response = urllib.request.urlopen(parse_url, data=None)
                html_code = response.read()
                soup = BeautifulSoup(html_code.decode("utf-8"),"lxml")
                a_links = soup.find_all("a")
                for a_link in a_links:
                    link = a_link.get("href")
                    if type(link) is str:

                        if link.startswith("http://") or link.startswith("https://"):
                            links.append(link)
                        elif link.startswith("mailto:"):
                            links.append(link)
                        else:
                            link = parse_url + link
                            links.append(link)


                # Need to define a dictionary to save the location of URLs.
                # parse_url is the root page


            except urllib.request.URLError as e:
                print(e)


        with open(full_report_name, "w+", encoding="utf-8") as f:
            for link in links:
                f.write(link + "\n")
        # writelines() is also stupid because it does not add new line characters


# Get sitemap
SitemapURLMilvus = GetURLsFromSitemap("https://milvus.io/sitemap.xml")
SitemapURLMilvus.get_url_list("https://milvus.io/sitemap.xml")

# Extract URLs from pages in the sitemap
GetURLFromEachPageMilvus = GetURLFromEachPage("outputlinks.txt")
GetURLFromEachPageMilvus.extract_url_from_html("outputlinks.txt")


# Validate all links
CheckLinkStatusMilvus = CheckLinkStatus("full_link_report.txt")
CheckLinkStatusMilvus.check_link_status("full_link_report.txt")