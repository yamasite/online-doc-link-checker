# encoding utf-8
# using Python 3.5.1
# Crawls all doc pages from the sitemap and check if all links are valid

import urllib.request
from lxml import etree
from pathlib import Path
import os
import requests
from bs4 import BeautifulSoup
import json


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
            links.append(link_loc.decode("utf-8"))

        #print(links)

        # Writes the URL list to a text file
        text_file = Path(file_name)
        if text_file.is_file():
            os.remove(file_name)

        with open(file_name,"a") as f:
            for link in links:
             f.write(link + "\n")

        return file_name


class GetURLFromEachPage(object):
    def __init__(self, sitemap_link_file):
        self.sitemap_url_list = sitemap_link_file

    def extract_url_from_html(self, sitemap_link_file):

        child_links = ()

        url_dict = {}

        full_report_name = "full_link_report.json"

        milvus_home = "https://www.milvus.io/"

        with open(sitemap_link_file, "r", encoding="utf-8") as f:
            parse_url_list = f.read().splitlines()

        for parse_url in parse_url_list:

            try:
                response = urllib.request.urlopen(parse_url, data=None)
                html_code = response.read()
                soup = BeautifulSoup(html_code.decode("utf-8"), "lxml")
                a_links = soup.find_all("a")
                # print(a_links)
                for a_link in a_links:
                    link = a_link.get("href")
                    if type(link) is str:
                        # Absolute URLs
                        if link.startswith("http://") or link.startswith("https://"):
                            child_links = (*child_links, link)
                        # Relative URLs
                        elif link.startswith("/"):
                            # parse_url does not end with "/"
                            child_links= (*child_links,str(milvus_home + link))
                        # mailto:, ftp://, telnet, etc. are off the table because this is a doc checker
                # print(child_links)
                # Wash the data to convert any key that is not a string into a string
                # The keys are child links and the values are root links
                url_dict.update({str(child_links):parse_url})
                # print(url_dict)

            except urllib.request.URLError as e:
                print(e)
                # tuples in python are defined by the existence of commas, not brackets
                empty_link = ("broken link",)
                url_dict.update({str(empty_link):parse_url})


        with open(full_report_name, "w+", encoding="utf-8") as f:
            json.dump(url_dict,f)
            # for link in links:
                # f.write(link + "\n")
                # writelines() is also stupid because it does not add new line characters

class CheckLinkStatus(object):

    def __init__(self, file_name):
        self.file_name = file_name

    def check_link_status(self, file_name):

        report_name="link_validation_report.html"

        html_code = """<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Link Validation Report</title></head><body><h1>Link Validation Report</h1>"""

        with open(report_name, "w+", encoding="utf-8") as f:
            f.write(html_code)

        with open(file_name,"r",encoding="utf-8") as f:
            json_text = f.read()

        link_dict = json.loads(json_text)

        # If the report file exists, remove the file.
        text_file = Path(report_name)
        if text_file.is_file():
            os.remove(report_name)


        for key in link_dict.keys():

            head_code = ""
            table_code = ""

            new_key = eval(key)
            print(type(key))
            print(key)

            try:
                if key != """('broken link',)""":
                    print(key)

                    head_code = """<p>""" + link_dict[
                        key] + """ contains the following links:</p><table><tr><th>Link</th><th>Status</th></tr>"""

                    with open(report_name, "a", encoding="utf-8") as f:
                        f.write(head_code)

                    # Use set to remove duplicate links. This can significantly reduce execution time
                    for link in set(new_key):
                        link_response = requests.get(link, timeout=10)
                        status_code = link_response.status_code
                        row_code = """<tr><td>""" + link + """</td><td>""" + str(status_code) + """</td></tr>"""

                        with open(report_name, "a", encoding="utf-8") as f:
                            f.write(row_code)

                        print("""Checked link for """ + link)

                    with open(report_name, "a", encoding="utf-8") as f:
                        f.write("</table>")

                else:
                    head_code = """<p>""" + link_dict[key] + """ is broken</p>"""
                    with open(report_name, "a", encoding="utf-8") as f:
                        f.write(head_code)
                    # print(head_code)

                """
                
                Informational responses (100–199),
                Successful responses (200–299),
                Redirects (300–399),
                Client errors (400–499),
                and Server errors (500–599).
                
                """


            except requests.exceptions.Timeout as timeout_error:
                print(timeout_error)

        with open(report_name, "a", encoding="utf-8") as f:
            f.write("""</body></html>""")


# Get sitemap
# SitemapURLMilvus = GetURLsFromSitemap("https://milvus.io/sitemap.xml")
# SitemapURLMilvus.get_url_list("https://milvus.io/sitemap.xml")

# Extract URLs from pages in the sitemap and generate a JSON file to store link info
GetURLFromEachPageMilvus = GetURLFromEachPage("outputlinks.txt")
GetURLFromEachPageMilvus.extract_url_from_html("outputlinks.txt")


# Validate all links
CheckLinkStatusMilvus = CheckLinkStatus("full_link_report.json")
CheckLinkStatusMilvus.check_link_status("full_link_report.json")

