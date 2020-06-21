import os
import urllib
import socket
import time
import re
import requests
from tqdm import tqdm
from bs4 import BeautifulSoup
from difflib import SequenceMatcher


def download_asset(url_to_download, file_name_to_save):

    try:
        http_status_code = urllib.request.urlopen(url_to_download).getcode()
    except:
        print('Error: ', url_to_download)
        return False

    if http_status_code is 200: # if remote url exists

        try:
            urllib.request.urlretrieve(url_to_download, file_name_to_save)
        except:
            print('Timeout')
            return False

    else: # url not found
        print('URL not found')
        return False

    return True

def download_asset_with_retries(url_to_download, file_name_to_save, max_retries=3):

    retries = 0

    while True:
        if retries >= max_retries:
            return False

        success_download = download_asset(url_to_download, file_name_to_save)

        if not success_download:
            time.sleep(0.1)
            retries += 1
        else:
            break

    return True

def parse_cvpr_main_conf():

    main_conf_url = 'http://cvpr2020.thecvf.com/program/main-conference'

    request = urllib.request.Request(main_conf_url)
    response = urllib.request.urlopen(request)
    htmlBytes = response.read()
    htmlStr = htmlBytes.decode("utf8")
    htmlSplit = htmlStr.split('\n')

    session_replacements =\
        {'&nbsp;': '_',
         ' ': '_',
         '&amp': '_',
         ';': '',
         '/': '_',
         ',': '',
         '(1)': '',
         '(2)': '',
         '(3)': '',
        }

    rep = dict((re.escape(k), v) for k, v in session_replacements.items())
    pattern = re.compile("|".join(rep.keys()))

    curr_line = 0
    data_struct = {}

    while curr_line < len(htmlSplit):
        text_line = htmlSplit[curr_line]

        if 'Session:' in text_line:
            session_name = text_line[29:].split('<')[0]
            session_name = pattern.sub(lambda m: rep[re.escape(m.group(0))], session_name)
            data_struct[session_name] = []

            curr_line+=24  # Jump to first paper

            while True:
                paper_title = htmlSplit[curr_line].split('>')[1].split('<')[-2].replace(':', '').lower()
                data_struct[session_name].append(paper_title)

                if 'tbody' in htmlSplit[curr_line+4]:
                    curr_line += 4
                    break
                else:
                    curr_line += 8
        else:
            curr_line += 1

    return data_struct

def compare_titles(str1, str2):
    a = set(str1.split())
    b = set(str2.split())
    c = a.intersection(b)
    score = float(len(c)) / (len(a) + len(b) - len(c))
    return score

if __name__ == "__main__":

    base_url = 'http://openaccess.thecvf.com'
    failed_papers = []

    download_papers_conference = True
    download_paper_workshops = False

    # Download papers

    if download_papers_conference:

        data_cvpr = parse_cvpr_main_conf()

        pdf_local_folder_name = 'cvpr2020/'

        if not os.path.exists(pdf_local_folder_name):
            os.makedirs(pdf_local_folder_name)

        req = urllib.request.Request(base_url + '/CVPR2020.py')
        html = urllib.request.urlopen(req)
        soup = BeautifulSoup(html, 'html.parser')
        paper_infos = soup.find('dl')
        paper_titles = paper_infos.find_all('a')

        urls_to_download = []
        for curr_title in paper_titles:
            str_to_check = str(curr_title.get('href'))
            if 'supplemental.pdf' not in str_to_check and 'pdf' in str_to_check:

                bag_words = ' '.join(str_to_check.split('/')[2].lower().split('_')[1:-3])
                urls_to_download.append((bag_words, base_url + '/' + str_to_check))

        for curr_session, curr_list in data_cvpr.items():
            print(curr_session)
            curr_session_dir = pdf_local_folder_name + '/' + curr_session

            if not os.path.exists(curr_session_dir):
                os.makedirs(curr_session_dir)

            for curr_paper in curr_list:
                max_words = -1.
                max_url = None
                max_bag_words = None

                for bag_words, curr_url in urls_to_download:
                    curr_i = compare_titles(bag_words, curr_paper)

                    if curr_i > max_words:
                        max_words = curr_i
                        max_url = curr_url
                        max_bag_words = bag_words

                if max_url == None:
                    print('ERROR downloading ', curr_paper)
                    continue

                filename = max_url.split('/')[-1]
                save_name = os.path.join(curr_session_dir, filename)

                # print('Downloading ', curr_paper, max_words, max_url, max_bag_words)

                urls_to_download.remove((max_bag_words, max_url))

                if os.path.exists(save_name):
                    continue

                if not download_asset_with_retries(max_url, save_name):
                    failed_papers.append(filename)


            print('------------------------------------------')

    # Download workshop papers

    if download_paper_workshops:

        pdf_workshops_local_folder_name = 'cvpr2020_workshops'

        if not os.path.exists(pdf_workshops_local_folder_name):
            os.makedirs(pdf_workshops_local_folder_name)

        req = urllib.request.Request(base_url + '/CVPR2020_workshops/menu.py')
        html = urllib.request.urlopen(req)
        soup = BeautifulSoup(html, 'html.parser')
        workshop_infos = soup.find('dl')
        workshop_titles = workshop_infos.find_all('a')

        workshops_to_download = []

        for curr_title in workshop_titles[:-1]:
            str_to_check = str(curr_title.get('href'))

            if '.py' in str_to_check:
                curr_title = str(curr_title).split('>')[1].split('<')[0].replace(' ','_').replace(',','').replace(':','').replace('.','_').replace('-','_').replace('?','').replace('/','_')
                workshops_to_download.append((curr_title, base_url + '/CVPR2020_workshops/' + str_to_check))

        print("Downloading {} workshops...".format(len(workshops_to_download)))

        for curr_workshop in tqdm(workshops_to_download):
            workshop_name = curr_workshop[0] #.split('/')[-1][9:-3]
            curr_dir = pdf_workshops_local_folder_name + '/' + workshop_name

            if not os.path.exists(curr_dir):
                os.makedirs(curr_dir)

            req = urllib.request.Request(curr_workshop[1])
            html = urllib.request.urlopen(req)
            soup = BeautifulSoup(html, 'html.parser')
            paper_infos = soup.find('dl')
            paper_titles = paper_infos.find_all('a')

            workshop_urls_to_download = []

            for curr_title in paper_titles:
                str_to_check = str(curr_title.get('href'))
                if 'pdf' in str_to_check:
                    workshop_urls_to_download += [base_url + '/' + urllib.parse.quote(str_to_check[3:])]

            for curr_url in workshop_urls_to_download:

                filename = curr_url.split('/')[-1]
                save_name = os.path.join(curr_dir, filename)

                if os.path.exists(save_name):
                    continue

                if not download_asset_with_retries(curr_url, save_name):
                    failed_papers.append(filename)

    if failed_papers:
        print('Failed to download {} papers'.format(len(failed_papers)))
        print('Re-run script to retry download of missing papers')
