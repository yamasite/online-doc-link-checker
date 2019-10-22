# encoding utf-8
# using Python 3.5.x
# Crawls all doc pages from the sitemap and check if all links are valid

import urllib.request
import urllib.error
from lxml import etree
from pathlib import Path
import os
import requests
from bs4 import BeautifulSoup
import json
import ssl
from urllib.parse import urljoin
from urllib.parse import urlparse


class GetURLsFromSitemap(object):
    def __init__(self, url):
        self.url = url

    def get_url_list(self, url):

        file_name = "outputlinks.txt"

        # Gets the sitemap file per the URL
        def get_sitemap(url):

            try:

                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) Gecko/20100101 Firefox/23.0'}
                req = urllib.request.Request(url=url, headers=headers)
                ssl._create_default_https_context = ssl._create_unverified_context
                response = urllib.request.urlopen(req)
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

        # print(links)

        # Writes the URL list to a text file
        text_file = Path(file_name)
        if text_file.is_file():
            os.remove(file_name)

        with open(file_name, "a") as f:
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

        with open(sitemap_link_file, "r", encoding="utf-8") as f:
            parse_url_list = f.read().splitlines()

        for parse_url in parse_url_list:

            try:
                response = urllib.request.urlopen(parse_url, data=None)
                html_code = response.read()
                soup = BeautifulSoup(html_code.decode("utf-8"), "lxml")
                a_links = soup.find_all("a")
                img_links = soup.find_all("img")
                # print(a_links)
                # Get links from <a>
                for a_link in a_links:
                    link = a_link.get("href")
                    if type(link) is str:
                        # Absolute URLs
                        if link.startswith("http://") or link.startswith("https://"):
                            child_links = (*child_links, link)
                        # Relative URLs
                        elif link.startswith("/"):
                            # parse_url does not end with "/"
                            child_links = (*child_links, str(urljoin(parse_url, link)))
                        # Anchors
                        elif link.startswith("#") and link != "#":
                            child_links = (*child_links, str(parse_url + link))
                            # We only check http/https here https://tools.ietf.org/html/rfc1738
                # Get links from <img>
                for img_link in img_links:
                    link = img_link.get("src")
                    if type(link) is str:
                        # Absolute URLs
                        if link.startswith("http://") or link.startswith("https://"):
                            child_links = (*child_links, link)
                        # Relative URLs
                        elif link.startswith("/"):
                            # parse_url does not end with "/"
                            child_links = (*child_links, str(urljoin(parse_url, link)))
                        # Anchors

                # print(child_links)
                # Wash the data to convert any key that is not a string into a string
                # The keys are child links and the values are root links
                url_dict.update({str(child_links): parse_url})
                # print(url_dict)

            except urllib.request.URLError as e:
                print(e)
                # tuples in python are defined by the existence of commas, not brackets
                empty_link = ("broken link",)
                url_dict.update({str(empty_link): parse_url})

        with open(full_report_name, "w+", encoding="utf-8") as f:
            json.dump(url_dict, f)
            # for link in links:
            # f.write(link + "\n")
            # writelines() is also stupid because it does not add new line characters


class CheckLinkStatus(object):
    def __init__(self, file_name):
        self.file_name = file_name

    def check_link_status(self, file_name):

        report_name = "link_validation_report.html"
        root_page = "https://www.milvus.io"

        html_code = """<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Link Validation Detailed Report</title></head><body><h1>Link Validation Detailed Report</h1>"""

        with open(file_name, "r", encoding="utf-8") as f:
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

            new_key = eval(key)
            print(type(new_key))
            print(new_key)

            if key != """('broken link',)""":
                # print(key)

                head_code = """<table border="1"><tr><th>Link</th><th>Status</th><th>Parent Page</th></tr>"""

                with open(report_name, "a", encoding="utf-8") as f:
                    f.write("""<h2>Child links for <a href=\"""" + link_dict[key] + """\">""" + link_dict[
                        key] + """</a>""" + """</h2>""")
                    f.write(head_code)

                # Use set to remove duplicate links. This can significantly reduce execution time
                for link in set(new_key):

                    # Need JavaScript to check anchor links, i.e. links with hash tags
                    try:
                        link_response = requests.get(link, timeout=60)
                        status_code = link_response.status_code
                        """
                            Informational responses (100–199),
                            Successful responses (200–299),
                            Redirects (300–399),
                            Client errors (400–499),
                            and Server errors (500–599).
                        """
                        if "//" not in urlparse(link).path:

                            if status_code in range(200, 299):

                                if "#" not in link:
                                    row_code = """<tr class="success" bgcolor="#32CD32"><td>""" + """<a href=\"""" + link + """\">""" + link + """</a>""" + """</td><td>""" + str(
                                        status_code) + """</td><td>""" + """<a href=\"""" + link_dict[key] + """\">""" + \
                                               link_dict[key] + """</a>""" + """</td></tr>"""
                                else:
                                    try:

                                        headers = {
                                            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) Gecko/20100101 Firefox/23.0'}

                                        req = urllib.request.Request(url=str(
                                            urlparse(link).scheme + "://" + urlparse(link).netloc + urlparse(
                                                link).path), headers=headers)
                                        response = urllib.request.urlopen(req, data=None)
                                        html_code = response.read()
                                        soup = BeautifulSoup(html_code.decode("utf-8"), "lxml")
                                        a_hash = soup.find("a", {"id": str(urlparse(link).fragment)})
                                        h1_hash = soup.find("h1", {"id": str(urlparse(link).fragment)})
                                        h2_hash = soup.find("h2", {"id": str(urlparse(link).fragment)})
                                        h3_hash = soup.find("h3", {"id": str(urlparse(link).fragment)})
                                        h4_hash = soup.find("h4", {"id": str(urlparse(link).fragment)})
                                        h5_hash = soup.find("h5", {"id": str(urlparse(link).fragment)})
                                        h6_hash = soup.find("h6", {"id": str(urlparse(link).fragment)})
                                        div_hash = soup.find("div", {"id": str(urlparse(link).fragment)})

                                        if (None, None, None, None, None, None, None, None) != (
                                                a_hash, h1_hash, h2_hash, h3_hash, h4_hash, h5_hash, h6_hash, div_hash):
                                            row_code = """<tr class="success" bgcolor="#32CD32"><td>""" + """<a href=\"""" + link + """\">""" + link + """</a>""" + """</td><td>""" + str(
                                                status_code) + """</td><td>""" + """<a href=\"""" + link_dict[
                                                           key] + """\">""" + \
                                                       link_dict[key] + """</a>""" + """</td></tr>"""
                                        else:
                                            row_code = """<tr class="fail" bgcolor="#FF0000"><td>""" + """<a href=\"""" + link + """\">""" + link + """</a>""" + """</td><td>""" + str(
                                                status_code) + """ The URL looks good but the anchor link does not work or is not using an anchor tag.""" + """</td><td>""" + """<a href=\"""" + link_dict[
                                                           key] + """\">""" + \
                                                       link_dict[key] + """</a>""" + """</td></tr>"""
                                    except urllib.error.HTTPError as http_error:
                                        row_code = """<tr class="fail" bgcolor="#FF0000"><td>""" + """<a href=\"""" + link + """\">""" + link + """</a>""" + """</td><td>""" + str(
                                            status_code) + """ """ + str(http_error) + """ The URL looks good but the page then returns an HTTP error.</td><td>""" + """<a href=\"""" + link_dict[
                                                       key] + """\">""" + \
                                                   link_dict[key] + """</a>""" + """</td></tr>"""
                                    except urllib.error.URLError as url_error:
                                        row_code = """<tr class="fail" bgcolor="#FF0000"><td>""" + """<a href=\"""" + link + """\">""" + link + """</a>""" + """</td><td>""" + str(
                                            status_code) + """ """ + str(url_error) + """ The URL looks good but the page then returns a URL error.</td><td>""" + """<a href=\"""" + link_dict[
                                                       key] + """\">""" + \
                                                   link_dict[key] + """</a>""" + """</td></tr>"""



                            elif status_code in range(400, 599):
                                row_code = """<tr class="fail" bgcolor="#FF0000"><td>""" + """<a href=\"""" + link + """\">""" + link + """</a>""" + """</td><td>""" + str(
                                    status_code) + """</td><td>""" + """<a href=\"""" + link_dict[key] + """\">""" + \
                                           link_dict[key] + """</a>""" + """</td></tr>"""

                            
                        else:
                            row_code = """<tr class="fail" bgcolor="#FF0000"><td>""" + """<a href=\"""" + link + """\">""" + link + """</a>""" + """</td><td>""" + str(
                                status_code) + """ '//' is always an error when checking remote URLs""" + """</td><td>""" + """<a href=\"""" + link_dict[key] + """\">""" + \
                                       link_dict[key] + """</a>""" + """</td></tr>"""
                            
                        with open(report_name, "a", encoding="utf-8") as f:
                                f.write(row_code)
                                # print(row_code)
                                print("""Checked link for """ + link)


                    except requests.exceptions.Timeout as timeout_error:
                        print(timeout_error)
                        row_code = """<tr class="fail" bgcolor="#FF0000"><td>""" + """<a href=\"""" + link + """\">""" + link + """</a>""" + """</td><td>""" + str(
                            timeout_error) + """</td><td>""" + """<a href=\"""" + link_dict[key] + """\">""" + \
                                   link_dict[key] + """</a>""" + """</td></tr>"""
                        with open(report_name, "a", encoding="utf-8") as f:
                            f.write(row_code)


                    except requests.exceptions.ConnectionError as connection_error:
                        print(connection_error)
                        row_code = """<tr class="fail" bgcolor="#FF0000"><td>""" + """<a href=\"""" + link + """\">""" + link + """</a>""" + """</td><td>""" + str(
                            connection_error) + """</td><td>""" + """<a href=\"""" + link_dict[key] + """\">""" + \
                                   link_dict[key] + """</a>""" + """</td></tr>"""
                        with open(report_name, "a", encoding="utf-8") as f:
                            f.write(row_code)

                    except requests.exceptions.HTTPError as http_error:
                        print(http_error)
                        row_code = """<tr class="fail" bgcolor="#FF0000"><td>""" + """<a href=\"""" + link + """\">""" + link + """</a>""" + """</td><td>""" + str(
                           http_error) + """</td><td>""" + """<a href=\"""" + link_dict[key] + """\">""" + \
                                   link_dict[key] + """</a>""" + """</td></tr>"""
                        with open(report_name, "a", encoding="utf-8") as f:
                            f.write(row_code)

                with open(report_name, "a", encoding="utf-8") as f:
                    f.write("</table>")

            else:
                head_code = """<p class="fail">""" + """<a href=\"""" + link_dict[key] + """\">""" + link_dict[
                    key] + """</a>""" + """ is broken</p>"""
                with open(report_name, "a", encoding="utf-8") as f:
                    f.write(head_code)
                    # print(head_code)

        with open(report_name, "a", encoding="utf-8") as f:
            f.write("""</body></html>""")

class GenerateReportSummary(object):

    def __init__(self, report_name):
        self.report_name = report_name

    def generate_report_summary(self, report_name):

        summary_name = "link_validation_summary.html"

        # Use BeautifulSoup to read this report and return statistics
        with open(report_name, "r", encoding="utf-8") as f:
            html_code = f.read()
            soup = BeautifulSoup(html_code, "lxml")
            failed_links_rows = soup.find_all("tr", {"class": "fail"})
            for failed_links_row in failed_links_rows:
                del failed_links_row.attrs["bgcolor"]
            print(type(failed_links_rows))


        # Write report summary to another HTML file
        with open(summary_name, "w+", encoding="utf-8") as f:
            f.write(
                """<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Link Validation Report Summary</title></head><body><h1>Link Validation Report Summary</h1>""")
            f.write("""<p>Click the button to sort the table by link:</p>
<p><button onclick="sortTable()">Sort</button></p>""")
            f.write("""<script>
function sortTable() {
  var table, rows, switching, i, x, y, shouldSwitch;
  table = document.getElementById("myTable");
  switching = true;
  /*Make a loop that will continue until
  no switching has been done:*/
  while (switching) {
    //start by saying: no switching is done:
    switching = false;
    rows = table.rows;
    /*Loop through all table rows (except the
    first, which contains table headers):*/
    for (i = 1; i < (rows.length - 1); i++) {
      //start by saying there should be no switching:
      shouldSwitch = false;
      /*Get the two elements you want to compare,
      one from current row and one from the next:*/
      x = rows[i].getElementsByTagName("TD")[0];
      y = rows[i + 1].getElementsByTagName("TD")[0];
      //check if the two rows should switch place:
      if (x.innerHTML.toLowerCase() > y.innerHTML.toLowerCase()) {
        //if so, mark as a switch and break the loop:
        shouldSwitch = true;
        break;
      }
    }
    if (shouldSwitch) {
      /*If a switch has been marked, make the switch
      and mark that a switch has been done:*/
      rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
      switching = true;
    }
  }
}
</script>""")
            f.write("""<table id="myTable" border="1"><tr><th>Failed Links</th><th>Status Code</th><th>Parent Page</th></tr>""")



            for failed_link in set(failed_links_rows):
                f.write(str(failed_link))
            f.write(
                """</table><p>""" + """Refer to <a href=\"""" + report_name + """\">this link</a> for detailed report.""" + """</p></body></html>""")


# Get sitemap
SitemapURLMilvus = GetURLsFromSitemap("https://milvus.io/sitemap.xml")
SitemapURLMilvus.get_url_list("https://milvus.io/sitemap.xml")

# Extract URLs from pages in the sitemap and generate a JSON file to store link info
GetURLFromEachPageMilvus = GetURLFromEachPage("outputlinks.txt")
GetURLFromEachPageMilvus.extract_url_from_html("outputlinks.txt")

# Validate all links
CheckLinkStatusMilvus = CheckLinkStatus("full_link_report.json")
CheckLinkStatusMilvus.check_link_status("full_link_report.json")

# Generate Report Summary
GenerateReportSummaryMilvus = GenerateReportSummary("link_validation_report.html")
GenerateReportSummaryMilvus.generate_report_summary("link_validation_report.html")
