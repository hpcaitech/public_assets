from abc import ABC, abstractmethod
from .wheel_record import WheelRecordCollection
from typing import List

class BaseCrawler(ABC):

    def __init__(self, name, crawl_src, download_prefix, min_torch_version, min_cuda_version, exclude_torch_version) -> None:
        self.name = name
        self.crawl_src = crawl_src
        self.download_prefix = download_prefix
        self.min_torch_version = min_torch_version
        self.min_cuda_version = min_cuda_version
        self.exclude_torch_version = exclude_torch_version

    def get_download_url(self, file_name):
        return f'{self.download_prefix}/{file_name}'

    @abstractmethod
    def crawl(self) -> List[WheelRecordCollection]:
        pass
        