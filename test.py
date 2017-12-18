import os, sys, shutil
import subprocess, io
import time
from filecmp import dircmp


dir = 'data/bin_4obs'
encodefile = 'out/encoded.bin'
unzipdir = 'out/unzip'
defaultfile = 'data/bin_4obs.tar.bz2'


def test_encode(min=False):
    if os.path.exists(encodefile): os.remove(encodefile)

    t1 = time.time()
    encode(min)
    elapsed = time.time() - t1

    size = os.path.getsize(encodefile)
    defaultsize = os.path.getsize(defaultfile)
    compression = 1- size / defaultsize

    print('{:.3f} s / {:.1f} MB / {:.2%}'.format(elapsed, size / 1024 / 1024, compression))

def encode(min):
    files = os.listdir(dir)
    if min: files = files[:4]
    filelist = [file + ' ' + str(os.path.getsize(dir + '/' + file)) for file in files]

    input = '\n'.join(['encode', encodefile, dir, str(len(files))])
    input += '\n' + '\n'.join(filelist) + '\n'

    print(input)
    proc = subprocess.check_output('echo "' + input + '" | python3 main.py', shell=True)


def test_decode(min=None):
    if os.path.exists(unzipdir): shutil.rmtree(unzipdir)
    os.mkdir(unzipdir)
    
    t1 = time.time()
    decode()
    elapsed = time.time() - t1
    print('{:.3f} s'.format(elapsed))

    check_decoded(min)

def decode():
    input = '\n'.join(['decode', encodefile, unzipdir]) + '\n'
    proc = subprocess.check_output('echo "' + input + '" | python3 main.py', shell=True)


def check_decoded(min):
    dcmp = dircmp(dir, unzipdir)
    if min:
        print("right", dcmp.right_only)
        print("diff", dcmp.diff_files)
        return

    if len(dcmp.left_only) + len(dcmp.right_only) + len(dcmp.diff_files) == 0:
        print("ok")

    else:
        print("left", dcmp.left_only, "right", dcmp.right_only)
        print("diff", dcmp.diff_files)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == 'encode':
            if len(sys.argv) > 2:
                test_encode(True) # min test
            else:
                test_encode()

        elif sys.argv[1] == 'decode':
            if len(sys.argv) > 2:
                test_decode(True) # min test
            else:
                test_decode()

        elif sys.argv[1] == 'check':
            check_decoded()

    else:
        test_encode()
        test_decode()


