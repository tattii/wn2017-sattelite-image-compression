import zipfile

def encode():
    encodefile = input()
    directory = input()
    N = int(input())
    files = [input().split()[0] for _ in range(N)] # filename filesize

    with zipfile.ZipFile(encodefile, 'w', zipfile.ZIP_DEFLATED) as zf:
        for name in files:
            zf.write(directory + '/' + name, name)

def decode():
    encodefile = input()
    directory = input()
    with zipfile.ZipFile(encodefile, 'r') as zf:
        zf.extractall(directory)


command = input()
if command == "encode":
    encode()
else:
    decode()

