import os
import urllib.request
import socket
import time
from tqdm import tqdm
from bs4 import BeautifulSoup


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

        success_download = download_asset(curr_url, save_name)

        if not success_download:
            time.sleep(0.1)
            retries += 1
        else:
            break

    return True


if __name__ == "__main__":

    base_url = 'http://openaccess.thecvf.com'
    failed_papers = []

    download_papers_conference = True
    download_paper_workshops = True

    # Download papers

    if download_papers_conference:

        pdf_local_folder_name = 'cvpr2019/'

        if not os.path.exists(pdf_local_folder_name):
            os.makedirs(pdf_local_folder_name)

        req = urllib.request.Request(base_url + '/CVPR2019.py')
        html = urllib.request.urlopen(req)
        soup = BeautifulSoup(html, 'html.parser')
        paper_infos = soup.find('dl')
        paper_titles = paper_infos.find_all('a')

        urls_to_download = []
        for curr_title in paper_titles:
            str_to_check = str(curr_title.get('href'))
            if 'pdf' in str_to_check:
                urls_to_download += [base_url + '/' + str_to_check]

        for curr_url in tqdm(urls_to_download):

            filename = curr_url.split('/')[-1]
            save_name = os.path.join(pdf_local_folder_name, filename)

            if os.path.exists(save_name):
                continue

            if not download_asset_with_retries(curr_url, save_name):
                failed_papers.append(filename)


    # Download workshop papers

    if download_paper_workshops:

        pdf_workshops_local_folder_name = 'cvpr2019_workshops'

        if not os.path.exists(pdf_workshops_local_folder_name):
            os.makedirs(pdf_workshops_local_folder_name)

        req = urllib.request.Request(base_url + '/CVPR2019_workshops/menu.py')
        html = urllib.request.urlopen(req)
        soup = BeautifulSoup(html, 'html.parser')
        workshop_infos = soup.find('dl')
        workshop_titles = workshop_infos.find_all('a')

        workshops_to_download = []

        for curr_title in workshop_titles:
            str_to_check = str(curr_title.get('href'))
            if '.py' in str_to_check:
                workshops_to_download += [base_url + '/CVPR2019_workshops/' + str_to_check]

        workshops_to_download = workshops_to_download[:-1]

        print("Downloading {} workshops...".format(len(workshops_to_download)))

        for curr_workshop in tqdm(workshops_to_download):
            workshop_name = curr_workshop.split('/')[-1][9:-3]

            curr_dir = pdf_workshops_local_folder_name + '/' + workshop_name

            if not os.path.exists(curr_dir):
                os.makedirs(curr_dir)

            req = urllib.request.Request(curr_workshop)
            html = urllib.request.urlopen(req)
            soup = BeautifulSoup(html, 'html.parser')
            paper_infos = soup.find('dl')
            paper_titles = paper_infos.find_all('a')

            workshop_urls_to_download = []

            for curr_title in paper_titles:
                str_to_check = str(curr_title.get('href'))
                if 'pdf' in str_to_check:
                    workshop_urls_to_download += [base_url + '/' + str_to_check[3:]]

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
