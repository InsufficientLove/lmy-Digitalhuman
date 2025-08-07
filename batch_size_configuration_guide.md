# BatchSize 配置指南

## 配置方法

在 `appsettings.json` 中修改：

```json
"MuseTalk": {
  "BatchSize": 4,  // 根据您的GPU内存调整此值
  ...
}
```

## 推荐配置

基于您的错误信息分析：
- batch_size=6 需要 18.34GB
- 可用内存约 15GB

### 推荐值：

| GPU内存 | 推荐BatchSize | 预计内存使用 |
|---------|---------------|--------------|
| 24GB    | 4-5           | 12-15GB      |
| 16GB    | 3             | 9GB          |
| 12GB    | 2             | 6GB          |
| 8GB     | 1             | 3GB          |

### 计算公式：
- 每个batch约需要 3.06GB
- batch_size=4: 约12.2GB
- batch_size=5: 约15.3GB

## 调整步骤

1. 编辑 `appsettings.json`
2. 修改 `MuseTalk.BatchSize` 值
3. 保存文件
4. 重启应用程序

## 性能影响

- **BatchSize越大**：处理速度越快，但需要更多内存
- **BatchSize越小**：内存使用越少，但处理速度较慢

## 故障排除

如果仍然出现内存错误：

1. **降低BatchSize**
   ```json
   "BatchSize": 3
   ```

2. **检查GPU内存使用**
   ```cmd
   nvidia-smi
   ```

3. **查看实际内存需求**
   日志中会显示：`Tried to allocate XX.XX GiB`

4. **动态调整**
   - 如果显示需要18GB，而您只有15GB可用
   - 将BatchSize从6降到4或5

## 高级配置

如果需要更精细的控制，可以考虑：

1. **不同模板使用不同BatchSize**
2. **根据音频长度动态调整**
3. **根据GPU负载自动调整**

## 监控和优化

重启后观察日志：
- `批次大小: X (从配置读取)`
- `Latent batch shape: torch.Size([X, 8, 247, 164])`
- 确保X等于您配置的BatchSize

通过配置文件调整，您可以快速找到最适合您硬件的设置！