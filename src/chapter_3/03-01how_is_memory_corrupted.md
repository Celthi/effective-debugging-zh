# 内存是怎么损坏的

一块内存损坏的方式有很多种。不用关应用程序逻辑层面各式各样的错误，内存损坏的普遍原因是有问题的代码访问了超出了被内存管理器或者编译器分配的底层内存块的的边界的数据对象。下面列出了在实践中常看到的各式各样内存访问错误。跟那些因为大量的变量和许多逻辑层总是更加隐晦的大型程序的实际bug一比，这些例子看上去可能简单和愚蠢。但是元数据被损坏是一样的，可以用相同的策略来攻克。

## 内存溢出/下溢

内存溢出肯定是最常捡到的内存损坏。当用户代码访问的内存超出了内存管理器或者编译分配给用户的内存块的最后一个字节。正如我前面展示的，一个典型的内存管理器的实现会在每一个内存块开始出隐藏一个小的数据结构，块标签。这个数据结构包含了内存块的大小，也包含了它的状态信息，空闲或者使用中，和其他取决于特定实现的更多信息

如果用户代码写入超过了分配的内存块用户空间，它会覆写下一个内存块的标签。这会损坏内存管理器的堆数据结构和导致未定义行为。只有当下一个块被释放或者分配，也就是当下一个块的标签被内存管理器用来计算的时候，破坏才会露出来或者往下游传播。有一些内存管理器不会在内存块镶嵌块标签，比如？？。这时被损坏的内存会是下一个块里的应用数据。后果取决于数据稍后是怎么被使用的。如果用户超出分配块的范围读入内存管理器的数据结构，结果也是不能预测的和更微妙的是依赖读入的数据如何被使用。

下面的代码显示了两个内存管理器分配的内存块被覆写的例子。

```c
// Memory overrun example one
char* CopyString(char* s)
{
    char* newString = (char*) malloc(strlen(s));
    strcpy(newString, s);

    return newString;
}

// Memory overrun example two
int* p = (int*) malloc(N*sizeof(int));
for (int i=0; i<=N; i++)
{
    p[i] = 0;
}

```

在第一个个例子中，用户代码没有考虑到字符串结尾的字符'\0'，因而覆写内存块一个字节。第二个例子往内存`p[0]`到`p[N]`写入，总共是`N+1`个整数而不是被分配的`N`个整数。它会在分配的内存块的后一个字节覆写如一个整数。我们最好可以通过检查它的内容来理解内存是怎么样被破坏的。下面的输出展示了第一个例子给Ptmalloc的元数据带来的破坏。

```
// Before memory corruption (calling function strcpy)
(gdb) print newString
$1 = 0x501030 ""
(gdb) x/5gx 0x501030-8
0x501028:       0x0000000000000021      0x0000000000000000
0x501038:       0x0000000000000000      0x0000000000000000
0x501048:       0x0000000000000031

// After calling strcpy
(gdb) x/5gx 0x501030-8
0x501028:       0x0000000000000021      0x7274732073696854
0x501038:       0x3220736920676e69      0x2e73657479622034 
0x501048:       0x0000000000000000

```
变量`newString`被分配到地址为0x501030的内存块。标签块坐落在前面8字节，即0x501028，值0x21意味着这个块的大小是32字节和在使用中。下一个块的标签可以通过相加当前块的地址和它的大小来计算，即0x501048。它显示了下一个块的大小是48字节和也在使用中。当函数`strcpy`被调用以后，内存被传入的字符串填充。这个块标签没有被改变，但是下一个块的标签被字符串结尾字符抹掉了。接下来，当下一个内存块被用户释放，Ptmalloc将会遇到问题。

It is worth mentioning that the bugs in the examples will not always corrupt heap metadata. Every memory manager has requirements for minimum block size and alignment. If the user requested size is less than the minimum block size, it is set to minimum block size; if the size is not multiples of alignment, it is rounded up to meet the requirement. As a result of the size adjustment, the actual memory allocated to a user may be bigger than the requested size. The added padding bytes expand the available space for the user. 



For the first example,  if the length of the pass-in string (including 8 bytes for the block tag) is less than 32 bytes or is not multiples of 16 bytes (Ptmalloc’s minimum block size and alignment requirement), there is at least one byte padding in the allocated memory block, in which case the overrunning one-byte terminating character is silently tolerated. It is no wonder that the bug could hibernate for long time without being flushed out until the pass-in string has the “right” length. Another subtle point is the endianness in this example. Because the test is run on a little endian machine, the least significant byte of the next block’s tag is overwritten by the terminating character. If the program is run on a big endian machine, the most significant byte of the block tag is going to be overwritten instead. Since that byte is very likely zero anyway (for block less than 65536 terabytes), the overrun would have no adverse impact.

Just opposite to the overrun, a memory block can also be underrun, meaning the user code modifies a memory block before its first usable byte. It is obvious from previous discussion that the current block’s tag is going to be corrupted instead of the tag of the next block. The consequence is similar to the memory overrun which is also unpredictable depending on the nature of the corruption and when the block is freed by the user.
