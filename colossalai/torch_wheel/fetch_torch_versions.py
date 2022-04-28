import re
import requests
import os.path as osp
from bs4 import BeautifulSoup
from typing import List, Dict
from packaging import version



TORCH_DIST_URL = 'https://download.pytorch.org/whl/torch_stable.html'
DOWNLOAD_PREFIX = 'https://download.pytorch.org/whl'
MIN_TORCH_VERSION = '1.8.0'
MIN_CUDA_VERSION = '10.2'

def fetch_all_wheel_urls() -> Dict:
    page_text = requests.get(TORCH_DIST_URL).text
    soup = BeautifulSoup(page_text)
    a_tag_elements = soup.find_all('a')
    results = dict()

    for ele in a_tag_elements:
        name = ele.text
        href = ele['href']
        download_url = f'{DOWNLOAD_PREFIX}/{href}'
        results[name] = download_url
    return results

def find_all_cuda_versions_available(wheel_url: Dict):
    cuda_versions = []

    for name in wheel_url.keys():
        if name.startswith('cu'):
            cuda_version = name.split('/')[0]

            if cuda_version not in cuda_versions:
                cuda_versions.append(cuda_version)
    return cuda_versions

def find_all_torch_versions_available(wheel_url: Dict):
    pattern = r'^cu\d+\/torch-1\.(\d+)\.(\d).*$'
    torch_versions = []

    for name in wheel_url.keys():
        if re.search(pattern, name):
            torch_version = name.split('/')[1].split('%')[0].split('-')[1]
            
            if torch_version not in torch_versions:
                torch_versions.append(torch_version)
            
    return torch_versions


def filter_by_keywords(wheel_url: Dict, include: List, exclude: List):
    results = dict()

    for name, url in wheel_url.items():
        all_included = True
        all_excluded = True

        for keyword in include:
            if keyword not in name:
                all_included = False
        
        for keyword in exclude:
            if keyword in name:
                all_excluded = False

        if not (all_included and all_excluded):
            continue
        else:
            results[name] = url
    return results

def main():
    all_wheel_urls = fetch_all_wheel_urls()
    all_cuda_versions = find_all_cuda_versions_available(all_wheel_urls)
    all_torch_versions = find_all_torch_versions_available(all_wheel_urls)

    # this data structure will index by torch_version -> cuda_version -> list of python-versioned wheel urls
    collated_urls = dict()

    # iterate and check all files
    for torch_version in all_torch_versions:
        collated_urls[torch_version] = dict()

        for cuda_version in all_cuda_versions:
            # fetch all wheel download urls
            include_keywords = [torch_version, cuda_version, 'linux', 'x86']
            exclude_keywords = ['cpu']
            filtered_wheel_urls = filter_by_keywords(all_wheel_urls, include_keywords, exclude_keywords)

            if len(filtered_wheel_urls) > 0:
                collated_urls[torch_version][cuda_version] = list(filtered_wheel_urls.values())

    for torch_version in collated_urls.keys():
        if version.parse(torch_version) < version.parse(MIN_TORCH_VERSION):
            continue

        wheels_dict = collated_urls[torch_version]

        for cuda_version, wheel_list in wheels_dict.items():
            if int(cuda_version.lstrip('cu')) < int(MIN_CUDA_VERSION.replace('.', '')):
                continue

            filename = f'./wheel_urls/{torch_version}-{cuda_version}.txt'

            def _sort_by_python_version(url):
                parts = url.split('-')
                for part in parts:
                    if re.search(pattern=r'cp\d+', string=part):
                        return int(part.lstrip('cp'))
                return None
            wheel_list = sorted(wheel_list, key=_sort_by_python_version)

            write_flag = False

            if osp.exists(filename):
                # check if the file content is the same
                with open(filename, 'r') as f:
                    lines = f.readlines()
                    for idx, url in enumerate(wheel_list):
                        if url.strip() != wheel_list[idx].strip():
                            write_flag = True
            else:
                write_flag = True

            if write_flag:
                with open(filename, 'w') as f:
                    for url in wheel_list:
                        f.write(f'{url}\n')

if __name__ == '__main__':
    main()