# 内存保护
在一些平台，如HP-UX，一个用户可能不能够在加载的共享库里面设置断点。理由是共享库默认被加载在公共可读的段。因此调试器不能够在代码段插入断点的陷入指令。为了改变这个默认行为，用户需要修改共享库加载的模式。下面的HP-UX命令在特定的模块设置一个标志位和指导系统运行把它们加载到私有的、可写的段中。
`chatr +dbg enable <modules>`

系统加载器也会获取下面的环境变量和加载所有的模块进入私有、可写的段。

`setenv _HP_DLDOPTS –text_private`

或者加载特定模块到私有、可写的段。
`setenv _HP_DLDOPTS –text_private=libfoo.sl;libbar.sl`

