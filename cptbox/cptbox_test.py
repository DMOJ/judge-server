from _cptbox import Process

allowed = [
    0, 1, 2, 3, 5, 9, 10, 11, 12, 13, 14, 16, 21, 59, 72,
    78, 97, 137, 158, 202, 218, 231, 273,
]


def main():
    proc = Process(64)
    for call in allowed:
        proc._handler(call, 1)
    proc._spawn('/bin/ls', ['ls'])
    print 'Return: %d' % proc._monitor()

if __name__ == '__main__':
    main()