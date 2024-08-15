  #! python3

"""
Usage:

    reddit-wiki-downloader.py subreddit1 subreddit2... - Download all wiki pages from a subreddit(s)

    reddit-wiki-downloader.py -p subreddit page1 page2... - download specific page(s)
"""

from pathlib import Path
import os
import re
import sys
import time
import requests
from bs4 import BeautifulSoup


def printhelp():
    print(
        """Usage:

    reddit-wiki-downloader.py subreddit1 subreddit2... - Download all wiki pages from a subreddit(s)

    reddit-wiki-downloader.py -p subreddit page1 page2... - download specific page(s)
"""
    )


def download_wiki(subreddit, page="index", wiki_pages=None):
    if wiki_pages is None:
        wiki_pages = set()
    pages_to_download = set()
    response = 0

    if page in "index":
        cwd = Path.cwd()
    else:
        cwd = Path.cwd().parent

    # Make new directory
    if page == "index":
        try:
            (Path(cwd) / subreddit).mkdir()
        except FileExistsError:
            print(f"Error: Directory {subreddit} already exists")
            sys.exit(1)
        else:
            os.chdir(Path(cwd) / subreddit)  #  Change directory

    for file in os.listdir(Path(cwd) / subreddit):
        wiki_pages.add(file[:-5])
        if file[:-5].lower() == page.lower():
            return None

    print(f"Downloading {subreddit}/wiki/{page} ...")
    try:
        time.sleep(2)
        response = requests.get(
            f"https://old.reddit.com/r/{subreddit}/wiki/{page}",
            headers={"User-agent": "user"},
            timeout=10
        )
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(e)
        print(f"Can't download page: {page}")
    except requests.exceptions.ConnectionError as e:
        print(e)
        print("No internet connection")

    if response:
        soup = BeautifulSoup(response.text, "html.parser")
        wiki_text = str(soup.select("div.md.wiki")[0])

        # Replace reddit.com with old.reddit
        regex = re.compile(r"((https?://(www.)?reddit.com)?/r/\w*/wiki)")
        wiki_text = regex.sub(f"https://old.reddit.com/r/{subreddit}/wiki", wiki_text)

        # Search for other pages to download
        regex2 = re.compile(r"https://old.reddit.com/r/\w*/wiki/([\w,\-,_,%,/]*)")
        pages = regex2.findall(wiki_text)
        for p in pages:
            pages_to_download.add(p)

        pages_to_download = pages_to_download - wiki_pages
        # print(pages_to_download)

        wiki_pages |= pages_to_download

        # Change old.reddit to file://
        for p in wiki_pages:
            if p.isalnum():
                wiki_text = re.sub(
                    r"https://old.reddit.com/r/\w*/wiki/" + p,
                    (cwd.as_uri() + f"/{subreddit}/" + p.lower() + r".html"),
                    wiki_text,
                )
            else:
                q = p.split("/")
                if "" in q:
                    q.remove("")
                wiki_text = re.sub(
                    r"https://old.reddit.com/r/\w*/wiki/" + p,
                    (cwd.as_uri() + f"/{subreddit}/" + q[-1].lower() + r".html"),
                    wiki_text,
                )

        # Create page
        name = soup.select("h1.hover.redditname")
        html_text = f"<html><head><title>{subreddit}/{page}</title></head><body>{str(name[0])}\n{wiki_text}</body></html>"
        soup = BeautifulSoup(html_text, "html.parser")
        html_text = soup.prettify()

        if not page.isalnum():
            page2 = page.split("/")
            if "" in page2:
                page2.remove("")
            with open(f"{page2[-1].lower()}.html", "w", encoding="utf-8") as file:
                file.write(html_text)
        else:
            with open(f"{page.lower()}.html", "w", encoding="utf-8") as file:
                file.write(html_text)

        # Download other pages
        for p in pages_to_download:
            download_wiki(subreddit, p, wiki_pages)

    if page == "index":
        wiki_pages.add("index")
        wiki_pages.add("index/")
        os.chdir(cwd)
        return None

    return pages_to_download


if len(sys.argv) == 1 or sys.argv[1] == "-h":
    printhelp()
    sys.exit(1)
elif sys.argv[1] == "-p":
    if len(sys.argv) < 4:
        printhelp()
        sys.exit(1)
    else:
        if (Path.cwd() / sys.argv[2]).exists():
            os.chdir(Path.cwd() / sys.argv[2])
        else:
            print(f"Directory {sys.argv[2]} doesn't exist")
            sys.exit(1)
        for i in range(3, len(sys.argv)):
            download_wiki(sys.argv[2], sys.argv[i])
else:
    for i in range(1, len(sys.argv)):
        download_wiki(sys.argv[i])
