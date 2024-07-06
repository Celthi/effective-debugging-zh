
# 更新
2024-07-05
本书已经出版
![image](https://github.com/Celthi/effective-debugging-zh/assets/5187962/29b04963-5535-432c-b56f-8a2d5dbc2ec6)
由于本库的草稿是我之前一个人写的，所以质量和正确性都不如经过两位作者和出版社编辑审阅和校正过的书稿。
如果你想阅读更加完善的版本，推荐购买正版书籍。
# 调试器的内在

大部分程序员通过实践学习怎样使用一个调试器。依赖于经验，一些人比另外一些人更熟悉调试器各种命令。但是只有一小部分知道调试器的内在结构。在本节中，我将从用户的视角讨论一些编译器的实现细节。这不仅仅是为了满足你对调试器魔法的好奇，也可能更重要的是帮助你更好地理解调试器，因而你知道最大优势地使用工具。

调试器仅仅是另外一个应用程序。有趣的是用户可以使用一个调试器跟踪另外一个调试器实例。这其实是一个学习调试器如何工作有效的方法。过去为了日常的调试工作，我编译了一个调试版本的gdb调试器。每当我有调试器本身的问题，我就会启动一个gdb并把它依附到另外一个活跃的gdb。这样子，我可以看到所有它的内在数据结构。


一个源代码级别的调试器通常有三个模块：用户界面，符号管理和目标处理。

用户界面是调试器的代表层，服务它的前端。它跟其他应用程序一样与用户交互。一个调试器可以有一个图形接口或者命令行接口，或者两者皆有。它的基本功能是将用户输入转换成后端调试引擎的API调用。几乎所有的菜单或者按钮都有到后端命令的直接映射。事实上，许多具有图形接口的调试器，像ldd（data display debugger)，Windbg和sunstudio，有一个让用户直接输入命令的目标调试器的命令行窗口。

符号管理负责提供目标的调试符号。这个模块读入二进制文件，然后解析文件里面的调试符号。它创建一个调试符号的内部表示和给打印变量提供类型信息。调试符号的可用性和它的内容决定了一个调试器可以为了你做什么。如果调试符号不对或者不全，那么调试器不能按预想的那样工作。比如，不匹配的文件（可执行文件或者程序数据库文件）拥有错误的调试符号；可执行文件的调试符号被去掉了或者没有pdb文件的DLLs或者具有公开（部分）的调试符号只会提供有限的调试能力。


在前面的章节，我们已经看到调试符号是怎么组织和存储在文件中的。开始，调试器按照给定的调试符号路径搜索文件，接着它检查文件的大小，时间戳，checksum等等，来验证与被调试进程加载的镜像文件的一致性。没有正确的匹配调试符号，一个调试器不能够正常的工作。比如，如果找到没有匹配的内核符号，Windows调试器Windbg会发出如下的警告信息，

```
Frames below may be incorrect and/or missing, no symbols loaded for msvcr80.dll]
msvcr80.dll!78138a04() 
msvcr80.dll!78138a8c() 
SHSMP.DLL!_MemFreePtr@4()  + 0x4b bytes 
SHSMP.DLL!_shi_free1()  + 0x1c bytes 
SHSMP.DLL!_shi_free()  + 0xa bytes 
M8Log2.dll!std::allocator<MBase::SmartPtrI<MLog::Destination> >::deallocate(MBase::SmartPtrI<MLog::Destination> * _Ptr=0x01a51638, unsigned int __formal=2)  Line 141 + 0x9 bytes C++ 
M8Log2.dll!MLog::Dispatcher_Impl::LogMessage(const MLog::Logger & iLogger={...}, const char * iMessageText=0x00770010, unsigned int iMessageID=8)  Line 78 + 0x1c bytes      C++

```
注意属于系统运行库msvcr80.dll的前两个帧。此时Windbg抱怨没有找到这个DLL的调试符号。优化的代码想系统库默认打开了FPO编译器选项。因此，一个调试器需要FPO调试符号来成功回卷调用栈。否则，一个用户可能看到不合逻辑的调用栈。在这个特别的案子了，我们可以设置Windbg从微软在线调试符号网址下载系统库的公开调试符号。稍后我会简单讨论Windows符号服务器。

如果调试符号匹配了，那么调试器的符号管理就会打开文件和从前面描述的文件的各个调试section或者单独的数据库来读入调试符号。调试符号被解析用来创建一个内部表示。但是，调试器通常为了避免在启动时消耗太多时间和空间，不会一次性读入所有的调试符号。有些信息，比如行号表和基准栈信息表是在他们需要的时候创建。初始时，它仅仅扫描文件来快速的找到基本信息如源文件和当前作用域的符号。当一个用户执行一个需要详细的调试符号（如打印变量）的命令，调试器会按需的从对应的文件读入详细的调试符号。有趣地是，gdb的符号加载命令的“-readnow”选项允许用户覆盖这个两阶段符号读入策略。

目标处理模块在系统和硬件层面处理被调试的进程，也就是，debugee。比如，它控制debugee的运行，读写debugee的内存，获取一个线程的调用栈等等。因为底层的操作，它是平台相关的。在Linux，含许多其他的UNIX变化，内核提供了一个系统调用`ptrace`使得一个进程，调试器或者其他工具像系统调用跟踪器strace，查询和控制另外一个进程debugee的运行。Linux使用信号来同步调试器和debugee。系统服务，ptrace支持下面的功能：

- 依附和不依附一个进程。被跟踪的进程被依附时，会收到一个SIGTRAP或者SIGSTOP信号。

- 读写debugee的地址空间含文本和数据段的内存内容。

- 查询和修改debugee的进程用户区域。比如，寄存器和其他信息。

- 查询和修改debugee的信号信息和设置如等待信号和忽略信号等等。

- 设置时间触发器。比如，当系统API fork、clone、exec等等被调用的时候或者debugee进程退出的时候停止debugee。

- 控制debugee的运行。比如，让它从一个停止的状态继续运行。debugee可以在下一个系统调用停止或者单步进入下一个指令。

- 发送各种信号如SIGKIL信号到debugee来结束进程。

这些内核服务提供了实现各种调试器特性的基础。稍后我们将以断点为例子。`ptrace`的原型声明在头文件`sys/ptrace.h`里。它有四个参数。第一个参数是一个类型为`__ptrace_request`指定内核支持的服务，支持的服务在文件被清楚的说明。第二个参数是debugee的进程id。第三个参数是debugee地址空间里将被读写的内存地址。最后一个参数是将被读写的字的缓冲。

```
/* Type of the REQUEST argument to `ptrace.'  */
enum __ptrace_request
{
  /* Indicate that the process making this request should be traced. */
  PTRACE_TRACEME = 0,

  /* Return the word in the process's text space at address addr.  */
  PTRACE_PEEKTEXT = 1,

  /* Return the word in the process's data space at address addr.  */
  PTRACE_PEEKDATA = 2,

  /* Return the word in the process's user area at offset addr.  */
  PTRACE_PEEKUSER = 3,

  /* Write the word data into the process's text space at address addr. */
  PTRACE_POKETEXT = 4,

  /* Write the word data into the process's data space at address addr. */
  PTRACE_POKEDATA = 5,

  /* Write the word data into the process's user area at offset addr.  */
  PTRACE_POKEUSER = 6,

  /* Continue the process.  */
  PTRACE_CONT = 7,

  /* Kill the process.  */
  PTRACE_KILL = 8,

  /* Single step the process.  */
  PTRACE_SINGLESTEP = 9,

  /* Get all general purpose registers used by a processes.  */
   PTRACE_GETREGS = 12,

  /* Set all general purpose registers used by a processes. */
   PTRACE_SETREGS = 13,

  ...

  /* Set ptrace filter options.  */
  PTRACE_SETOPTIONS = 0x4200,

  /* Get last ptrace message.  */
  PTRACE_GETEVENTMSG = 0x4201,
};

/* Perform process tracing functions.  REQUEST is one of the values
   above, and determines the action to be taken.  */
long ptrace (enum __ptrace_request request, pid_t pid, void *addr, void *data);

```

作为一个例子，下面的`strace`命令打印调试器gdb调用的所有`ptrace`调用。这个调试器进程有一个简单的调试会话。程序`a.out`做什么不重要。我们只对调试器的操作感兴趣。这里gdb在测试程序的入口函数main设置了一个断点，接着运行这个程序。等程序完成以后，gdb也退出了这个会话。系统调用跟踪程序打印了许多`ptrace`调用。这个列出的摘取简单地强调了gdb底层的实现。

```
$ strace –o/home/myan/ptrace.log –eptrace gdb a.out

 (gdb) break main
Breakpoint 1 at 0x400590: file foo.cpp, line 12.
(gdb) run
Starting program: /home/myan/a.out

Breakpoint 1, main () at foo.cpp:12
12              int* ip = new int;
(gdb) cont
Continuing.

Program exited normally.
(gdb) quit

$ cat /home/myan/ptrace.log
ptrace(PTRACE_GETREGS, 28361, 0, 0x7fbfffe650) = 0
ptrace(PTRACE_PEEKUSER, 28361, offsetof(struct user, u_debugreg) + 48, [0]) = 0
ptrace(PTRACE_CONT, 28361, 0x1, SIG_0)  = 0
--- SIGCHLD (Child exited) @ 0 (0) ---
ptrace(PTRACE_GETREGS, 28361, 0, 0x7fbfffe650) = 0
ptrace(PTRACE_PEEKUSER, 28361, offsetof(struct user, u_debugreg) + 48, [0]) = 0
ptrace(PTRACE_SETOPTIONS, 28361, 0, 0x2) = 0
ptrace(PTRACE_SETOPTIONS, 28366, 0, 0x2) = 0
ptrace(PTRACE_SETOPTIONS, 28366, 0, 0x22) = 0
ptrace(PTRACE_CONT, 28366, 0, SIG_0)    = 0
--- SIGCHLD (Child exited) @ 0 (0) ---
ptrace(PTRACE_GETEVENTMSG, 28366, 0, 0x7fbfffeb90) = 0
ptrace(PTRACE_SETOPTIONS, 28361, 0, 0x3e) = 0
ptrace(PTRACE_PEEKTEXT, 28361, 0x5007e0, [0x1]) = 0
ptrace(PTRACE_PEEKTEXT, 28361, 0x5007e8, [0x1]) = 0
...
==>ptrace(PTRACE_PEEKTEXT, 28361, 0x400590, [0xff06e800000004bf]) = 0
==>ptrace(PTRACE_POKEDATA, 28361, 0x400590, 0xff06e800000004cc) = 0
ptrace(PTRACE_PEEKTEXT, 28361, 0x36a550b830, [0x909090909090c3f3]) = 0
ptrace(PTRACE_PEEKTEXT, 28361, 0x36a550b830, [0x909090909090c3f3]) = 0
ptrace(PTRACE_POKEDATA, 28361, 0x36a550b830, 0x909090909090c3cc) = 0
ptrace(PTRACE_CONT, 28361, 0x1, SIG_0)  = 0
--- SIGCHLD (Child exited) @ 0 (0) ---
ptrace(PTRACE_GETREGS, 28361, 0, 0x7fbfffe750) = 0
ptrace(PTRACE_GETREGS, 28361, 0, 0x7fbfffe790) = 0
ptrace(PTRACE_SETREGS, 28361, 0, 0x7fbfffe790) = 0
ptrace(PTRACE_PEEKUSER, 28361, offsetof(struct user, u_debugreg) + 48, [0]) = 0
==>ptrace(PTRACE_PEEKTEXT, 28361, 0x400590, [0xff06e800000004cc]) = 0
==>ptrace(PTRACE_POKEDATA, 28361, 0x400590, 0xff06e800000004bf) = 0
ptrace(PTRACE_PEEKTEXT, 28361, 0x36a550b830, [0x909090909090c3cc]) = 0
ptrace(PTRACE_POKEDATA, 28361, 0x36a550b830, 0x909090909090c3f3) = 0
ptrace(PTRACE_PEEKTEXT, 28361, 0x5007e0, [0x1]) = 0
...
ptrace(PTRACE_PEEKTEXT, 28361, 0x400588, [0x10ec8348e5894855]) = 0
==>ptrace(PTRACE_SINGLESTEP, 28361, 0x1, SIG_0) = 0
--- SIGCHLD (Child exited) @ 0 (0) ---
ptrace(PTRACE_GETREGS, 28361, 0, 0x7fbfffe750) = 0
ptrace(PTRACE_PEEKUSER, 28361, offsetof(struct user, u_debugreg) + 48, [0xffff4ff0]) = 0
==>ptrace(PTRACE_PEEKTEXT, 28361, 0x400590, [0xff06e800000004bf]) = 0
==>ptrace(PTRACE_POKEDATA, 28361, 0x400590, 0xff06e800000004cc) = 0
ptrace(PTRACE_PEEKTEXT, 28361, 0x36a550b830, [0x909090909090c3f3]) = 0
ptrace(PTRACE_PEEKTEXT, 28361, 0x36a550b830, [0x909090909090c3f3]) = 0
ptrace(PTRACE_POKEDATA, 28361, 0x36a550b830, 0x909090909090c3cc) = 0
ptrace(PTRACE_CONT, 28361, 0x1, SIG_0)  = 0

```

如上显示，gdb通过`PTRACE_GETREGS`和`PTRACE_SETREGS`请求来查询和修改debugee的上下文，通过`PTRACE_PEEKTEXT`和`PTRACE_POKETEXT`请求来读取和写入debugee的内存，以及其他更多的操作。当有事件发生时内核通过SIGCHLD信号来停止debugger。(??)


让我们来更近一点的查看断点是怎么实现的。从gdb的控制台，我们知道断点设在了函数`main`的地址`0x400590`。调试器首先读入地址`0x400590`的代码，即`{0xbf 0x04 0x00 0x00 0x00 0xe8 0x06 0xff}`，注意x86_64架构是小端。接着gdb通过`PTRACE_POKEDATA`请求来修改代码。对比读入的数据`0xff06e800000004bf`，写入的值`0xff06e800000004cc`仅仅改变了第一个字节，从`0xbf`改成`0xcc`。`0xcc`是陷入指令（特殊的中断指令）。这个操作在debugee的代码段设置了断点。之后gdb通过`PTRACE_CONT`来继续运行debugee。当程序在执行在地址`0x400590`的指令`0xcc`是，会碰到断点，它会被内核陷入和停止。内核在检查它的状态比特以后，会意识到它被跟踪了。因此它会发送信号到调试器。gdb在它的用户接口显示这个信息并等待用户涮涮下一跳命令来执行。在这个例子中，我们决定继续运行程序。为了虔诚地按照debugee的程序逻辑，gdb恢复在地址0x400590原来的指令`0xbf`和通过`PTRACE_SINGLESTEP`请求内核执行一个指令。在单独进入执行以后，调试器会再次插入陷入指令`0xcc`，为的是在将来能够触发断点除非这是一个一次性的断点。它通过`PTRACE_CONT`请求继续程序的运行。


从最高的维度看，调试器跑着一个循环，等待着debugee发生的事件或者是用户中断。当debugee碰到一件事件和停止下来后，内核通过发送一个信号来告知调试器。调试器接着查询和检查事件。取决于它的本性，它会采取适当的措施。





