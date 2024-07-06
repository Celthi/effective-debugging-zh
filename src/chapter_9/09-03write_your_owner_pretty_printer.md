
# 更新
2024-07-05
本书已经出版
![image](https://github.com/Celthi/effective-debugging-zh/assets/5187962/29b04963-5535-432c-b56f-8a2d5dbc2ec6)
由于本库的草稿是我之前一个人写的，所以质量和正确性都不如经过两位作者和出版社编辑审阅和校正过的书稿。
如果你想阅读更加完善的版本，推荐购买正版书籍。
# 编写你自己的美化器
前言
在CrackingOysters：你还在用GDB调试程序吗？介绍了使用Python拓展gdb方便平时的debug体验。
其中的一项功能是pretty printer。本文详细介绍编写pretty printer，用于打印自己的数据结构。
比如你有一个结构体很多数据成员，
```c++
struct MyStruct {
  std::name mName;
  std::map mField1;
  std::set mField2;
  int mI;
  int mj;
};
```
但是你大部分时候打印都是只看字段mName和mI，那么就可以定义一个针对这个数据结构的pretty printer，这样大部分时候你就只看到需要的字段。而不用在几十个字段找你所关心。
如果不使用任何的pretty printer，打印一个MyStruct的数据结构会得到
```
$2 = {mName = {static npos = <optimized out>, 
    _M_dataplus = {<std::allocator<char>> = {<__gnu_cxx::new_allocator<char>> = {<No data fields>}, <No data fields>}, 
      _M_p = 0x618c38 "student"}}, mField1 = {_M_t = {
      _M_impl = {<std::allocator<std::_Rb_tree_node<std::pair<int const, std::basic_string<char, std::char_traits<char>, std::allocator<char> > > > >> = {<__gnu_cxx::new_allocator<std::_Rb_tree_node<std::pair<int const, std::basic_string<char, std::char_traits<char>, std::allocator<char> > > > >> = {<No data fields>}, <No data fields>}, <std::_Rb_tree_key_compare<std::less<int> >> = {
          _M_key_compare = {<std::binary_function<int, int, bool>> = {<No data fields>}, <No data fields>}}, <std::_Rb_tree_header> = {
          _M_header = {_M_color = std::_S_red, _M_parent = 0x0, _M_left = 0x7fffffffe4e0, _M_right = 0x7fffffffe4e0}, 
          _M_node_count = 0}, <No data fields>}}}, mField2 = {_M_t = {
      _M_impl = {<std::allocator<std::_Rb_tree_node<std::basic_string<char, std::char_traits<char>, std::allocator<char> > > >> = {<__gnu_cxx::new_allocator<std::_Rb_tree_node<std::basic_string<char, std::char_traits<char>, std::allocator<char> > > >> = {<No data fields>}, <No data fields>}, <std::_Rb_tree_key_compare<std::less<std::basic_string<char, std::char_traits<char>, std::allocator<char> > > >> = {
          _M_key_compare = {<std::binary_function<std::basic_string<char, std::char_traits<char>, std::allocator<char> >, std::basic_string<char, std::char_traits<char>, std::allocator<char> >, bool>> = {<No data fields>}, <No data fields>}}, <std::_Rb_tree_header> = {_M_header = {
            _M_color = std::_S_red, _M_parent = 0x0, _M_left = 0x7fffffffe510, _M_right = 0x7fffffffe510}, 
          _M_node_count = 0}, <No data fields>}}}, mI = 3, mj = 4}
```
看起来会头皮发麻！
如果使用gdb 自带的STL pretty printer,那么我们会得到如下简洁的结果，
```
(gdb) p s
$1 = {mName = "student", mField1 = std::map with 0 elements, mField2 = std::set with 0 elements, mI = 3, mj = 4}\
```
如果自己编写pretty printer，那么就会得到如下的结果，
```
(gdb) p s
$2 = MyStruct
 name: "student"  integer: 3
 ```

这样子，只会打印自己关心的数据，如果希望看看原始的数据，那么p /r s 
整体思路
需要做的是三件事情：
定义打印类，提供to_string()方法，这个方法返回你要打印出来的字符串。
判断一个value，是否需要使用你定义的类来打印。
注册你的判断函数到gdb pretty printing里面
定义打印类

```python
class MyPrinter:
    def __init__(self, val):
        self.val = val
    def to_string(self):
         return ”name: {}  integer: {}".format(self.val['mName'], self.val['mI']
```
判断一个value，是否需要使用自己定义的打印类
```python
def lookup_pretty_printer(val):
    if val.type.code == gdb.TYPE_CODE_PTR:
        return None # to add 
    if 'MyStruct' == val.type.tag:
        return MyPrinter(val)
    return None
```

注册到gdb

```python
gdb.printing.register_pretty_printer(
    gdb.current_objfile(),
    lookup_pretty_printer, replace=True)
```

将下面的程序编译，并测试
```c++
struct MyStruct {
  std::string mName;
  std::map<int, std::string> mField1;
  std::set<std::string> mField2;
  int mI;
  int mj;
};

int main() {
   MyStruct s = {std::string("student"), lm, ls, 3, 4}
   return 0;
}
```
