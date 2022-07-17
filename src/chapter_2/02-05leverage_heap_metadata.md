# 利用堆元数据

在前一个章节中，我们看到了两个受欢迎的内存管理器的实现。正如我在本章说的，理解堆的数据结构对调试内存问题有很大帮助。因为堆元素告诉我们应用程序数据对象的基本状态，它可以提供内存损坏是如何产生的线索。

尽管许多内存管理器看起来很像，不用说，它们使用不同的数据结构或多或少地记录正在使用和已经释放的内存块。不管我们在程序中决定使用何种内存管理器，为了尽可能的使用我们知识优势，我们应该尽量去学一点它的堆数据结构。通过解密一个内存块的比特和字节，它可以揭露底层的数据对象的见解信息和帮助在各种方向调试，我会在稍后展示一些例子。

从广义上讲，调试器不知道如何去解释堆元数据。我们可以通过检查内存的内容来获取信息。但是，手动调查一个巨大的内存区域是效率地的。因此，此刻是我们使用调试器插件自动化工作的好时候。在我每天的工作中，我使用一些这样的调试器插件。我已经把这些插件集成到了[core analyzer](https://github.com/yanqi27/core_analyzer)里面，关于带有core analyzer功能的gdb的安装和入门可以查看对应的文档。


这些拓展的功能命令显示一个被Ptmalloc管理的内存块或者舞台的信息。这些命令的实现利用了内存管理器的内部数据结构体，从而查询和检验一个堆的地址、或者遍历整个堆来寻找潜在的内存损坏、或者打印出堆的统计情况。下面的列表是这些命令用法的一些例子。

第一个命令显示`block`，接收一个地址然后输出在这个地址内存块的状态。在这个例子中，数据组的第十二个元素存了一个指向大小为56个字节的内存块且这个内存块正在使用中。注意在括号里的chunk的信息是Ptmalloc的内部数据结构。它在用户内存块前面16个字节的地方开始，大小是64字节。用户空间开始于地址0x503440，大小是56字节。我们可以看到有8个字节的内部数据结构消耗。

```
(gdb) block  parray[12]
[Block] In-use
        (chunk=0x503430, size=64)
        [Start Addr] 0x503440
        [Block Size] 56
```

第二个例子显示了Ptmalloc管理的主舞台的可调整参数和统计信息。舞台开始地址是0x501000，结束地址是0x60b000。在这1064KB的内存堆，总共1070640字节的1021个内存块被分配给了用户。剩下的18896字节是空闲的，被分为5个块。

```
gdb) heap
Main Arena [0x501000 - 0x60b000] 1064 KB
        Top chunk [0x606860 - 0x60b000] 18336 bytes
        Max size for fastbin is 80 bytes
        Bins (free lists) contain 4 blocks 560 bytes
        Walking arena:
                [Free]   5 blocks 18896 bytes
                [In-Use] 1021 blocks 1070640 bytes
```


我们是怎么从Ptmalloc获取这些信息的？正如我们在前面的章节知道的，每一个内存块前放着一个小的数据结构，叫`malloc_chunk`，块标签。如果用户输入一个有效的地址，由函数`malloc`返回的，内存块的标签正好在这个地址的前面。`size`字段说明当前块的大小。为了知道当前块是使用中还是空闲的，我们需要计算下一个块的地址。当前块的状态编码在下一个块的`size`字段。可以看这里的代码实现https://github.com/yanqi27/core_analyzer/blob/master/src/heap_ptmalloc_2_27.cpp#L580

The above script commands block and arena use Ptmalloc’s key data structures as we discussed before. I put fairly detailed comments in the listing so that it is easy to understand. I would like to highlight a few points about this implementation:
•	The commands deal with both 32 bit and 64 bit applications. The memory layout of data structures is calculated through sizeof operator instead of hard coded offsets.
•	The commands choose main_arena or one of the dynamic arenas to start with. If it turns out the arena doesn’t contain the input address, the command will select the next arena on the linked list to work on until either the memory block is found or all arenas are exhausted.
•	Since the script walks through the whole arena from head to toe, it doesn’t matter if the address is in the middle of a memory block or otherwise invalid pointer value. The result reveals the memory block from the memory manager’s point of view which may be compared with the application’s view to find any inconsistency.
•	The arena walk is done through the block tag, or malloc_chunk data structure. All blocks of an arena are linked together (the next block is found by its offset from current block or malloc_chunk’s size field instead of its actual address) from the first chunk to the last one, a.k.a. top chunk. If one of the malloc_chunk is corrupted along the way which is quite often in case of memory corruption, the walk will fail and the error is reported. The engineer could inspect the memory blocks surrounding the bad chunk for further clues to the problem.
•	Small memory blocks that are less than Ptmalloc’s tuning parameter max_fast (default value is 80 bytes on 64 bit and 72 bytes on 32 bit) are put in special bins, fastbins, when freed. However the malloc_chunk associated with these freed blocks is not changed from in-use to free status. This is designed for rapid reuse of small blocks often seen in C++ applications. The user-defined command takes this into consideration. If a block is small and appears to be in-use, fastbins are also checked. If the block is found in fastbins, it is actually freed; otherwise, it is indeed in-use.
•	Big memory blocks, which are larger than Ptmalloc’s tuning parameter mmap_threshold (128 kilobytes by default), are allocated directly from kernel through system API mmap. They are usually isolated from other arenas in address space. Therefore there is no way to tell if the given address is in the middle of the block. The command works correctly only if the input address is the beginning address of this type of block.
