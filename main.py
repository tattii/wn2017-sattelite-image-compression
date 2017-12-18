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

    with open(encodefile, 'wb') as f:
        for i, file in enumerate(files):
            f.write(encode_file(directory, file, i % 4))
        

def encode_file(directory, file, t):
    array = load_array(directory + '/' + file)

    #print(array)
    #print(array.min(), array.max())

    diff = diff_array(array, t)
    #print(diff)
    #print(diff.min(), diff.max())
    
    compressed = compress(diff)

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
    compressed = bz2.compress(d.tostring())
    return struct.pack('I', len(compressed)) + compressed


def delta_array(array):
    # shift down array
    down = np.roll(array, 1, axis=0)
    down[0, :] = 0
    
    delta = array - down + 128
    #print(delta)
    #print(delta.min(), delta.max())

    return delta


def diff_array(array, t):
    global prev_array
    if t > 0:
        diff = array - prev_array
    else:
        diff = array

    prev_array = array

    return diff

def decode():
    encodefile = input()
    directory = input()

    decode_files(encodefile, directory)

def decode_files(encodefile, directory):
    count = 0
    with open(encodefile, 'rb') as f:
        while True:
            h = f.read(1)
            if not h: break
            decode_file(directory, f, h, count)
            count += 1

def decode_file(directory, f, h, count):
    filename_size = struct.unpack('B', h)[0]
    filename = f.read(filename_size).decode('utf-8')

    array1 = read_block(f)
    array2 = read_block(f)

    array = array1.astype(np.uint16)
    array2 = array2.astype(np.uint16)
    array += np.left_shift(array2, 8)

    array = array.astype(np.int16)
    delta = reshape_array(array)

    diff = reverse_delta(delta)
    decoded = add_array(diff, count % 4) 

    data = decoded.tostring()

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

def add_array(diff, t):
    global prev_array
    if t > 0:
        array = diff + prev_array
    else:
        array = diff

    prev_array = array

    return array
    


command = input()
if command == "encode":
    encode()
else:
    decode()

