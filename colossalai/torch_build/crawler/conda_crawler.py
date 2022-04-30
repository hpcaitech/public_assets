from lib2to3.pytree import Base
from .base_crawler import BaseCrawler
from .wheel_record import WheelRecordCollection
from typing import List

class CondaCrawler(BaseCrawler):

    def __init__(self, min_torch_version, min_cuda_version) -> None:
        name = 'conda'
        crawl_src = 'https://anaconda.org/pytorch/pytorch/files'
        download_prefix = 'https://anaconda.org/pytorch/pytorch/1.11.0/download'
        super().__init__(name, crawl_src, download_prefix, min_torch_version, min_cuda_version)

    def crawl(self) -> List[WheelRecordCollection]:
        return super().crawl()