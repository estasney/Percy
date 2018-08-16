from bs4 import BeautifulSoup as bs4
import re
import requests
from unicodedata import normalize


class PageFetchException(Exception):
    def __init__(self, message, url, status_code):
        super().__init__(message)
        self.url = url
        self.status_code = status_code


class ElementNotFoundException(Exception):
    def __init__(self, message, element):
        super().__init__(message)
        self.element = element


def get_job_posting(req_id):
    job_fetcher = CiscoJobs()
    try:
        req_text = job_fetcher.fetch_req(req_id)
        return req_text
    except:
        return None


class CiscoJobs(object):

    def __init__(self):
        self.JD_HEADERS = re.compile(r"^(What|Who|Why)")

    def fetch_req(self, req_num):
        url = "https://jobs.cisco.com/jobs/ProjectDetail/{}".format(req_num)
        r = requests.get(url)
        if r.status_code != 200:
            raise PageFetchException(message="Getting page {} returned status code {}".format(url, r.status_code), url=url,
                                     status_code=r.status_code)
        page = bs4(r.content, 'html.parser')
        jd_element = page.find(class_="job_description")
        if not jd_element:
            raise ElementNotFoundException(message="Job Description Element Not Found", element="job_description")

        raw_text = jd_element.get_text("\n")  # Join with newlines
        raw_text = normalize('NFKD', raw_text)
        text_lines = raw_text.splitlines()

        def remove_boilerplate(x):
            if self.JD_HEADERS.findall(x):
                return False
            else:
                return True

        text_lines = list(filter(lambda x: remove_boilerplate(x), text_lines))

        def slice_cisco(lines):
            counter = 0
            while counter < len(lines):
                if "why cisco" in lines[counter].lower() or "we connect" in lines[counter].lower():
                    return counter
                else:
                    counter += 1
            return -1

        sliced_lines_idx = slice_cisco(text_lines)
        if sliced_lines_idx > 0:
            return " ".join(text_lines[:sliced_lines_idx])
        else:
            return " ".join(text_lines)
