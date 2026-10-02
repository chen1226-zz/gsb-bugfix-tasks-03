# 11032 · 批处理

本目录是开源项目 `github.com/eapache/go-resiliency ` 的源码快照（许可：MIT，见同目录 LICENSE，版权归原作者所有）。
为了能在离线环境直接构建，已去掉依赖外部模块的示例/用例，并补上 `go.mod`；其余源码保持上游原样。

**缺陷来源**：上游真实缺陷：直接采用上游修复提交 `8652ab4`（Refactor batcher to fix race issues）的父提交 `18a6173` 的 `batcher/batcher.go`。

## 构建与自测

```
go build ./...
go test ./...
```
