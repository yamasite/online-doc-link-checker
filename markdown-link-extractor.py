# encoding utf-8
# Using Python 3.x

import urllib.request
import urllib.error
from pathlib import Path
import requests
import json
from urllib.parse import urlparse
import markdown
import os
from os.path import join, getsize
from bs4 import BeautifulSoup


class LinksFromMarkdown(object):

    def __init__(self, repository):
        self.dictionary = repository

    def extract_links_from_markdown(self, repository):

        repository = "D:\GithubRepo\docs-master"
        link_file = "extracted_links.json"

        md_files = []
        pics = []

        for root, dirs, files in os.walk(repository):
            # print(root, "consumes", end=" ")
            # print(sum(getsize(join(root, name)) for name in files), end=" ")
            # print("bytes in", len(files), "non-directory files")
            if len(files) != 0:
                # print(files)
                for file in files:
                    if file.endswith(".md") or file.endswith(".MD"):
                        md_files.append(join(root, file))
                    elif file.endswith(".png") or file.endswith(".PNG"):
                        pics.append((join(root, file)))

        # print(md_files)
        # print(pics)

        a_href_list = []

        for md_file in md_files:
            with open(md_file, "r", encoding="utf-8") as f:
                html = markdown.markdown(f.read())
                # print(html)
                soup = BeautifulSoup(html, "lxml")
                a_hrefs = [(x.get('href')) for x in soup.find_all("a")]

                a_href_list.append(a_hrefs)
                # print(a_hrefs)
                # print(md_file)

        # Generates a dictionary that indicates each MD file and links extracted from the MD file
        dictionary = dict(zip(md_files, a_href_list))

        with open(link_file, "w+", encoding="utf-8") as f:
            json.dump(dictionary, f)


        # print(dictionary)

class CheckExtractedLinksFromMarkdown(object):

    def __init__(self, link_file):
        self.link_file = link_file

    def check_extracted_links(self, link_file):

        report_name = "link_validation_report.html"
        html_code = """<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Link Validation Detailed Report</title></head><body><h1>Link Validation Detailed Report</h1>"""

        with open(link_file, "r", encoding="utf-8") as f:
            json_text = f.read()

        link_dict = json.loads(json_text)

        # If the report file exists, remove the file.
        text_file = Path(report_name)
        if text_file.is_file():
            os.remove(report_name)

        with open(report_name, "w+", encoding="utf-8") as f:
            f.write(html_code)

        for key in link_dict.keys():
            head_code = ""
            table_code = ""

            head_code = """<table border="1"><tr><th>Link</th><th>Status</th><th>Parent Page</th></tr>"""

            with open(report_name, "a", encoding="utf-8") as f:
                f.write("""<h2>Checking links in """ + key)
                f.write(head_code)

            # links = link_dict.get(key)
            # for link in link_dict.get(key):




# Get link JSON file
LinksFromMarkdown_Milvus = LinksFromMarkdown("D:\GithubRepo\docs-master")
LinksFromMarkdown_Milvus.extract_links_from_markdown("D:\GithubRepo\docs-master")


# Generate link validation report


