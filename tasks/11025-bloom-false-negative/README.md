# 11025 · 布隆过滤器

本目录是开源项目 `github.com/bits-and-blooms/bloom ` 的源码快照（许可：BSD-3-Clause，见同目录 LICENSE，版权归原作者所有）。
为了能在离线环境直接构建，已去掉依赖外部模块的示例/用例，并补上 `go.mod`；其余源码保持上游原样。

**缺陷来源**：上游原样（未注入）：该版本没有对 `Add`/`Test`/`Count` 做并发保护，多 goroutine 同时读写位图会产生数据竞争。

## 构建与自测

```
go build ./...
go test ./...
```
