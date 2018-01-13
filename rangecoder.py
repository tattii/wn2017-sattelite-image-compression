import time, sys, getopt, os.path

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
    def __init__(self, file, mode):
        self.file = file
        self.range = MAX_RANGE
        self.buff = 0
        self.cnt = 0
        if mode == ENCODE:
            self.low = 0
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

    # 符号化の正規化
    def encode_normalize(self):
        if self.low >= MAX_RANGE:
            # 桁上がり
            self.buff += 1
            self.low &= MASK
            if self.cnt > 0:
                putc(self.file, self.buff)
                for _ in range(self.cnt - 1): putc(self.file, 0)
                self.buff = 0
                self.cnt = 0
        while self.range < MIN_RANGE:
            if self.low < (0xff << SHIFT):
                putc(self.file, self.buff)
                for _ in range(self.cnt): putc(self.file, 0xff)
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
        putc(self.file, self.buff)
        for _ in range(self.cnt): putc(self.file, c)
        #
        putc(self.file, (self.low >> 24) & 0xff)
        putc(self.file, (self.low >> 16) & 0xff)
        putc(self.file, (self.low >> 8) & 0xff)
        putc(self.file, self.low & 0xff)


# 出現頻度表
class Freq:
    def __init__(self, count):
        size = len(count)
        self.size = size
        m = max(count)
        # 2 バイトに収める
        if m > 0xffff:
            self.count = [0] * size
            n = 0
            while m > 0xffff:
                m >>= 1
                n += 1
            for x in range(size):
                if count[x] != 0:
                    self.count[x] = (count[x] >> n) | 1
        else:
            self.count = count[:]
        self.count_sum = [0] * (size + 1)
        # 累積度数表
        for x in range(size):
            self.count_sum[x + 1] = self.count_sum[x] + self.count[x]

    #
    def write_count_table(self, fout):
        for x in self.count:
            putc(fout, x >> 8)
            putc(fout, x & 0xff)
    
    # 符号化
    def encode(self, rc, c):
        temp = int(rc.range / self.count_sum[self.size])
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
def encode(fin, fout):
    count = [0] * 256
    for x in read_file(fin):
        count[x] += 1
    rc = RangeCoder(fout, ENCODE)
    freq = Freq(count)
    freq.write_count_table(fout)
    fin.seek(0)
    for x in read_file(fin):
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

# 符号化
def encode_file(name1, name2):
    size = os.path.getsize(name1)
    infile = open(name1, "rb")
    outfile = open(name2, "wb")
    putc(outfile, (size >> 24) & 0xff)
    putc(outfile, (size >> 16) & 0xff)
    putc(outfile, (size >> 8) & 0xff)
    putc(outfile, size & 0xff)
    print(size)
    if size > 0: encode(infile, outfile)
    infile.close()
    outfile.close()

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
