## scripter for [sendo erika](https://github.com/cleoold/sendo-erika) on [NoneBot](https://github.com/richardchien/nonebot)
![Python](https://img.shields.io/badge/python-3.7%2B-blue.svg)
<hr />

某天突发奇想，然后就写出了这个插件的雏形。这个插件可以在聊天窗口控制 Nonebot 群聊机器人来发送消息。目前还仅支持延时发送。您可以通过本文档快速学习它的用法（这个插件相当于一个远程 `eval`）：

### 样例
```py
    script
    speak "开始计时"
    wait 10
    speak "十秒钟到！"

[00:00:01]开始计时
[00:00:11]十秒钟到！
```

### 安装
只需要把文件夹复制粘贴到 `plugin` 中就可以了。

### 使用
群成员可以在群聊中直接发送
```py
    script
    [代码]
```
来操作机器人，在此情况下会有消息数目，持续时间和冷却的限制。此时机器人直接将消息发送到当前的群。超级用户可以在私聊窗口里发送
```py
    scriptto 12345678
    [代码]
```
来把消息发送到特定的群 12345678 里。

#### 还不支持...
条件，表达式，等等……如果要实现可能要推翻现在已有的进展……目前的主要目的是延时发送消息。

#### 数据类型
和 宿主机 Python 的 __整形__ 和 __字符串__ 相同。

#### 关键字
插件会顺序解释脚本的关键字并且把行为推入事件队列，最后按照这个顺序发送消息。

*   __`speak "a string literal"`__
    机器人会发送消息到目前的 session，其中字符串必须由一对双引号包围。
    例子：
    ```py
        script
        speak "hello world"

    [00:00:01]hello world
    ```
*   __`wait some_int`__
    机器人会在此暂停 some_int 秒再执行下一步操作。
    例子：
    ```py
        script
        wait 5
        speak "hello world"

    [00:00:05]hello world
    ```

*   __`setv var_name = some_value`__
    定义一个变量（大多数是字符串）将 some_value 的内容赋予 var_name 中。
    例子：
    ```py
        script
        setv msg = "hello"
        setv delay = 5
        speak msg
        wait delay
        speak msg

    [00:00:01]hello
    [00:00:05]hello
    ```
    例子（覆盖变量）：
    ```py
        script
        setv x = "hello"
        setv x = "henlo"
        speak x
    
    [00:00:01]henlo
    ```

*   __`unsetv var_name`__
    虽然这可能不是必要的，但是这样会删除一个变量并且使之不可引用。
    （如果遇到了 bug 删除变量会可能有用？）
    例子：
    ```py
        script
        setv x = "a"
        unsetv x
        speak x

    [00:00:01]ERROR: x is not defined. --TERMINAING
    ```

*   `...`
    处理相关关键字的函数都颇为相似，在类定义里复制你的命令，再把实现函数传入到 `EvalGrammar` 对象的字典就好，可参考 `speak`。

That's almost it! 这就是本插件的大多数功能了。以后就可以延时控制机器人说话了。

#### 关键字（自增）
*   __`setv var_name + amt`__
    也支持 `-` 和 `*`。可以把 `var_name` 的值增加 `amt`。
    例子（没有表达式的妥协）：
    ```py
        script
        setv a = 10
        setv a + 5
        setv a * 2
        setv a - 2
        speak a

    [00:00:01]28
    ```

*   __`setv var_name \+ amt`__
    在普通算符前面加上斜杠表示交换两个值之间的运算顺序
    例子：
    ```py
        script
        setv a = "|||"
        setv a + "]]]"
        setv a \+ "[[["
        speak a

    [00:00:01][[[|||]]]
    ```
    例子（减法没有交换律）：
    ```py
        script
        setv x = 3
        setv y = x
        setv x - 10
        setv y \- 10
        speak x; speak y

    [00:00:01]-7
    [00:00:01]7
    ```


#### 关键字（控制）

*   __`loop`__
    可以重复地执行某段代码片段。在开始时会创建覆写一个变量，需要注意。
    例子（每隔 10 秒发送一条消息，发送 3 次）：
    ```py
        script
        loop setv i = 1 to 4 that
            setv temp = "hi"
            setv temp * i
            speak temp
            wait 10
        endloop

    [00:00:01]hi
    [00:00:11]hihi
    [00:00:21]hihihi
    ```
    例子（可选步长）：
    ```py
        script
        setv r = ""
        loop setv i = 0 to 100 step 5 that
            setv r + i
            setv r + " "
        endloop
        speak r

    [00:00:01]0 5 10 15 20 25 30 35 40 45 50 55 60 65 70 75 80 85 90 95 
    ```
    默认设置只允许嵌套两层循环。
    例子（笨办法打印一个乘法表）：
    ```py
        script:
        setv sum = ""
        loop setv i = 0 to 10 that 
            loop setv j = 0 to i that
                setv jj = j 
                setv jj + 1
                setv v = i
                setv v * jj

                setv sum + jj
                setv sum + "*"
                setv sum + i
                setv sum + "="
                setv sum + v
                setv sum + "   "
            endloop
            setv sum + "\n"
        endloop 
        speak sum

    
    [00:00:01]1*1=1   
    1*2=2   2*2=4   
    1*3=3   2*3=6   3*3=9   
    1*4=4   2*4=8   3*4=12   4*4=16   
    1*5=5   2*5=10   3*5=15   4*5=20   5*5=25   
    1*6=6   2*6=12   3*6=18   4*6=24   5*6=30   6*6=36   
    1*7=7   2*7=14   3*7=21   4*7=28   5*7=35   6*7=42   7*7=49   
    1*8=8   2*8=16   3*8=24   4*8=32   5*8=40   6*8=48   7*8=56   8*8=64   
    1*9=9   2*9=18   3*9=27   4*9=36   5*9=45   6*9=54   7*9=63   8*9=72  9*9=81

    ```

#### features coming in their way

### License
MIT
