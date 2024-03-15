KeyCrawling ist ein WebCrawler, welcher private RSA Schlüssel sucht und die dazugehörigen öffentlichen Schlüssel erstellt, um sie als unsicher klassifizieren zu können.
# KeyCrawling

Teil des Web Crawlers:
base_url_class.py
key_crawling.py
starting_urls.txt 

scrapying.py wandelt private keys zu public keys um,
es müssen Webseiten manuel angegeben werden von denen die privaten Schlüssel extrahiert werden sollen.
Google Suchen wie: https://www.google.com/search?q=%22-----BEGIN%20RSA%20PRIVATE%20KEY-----%22%20inurl:id_rsa#ip=1 führen zu unsicheren privaten Schlüsseln. 
Diese kann man mit Hilfe von scrapying.py extrahieren und in public keys umwandeln.
