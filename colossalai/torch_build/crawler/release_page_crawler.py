from .base_crawler import BaseCrawler
import requests
from bs4 import BeautifulSoup
from .wheel_record import WheelRecord, WheelRecordCollection, Method
from typing import List, Tuple
from packaging import version

PYTYHON_VERSIONS = ['3.6', '3.7', '3.8', '3.9']

class ReleasePageCrawler(BaseCrawler):

    def __init__(self, min_torch_version, min_cuda_version, exclude_torch_version) -> None:
        name = 'release_page'
        crawl_src = 'https://pytorch.org/get-started/previous-versions/'
        download_prefix = 'nil'
        super().__init__(name, crawl_src, download_prefix, min_torch_version, min_cuda_version, exclude_torch_version)

    def crawl(self) -> List[WheelRecordCollection]:
        page_text = requests.get('https://pytorch.org/get-started/previous-versions').text
        soup = BeautifulSoup(page_text)
        all_code_snippets = soup.find_all('code')
        all_code_snippets = [ele.text for ele in all_code_snippets if '# CUDA' in ele.text]
        

        installation_commands = []

        for snippet in all_code_snippets:
            lines = snippet.split('\n')
            for line in lines:
                if 'conda install' in line and 'cudatoolkit' in line:
                    installation_commands.append(line)
            
        installation_info = [self._parse_command(cmd) for cmd in installation_commands]
        filtered_installation_info = list(filter(self._filter_by_version, installation_info))
        filtered_installation_info = self._keep_max_revision_version(filtered_installation_info)

        results = []
        for info in filtered_installation_info:
            torch_version, cuda_version, flags = info

            if torch_version in self.exclude_torch_version:
                continue
                    
            record_list = []
            for py_ver in PYTYHON_VERSIONS:
                record = WheelRecord(method=Method.CONDA, url='nil', py_ver=py_ver, flags=flags)
                record_list.append(record)
            record_collection = WheelRecordCollection(torch_ver=torch_version, cuda_ver=cuda_version, records=record_list)
            results.append(record_collection)
        return results

    def _parse_command(self, cmd):
        parts = cmd.split()
        for part in parts:
            if part.startswith('pytorch'):
                torch_version = part.split('==')[-1]
                break
        
        for part in parts:
            if part.startswith('cudatoolkit'):
                cuda_version = part.split('=')[-1]
                break

        for idx, part in enumerate(parts):
            if part.startswith('-c'):
                channels = parts[idx:]
                break
        return torch_version, cuda_version, channels
    
    def _filter_by_version(self, item):
        torch_version, cuda_version, flags = item

        if version.parse(torch_version) < version.parse(self.min_torch_version):
            return False
        if version.parse(cuda_version) < version.parse(self.min_cuda_version):
            return False
        return True

    def _keep_max_revision_version(self, installation_info: List[Tuple[str]]):
        max_revision_versions = dict()

        for info in installation_info:
            torch_version, cuda_version, flags = info
            key = '.'.join(torch_version.split('.')[:2])

            if key not in max_revision_versions:
                max_revision_versions[key] = torch_version
            elif version.parse(torch_version) > version.parse(max_revision_versions[key]):
                max_revision_versions[key] = torch_version
        
        kept_versions = list(max_revision_versions.values())
        new_installation_info = []

        for info in installation_info:
            torch_version, cuda_version, flags = info
            if torch_version in kept_versions:
                new_installation_info.append(info)
        
        return new_installation_info





        


