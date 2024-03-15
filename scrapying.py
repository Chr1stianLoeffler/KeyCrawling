import requests
from bs4 import BeautifulSoup
import re
import os.path
from cryptography.hazmat.primitives import serialization


# convert key, extrahiert aus einem gefundenen privaten schlüssel den öffentlichen Schlüssel
# dieser wird anschließend in keys_found gespeichert
def convert_key():
    with open("private_key.pem", "rb") as private_key_file:
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
        results = re.search(r"-----BEGIN PRIVATE KEY-----(.*)-----END PRIVATE KEY-----", html_in_text)
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


if __name__ == '__main__':
    dir_for_keys = "keys_found"
    if not os.path.exists(dir_for_keys):
        os.makedirs(dir_for_keys)
    if 1:
        list = ["https://github.com/cbsd/reggae/blob/master/id_rsa",
                "https://github.com/stefanprodan/AndroidDevLab/blob/master/ssh/id_rsa",
                "https://github.com/stefanprodan/AndroidDevLab/blob/master/ssh/id_rsa",
                "https://dbgroup.cdm.depaul.edu/SysGen/HostFiles/id_rsa",
                "https://hxp.io/assets/data/posts/really_slow_arithmetic/id_rsa.good",
                "https://github.com/cbsd/reggae/blob/master/id_rsa",
                "https://apps.cpanel.net/threads/error-convert-the-id_rsa-key-to-ppk-format.686929/",
                "https://repos.sakhaglobal.com/root/infowork/-/blob/c70afa09893523cede1bd87eb0512a503069afd1/aws/id_rsa"]
        for element in list:
            try:
                response = requests.get(element)
                soup = BeautifulSoup(response.content, "html.parser")
                #print(soup.getText())
                print(scrape_page(soup.getText()))
            except Exception:
                pass
    else:
        with open("test_html.txt", "r") as text:
            soup = text.read()
            text.close()
        scrape_page(soup)