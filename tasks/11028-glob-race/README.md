# 11028 · 通配符匹配

本目录是开源项目 `github.com/gobwas/glob ` 的源码快照（许可：MIT，见同目录 LICENSE，版权归原作者所有）。
为了能在离线环境直接构建，已去掉依赖外部模块的示例/用例，并补上 `go.mod`；其余源码保持上游原样。

**缺陷来源**：注入（标注）：在 `Compile` 里加了一个无锁的包级缓存，并发编译会同时读写同一个 map。

为避免仓库里直接出现失败用例，上游 `glob_test.go` 中与缓存别名行为相冲突的 `TestPatternSeparatorsAliasing` 已移除。

## 构建与自测

```
go build ./...
go test ./...
```
