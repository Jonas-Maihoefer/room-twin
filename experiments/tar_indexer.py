import math
import requests
from pathlib import Path

TAR_HEADER_SIZE = 512
TAR_BLOCK_SIZE = 512

def fetch_bytes (url: str, start: int, length: int) -> bytes:
    if type(start) is not int:
        raise TypeError("start must be an integer")
    if type(length) is not int:
        raise TypeError("length must be an integer")
    
    if start < 0:
        raise ValueError("start must be non negative")
    if length <= 0:
        raise ValueError("length must be greater than 0")
    
    
    headers = {"Range": f"bytes={start}-{start + length - 1}"}


    with requests.get(url, headers=headers, stream=True, timeout=10) as response:
        if response.status_code != 206:
            raise ValueError("Server did not return partial content")
        
        content_range = response.headers.get("Content-Range")
        if content_range is None:
            raise ValueError("Missing Content-Range header")
        if not content_range.startswith(f"bytes {start}-{start+length-1}/"):
            raise ValueError("Unexpected byte range")

        data = bytearray()
        for chunk in response.iter_content(chunk_size=4096):
            if len(data) + len(chunk) > length:
                raise ValueError("Response bigger than expected")
            
            data.extend(chunk)


        content = bytes(data)
        if len(content) != length:
            raise ValueError("Response incorrect length")

        return content
    
def parse_tar_header(header: bytes):
    if len(header) != TAR_HEADER_SIZE:
        raise ValueError("Incorrect header size")

    name_ascii = header[0:100].decode("ascii").rstrip("\x00")
    if header[345:500] != bytes(155): # if byte 345 to including 499 (name prefix) is not empty 
        name_ascii = header[345:500].decode("ascii").rstrip("\x00") + "/" + name_ascii
    size = int(header[124: 136].decode("ascii").rstrip("\x00"), 8)
    type_flag = header[156:157].decode("ascii")
    
    return name_ascii, size, type_flag

def next_header_offset(offset:int, size: int) -> int:
    return offset + TAR_HEADER_SIZE + TAR_BLOCK_SIZE * math.ceil(size/TAR_BLOCK_SIZE)
    
def scan_tar(url: str, limit: int | None = None):

    if limit is not None:
        if type(limit) is not int:
            raise TypeError("limit must be an integer")
        if limit < 0:
            raise ValueError("limit must be non negative")

    offset = 0
    iteration = 0
    tar_entries = {}
    while limit is None or iteration < limit:
        header = fetch_bytes(url, offset, TAR_HEADER_SIZE)
        if header == bytes(TAR_HEADER_SIZE):
            if fetch_bytes(url, offset + TAR_HEADER_SIZE, TAR_HEADER_SIZE) == bytes(TAR_HEADER_SIZE):
                break # The end of a TAR consists of two Blocks of zero-bytes, we break when the end of the TAR is reached
            else:
                raise ValueError("Unexpected zero-byte block encountered")
            
        name, size, type_flag = parse_tar_header(header)
        # save size, offset and type_flag in the dictionary under the file name
        tar_entries[name] = {
            "size": size,
            "offset": offset + TAR_HEADER_SIZE,
            "type": type_flag
        }



        offset = next_header_offset(offset, size)
        iteration += 1

    return tar_entries

def download_entry(url: str, entry: dict, destination: str):
    Path(destination).write_bytes(fetch_bytes(url, entry["offset"], entry["size"]))




url = "https://huggingface.co/datasets/zhening/LiteReality-DataBase/resolve/main/3D_assets.tar"

entries = scan_tar(url, 5)
entry = entries["3D_assets/Windows/win_1/image.png"]
download_entry(url, entry, "test_image.png")