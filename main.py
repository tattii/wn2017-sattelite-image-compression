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

            #print(band, t)
            f.write(encode_file(directory, file, band, t))
        

def encode_file(directory, file, band, t):
    array = load_array(directory + '/' + file)

    #print(array)
    #print(array.min(), array.max())
    
    compressed = compress(array)

    header = struct.pack('B', len(file)) + file.encode('utf-8')
    return header + compressed


def load_array(file):
    array = np.fromfile(file, dtype=np.int16)
    return reshape_array(array)

def reshape_array(array):
    # reshape  3 types
    if array.size == 3750000:
        array = np.reshape(array, (1500, 2500))

    elif array.size == 15000000:
        array = np.reshape(array, (3000, 5000))

    else:
        array = np.reshape(array, (6000, 10000))

    return array


def compress(array):
    delta = delta_array(array)
    
    delta1 = delta.astype(np.uint8)
    delta2 = np.right_shift(delta, 8).astype(np.uint8)

    #print(delta1)
    #print(delta2)

    return block(delta1) + block(delta2)
    
def block(d):
    #zlib.compress(delta.tostring(), level=-1)
    compressed = bz2.compress(d.tobytes())
    return struct.pack('I', len(compressed)) + compressed


def delta_array(array):
    # shift down array
    down = np.roll(array, 1, axis=0)
    down[0, :] = 0
    
    delta = array - down + 128
    #print(delta)
    #print(delta.min(), delta.max())

    return delta


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

    array1 = read_block(f)
    array2 = read_block(f)

    array = array1.astype(np.uint16)
    array2 = array2.astype(np.uint16)
    array += np.left_shift(array2, 8)


    array = array.astype(np.int16)
    delta = reshape_array(array)

    decoded = reverse_delta(delta)

    data = decoded.tobytes()

    with open(directory + '/' + filename, 'wb') as out:
        out.write(data)
    
def read_block(f):
    size = struct.unpack('I', f.read(4))[0]
    data = bz2.decompress(f.read(size))
    return np.fromstring(data, dtype=np.uint8)

def reverse_delta(delta):
    delta -= 128

    for i in range(1, delta.shape[0]):
        delta[i, :] += delta[i-1, :]

    #print(delta)

    return delta


command = input()
if command == "encode":
    encode()
else:
    decode()

