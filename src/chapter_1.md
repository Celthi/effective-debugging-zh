# 第一章 调试符号和调试器

当谈论调试一个程序的时候，调试器也许是人们想到的第一个事物，因为它是这个过程中不可避免的部分。而这源于就算不是无法实现，考虑到现代编程语言和操作系统的复杂性，知道一个程序的状态也是非常困难。一个写代码的开发人员应该已经知道什么是调试器和如何或多或少去使用一个调试器。但是你了解调试器足够多吗？答案很大程度取决于你在问谁。对于一些人，设置断点和检查变量的值是他们所有的需要，但是另外一些需要检查程序的比特和字节来产生线索。从我个人的经验，每一个程序员都应该知道一点调试器是如何实现它的魔法。尽管不必要去了解深入血肉的调试内在细节，如调试符号是如何产生、组织和最终被调试器使用，但知道概念和一些它的实现细节可以帮助你理解调试的强项，也理解它的不足。有了这些知识，你将更有效率地使用调试器。举个例子，如果你明白什么样的调试符号在调试优化后的代码（如发行版或者系统库），你将知道在哪里设置断点，来获取你所需要的；你会知道尽可能地怎样减少调试侵入式的影响，比如为了使成功地重现问题，使用硬件断点。本章节揭露一些调试器内在，从而让我们比平常知道更多一点。你将不仅知道调试器可以做什么，也将知道它是怎么做的，而也许更重要的是，为什么有时候它没有做到你期望的事情，在哪些情况下，你可以变通一下。我们也将看到如何使用自定义命令如插件函数来增强调试器的能力。

## 调试符号

调试符号是和相关的机器码、全局数据对象等等一起由编译器生成的。接着它们被链接器收集和组织，写入到可执行文件（大部分UNIX平台）的调试section或者是一个单独的文件（Windows 程序数据库，或者pdb文件）。一个源码级别的调试器为了理解一个进程的内存镜像如一个程序的运行示例，需要从它的仓库里面读取调试符号。在它的众多特性中，一个调试符号可能关联一个进程的指令和对应的程序源码行数或者表达式；或者从源程序声明的结构化的数据对象角度，描述一块内存。有了这些映射，一个调试可以在源码层面，执行用户的命令来查询和操作进程。比如，一个在特定源代码行的断点会被翻译为一个指令的地址；一块内存会被标记为在源代码语言上下文的变量和可以被格式化为它的声明类型。简而言之，调试符号构建了高层面源码程序和运行着程序的原始内存内容的桥梁。

## 调试符号概览

为了具有完全的源码级别调试能力，编译器需要生成许多调试符号信息，它们可以根据描述的对象分类如下：

- 全局函数和变量

    这一类包含了在各个编译单元课件的全局符号的类型和位置信息。全局变量具有相对它们属于的加载模块机制固定的地址。它们在当程序退出或者程序调用运行期链接器API显示卸载模块前都是有效和可访问的。因为可见性，固定位置和长的生命跨度，全局变量在任何时候和任何位置都是可以调试的。这意味着一个调试器在全局变量整个生命期内，无论程序在运行哪一个分支，都可以可以观察、改变和设置数据断点。

- 源文件和行信息

    众多任何调试器的主要特性中，有一个特性，使得用户可以在程序源语言的上下文，在源码级别跟踪和监测一个被调试的程序。这个功能依赖将一系列指令映射为在源文件的一行源代码的源文件和行数的调试符号。因为一个函数是占据连续内存空间的可执行代码的最小单元，源文件和行号调试符号记录着每个函数的开始和结束地址。当编译器将一行源代码翻译为一群机器指令，同时它也生成行号调试信息，用于跟踪对应这一行的指令地址。当多行源代码被编译器移来移去，它可能会变得复杂，用于提供程序的性能或者减少生成机器码的大小。 由一行源代码生柴恩指令可能在地址空间不是连续的。它们可能跟其他源代码行交织在一起。宏和内联函数使得境况变得更复杂。

- 类型信息

    类型调试符号描述了一个数据类型的数组和属性，要么是原始的数据，要么是其他数据的聚合。对于组合类型，调试符号包含每一个子字段的名字，大小和相对整个结构开头的偏移。一个子字段可以指向其他组合类型，而这些组合类型的调试符号在其他地方定义。调试需要一个对象的类型信息，从而能够在程序源码语言的形式打印它。否则，它会是内存内容的原始比特和字节。对于复杂的语言比如C++，这是特别有用的，因为为了实现语言的语义，编译器添加了隐藏的数据成员到数据对象里面。这些隐藏的数据成员是依赖编译器实现。检验对象内存值时，将它们从”真正“的数据成员区分开来非常困难。类型信息也包含了函数签名和其他的链接属性。

- 静态函数和局部变量

    跟全局符号相反，静态函数和局部变量仅仅在特定的作用域课件：一个文件，一个函数，或者一块被包围的块。一个局部变量仅仅在作用域存在和存在，所以说它是临时的。当线程的执行流出作用域，作用域的局部变量会被销毁和在语义上变得无效。基于局部变量在栈上分配或者跟容易失效的寄存器挂钩，它的存储位置在程序运行到这个作用域之前都是不可知的。因此，调试器仅仅可以在特定的作用域对变量进行观察、修改和设置断点，这有时是困难的。局部变量的调试符号包含作用域的信息，也包含局部变量的位置。作用域通常表示为指令的范围和位置表示为相对函数栈帧的偏移。

- 架构和编译器依赖信息

    一些调试功能是跟特定架构和编译器相关。举个例子，英特尔芯片的FPO (Frame Pointer Omission,栈指针省略)，微软Visual Studio的修改和运行，等等。




正如你可以想象的，从编译器向调试器通过调试符号传达所有的调试信息不简单。相对生成的机器代码，编译器生成许多调试符号，即使简单的程序也如此。因此，调试符号通常编码来减少大小。不幸的是，没有标准指明如何实现调试符号。编译器厂商因历史在不同的平台采用不太的调试符号格式。举个例子，Linux，Solaris和HP-UX现在使用 DWARF (Debugging with attributed Record Formats); AIX和老版本的Solaris使用stabs（symbol table string)；Windows有多种在用的格式，最受欢迎的时候程序数据库或者pdb。调试符号格式的文档通常要么难找要么不全。格式它自己也持续随着编译器新的发布而演进。在这之上，工具厂商在他们自己的编译器和调试器有各种拓展。
结果就是，在经常特定平台打包在一起的编译器和调试器，一个调试符号格式或多或少是秘密的协议。DWARF在这方面是比较好的，多亏开源社区。因此我将在接下来的章节里使用它来作为调试符号是怎么实现的例子。

## DWARF Format

DWARF像结构体一样以树的形式组织调试符号。这跟大部分语言内在也是树结构的词法作用域对应。每一个树节点是一个DIE (Debug information entry)，它带了特定的调试符号：一个对象，一个函数，一个源文件等等。一个结点可能具有任意数量的子结点或者兄弟结点。比如，一个函数DIE可能有很多代表函数局部变量的子DIEs。

我不会深入每一个基准DWARF格式和可以在线获取的细节。举个例子，在 http://www.dwarfstd.org有许多关于DWARF的论文，教程和形式化的文档。另外一个有效的方式是深入开源GNU编译器gcc和调试器gdb，他们采用DWARF.从调试的角度，知道调试符号是什么，它们是怎么组织的，和怎样在有兴趣的时候观察它们，是足够了。最好学习的方式大概是学习一个例子。让我们来看看在下面列出来的简单程序.

```c,editable
int gInt = 1;

int GlobalFunc(int i)
{
    return i+gInt;
}

```