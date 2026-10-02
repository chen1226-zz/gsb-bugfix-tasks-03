# 11031 · 退避重试

本目录是开源项目 `github.com/cenkalti/backoff/v7 ` 的源码快照（许可：MIT，见同目录 LICENSE，版权归原作者所有）。
为了能在离线环境直接构建，已去掉依赖外部模块的示例/用例，并补上 `go.mod`；其余源码保持上游原样。

**缺陷来源**：上游真实缺陷：反向应用上游修复提交 `61ba96c`（Fix data race when querying GetElapsedTime）与 `0337cbf`（do not block if there is no receiver）。

## 构建与自测

```
go build ./...
go test ./...
```
