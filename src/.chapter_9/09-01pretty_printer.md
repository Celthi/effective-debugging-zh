# 美化输出


## 将难看的数据变得好看
以下面的代码为例
```c++
#include <map>
#include <iostream>
#include <string>
using namespace  std;

int main() {
    std::map<string, string> lm;
    lm["good"] = "heart";
    // 查看map 里面内容
    std::cout<<lm["good"];
}
```
当代码运行到std<<cout时, 你想查看map里面的内容，如果没有python和自定义的脚本，print lm看到的是
```
$2 = {_M_t = {
    _M_impl = {<std::allocator<std::_Rb_tree_node<std::pair<std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const, std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > > > >> = {<__gnu_cxx::new_allocator<std::_Rb_tree_node<std::pair<std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const, std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > > > >> = {<No data fields>}, <No data fields>}, <std::_Rb_tree_key_compare<std::less<std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > > >> = {
        _M_key_compare = {<std::binary_function<std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> >, std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> >, bool>> = {<No data fields>}, <No data fields>}}, <std::_Rb_tree_header> = {_M_header = {
          _M_color = std::_S_red, _M_parent = 0x55555556eeb0, 
          _M_left = 0x55555556eeb0, _M_right = 0x55555556eeb0}, 
        _M_node_count = 1}, <No data fields>}}}
```
但是当你在gdb9.2里面输入print lm的时候，你看到的将是
```
(gdb) p lm
$3 = std::map with 1 element = {["good"] = "heart"}
```
map里面有什么一清二楚。这是因为gdb9.x自带了一系列标准库的Python pretty priniter。 如果你使用的是gdb7.x，那么你可以手动的导入这些pretty printer实现同样的效果。具体步骤如下：

1. 下载pretty printer: svn co svn://gcc.gnu.org/svn/gcc/trunk/libstdc++-v3/python
2. 在gdb里面输入(将路径改成你下载的路径)：
    ```
    python
    import sys
    sys.path.insert(0, '/home/maude/gdb_printers/python')
    from libstdcxx.v6.printers import register_libstdcxx_printers
    register_libstdcxx_printers (None)
    end
    ```
这样你就可以放心使用了~
详细请看：
https://sourceware.org/gdb/wiki/STLSupport
https://codeyarns.com/2014/07/17/how-to-enable-pretty-printing-for-stl-in-gdb/
