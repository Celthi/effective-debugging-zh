# 调试内存损坏

调试内存损坏真正的挑战是观察到的程序错误没有揭露导致它的错误代码。一个程序通常在有bug的代码作出错误的内存访问的时候不会显示任何症状。但是程序其中一个变量被意外地改变为一个不正确的值；在一些文献中它被叫做传染。这个变量随着程序继续运行会感染其他变量。这些问题传播最终会发展为一个严重的失败：程序要么crash要么生成错误的结果。因为原因和结果的距离，当错误被注意到时候，最后的变量和正在运行的代码通常跟实际的bug不相关和可以展露出很多在时间和位置随机性。

图3-1展示了一个典型的从初始感染变量到最终程序失败的传染链。水平轴代表以时间为刻度的程序的运行（每一个时间事件代表一次程序状态改变）。纵轴是程序的状态，即变量集合。有符号”0“的变量是有效状态，而”X“表示感染了。但是，它不是灾难性的。程序随t2,t3,等等往前进，知道tn。在时间t2，变量v3被感染。在t3，变量v2被感染。在这个时间点，变量v4出了作用域（它的”X“已经灰掉）。当最后的感染变量v1在tn搞垮程序，它已经跟最初的感染点也就是在t1的变量v4距离很远了。注意变量`v2`已经跑出了作用域和变量v3已经从感染状态改成了有效状态。这是有可能的，因为成I徐可能正确地处理了错误的数据尽管它不能反省性的定位和修正错误的原因。对于工程师来说，给定现有的复杂性和各种程序可以达到错误状态的可能性，搞明白第一个感染的变量v4和相关的有错误的代码无疑是非常困难的。
![内存错误的传播](../images/fig-3-1-Propagation_of_Memory_Error.png)

下面的例子展示了违规的代码是怎样没有在犯罪现场留下让我们调查的痕迹。这个简单的程序往一块释放后的内存写入。它最终在一个内存分配函数crash，没有显示一点跟罪犯相关的东西。

```c
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

void AccessFree()
{
    // a temporary array
    long* lArray = new long[10];
    delete lArray;

    // Accee freed memory and corrupt it.
    lArray[1] = 1;
}

void Victim()
{
    void* p = malloc(32);
    free(p);
}

int main(int argc, char** argv)
{
    // program initialization
    void* p = malloc(128);
    char* str = strdup("a string");
    free(p);

    // The initial infection
    AccessFree();

    // more work ...

    // Failure due to previous infection
    Victim();

    return 0;
}
```
在使用了Ptmalloc作为默认内存管理器的Linux Redhat发行版运行这个程序，当程序接收到段错误信号的时候，我们将会看到下面的调用栈。线程正在调用函数`Victim`，简单的在尝试向堆分配32字节。但是，正如在前面章节展示的，这个函数覆写了一块释放的内存因此损坏了堆元数据，更准确的说是用来空闲块链表的指针。这个问题直到为了重用空闲块的时候访问指针才会出现。

```
Program received signal SIGSEGV, Segmentation fault.
0x0000003f53a697e1 in _int_malloc () from /lib64/tls/libc.so.6
(gdb) bt
#0  0x0000003f53a697e1 in _int_malloc () from /lib64/tls/libc.so.6
#1  0x0000003f53a6b682 in malloc () from /lib64/tls/libc.so.6
#2  0x00000000004006ea in Victim () at access_free.cpp:17
#3  0x0000000000400738 in main (argc=1, argv=0x7fbffff4b8) at access_free.cpp:34
```

在这例子，通过简单地审阅代码bug很明显。但是对于不简单的程序，它不会是一个有效的方法。不从例子的原因出发，内存损坏难以调试是清楚的。程序在失败时的状态通常没有足够信息来下任何结论。

## 初始调查

基本上，调试内存损坏是从失败的地方追踪回提交这个开始感染的罪魁祸首代码。如果不是不可能，这会是很难的，即使看上去简单的情况也如此，像上面的例子。但是，我们应该尽可能地发现越多的感染变量，因此我们可以离有问题的代码更近。这个恢复传染链的分析过程需要，最小程度上，程序的深入知识，架构相关的信息和调试器的经验。

当一个问题发现的时候，第一个动作是调查程序的当前状态，即感染链的末尾。这个分析很重要因为它决定了接下来我们有采取的措施。有许多各式各样的方法和风格来获取和分析失败程序的大量信息。下面的列表试图描述一些基本但可触摸的步骤开始步骤。每一个步骤可以缩小搜索的范围和给出下一步的指导。一些步骤仅仅适用于一些场景，如堆分析也许只有在被感染的变量是从堆分配来的才有必要。


- 失败错误的直接原因。这是任何调查的开始地方。一个可以看到的失败必然是源代码最后一条语句导致的，或者更准确地说是CPU正在运行的最后一条指令。在crash的情况下很显然但是在不是crash的失败情况下可能有些困难。crash的情况可能会与信号或者进程接收的说明异常退出的原因的异常结合。比如，段错误信号或者AV（访问违规）异常意味着不属于任何进程段集合的内存地址的无效访问；信号bus错误意味着不对齐的地址内存访问；信号非法指令意味着一个坏的函数指令；当一个异常抛出，程序没有一个处理器，未处理的异常发生。C++运行库的实现的默认动作是处理未处理的异常，通常是生成一个core dump文件和停止程序。

- 定位最后一个感染的变量和它是怎么让程序失败的。程序失败通常跟最后一个指令试图访问的地址关联。这个地址直接和间接通过感染的变量计算而来。有些时候地址简单的是很容易确定直接原因的变量的值。但是有时候地址是多个计算步骤和内存解引用的结果，这需要自习的检查在计算的复杂表达式。比如，访问一个变量或者它的数据组成员指向的内存可能会因为引用的地址是无效的如空指针而失败；调用对象的虚拟函数可能因指向对象虚拟表的无效指针而失败；读取一个对象的数据成员因不对齐而失败等等；变量可能是传入的参数，本地变量，全局对象或者编译器创建的临时对象。我们应该对变量的存储类型、作用域和当前状态有一个清楚的理解。它是在线程栈、进程堆、模块的全局数据段、寄存器里或者属于线程的特定存储对问题的原因有很重要的影响。在大多数情况下，变量是堆数据对象。我们应该确保底层的内存块与变量符合和内存看在使用还是空闲。如果它是空闲的，我们一开始就不应该访问它。

- 检查所有在当前线程上下文的其他变量。注意那些可以影响被感染的变量。它们中的一些可能也被感染了。失败的线程上下文包括所有的寄存器值、本地变量、传入的参数、被访问的全局变量。通过审阅代码和线程上下文，我们可以更好地梳理感染链是什么样的。

- 如果没有结论，我们应该检查感染的变量是不是共享的和潜在地被其他线程访问。如果是的，过一过其他线程的上下文是有必要的。如果幸运，我们可以找到在其他线程的罪魁祸首。但是，这样的好运不是那么容易有的。即使我们没有看到其他线程破坏了感染的变量，通过观察此刻其他线程在做什么，仍然可以让我们知道问题背景的总体情况。这最终会帮我们建议更有现实意义原因的理论。

- 如果涉及到位置的内存，了解感染区域的内存模式对弄明白它是怎么感染即被谁感染通常是有效的。一些模式具有揭露性和直接连接着原因。比如，有可认识内容的字符串；具有区别性的签名的熟知的数据结构；具有调试符号的指令或者全局对象；指向其他有效内存地址的指针等等。当我们用ASCII格式打印出一块内存，识别字符串是容易的。指针则不是那么明显。但是有一些方式来区别它们与整形、浮点数和其他数据类型：检查进程的地址图和一个内存指针应该落在有效的内存段里面；指向数据对象的指针需要在合适的边界对齐；64位指针有许多位是0或者1因为64位线性虚拟地址在实际中只有一小部分是被使用（32位地址比较难认出来），比如AIX/PowerPC的堆地址总是9个16进制数字，剩下的全是0.
Let’s see a couple of examples. By simply looking at the memory contents in the following listing, it appears to be an array of printable characters. If we print the memory out as a string, it turns out something like a domain name. By further searching the code, we could find out places where the name string is used.



```
(gdb) x/4x 0xc03318
0xc03318:  0x7461686465726d76  0x61646c6e65706f2e
0xc03328:  0x736f7263696d2e70  0x2e79676574617274
(gdb) x/s 0xc03318
0xc03318:  "vmredhat.openldap.microstrategy.com"

```


Global objects, either functions or data, have associated debug symbols like the following memory area. The first eight bytes of the memory area of interest looks like a pointer. By asking the debugger if the memory referenced by the pointer is associated with a known symbol (gdb command “info symbol”), it turns out to be an instruction of method CreateInstance. The second pointer points to an object’s vtable which is located in the .data section of a library. The third address above belongs to a global object in the library’s .bss or uninitialized data section. Also notice the byte pattern of 0xfdfdfdfdfdfdfdfd at address 0x1ff6c00, which is the signature of a data structure used by an in-house tool to track memory usage.


```
(gdb) x/64gx 0x1ff6ad8
0x1ff6ad8:  0x0000002ab0ce860a  0x0000002ab0ce7f8f
0x1ff6ae8:  0x0000002a9701a48c  0x0000002a9701c8e9
0x1ff6af8:  0x0000002a97020cf1  0x0000002a9701ad8a
...
0x1ff6bc8:  0x0000000000000000  0x0000000001ff6a30
0x1ff6bd8:  0x0000000001ff3a80  0x00000000000000c8
0x1ff6be8:  0x0000000000030900  0x0000002000000000
0x1ff6bf8:  0xffffffff40200960  0xfdfdfdfdfdfdfdfd
0x1ff6c08:  0x0000002ab0ea0930  0x0000002ab0ea0a48

(gdb) info symbol 0x0000002ab0ce860a
ATL::CComCreator<ATL::CComObject<CDSSAuthServer> >::CreateInstance(void*, _GUID const&, void**) + 46 in section .text

(gdb) info symbol 0x0000002ab0ea0930
vtable for ATL::CComObject<CDSSAuthServer> + 16 in section .data

(gdb) info symbol 0x2ab0b00e20
gMSTR_LDAP_AuthAux in section .bss

```


The following listing illustrates another pattern. Judging from the surface, the 40-byte memory block seems to consist of an integer, three pointers and two more integers. The memory blocks pointed to by the two pointers have similar constituents. Since our program uses a lot of STL data structures, it is not difficult to guess this is a tree node of class std::map<init,int>. The STL map implemented by the g++ compiler uses red black tree. The tree node is declared as std::_Rb_tree_node_base followed implicitly by std::pair<key,value> (both key and value are integers in our case). This is exactly what we observe in the listing. Our guess can be further confirmed by querying the memory manager for the size and status of the memory blocks addressed by the pointers.

```
(gdb) x/5gx 0x503100
0x503100:  0x0000000000000001  0x00000000005030a0
0x503110:  0x00000000005030d0  0x0000000000503160
0x503120:  0x0000000a00000005

(gdb) ptype std::_Rb_tree_node_base
type = class std::_Rb_tree_node_base {
  public:
    std::_Rb_tree_color _M_color;
    std::_Rb_tree_node_base *_M_parent;
    std::_Rb_tree_node_base *_M_left;
    std::_Rb_tree_node_base *_M_right;
    ...
}

(gdb) block 0x503100
[Block] In-use
        (chunk=0x5030f0, size=48)
        [Start Addr] 0x503100
        [Block Size] 40

(gdb) block 0x00000000005030a0
[Block] In-use
        (chunk=0x503090, size=48)
        [Start Addr] 0x5030a0
        [Block Size] 40
...

```

Once we put all these pieces together, we might have a good understanding of how memory was accessed. Chapter six introduces a power tool “Core Analyzer” which has a function to analyze memory pattern automatically.


•	If a piece of memory is corrupted in a seemingly random fashion and cannot be explained by the design logic after code review, you should expand the investigation to the memory blocks adjacent to the infected variable. Since memory overflow is much more often than memory underflow, the memory block immediately before the infected memory area should be inspected with higher priority. Try to find the variable that owns the suspected block and review related code to determine if it is a real possibility.
•	If the infected variables are from the heap and multiple heaps exist in the process, find out which heap the data objects belong to. Why do I care about this? Because much of the debugging process is about narrowing down from a large set of possibilities to a few and eventually locating the bug (divide and conquer strategy).
•	If a heap is involved, a complete heap analysis may be helpful. The simplest analysis could be walking the heap and validating heap data structures and all memory blocks. The way heap data structures are corrupted, if any, could be a signature of the problem.
•	If more than one instance of failure occurs, we should strive to find commonality among them. It would be obvious if all failures occur at the same place with the same call stack. It would be even more indicative if the involved data objects are of the same types even if they are allocated dynamically for the heap. This knowledge of failure pattern is a good guide for the next debugging step which might involve a memory checking tool or instrument code.
•	Construct a hypothesis on why the program fails based on collected information. If there isn’t enough evidence to suggest any theory, we should either redo the previous steps and dig deeper or run more tests to expose the problem in a different way and hopefully with more relevant information.

For any non-trivial program, there is usually a large amount of variables and information to sift through. It requires a lot of patience and persistence. But the reward is also immense when you finally nail the bug.

