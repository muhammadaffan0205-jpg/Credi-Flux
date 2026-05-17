# backend/utils/encryption.py
key = 'abcdefghijklmnopqrstuvwxyz'

def enc_substitution(n, plaintext):
    result = ''
    for l in plaintext.lower():
        try:
            i = key.index(l)
            result += key[(i + n) % 26]
        except ValueError:
            result += l
    return result

def dec_substitution(n, ciphertext):
    result = ''
    for l in ciphertext:
        try:
            i = key.index(l)
            result += key[(i - n) % 26]
        except ValueError:
            result += l
    return result

SHIFT = 13
def encrypt(text):
    """Encrypt a string using ROT13."""
    return enc_substitution(SHIFT, text)

def decrypt(text):
    """Decrypt a string using ROT13 (same as encrypt)."""
    return dec_substitution(SHIFT, text)