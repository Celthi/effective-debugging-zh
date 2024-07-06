# find all the markdown files and add the epilogue to them
import os
import re

def find_files_recursively():
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.md'):
                yield os.path.join(root, file)

def add_epilogue(file, epilogue):
    with open(file, 'r') as f:
        content = f.read()
        with open(file, 'w') as f:
            f.write('\n')
            f.write(epilogue)
            f.write('\n')
            f.write(content)
def main():
    epilogue = '''# 更新
2024-07-05
本书已经出版
![image](https://github.com/Celthi/effective-debugging-zh/assets/5187962/29b04963-5535-432c-b56f-8a2d5dbc2ec6)
由于本库的草稿是我之前一个人写的，所以质量和正确性都不如经过两位作者和出版社编辑审阅和校正过的书稿。
如果你想阅读更加完善的版本，推荐购买正版书籍。'''
    for file in find_files_recursively():
        add_epilogue(file, epilogue)

if __name__ == '__main__':
    main()
