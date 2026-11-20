# 判定口径（请严格遵守）

固定版本：`500158f732419217507c7656904b8e6aa1bcc0d6`

| 问题 | 本轮规定 |
| --- | --- |
| 看哪些代码 | 只看 **`src/main/java`** |
| 测试代码 `src/test` | **不算** Direct / Indirect |
| 方法**参数、返回类型**里出现的类型 | **算**（uses_type） |
| 只在方法**方法体局部变量**里出现的类型 | **不算** uses_type |
| 泛型参数，如 `Page<Vet>`、`List<Owner>` | **不算** |
| `Person.class` 这类 class 字面量 | **不算** |
| Direct | 构造器注入、extends、implements、方法签名上的类型使用 |
| Indirect（仅 h_impact_person） | Person 的子类为 Owner / Vet；生产代码里谁在**方法签名**使用了这些子类，谁算 Indirect |

`h_impact_*_repository`：只列生产代码里的注入点，不要列测试类。

提示：看方法时请认准「括号里的参数类型 / 返回类型」，不要只扫方法体。
