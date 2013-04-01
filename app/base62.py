
CHARSET = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
BASE = 62

def encode(n):
    s = []
    while n > 0:
        r = n % BASE
        n /= BASE

        s.append(CHARSET[r])

    s.reverse()

    return ''.join(s)
