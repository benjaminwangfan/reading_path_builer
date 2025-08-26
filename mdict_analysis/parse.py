from readmdict import MDX, MDD
# import pandas as pd
# from bs4 import BeautifulSoup as bs

mdx = MDX("vocabulary.com.mdx")
items = list(mdx.items())

words = []
for key, value in items:
    words.append(key.decode('utf-8'))
words = '\n'.join(words)
# with open('mwvbwords.txt', 'w') as f:
#     f.write(words)

for i in items:
    if i[0].decode('utf-8') == 'school':
        content = i[1].decode('utf-8')
        with open('school.html', 'w') as f:
            f.write(content)
        break