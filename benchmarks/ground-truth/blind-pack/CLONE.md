# 如何拿到固定版本源码

需要安装 Git。在任意空目录执行：

```bash
git clone https://github.com/spring-projects/spring-petclinic.git spring-petclinic
cd spring-petclinic
git checkout 500158f732419217507c7656904b8e6aa1bcc0d6
```

然后核对：

`spring-petclinic/src/main/java/`

可用编辑器全局搜索类名（如 `OwnerController`、`VisitController`）。

没有 Git：告诉发包的人，让他另发该版本源码 zip。
