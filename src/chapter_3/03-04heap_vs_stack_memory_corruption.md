
# 更新
2024-07-05
本书已经出版
![image](https://github.com/Celthi/effective-debugging-zh/assets/5187962/29b04963-5535-432c-b56f-8a2d5dbc2ec6)
由于本库的草稿是我之前一个人写的，所以质量和正确性都不如经过两位作者和出版社编辑审阅和校正过的书稿。
如果你想阅读更加完善的版本，推荐购买正版书籍。
---
# 更新
2024-07-05
本书已经出版
![image](https://github.com/Celthi/effective-debugging-zh/assets/5187962/29b04963-5535-432c-b56f-8a2d5dbc2ec6)
由于本库的草稿是我之前一个人写的，所以质量和正确性都不如经过两位作者和出版社编辑审阅和校正过的书稿。
如果你想阅读更加完善的版本，推荐购买正版书籍。---
# 堆与栈内存损坏

在内存损坏的情况下，数据对象是从堆上分配还是在堆栈上分配有显着差异。堆对象由内存管理器在运行时分配。它的地址取决于很多因素：具体内存管理器实现的分配策略；内存分配/释放请求的历史，它们的大小分布和顺序，这会影响内存管理器缓存哪些空闲内存块，以及是从缓存中选择新内存块还是从全新的段分配；多线程多处理器环境下的并发内存请求等。由于其动态特性，堆对象通常在同一程序的各个实例中具有不同的地址。每次分配时，其相邻的数据对象也可能不同。另一方面，堆栈变量是由编译器静态分配的。它相对于函数堆栈帧的地址是固定的，并且前后变量是已知且不变的。因为内存损坏与罪魁祸首和受害者的相对位置有很大关系（它们通常是地址空间中的邻居），所以堆内存损坏通常呈现出更多的随机性，而栈内存损坏可能是一致的。