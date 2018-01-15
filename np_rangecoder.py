import time, sys, getopt, os.path
import numpy as np
import struct

ENCODE = "encode"
DECODE = "decode"
MAX_RANGE = 0x100000000
MIN_RANGE = 0x1000000
MASK      = 0xffffffff
SHIFT     = 24

# バイト単位の入出力
def getc(f):
    c = f.read(1)
    if c == b'': return None
    #return ord(c)
    return int.from_bytes(c, "big")

def putc(f, x):
    #f.write(chr(x & 0xff))
    f.write(x.to_bytes(1, "big"))

#
class RangeCoder:
    def __init__(self, file, mode, inputsize):
        self.file = file
        self.range = MAX_RANGE
        self.buff = 0
        self.cnt = 0
        if mode == ENCODE:
            self.low = 0
            self.array = np.empty(inputsize, dtype=np.uint8)
            self.size = 0

        elif mode == DECODE:
            # buff の初期値 (0) を読み捨てる
            getc(self.file)
            # 4 byte read
            self.low = getc(self.file)
            self.low = (self.low << 8) + getc(self.file)
            self.low = (self.low << 8) + getc(self.file)
            self.low = (self.low << 8) + getc(self.file)
        else:
            raise "RangeCoder mode error"

    def puti(self, x):
        self.array[self.size] = x
        self.size += 1

    # 符号化の正規化
    def encode_normalize(self):
        if self.low >= MAX_RANGE:
            # 桁上がり
            self.buff += 1
            self.low &= MASK
            if self.cnt > 0:
                self.puti(self.buff)
                for _ in range(self.cnt - 1): self.puti(0)
                self.buff = 0
                self.cnt = 0

        while self.range < MIN_RANGE:
            if self.low < (0xff << SHIFT):
                self.puti(self.buff)
                for _ in range(self.cnt): self.puti(0xff)
                self.buff = (self.low >> SHIFT) & 0xff
                self.cnt = 0
            else:
                self.cnt += 1
            self.low = (self.low << 8) & MASK
            self.range <<= 8

    # 復号の正規化
    def decode_normalize(self):
        while self.range < MIN_RANGE:
            self.range <<= 8
            c = getc(self.file)
            if c == None: 
                self.low = ((self.low << 8) + 0) & MASK
                return
            self.low = ((self.low << 8) + c) & MASK

    # 終了
    def finish(self):
        c = 0xff
        if self.low >= MAX_RANGE:
            # 桁上がり
            self.buff += 1
            c = 0
        self.puti(self.buff)
        for _ in range(self.cnt): self.puti(c)

        # write file
        d = self.array[:self.size + 1].tostring()
        last_low = struct.pack('I', self.low)
        self.file.write(d + last_low)


# 出現頻度表
class Freq:
    def __init__(self, count):
        m = count.max()

        # 2 バイトに収める
        if m > 0xffff:
            n = int(m).bit_length() - 16
            count = np.where(count == 0, count, (count >> n) | 1)

        self.count = count
        self.count_sum = np.cumsum(count) # 累積度数表
        self.count_all = self.count_sum[count.size - 1]

    def write_count_table(self, fout):
        length = struct.pack('B', self.count.size - 1)
        table = self.count.astype(np.uint16).tostring()
        fout.write(length + table)

    
    # 符号化
    def encode(self, rc, c):
        temp = int(rc.range / self.count_all)
        rc.low += self.count_sum[c] * temp
        rc.range = self.count[c] * temp
        rc.encode_normalize()

    # 復号
    def decode(self, rc):
        # 記号の探索
        def search_code(value):
            i = 0
            j = self.size - 1
            while i < j:
                k = int((i + j) / 2)
                if self.count_sum[k + 1] <= value:
                    i = k + 1
                else:
                    j = k
            return i
        #
        temp = int(rc.range / self.count_sum[self.size])
        c = search_code(rc.low / temp)
        rc.low -= temp * self.count_sum[c]
        rc.range = temp * self.count[c]
        rc.decode_normalize()
        return c

# ファイルの読み込み
def read_file(fin):
    while True:
        c = getc(fin)
        if c is None: break
        yield c

# レンジコーダによる符号化
def encode(array, fout):
    count = np.bincount(array)

    rc = RangeCoder(fout, ENCODE, array.size)
    freq = Freq(count)
    freq.write_count_table(fout)
    
    for x in np.nditer(array):
        freq.encode(rc, x)
    rc.finish()

# 出現頻度表の読み込み
def read_count_table(fin):
    count = [0] * 256
    for x in range(256):
        count[x] = (getc(fin) << 8) + getc(fin)
    return count

# レンジコーダによる復号
def decode(fin, fout, size):
    freq = Freq(read_count_table(fin))
    rc = RangeCoder(fin, DECODE)
    for _ in range(size):
        putc(fout, freq.decode(rc))


def readfile(file):
    return np.fromfile(file, dtype=np.uint8)

# 符号化
def encode_file(name1, name2):
    array = readfile(name1)
    size = array.size
    print(size)
    if size <= 0: return

    with open(name2, "wb") as outfile:
        outfile.write(struct.pack('I', size))
        encode(array, outfile)


# 復号
def decode_file(name1, name2):
    infile = open(name1, "rb")
    outfile = open(name2, "wb")
    size = 0
    for _ in range(4):
        size = (size << 8) + getc(infile)
    print(size)
    if size > 0: decode(infile, outfile, size)
    infile.close()
    outfile.close()

#
def main():
    eflag = False
    dflag = False
    opts, args = getopt.getopt(sys.argv[1:], 'ed')
    for x, y in opts:
        if x == '-e' or x == '-E':
            eflag = True
        elif x == '-d' or x == '-D':
            dflag = True
    if eflag and dflag:
        print('option error')
    elif eflag:
        encode_file(args[0], args[1])
    elif dflag:
        decode_file(args[0], args[1])
    else:
        print('option error')

#
s = time.clock()
main()
e = time.clock()
print("%.3f" % (e - s))
