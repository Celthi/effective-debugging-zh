# 更新
2023-12-20
本书已经出版
![image](https://github.com/Celthi/effective-debugging-zh/assets/5187962/29b04963-5535-432c-b56f-8a2d5dbc2ec6)

书里的序言二说明了书和这个repo的关系，也可见[高效C/C++调试](https://zhuanlan.zhihu.com/p/675726977)

> 在编程的道路上，每一个程序员都不可避免地遇到调试的挑战。我仍然记得那些难忘的调试 经历；大学时期，我和朋友共同调试机器人的程序；进入职场后，我又开始钻研数百万行的 C++代 码。从初入编程世界时的探索与迷茫，到如今的稳健与沉稳。这背后蕴含着无数次的学习与实践。 更为关键的是，得益于站在诸多行业前辈的肩膀上。而本书的首作者 Michael，正是其中一位令人 尊敬的巨人。幸运的是，我在美国工作期间，有幸得到他的直接指导和悉心帮助。
当清华大学的编辑联系我，询问是否有兴趣出版书籍时，我想到了从学生时代到职场的点滴 经验。我常常与同学或者同事分享自己的体会，也在知乎账号(CrackingOysters1)上发表相关文章。 但要整理成一本完整的书籍，仍有不少工作要做。这时，我想到了 Michael 以及他那份关于高效调 试的英文书稿。于是，我建议我们基于这份书稿，共同打造一本新的书籍。因此，本书中绝大部 分的内容都深受他的经验智慧所启发，同时我也主要增添了关于 Google Address Sanitzer 和逆向调 试的章节、第 9 章以及第 12-18 章的内容。
希望这本书能为编程爱好者提供实用的知识和启示。如果你在书中发现了错误，欢迎指正。 我乐于分享我的学习体会，是因为总有热心的朋友愿意纠正我。另一方面，你所认为的"错误"可能 只是知识理解的不同，在讨论中可以加深或者修正理解。
# 译者注

_Effective Debugging_ by [Michael Yan](https://github.com/yanqi27)，讲述了如何更有效率地调试大型程序（以C/C++为例）的方法和技能。书中例子不仅丰富而且都是从实际的工作经验提取，观点和方法有效且具有可行性。

涉及的话题有：

- 调试符号
- 内存管理器数据结构
- 如何调试内存损坏bug
- C/C++对象布局
- 如何拓展调试器
- 优化后的程序怎么调试
- 进程镜像
- 等等


我自己读了以后，受益匪浅，萌生了翻译成中文的想法。经过Michael的同意，于是开始了断断续续地翻译，在这个过程中，学到了许多，也加深了理解。

本书都是我自己理解了以后的翻译，并对书中原来使用gdb脚本程序编写的插件，使用了最新的[core analyzer](https://github.com/yanqi27/core_analyzer)作了替换（如果可以替换的话）。因为core analyzer是Michael通过改造gdb将书中的点子变成了gdb的命令，使用更方便以及更强大。

在线阅读网址：https://celthi.github.io/effective-debugging-zh/

有些是我自己的理解，标记开头为XT，如，

XT: 举个例子可能会更好理解，如果申请32字节，那么返回的内存块的地址必须是可以整除32

限于本人水平，错误难免，请大家不吝赐教，或者提PR.

## 关于作者

http://core-analyzer.sourceforge.net/index_files/Page525.html

## 关于译者

https://www.zhihu.com/people/lan-tian-89

## 一些说明

- 有一些暂时找不到跟英文对应的词语，要么保留英文词，如bug；要么我根据自己的理解选了词，如unwind callstack，回卷调用栈。如果有更好的翻译，请不吝赐教。

- 如果有一些内容我不理解，我在翻译的附近标上(??)，提示可能翻译错误，方便日后推敲再次翻译。

- 可能会添加一些章节，因为现在新的调试技术的出现，目前计划是使用Python拓展gdb，以及Linux的符号服务器debuginfod。


## License

如果商业用途，请联系译者和原作者。
