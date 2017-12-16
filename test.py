import os, sys, shutil
import subprocess, io
import time


dir = 'data/bin_4obs'
encodefile = 'out/encoded.bin'
unzipdir = 'out/unzip/'
defaultfile = 'data/bin_4obs.tar.bz2'


def test_encode():
    if os.path.exists(encodefile): os.remove(encodefile)

    t1 = time.time()
    encode()
    elapsed = time.time() - t1

    size = os.path.getsize(encodefile)
    defaultsize = os.path.getsize(defaultfile)
    compression = 1- size / defaultsize

    print('{:.3f} s / {:.1f} MB / {:.2%}'.format(elapsed, size / 1024 / 1024, compression))

def encode():
    files = os.listdir(dir)
    filelist = [file + ' ' + str(os.path.getsize(dir + '/' + file)) for file in files]

    input = '\n'.join(['encode', encodefile, dir, str(len(files))])
    input += '\n' + '\n'.join(filelist) + '\n'

    print(input)
    proc = subprocess.run(['python3', 'main.py'], input=input, encoding='ascii')


def test_decode():
    if os.path.exists(unzipdir): shutil.rmtree(unzipdir)
    
    t1 = time.time()
    decode()
    elapsed = time.time() - t1
    print('{:.3f} s'.format(elapsed))

    # check decoded files

def decode():
    input = '\n'.join(['decode', encodefile, unzipdir]) + '\n'
    proc = subprocess.run(['python3', 'main.py'], input=input, encoding='ascii')


if __name__ == '__main__':
    if sys.argv[1] == 'decode':
        test_decode()

    else:
        test_encode()


