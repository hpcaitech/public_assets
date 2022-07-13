import os
import os.path as osp

from crawler import PipCrawler, WheelRecordCollection, CondaForgeCrawler, PyTorchCondaChannelCrawler, ReleasePageCrawler
from packaging import version

MIN_TORCH_VERSION = '1.10.2'
MIN_CUDA_VERSION = '10.2'

def write_record_collection_to_file(record_collection: WheelRecordCollection, root='./torch_wheels'):
    files = os.listdir(root)
    versions_by_key = dict()

    for file in files:
        torch_version = file.split('-')[0]
        key = '.'.join(torch_version.split('.')[:2])

        if key not in versions_by_key:
            versions_by_key[key] = torch_version

    current_key = '.'.join(record_collection.torch_ver.split('.')[:2])
    if current_key in versions_by_key and version.parse(record_collection.torch_ver) < version.parse(versions_by_key[current_key]):
        return 

    filename = f'{root}/{record_collection.torch_ver}-cuda{record_collection.cuda_ver}.txt'

    if osp.exists(filename):
        avai_python_dist = []
        with open(filename, 'r') as f:
            for line in f:
                avai_python_dist.append(line.strip().split()[2])
        
        with open(filename, 'a') as f:
            for record in record_collection.records:
                if record.py_ver not in avai_python_dist:
                    if record.flags is not None:
                        flags = '+'.join(record.flags)
                        f.write(f'{record.method.value}\t{record.url}\t{record.py_ver}\t{flags}\n')
                    else:
                        f.write(f'{record.method.value}\t{record.url}\t{record.py_ver}\n')

    else:
        with open(filename, 'w') as f:
            for record in record_collection.records:
                if record.flags is not None:
                    flags = '+'.join(record.flags)
                    f.write(f'{record.method.value}\t{record.url}\t{record.py_ver}\t{flags}\n')
                else:
                    f.write(f'{record.method.value}\t{record.url}\t{record.py_ver}\n')

def crawl_and_write(crawler):
    wheel_list = crawler.crawl()

    for record_collection in wheel_list:
        write_record_collection_to_file(record_collection)

def main():
    pip_crawler = PipCrawler(min_cuda_version=MIN_CUDA_VERSION, min_torch_version=MIN_TORCH_VERSION)
    release_page_crawler = ReleasePageCrawler(min_cuda_version=MIN_CUDA_VERSION, min_torch_version=MIN_TORCH_VERSION)
    pytorch_channel_crawler = PyTorchCondaChannelCrawler(min_cuda_version=MIN_CUDA_VERSION, min_torch_version=MIN_TORCH_VERSION)
    conda_forge_crawler = CondaForgeCrawler(min_cuda_version=MIN_CUDA_VERSION, min_torch_version=MIN_TORCH_VERSION)

    crawl_and_write(pip_crawler)
    crawl_and_write(release_page_crawler)
    crawl_and_write(pytorch_channel_crawler)
    crawl_and_write(conda_forge_crawler)

if __name__ == '__main__':
    main()