import os, sys, shutil
import subprocess, io

dir = 'data/bin_4obs'
encodefile = 'out/encoded.bin'
unzipdir = 'out/unzip/'

def test_encode():
    if os.path.exists(encodefile): os.remove(encodefile)

    files = os.listdir(dir)
    filelist = [file + ' ' + str(os.path.getsize(dir + '/' + file)) for file in files]

    input = '\n'.join(['encode', encodefile, dir, str(len(files))])
    input += '\n' + '\n'.join(filelist) + '\n'

    print(input)
    proc = subprocess.run(['python3', 'main.py'], input=input, encoding='ascii')


def test_decode():
    if os.path.exists(unzipdir): shutil.rmtree(unzipdir)

    input = '\n'.join(['decode', encodefile, unzipdir]) + '\n'
    proc = subprocess.run(['python3', 'main.py'], input=input, encoding='ascii')


if __name__ == '__main__':
    if sys.argv[1] == 'decode':
        test_decode()

    else:
        test_encode()


