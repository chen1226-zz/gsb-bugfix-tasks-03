# 11030 · 磁盘队列

本目录是开源项目 `github.com/nsqio/go-diskqueue ` 的源码快照（许可：MIT，见同目录 LICENSE，版权归原作者所有）。
为了能在离线环境直接构建，已去掉依赖外部模块的示例/用例，并补上 `go.mod`；其余源码保持上游原样。

**缺陷来源**：注入（标注）：轮转到新文件时去掉了那次 `sync()`，元数据不再随轮转落盘。

为避免仓库里直接出现失败用例，上游 `diskqueue_test.go` 中会直接暴露该缺陷的 `TestWriteRollReadEOF` 已移除。

## 构建与自测

```
go build ./...
go test ./...
```
