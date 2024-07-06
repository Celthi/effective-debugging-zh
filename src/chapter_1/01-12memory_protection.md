
# 更新
2024-07-05
本书已经出版
![image](https://github.com/Celthi/effective-debugging-zh/assets/5187962/29b04963-5535-432c-b56f-8a2d5dbc2ec6)
由于本库的草稿是我之前一个人写的，所以质量和正确性都不如经过两位作者和出版社编辑审阅和校正过的书稿。
如果你想阅读更加完善的版本，推荐购买正版书籍。
# 内存保护

在一些平台，如HP-UX，一个用户可能不能够在加载的共享库里面设置断点。理由是共享库默认被加载在公共可读的段。因此调试器不能够在代码段插入断点的陷入指令。为了改变这个默认行为，用户需要修改共享库加载的模式。下面的HP-UX命令在特定的模块设置一个标志位和指导系统运行把它们加载到私有的、可写的段中。
`chatr +dbg enable <modules>`

系统加载器也会获取下面的环境变量和加载所有的模块进入私有、可写的段。

`setenv _HP_DLDOPTS –text_private`

或者加载特定模块到私有、可写的段。
`setenv _HP_DLDOPTS –text_private=libfoo.sl;libbar.sl`

