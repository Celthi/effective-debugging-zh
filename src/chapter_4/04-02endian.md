
# 更新
2024-07-05
本书已经出版
![image](https://github.com/Celthi/effective-debugging-zh/assets/5187962/29b04963-5535-432c-b56f-8a2d5dbc2ec6)
由于本库的草稿是我之前一个人写的，所以质量和正确性都不如经过两位作者和出版社编辑审阅和校正过的书稿。
如果你想阅读更加完善的版本，推荐购买正版书籍。
# 大小端

具体的架构也需要确定内存中数据的字节顺序，或者是大小端方案。

小端指数据最低字节放在最低的地址，最高的字节放在地址最高的地方。

x86 CPU是小端。PowerPC 和SPARC则是大端。有趣地是，Itanium芯片可以通过一个开关来设置为大端或者小端。

举个例子，让我们看看下面的变量。
```
 unsigned long var = 0x0123456789abcdef;
```
在小端架构中(x86_64)，调试器显示的内存布局如下，
```
 (gdb) x/8x &var
 0x7fbffff4a8:  0xef 0xcd 0xab 0x89 0x67 0x45 0x23 0x01
```
最低字节0xef被放在了低地址0x7fbff4a8，同时最高字节0x01被放在了高地址0x7fbfff4af

同样的变量，在大端的机器上（UltraSPARC)，显示相反的内存布局：

```
  0xffffffff7ffffa50: 0x01 0x23 0x45 0x67 0x89 0xab 0xcd 0xef
```
