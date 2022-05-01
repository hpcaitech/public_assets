import os.path as osp
from crawler import PipCrawler, WheelRecordCollection, CondaForgeCrawler, PyTorchCondaChannelCrawler


MIN_TORCH_VERSION = '1.8.0'
MIN_CUDA_VERSION = '10.2'

def write_record_collection_to_file(record_collection: WheelRecordCollection, root='./torch_wheels'):
    filename = f'{root}/{record_collection.torch_ver}-cuda{record_collection.cuda_ver}.txt'

    if osp.exists(filename):
        avai_python_dist = []
        with open(filename, 'r') as f:
            for line in f:
                avai_python_dist.append(line.strip().split()[-1])
        
        with open(filename, 'a') as f:
            for record in record_collection.records:
                if record.py_ver not in avai_python_dist:
                    f.write(f'{record.method.value}\t{record.url}\t{record.py_ver}\n')

    else:
        with open(filename, 'w') as f:
            for record in record_collection.records:
                f.write(f'{record.method.value}\t{record.url}\t{record.py_ver}\n')

def crawl_and_write(crawler):
    wheel_list = crawler.crawl()

    for record_collection in wheel_list:
        write_record_collection_to_file(record_collection)

def main():
    pip_crawler = PipCrawler(min_cuda_version=MIN_CUDA_VERSION, min_torch_version=MIN_TORCH_VERSION)
    pytorch_channel_crawler = PyTorchCondaChannelCrawler(min_cuda_version=MIN_CUDA_VERSION, min_torch_version=MIN_TORCH_VERSION)
    conda_forge_crawler = CondaForgeCrawler(min_cuda_version=MIN_CUDA_VERSION, min_torch_version=MIN_TORCH_VERSION)

    crawl_and_write(pip_crawler)
    crawl_and_write(pytorch_channel_crawler)
    crawl_and_write(conda_forge_crawler)



    

if __name__ == '__main__':
    main()