from bs4 import BeautifulSoup
from importlib_metadata import version
import re
import requests
from .base_crawler import BaseCrawler
from .wheel_record import WheelRecord, WheelRecordCollection, Method
from typing import List
from packaging import version
from abc import ABC, abstractmethod

class CondaCrawler(BaseCrawler, ABC):

    def crawl(self) -> List[WheelRecordCollection]:
        # indexed by coarse_torch_versiopn -> torch_version -> cuda_version -> python_version
        # coarse_torch_version only includes the major and minor version
        wheel_info = dict()

        # crawl by page
        page = 1
        while True:
            found_unneeded_torch_version = False
            filenames = self._fetch_filenames_by_page(page=page)
            filtered_filenames = list(filter(self._filter_by_platform, filenames))
            
            
            for filename in filtered_filenames:
                # check if this is the last page
                found_unneeded_torch_version = self._found_unneeded_torch_version(filename)

                if found_unneeded_torch_version:
                    break
                else:
                    # add wheel info by version
                    cuda_version, torch_version, py_version = self._parse_file_name_for_version(filename)

                    coarse_torch_version = '.'.join(torch_version.split('.')[:2])

                    if coarse_torch_version not in wheel_info:
                        wheel_info[coarse_torch_version] = dict()
                    
                    if torch_version not in wheel_info[coarse_torch_version]:
                        wheel_info[coarse_torch_version][torch_version] = dict()
                    
                    if cuda_version not in wheel_info[coarse_torch_version][torch_version]:
                        wheel_info[coarse_torch_version][torch_version][cuda_version] = dict()

                    wheel_info[coarse_torch_version][torch_version][cuda_version][py_version] = filename

            if found_unneeded_torch_version:
                break

            page += 1

        filtered_wheel_info = dict()
        # only keep the max revision version
        for coarse_torch_version, torch_versioned_wheel_info in wheel_info.items():
            if coarse_torch_version not in filtered_wheel_info:
                    filtered_wheel_info[coarse_torch_version] = dict()

            for torch_version, cuda_versioned_wheel_info in torch_versioned_wheel_info.items():
                if len(filtered_wheel_info[coarse_torch_version]) == 0:
                    filtered_wheel_info[coarse_torch_version][torch_version] = cuda_versioned_wheel_info
                else:
                    previous_version = list(filtered_wheel_info[coarse_torch_version].keys())[0]

                    if version.parse(torch_version) > version.parse(previous_version):
                        filtered_wheel_info[coarse_torch_version].pop(previous_version)
                        filtered_wheel_info[coarse_torch_version][torch_version] = cuda_versioned_wheel_info
        
        # rearrange into records
        rearranged_wheel_info = []
        for coarse_torch_version, torch_versioned_wheel_info in filtered_wheel_info.items():
            for torch_version, cuda_versioned_wheel_info in torch_versioned_wheel_info.items():
                for cuda_version, python_versioned_wheel_info in cuda_versioned_wheel_info.items():
                    wheel_record_list = []
                    for python_version, filename in python_versioned_wheel_info.items():
                        url = self.get_download_url(filename)
                        record = WheelRecord(method=Method.CONDA, url=url, py_ver=python_version)        
                        wheel_record_list.append(record)
                    record_collection = WheelRecordCollection(torch_ver=torch_version, cuda_ver=cuda_version, records=wheel_record_list)
                    rearranged_wheel_info.append(record_collection)
        
        return rearranged_wheel_info
        
    def _fetch_filenames_by_page(self, page: int) -> List[str]:
        paged_url = f'{self.crawl_src}?page={page}'
        page_text = requests.get(paged_url).text
        soup = BeautifulSoup(page_text)
        form = all_a_links = soup.find('form', {'id': 'fileForm'})
        all_table_rows = form.find_all('tr')
        
        # ignore the header row
        all_table_rows = all_table_rows[1:]

        # filter by download 
        # ignore any wheel whose
        def _filter_by_download(tr):
            download = int(tr.find_all('td')[6].find_all('strong')[0].text)
            if download == 0:
                return False
            else:
                return True
            
        all_table_rows = list(filter(_filter_by_download, all_table_rows))

        # get all download filenames
        def _map_to_filename(tr):
            filename = tr.find_all('td')[3].find_all('a')[-1].text
            return filename
        
        all_filenames = list(map(_map_to_filename, all_table_rows))
        return all_filenames

    def _filter_by_platform(self, filename):
        if 'linux' not in filename or 'cuda' not in filename:
            return False
        return True

    def _found_unneeded_torch_version(self, filename):
        cuda_version, torch_version, py_version = self._parse_file_name_for_version(filename)
        return version.parse(torch_version) < version.parse(self.min_torch_version)

    @abstractmethod
    def _parse_file_name_for_version(self, filename):
        pass


class PyTorchCondaChannelCrawler(CondaCrawler):

    def __init__(self, min_torch_version, min_cuda_version) -> None:
        name = 'conda'
        crawl_src = 'https://anaconda.org/pytorch/pytorch/files'
        download_prefix = 'https://anaconda.org/pytorch/pytorch/1.11.0/download'
        super().__init__(name, crawl_src, download_prefix, min_torch_version, min_cuda_version)

    def _parse_file_name_for_version(self, filename):
        version_parts = filename.split('/')[1].split('-')
        torch_version = version_parts[1]
        py_version = version_parts[2].split('_')[0].lstrip('py')
        cuda_version = version_parts[2].split('_')[1].lstrip('cuda')
        return cuda_version, torch_version, py_version

class CondaForgeCrawler(CondaCrawler):
    def __init__(self, min_torch_version, min_cuda_version) -> None:
        name = 'conda'
        crawl_src = 'https://anaconda.org/conda-forge/pytorch/files'
        download_prefix = 'https://anaconda.org/conda-forge/pytorch/1.11.0/download'
        super().__init__(name, crawl_src, download_prefix, min_torch_version, min_cuda_version)

    def _parse_file_name_for_version(self, filename):
        version_parts = filename.split('/')[1].split('-')
        torch_version = version_parts[1]

        py_version = re.findall('py\d+', version_parts[2])[0].lstrip('py')
        py_version = f'3.{py_version[1:]}'

        cuda_version = re.findall('cuda\d+', version_parts[2])[0].lstrip('cuda')

        if cuda_version.startswith('1'):
            cuda_version = f'{cuda_version[:2]}.{cuda_version[2:]}'
        else:
            cuda_version = f'{cuda_version[0]}.{cuda_version[1:]}'
        
        return cuda_version, torch_version, py_version
