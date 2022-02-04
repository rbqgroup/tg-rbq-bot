import hashlib
from encodings import utf_8

file = open('../help_about.txt', 'r', encoding='utf8')
print(hashlib.md5(file.read().encode()).hexdigest())
file.close()
file = open('../help_gag.txt', 'r', encoding='utf8')
print(hashlib.md5(file.read().encode()).hexdigest())
file.close()
