import requests
from .base_crawler import BaseCrawler
from .wheel_record import WheelRecord, WheelRecordCollection, Method
from typing import List
from bs4 import BeautifulSoup
import re
from .utils import has_larger_or_equal_cuda_version, has_larger_or_equal_torch_version
from packaging import version


class PipCrawler(BaseCrawler):

    def __init__(self, min_torch_version, min_cuda_version, exclude_torch_version) -> None:
        name = 'conda'
        crawl_src = 'https://download.pytorch.org/whl/torch_stable.html'
        download_prefix = 'https://download.pytorch.org/whl'
        super().__init__(name, crawl_src, download_prefix, min_torch_version, min_cuda_version, exclude_torch_version)

    def crawl(self) -> List[WheelRecordCollection]:
        all_wheel_urls = self._fetch_all_wheel_urls()
        filtered_wheel_urls = list(filter(self._filter_by_platform, all_wheel_urls))
        filtered_wheel_urls = list(filter(self._filter_by_version, filtered_wheel_urls))

        # key is indexed by torch_version -> cuda_version -> python version
        collated_records = dict()

        # order by version
        for filename, href in filtered_wheel_urls:
            cuda_version, torch_version, py_version = self._parse_filename(filename)

            if torch_version in self.exclude_torch_version:
                continue

            if torch_version not in collated_records:
                collated_records[torch_version] = dict()

            if cuda_version not in collated_records[torch_version]:
                collated_records[torch_version][cuda_version] = dict()
            
            url = f'{self.download_prefix}/{href}'
            record = WheelRecord(method=Method.PIP, url=url, py_ver=py_version)
            collated_records[torch_version][cuda_version][py_version] = record

        # only keep the max revision for each torch version
        filtered_collated_records = dict()

        for torch_version, cuda_versioned_info in collated_records.items():
            current_version = version.parse(torch_version)
            key = f'{current_version.major}.{current_version.minor}'

            if key not in filtered_collated_records:
                filtered_collated_records[key] = (torch_version, cuda_versioned_info)
            else:
                previous_torch_version = version.parse(filtered_collated_records[key][0])
                if current_version > previous_torch_version:
                    filtered_collated_records[key] = (torch_version, cuda_versioned_info)
        
        # arrange into a record collection
        record_collection_list = []
        for value in filtered_collated_records.values():
            torch_version = value[0]
            cuda_versioned_info = value[1]
            
            for cuda_version, python_versioned_info in cuda_versioned_info.items():
                record_list = []

                for python_version, wheel_record in python_versioned_info.items():
                    record_list.append(wheel_record)
                
                record_collection = WheelRecordCollection(torch_ver=torch_version, cuda_ver=cuda_version, records=record_list)
                record_collection_list.append(record_collection)
        return record_collection_list

    def _fetch_all_wheel_urls(self) -> List:
        page_text = requests.get(self.crawl_src).text
        soup = BeautifulSoup(page_text)
        a_tag_elements = soup.find_all('a')
        results = []

        for ele in a_tag_elements:
            name = ele.text
            href = ele['href']
            results.append((name, href))
        return results

    def _filter_by_platform(self, url_info: List[str]) -> bool:
        filename = url_info[0]
        if not re.search(r'cu\d+/torch-\d\.\d+\.\d', filename):
            return False
        if 'linux' not in filename:
            return False
        return True

    def _filter_by_version(self, url_info: List[str]) -> bool:
        filename = url_info[0]
        cuda_version, torch_version, py_version = self._parse_filename(filename)

        if not has_larger_or_equal_cuda_version(cuda_version, self.min_cuda_version):
            return False
        if not has_larger_or_equal_torch_version(torch_version, self.min_torch_version):
            return False
        return True
        
    def _parse_filename(self, filename: str) -> List[str]:
        cuda_version, remainder = filename.split('/')
        cuda_version = cuda_version.lstrip('cu')
        if cuda_version.startswith('1'):
            cuda_version = f'{cuda_version[:2]}.{cuda_version[2:]}'
        else:
            cuda_version = f'{cuda_version[0]}.{cuda_version[1:]}'

        torch_version = remainder.split('%')[0].split('-')[1]
        py_version = remainder.split('-')[2].lstrip('cp')
        py_version = f"3.{py_version.lstrip('3')}"

        return cuda_version, torch_version, py_version

