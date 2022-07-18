# 内存是怎么损坏的

一块内存损坏的方式有很多种。不用关应用程序逻辑层面各式各样的错误，内存损坏的普遍原因是有问题的代码访问了超出了被内存管理器或者译器分配的底层内存块的的边界的数据对象。下面列出了在实践中常看到的各式各样内存访问错误。跟那些因为大量的变量和许多逻辑层总是更加隐晦的大型程序的实际bug一比，这些例子看上去可能简单和愚蠢。但是元数据被损坏是一样的，可以用相同的策略来攻克。

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

值得提一下的是例子中的不公并不是一定会损坏堆元数据。每一个内存管理器有最小块大小和对齐的要求。如果用户请求的大小比最小块大小还小，它会被设置最小快的大小；如果大小不是对齐的倍数，它会取整到满足要求。作为大小调整的结果，实际分配给用户的内存会比请求大小要大。添加的填充会拓展用户可用的空间。

对于第一个例子，如果传入的字符串（包含8字节的块标签）小于32产品或者不是16字节的倍数（Ptmalloc最小块大小和对齐要求），那么就会至少有一个字节填充在分配的内存块，在这种情况下，覆写一个字节的结尾字符被静默容忍。这就不会奇怪这个bug可以在没有被冲出来的时候休眠很长一段时间直到传入的字符串局尊“正确”的大小。

另外一个微妙的点子是在这个例子的大小端。因为测试是跑在小端机器，下一个块的标签的最低字节被结尾字符覆写。如果程序跑在一个大端机器，则是块标签的最高字节将会被覆写。由于反正那个字节大概率是0，（对于小于65536terabytes的块），这个覆写会没有严重的后果。

跟溢出相反，一个内存块也可能被下溢，意味着用户代码修改了在内存块第一个可用的字节之前的内存。从前面的讨论可以看出，很明显当前块的标签会被破坏而不是下一个块的标签。这样跟内存溢出是相似的，依赖于破坏的内在性和什么时候块被用户释放，结果是无法预测的。

## 访问释放的内存

另外一个常见内存损坏的类型是非法访问释放的内存。它通常发生与用户代码只有一个悬挂指针或者引用被释放的内存块。当代码通过这样的指针修改内存值，它会破坏底层的数据。同样的，症状变化取决于很多因素。比如，释放的内存可能已经返回给内核了，在这种情况下，当程序访问这个内存的时候，它会立即crash；被释放的内存可能被重用和再一次分配给用户用于其他的数据对象，而数据对象会被意外地被破坏；如果他被内存管理器缓存这，这块内存可能会被用于内部数据结构，改变它会破坏堆元数据。

让我们来看看这种类型的内存损坏。下面版本的函数`copyString`从调用者接受一个缓冲区和拷贝源字符串进去。在这个例子中，我传入一个空闲的内存块作为缓冲区。这个块有16个字节，用户空间从地址0x501030开始。在用户的bug写入释放后的内存前，这16个字节被ptmal用来作为指向下一个和前一个空闲块的指针。正如我们前面章节讨论的，这些指针把同样大小的空闲块链接在一起和放到相对应的盒子里。当用户代码调入函数`strcpy`，这两个指针被破坏。在稍后当Ptmalloc访问这个空闲块，很大概率会crash或者破坏也会另外一个数据对象。


```
// Access freed memory
char* CopyString(char* buffer, char* s)
{
return strcpy(buffer, s);
}

// Before accessing freed memory
(gdb) x/5gx buffer-8
0x501028:       0x0000000000000021      0x00000036a59346b8
0x501038:       0x00000036a59346b8      0x0000000000000020
0x501048:       0x0000000000000030

// After calling strcpy with freed memory as destination
(gdb) x/5gx buffer-8
0x501028:       0x0000000000000021      0x6620737365636361
0x501038:       0x0000003600656572      0x0000000000000020
0x501048:       0x0000000000000030
```

## 使用未初始化的值


An uninitialized variable has random and unpredictable value in theory. Depending on how it is used, the adverse impact varies. Though use of uninitialized variable itself doesn’t corrupt any memory, it is usually the cause of memory corruption when acting on it.

One mystery that occurs often is that a program works fine and generates right result in debug build but behaves strangely or even crashes in release build given exactly the same input and runtime environment. Uninitialized variable is a common cause of this phenomenon. If the uninitialized variable resides in the heap, its consequence has a lot to do with the implementation of memory manager. It is not uncommon that a debug memory manager uses a different allocation algorithm from that of release version. Therefore, the location as well as the randomness of the allocated memory differs. Windows C runtime memory manager is a prominent example: it fills allocated memory with byte pattern 0xcd in debug mode while does nothing in release version. This will almost certainly change the symptom of using uninitialized memory. An uninitialized variable located on the stack doesn’t involve the memory manager. Instead it is allocated by the compiler at compilation time. The content of the uninitialized variable depends on where it is and the access history of the underlying memory. As the stack extends and shrinks dynamically along with control of flow, the stack memory changes constantly. However, the first time a stack memory is accessed, its value is always zero like any other type of memory, e.g. uninitialized global variables. This is because, for security reason, the physical memory pages provided by the kernel are zeroed out before being attached to a process’s virtual space. This may be the reason that a buggy program seems to run fine under debug version. Even though it doesn’t initialize a stack variable, yet its initial value of zero works just fine. The release build may be different because the compiler may choose a register to store the variable which is truly “random” compared with the stack memory. Another observation of this type of memory error is that various architectures have different possibilities to expose this kind of error. An architecture with more scratch registers, like x86_64, is more likely to manifest the problem than architectures with limited number of registers, e.g. x86, simply because the compiler could move more variables from stack into registers in optimized mode.
