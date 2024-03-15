from urllib.robotparser import RobotFileParser
from urllib.parse import urljoin


class BaseUrl:
    def __init__(self, base):
        self.base = base
        self.url_queue = [base]
        self.visited_urls = []
        self.robotTxT = None
        self.completed = False
        self.keys_found = 0

    # überprüft, ob die übergebene Url bekannt ist
    def is_url_known(self, url):
        if url in self.url_queue or url in self.visited_urls:
            return True
        return False

    def robot_txt_initialise(self):
        self.robotTxT = RobotFileParser()
        self.robotTxT.set_url(urljoin(self.base, '/robots.txt'))
        self.robotTxT.read()

    # Fügt eine Url der queue hinzu, nachdem überprüft wurde, ob die Url verwendet werden darf
    def insert_url(self, url):
        # Check if url is allowed to crawl
        # if not the url won't be crawled
        if self.robotTxT:
            if not self.robotTxT.can_fetch("*", url):
                self.visited_urls.append(url)
                return

        self.url_queue.append(url)
        # boolean completed zeigt, dass es noch Webseiten zu besuchen gibt.
        self.set_completed(False)

    def is_completed(self):
        return self.completed

    def get_url(self):
        if self.url_queue:
            url = self.url_queue.pop()
            self.visited_urls.append(url)
            if not self.url_queue:
                self.set_completed(True)
            return url

    def get_base_url(self):
        return self.base

    def set_completed(self, value):
        self.completed = value

    def get_count_visited_urls(self):
        return len(self.visited_urls)

    def update_key_count(self, found_keys):
        self.keys_found += found_keys
