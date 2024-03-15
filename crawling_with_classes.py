import os.path
import requests
from bs4 import BeautifulSoup
import re
import time
import queue
import urllib.request
import random
from base_url_class import BaseUrl
from threading import Thread
from cryptography.hazmat.primitives import serialization
from urllib.parse import urljoin
from urllib.parse import urlparse, urlunparse


# Sucht das HTML-Dokument nach weiteren Links
# neue Links der selben Domain werden hinzugefügt
# externe base-urls, die noch nicht bekannt sind, werden auch gespeichert
def crawl_page(soup, current_url, base_url_object):
    new_extern_urls = []
    # Fuegt alle gefundenen Links der zu bearbeitenden Queue zu
    for link in soup.find_all("a"):
        url = link.get("href")

        # Check dass url tatsächlich url und nicht tel oder mailto ist
        # und dass url noch nicht besucht wurde
        # print(url)
        if url:
            if re.match("/", url):
                url = urljoin(current_url, url)

            # Entfernen von Queries in der Url
            parsed_url = urlparse(url)
            filtered_query = ''
            modified_url = urlunparse((parsed_url.scheme, parsed_url.netloc, parsed_url.path, parsed_url.params,
                                       filtered_query, parsed_url.fragment))
            url = modified_url

            if re.match(base_url_object.base, url):
                if not base_url_object.is_url_known(url):
                    base_url_object.insert_url(url)
            else:  # url ist extern und muss ggf anderem Objekt hinzugefügt werden
                if re.match("^https?://", url):
                    if url not in new_extern_urls:
                        new_extern_urls.append(url)
            print(url)

        # neue externe Urls werden hinzugefügt
        for url in new_extern_urls:
            new_base_url = re.split("://", url)
            new_base_url = new_base_url[0] + "://" + re.split("/", new_base_url[1])[0]
            hashed_value = hash(new_base_url)
            base_url_object_new = [base_urls for base_urls in known_base_urls[hashed_value % line_count] if
                                    base_urls.get_base_url() == new_base_url]
            if base_url_object_new:
                base_url_object_new = base_url_object_new[0]
                if not base_url_object_new.is_url_known(url):
                    base_url_object_new.insert_url(url)
            else:
                new_object = BaseUrl(new_base_url)
                known_base_urls[hashed_value % line_count].append(new_object)
                threat_urls[hashed_value % num_worker].append(new_object)


# convert key, extrahiert aus einem gefundenen privaten schlüssel den öffentlichen Schlüssel
# dieser wird anschließend in keys_found gespeichert
def convert_key():
    with open("private_key.pem", "rb") as private_key_file: # "rb" öffnet die Datei in Binary
        try:
            private_key = serialization.load_pem_private_key(private_key_file.read(), password=None)
            public_key = private_key.public_key()
            pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
        except ValueError:  # ValueError tritt auf, wenn der gefundene Schlüssel nicht den Vorgaben entspricht
            return 0
        except TypeError:  # TypeError tritt auf, wenn der Schlüssel ein Passwort benötigt, welches nicht vorhanden ist
            return 0
    pem.splitlines()
    with open(f"keys_found/{hash(pem)}pub.pem", "wb") as file:
        file.write(pem)
        file.close()
    return 1


# Suche nach Private Keys,
# gesamtes html Dokument wird in String umgeformt
# und anschließend analysiert
# wurde Schlüssel gefunden, wird dieser konvertiert
def scrape_page(html_in_text):
    results = re.findall(r"-----BEGIN RSA PRIVATE KEY-----([^*]*?)-----END RSA PRIVATE KEY-----", html_in_text)
    count = 0
    if results:
        for result in results:
            # Es werden überflüssige HTML Zeichen entfernt
            result = "-----BEGIN RSA PRIVATE KEY-----" + result + "-----END RSA PRIVATE KEY-----"
            result = result.replace("\",\"", "\n")
            result = re.sub("<.*?>", "", result)
            with open("private_key.pem", "w") as private_key_file:
                private_key_file.write(result)
                private_key_file.close()
            # Umwandlung eines gefundenen privaten Schlüssels zum zugehörigen öffentlichen Schlüssel
            count += convert_key()
    else:
        results = re.search(r"-----BEGIN PRIVATE KEY-----(.*?)-----END PRIVATE KEY-----", html_in_text)
        if results:
            for result in results:
                # Es werden überflüssige HTML Zeichen entfernt
                result = result.replace("\",\"", "\n")
                result = re.sub("<.*?>", "", result)
                with open("private_key.pem", "w") as private_key_file:
                    private_key_file.write(result)
                    private_key_file.close()
                # Umwandlung eines gefundenen privaten Schlüssels zum zugehörigen öffentlichen Schlüssel
                count += convert_key()
    return count


def crawling(base_url_object):
    base_url = base_url_object.get_base_url()
    print(base_url)
    if not base_url_object.robotTxT:
        # Robot.txt file wird abgerufen für base_url
        base_url_object.robot_txt_initialise()
    i = 0
    while not base_url_object.is_completed() and i < 50:
        i += 1
        current_url = base_url_object.get_url()

        try:
            response = requests.get(current_url)
        except Exception:
            continue
        if response.status_code != 200:
            print(f"Error getting the Request in Url: {current_url}")
        else:
            soup = BeautifulSoup(response.content, "html.parser")

            keys_found = scrape_page(soup.getText())
            base_url_object.update_key_count(keys_found)

            crawl_page(soup, current_url, base_url_object)

        # time.sleep(random.uniform(0.25, 0.5))
    print(f"Count of Websites visited {i} in this url: {base_url_object.get_base_url()}")


def threat_task(threat_num, threat_urls):
    for base_domain_object in threat_urls[threat_num]:
        crawling(base_domain_object)


def main_method():
    for line in known_base_urls:
        for base_object in line:
            threat_urls[hash(base_object.base) % num_worker].append(base_object)
    for i in range(num_worker):
        Thread(target=threat_task, args=(i, threat_urls)).start()


if __name__ == '__main__':
    dir_for_keys = "keys_found"
    if not os.path.exists(dir_for_keys):
        os.makedirs(dir_for_keys)

    line_count = 12
    known_base_urls = [[] for _ in range(line_count)]
    num_worker = 4
    threat_urls = [[] for _ in range(num_worker)]

    file = open("starting_urls.txt", "r")
    lines = file.readlines()
    for url in lines:
        url = re.sub("\n", "", url)
        base = BaseUrl(url)
        known_base_urls[hash(url) % line_count].append(base)
    file.close()
    main_method()
    for part in known_base_urls:
        print(part)
