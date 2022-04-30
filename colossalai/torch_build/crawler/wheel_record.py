import re
from pydantic import BaseModel, validator, StrictStr
from enum import Enum
from typing import List

class Method(Enum):
    PIP = 'pip'
    CONDA = 'conda'

class WheelRecord(BaseModel):
    method: Method
    url: str
    py_ver: str

    @validator('py_ver')
    def check_py_ver(cls, v):
        assert re.search(r'^3\.\d+$', v)
        return v
    
class WheelRecordCollection(BaseModel):
    torch_ver: str
    cuda_ver: str
    records: List[WheelRecord]

    @validator('torch_ver')
    def check_torch(cls, v):
        assert re.search(r'^1\.\d+\.\d$', v)
        return v

    @validator('cuda_ver')
    def check_cuda_ver(cls, v):
        assert re.search(r'^1\d\.\d$', v)
        return v