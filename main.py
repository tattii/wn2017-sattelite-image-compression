import zlib, bz2
import struct
import numpy as np

prev_array = None

def encode():
    encodefile = input()
    directory = input()
    N = int(input())
    files = [input().split()[0] for _ in range(N)] # filename filesize

    encode_files(encodefile, directory, files)

def encode_files(encodefile, directory, files):
    files.sort()
    prev_band = None
    t = 0

    with open(encodefile, 'wb') as f:
        for file in files:
            band = int(file[19:21])
            if band != prev_band:
                prev_band = band
                t = 0
            else:
                t += 1

            print(band, t)
            f.write(encode_file(directory, file, band, t))
        

def encode_file(directory, file, band, t):
    array = load_array(directory + '/' + file)

    print(array)
    print(array.min(), array.max())
    
    array32 = array.astype(np.int32)

    compressed = compress(array32)

    header = struct.pack('B', len(file)) + file.encode('utf-8')
    return header + struct.pack('I', len(compressed)) + compressed


def load_array(file):
    array = np.fromfile(file, dtype=np.uint16)

    # reshape  3 types
    if array.size == 3750000:
        array = np.reshape(array, (1500, 2500))

    elif array.size == 15000000:
        array = np.reshape(array, (3000, 5000))

    else:
        array = np.reshape(array, (6000, 10000))

    return array


def compress(array32):
    delta = delta_array(array32)
    #return zlib.compress(delta.tostring(), level=-1)
    return bz2.compress(delta.tobytes())


def delta_array(array):
    # shift arrays
    A = np.roll(array, (1, 1), axis=(0, 1))
    A[0, :] = 0
    A[:, 0] = 0

    B = np.roll(array, 1, axis=0)
    B[0, :] = 0
    
    C = np.roll(array, 1, axis=1)
    C[:, 0] = 0

    delta = array + A - B - C
    print(delta)
    print(delta.min(), delta.max())

    return delta.astype(np.int16)


def diff(array):
    global prev_array
    array32 = array.astype(np.int32)
    if t > 0:
        diff = array32 - prev_array
    else:
        diff = array32

    prev_array = array32
    print(diff)


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

