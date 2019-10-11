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
import re


class LinksFromMarkdown(object):

    def __init__(self, repository):
        self.dictionary = repository

    def extract_links_from_markdown(self, repository):

        repository = "D:\\GithubRepo\\docs-master\\docs-master"
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
                    if file.endswith(".md") or file.endswith(".MD") or file.endswith(".mD") or file.endswith(".Md"):
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

        # Iterate over all MD files
        # key ---> MD file location
        # value ---> An array of links in the MD file, including internet links and file links
        for key in link_dict.keys():
            head_code = ""
            table_code = ""

            if link_dict.get(key) == []:

                with open(report_name, "a", encoding="utf-8") as f:
                    f.write("""<h2>Checking links in """ + key)
                    f.write("""<p style="color:green">This markdown file does not contain any links.</p>""")
            else:

                head_code = """<table border="1"><tr><th>Link</th><th>Status</th><th>Markdown File</th></tr>"""

                with open(report_name, "a", encoding="utf-8") as f:
                    f.write("""<h2>Checking links in """ + key)
                    f.write(head_code)

                # Iterate over all links in each MD file
                for link in link_dict.get(key):
                    # Check internet links: http,https
                    if link.startswith("http://") or link.startswith("https://"):
                        try:
                            link_response = requests.get(link, timeout=60)
                            status_code = link_response.status_code

                                # Informational responses (100–199),
                                # Successful responses (200–299),
                                # Redirects (300–399),
                                # Client errors (400–499),
                                # and Server errors (500–599).

                            if status_code in range(200,299):
                                # For links that do not contain hashes
                                if "#" not in link:
                                    row_code = """<tr class="success" bgcolor="#32CD32"><td>""" + """<a href=\"""" + link + """\">""" + link + """</a>""" + """</td><td>""" + str(status_code) + """</td><td>"""  + key + """</td></tr>"""
                                # For links that contain hashes
                                else:

                                    try:
                                        # Acquire the url after "#"
                                        response = urllib.request.urlopen(str(
                                            urlparse(link).scheme + "://" + urlparse(link).netloc + urlparse(link).path),data=None)
                                        html_code = response.read()
                                        soup = BeautifulSoup(html_code.decode("utf-8"), "lxml")
                                        a_hash = soup.find("a", {"id": str(urlparse(link).fragment)})
                                        h1_hash = soup.find("h1", {"id": str(urlparse(link).fragment)})
                                        h2_hash = soup.find("h2", {"id": str(urlparse(link).fragment)})
                                        h3_hash = soup.find("h3", {"id": str(urlparse(link).fragment)})
                                        h4_hash = soup.find("h4", {"id": str(urlparse(link).fragment)})
                                        h5_hash = soup.find("h5", {"id": str(urlparse(link).fragment)})
                                        h6_hash = soup.find("h6", {"id": str(urlparse(link).fragment)})

                                        if (None, None, None, None, None, None, None) != (
                                        a_hash, h1_hash, h2_hash, h3_hash, h4_hash, h5_hash, h6_hash):
                                            row_code = """<tr class="success" bgcolor="#32CD32"><td>""" + """<a href=\"""" + link + """\">""" + link + """</a>""" + """</td><td>""" + str(
                                                status_code) + """</td><td>""" +  key + """</td></tr>"""

                                        else:
                                            row_code = """<tr class="fail" bgcolor="#FF0000"><td>""" + """<a href=\"""" + link + """\">""" + link + """</a>""" + """</td><td>""" + str(
                                                status_code) + """ The URL looks good but the anchor link does not work or is not using an anchor tag.""" + """</td><td>""" +  key + """</td></tr>""" """</td></tr>"""


                                    except urllib.error.HTTPError as http_error:
                                            row_code = """<tr class="fail" bgcolor="#FF0000"><td>""" + """<a href=\"""" + link + """\">""" + link + """</a>""" + """</td><td>""" + str(
                                                status_code) + """ """ + str(http_error) + """ The URL looks good but the page then returns an HTTP error.</td><td>"""  + key + """</td></tr>"""
                                    except urllib.error.URLError as url_error:
                                            row_code = """<tr class="fail" bgcolor="#FF0000"><td>""" + """<a href=\"""" + link + """\">""" + link + """</a>""" + """</td><td>""" + str(
                                                status_code) + """ """ + str(url_error) + """ The URL looks good but the page then returns a URL error.</td><td>""" +  key + """</td></tr>"""

                            elif status_code in range(400,599):
                                row_code = """<tr class="fail" bgcolor="#FF0000"><td>""" + """<a href=\"""" + link + """\">""" + link + """</a>""" + """</td><td>""" + str(
                                    status_code) + """</td><td>""" + key + """</td></tr>"""


                        except requests.exceptions.Timeout as timeout_error:
                            print(timeout_error)
                            row_code = """<tr class="fail" bgcolor="#FF0000"><td>""" + """<a href=\"""" + link + """\">""" + link + """</a>""" + """</td><td>""" + str(
                                timeout_error) + """</td><td>""" + key + """</td></tr>"""
                            with open(report_name, "a", encoding="utf-8") as f:
                                f.write(row_code)


                        except requests.exceptions.ConnectionError as connection_error:
                            print(connection_error)
                            row_code = """<tr class="fail" bgcolor="#FF0000"><td>""" + """<a href=\"""" + link + """\">""" + link + """</a>""" + """</td><td>""" + str(
                                connection_error) + """</td><td>""" + key + """</td></tr>"""
                            with open(report_name, "a", encoding="utf-8") as f:
                                f.write(row_code)


                        except requests.exceptions.HTTPError as http_error:
                            print(http_error)
                            row_code = """<tr class="fail" bgcolor="#FF0000"><td>""" + """<a href=\"""" + link + """\">""" + link + """</a>""" + """</td><td>""" + str(
                                http_error) + """</td><td>""" + key + """</td></tr>"""
                            with open(report_name, "a", encoding="utf-8") as f:
                                f.write(row_code)

                    # elif link.startswith("mailto:"):

                    # Check MD file links

                    # File path formats on Windows systems from https://docs.microsoft.com/en-us/dotnet/standard/io/file-path-formats
                    # C:\Documents\Newsletters\Summer2018.pdf                An absolute file path from the root of drive C:
                    # \Program Files\Custom Utilities\StringFinder.exe       An absolute path from the root of the current drive.
                    # 2018\January.xlsx                                      A relative path to a file in a subdirectory of the current directory.
                    # ..\Publications\TravelBrochure.pdf                     A relative path to file in a directory that is a peer of the current directory.
                    # C:\Projects\apilibrary\apilibrary.sln                  An absolute path to a file from the root of drive C:
                    # C:Projects\apilibrary\apilibrary.sln                   A relative path from the current directory of the C: drive.

                    # We do not use absolute path formats in MD files and path formats are not likely to be from the root of the current drive. So here are possible formats:
                    # 2018\January.md
                    # ..\Publications\TravelBrochure.md

                    # Check if file exists

                    elif link.endswith(".md") or link.endswith(".MD") or link.endswith(".mD") or link.endswith(".Md"):
                        # A relative path to file in a directory that is a peer of the current directory.
                        if link.startswith("..\\"):
                            # Get the absolute location of the linked md
                            cur_direct = os.path.dirname(key)
                            final_direct = os.path.dirname(cur_direct)
                            linked_md = os.path.join(final_direct,link)
                            # Check if the linked md exists
                            if Path(linked_md).is_file():
                                row_code = """<tr class="success" bgcolor="#32CD32"><td>""" + link  + """</td><td>The file link looks good.</td><td>""" + key + """</td></tr>"""

                            else:
                                row_code = """<tr class="fail" bgcolor="#FF0000"><td>""" + link +  """</td><td>The file link is broken.</td><td>""" + key + """</td></tr>"""

                        # A relative path to a file in a subdirectory of the current directory.
                        else:
                            # Get the absolute location of the linked md
                            cur_direct = os.path.dirname(key)
                            linked_md = os.path.join(cur_direct, link)
                            # Check if the linked md exists
                            if Path(linked_md).is_file():
                                row_code = """<tr class="success" bgcolor="#32CD32"><td>""" + link + """</td><td>The file link looks good.</td><td>""" + key + """</td></tr>"""

                            else:
                                row_code = """<tr class="fail" bgcolor="#FF0000"><td>""" + link  + """</td><td>The file link is broken.</td><td>""" + key + """</td></tr>"""


                    with open(report_name, "a", encoding="utf-8") as f:
                        f.write(row_code)
                        # print(row_code)


                with open(report_name, "a", encoding="utf-8") as f:
                    f.write("</table>")     
                    print("Complete link checking for " + key)

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
            f.write("""<p>Click the button to sort the table by parent page:</p>
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
            f.write(
                """<table id="myTable" border="1"><tr><th>Failed Links</th><th>Status Code</th><th>Parent Page</th></tr>""")

            for failed_link in set(failed_links_rows):
                f.write(str(failed_link))
            f.write(
                """</table><p>""" + """Refer to <a href=\"""" + report_name + """\">this link</a> for detailed report.""" + """</p></body></html>""")

            
# Get link JSON file
LinksFromMarkdown_Milvus = LinksFromMarkdown("D:\GithubRepo\docs-master")
LinksFromMarkdown_Milvus.extract_links_from_markdown("D:\GithubRepo\docs-master")

# Generate link validation report
CheckExtractedLinksFromMarkdown_Milvus = CheckExtractedLinksFromMarkdown("extracted_links.json")
CheckExtractedLinksFromMarkdown_Milvus.check_extracted_links("extracted_links.json")

# Generate report summary
GenerateReportSummary_Milvus = GenerateReportSummary("link_validation_report.html")
GenerateReportSummary_Milvus.generate_report_summary("link_validation_report.html")