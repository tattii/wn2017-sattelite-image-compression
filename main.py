import zlib, bz2
import struct

def encode():
    encodefile = input()
    directory = input()
    N = int(input())
    files = [input().split()[0] for _ in range(N)] # filename filesize

    encode_files(encodefile, directory, files)

def encode_files(encodefile, directory, files):
    with open(encodefile, 'wb') as f:
        for file in files:
            f.write(encode_file(directory, file))
        

def encode_file(directory, file):
    with open(directory + '/' + file, 'rb') as f:
        #data = zlib.compress(f.read(), level=-1)
        data = bz2.compress(f.read())
    
        header = struct.pack('B', len(file)) + file.encode('utf-8') + struct.pack('I', len(data))
        return header + data

def decode():
    encodefile = input()
    directory = input()

    decode_files(encodefile, directory)

def decode_files(encodefile, directory):
    with open(encodefile, 'rb') as f:
        while True:
            h = f.read(1)
            if not h: break
            decode_file(directory, f, h)
        

def decode_file(directory, f, h):
    filename_size = struct.unpack('B', h)[0]
    filename = f.read(filename_size).decode('utf-8')

    data_size = struct.unpack('I', f.read(4))[0]
    data = bz2.decompress(f.read(data_size))

    with open(directory + '/' + filename, 'wb') as out:
        out.write(data)


command = input()
if command == "encode":
    encode()
else:
    decode()

