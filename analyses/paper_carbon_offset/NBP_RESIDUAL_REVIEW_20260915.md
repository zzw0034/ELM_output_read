# NBP 残差、累计碳汇和文献基准：源码核对

2026-09-22 阅读说明：本文保留历史核算审查及随后重算记录。第 1 节“当前脚本”
描述修正前状态，现有脚本已使用完整 fire 的反推恒等式；最新论文结构见
[MANUSCRIPT_BLUEPRINT.md](MANUSCRIPT_BLUEPRINT.md)。这些数值属于当时的
case 组合，不是新版/参数敏感性结果。该 NBP 漏项与尚未闭合的 stock-pool
残差是两个不同问题。

2026-09-15，Codex。回应用户提供的 Claude 问答。仅做本地阅读、文献核对和 Pathfinder 只读源码/NetCDF header 检查；没有重算全年域总量，也没有提交作业或修改远端文件。

## 1. 明确找到的漏项

当前 `check_nbp_decline_decomposition.py` 用：

```text
NBP_reconstructed = NEP - PFT_FIRE_CLOSS - LAND_USE_FLUX
```

但实际源码的定义为：

```text
NBP = NEP - fire_closs_col - dwt_closs_col - product_closs_col
LAND_USE_FLUX = dwt_closs_col + product_closs_col
fire_closs_col = fire_closs_p2c_col
              + sum_over_pools_and_depth(m_decomp_cpools_to_fire_vr * layer_thickness)
```

`fire_closs_p2c_col` 是 patch-level fire loss 聚合到 column 的结果。`FireMod.F90` 中分解池燃烧项对 litter 和 CWD 赋非零值：litter 使用烧毁面积率与 0.5 燃烧系数，CWD 使用扣除 crop burning 部分的面积率与 0.25 系数。这是燃烧碳输出，不是燃烧后进入 litter/CWD 的死亡生物量转移。

**因此，现有分解确定漏掉了凋落物和粗木质残体燃烧。** 在空间掩膜、权重、时间平均和字段映射一致的条件下：

```text
NBP_native - NBP_reconstructed = - omitted_decomposing_pool_fire_loss
```

用户报告 native NBP 小于 reconstructed，与这个漏项的符号一致。没有必要先猜 truncation、初始化漂移或质量守恒错误。不过，本次尚未逐年逐格数值验证，不声称已证明该漏项恰好解释每一个报告残差。

### 证据位置和版本

远端源码根：`/projects/hpcl-cli185/proj-shared/zw5/E3SM`。

- 当前 HEAD：`17efedae5f057782397e1a026cee40ff776f90ab`；检查时 `git status --short` 无输出。
- SSP3-7.0 0.5° case 的 `env_case.xml` SRCROOT 指向同一目录，`SourceMods/src.elm` 仅有 README。
- 该 case 的 2100 h0 文件记录 `source_id=45d413e7aa`。对下列四个文件比较该版本与 HEAD，`git diff --stat` 无输出；不是把当前上游任意版本当作运行版本。
- `components/elm/src/biogeochem/CNCarbonFluxType.F90:1954`：patch fire loss 的 p2c 聚合；`:2140` 附近：分解池火灾损失的垂直积分；`:2154`：完整 column fire loss；`:2172`：NBP；`:2179` 附近：NEE；`:2188`：LAND_USE_FLUX。
- `components/elm/src/biogeochem/FireMod.F90:1380`–1410：litter/CWD 燃烧项。
- `components/elm/src/data_types/ColumnDataType.F90:6686`：COL_FIRE_CLOSS 注册为 ptr_col，默认 inactive；紧随其后注册 DECOMP_FIRE_CLOSS，也默认 inactive。
- 同文件 `:7589` 附近实际计算完整 fire_closs，`:7608` 计算 NBP，随后计算 NEE 和 LAND_USE_FLUX；与上面 CNCarbonFluxType 的公式一致，已交叉核对。
- `components/elm/src/data_types/VegetationDataType.F90:6654`：PFT_FIRE_CLOSS 注册为 ptr_patch。

检查的输出文件：

```text
/scratch/hpcl-cli185/zw5/cime_output_dirs/20260910_seus_rerun/
20260911_seus_halfdeg_future_ssp370_dt3600/run/
20260911_seus_halfdeg_future_ssp370_dt3600.elm.h0.2100-02-01-00000.nc
```

header 确认 12 条 time records、noleap、四个所需字段均为 time: mean、gC/m^2/s。有 NEP、NBP、LAND_USE_FLUX、PFT_FIRE_CLOSS，没有 COL_FIRE_CLOSS 或 DECOMP_FIRE_CLOSS。

### 无需重跑即可得到的诊断量

在当前源码关系成立、相同掩膜/权重下，可由现有输出诊断：

```text
F_column_implied = NEP - LAND_USE_FLUX - NBP
F_decomp_implied = F_column_implied - PFT_FIRE_CLOSS
```

这给出 **NBP 核算里的 fire loss**，不自动等于包含泥炭等所有火灾路径的总排放。FireMod 自身还区分其他火灾路径，不能把上述量无条件叫全部 wildfire emissions。

这些是基于恒等式的反推，不是独立的预算验证。独立检查优先输出 COL_FIRE_CLOSS，比较它与反推值；若考虑 DECOMP_FIRE_CLOSS，先检查当前版本是否真正为它赋值，不能只因为注册了名字就假定该字段有效。只需有针对性地验证，不必立即重跑全部情景。

进一步搜索发现普通 CN 汇总路径未见为 fire_decomp_closs 单独赋值，另有 BeTR 路径赋值。因此不能直接建议只开启 DECOMP_FIRE_CLOSS 就一定得到有效诊断；优先用已明确计算的 COL_FIRE_CLOSS。

**修正这个分解不会自动改变现有累计 NBP 曲线。** 原生 NBP 已扣除完整的上述火灾损失；错误发生在事后归因只减掉其中一部分。

## 2. 同时解决“采伐是否直接算排放”的问题

这里的 NBP 扣的是 `product_closs_col`，即产品池损失，不是简单再扣 `WOOD_HARVESTC`（流入产品池的碳）。源码将 1、10、100 年产品池的 loss 相加。故用 `NEP - fire - WOOD_HARVESTC - conversion` 不能替代 NBP 定义。

NEE 额外包含 `hrv_xsmrpool_to_atm`，所以这一项不是上述 NBP 残差的候选；其不在 h0 中并不等于物理上不存在，判断依据应是公式而不是是否输出。

这也意味着累计 NBP 不应直接命名为 TOTECOSYSC 库存增加；仍需区分生态系统、产品池及其他相关碳库边界。

## 3. 0.07 PgC/yr 的文献匹配有错误

“1750–1950 平均源 0.13、过去 20–30 年变成汇 0.07”这一组表述来自 **Delcourt & Harris (1980), Science 210:321–323**，不是对 2014–2023 的当代观测评估。“过去 20–30 年”相对于 1980 年，不能平移到现在。

[原始研究记录与摘要](https://pubmed.ncbi.nlm.nih.gov/17796049/)，[DOI](https://doi.org/10.1126/science.210.4467.321)。

所链接的 [USGS 2014 新闻稿](https://www.usgs.gov/news/national-news-release/carbon-storage-us-eastern-ecosystems-helps-counter-greenhouse-gas) 则讲更大范围的美国东部、多种生态系统，并报告约 0.3 PgC/yr，基准期为 2001–2005。它不能作为用户引述的东南部现代 0.07 PgC/yr 的直接来源。

因此：0.0708 与 0.07 数字相近，至多是未经统一口径的量级参照，**不构成“历史完全验证通过”，更不能排除未来 forcing 或计算问题**。正式验证必须对齐年代、空间域、森林/全部陆地及产品池边界。

## 4. 对图和归因的正确表述

- 图画的是自 2024 年起累计 NBP，不是现存总碳库。用户提供的表中 Default 到 2100 是 −0.15、1.68、0.71、0.91 PgC，不是四个情景统一约 2.5 PgC。
- 若举 2.5 PgC 为例，77 年均值约为 0.0325 PgC/yr；使用问答中的 1.36×10^6 km² 陆地面积，约为 24 gC/m²/yr。这个净值本身不能判定偏低，需要同口径数据或模型对照。
- 将历史 0.0708 PgC/yr 乘 77 得约 5.45 PgC，是保持历史速率不变的参照线，不是未来真实期望值。
- 未来全时段均值低于历史十年，不等于未来逐年衰减。累计曲线有回升和突降，需看逐年通量、分时段均值和强扰动年的贡献。
- SSP1-1.9 年均略为负值，代表这次模型模拟的全期净源，不能推成每年都是源、所有低排放未来都是源，或减排使生态系统更差。
- RF 同时改变覆盖、恢复轨迹、采伐、NEP 和燃料；“RF 仍是汇”不排除气候效应，不能单独证明土地利用主导。
- 修正遗漏 fire loss 后，火灾在预算中的贡献可能比原表更大；精确比例应重算，不能直接保留 61%/95%/116%。贡献超过 100% 可以由其他项抵消解释，并不自动是错误。
- 预算归因回答哪类通量抵消了碳吸收；为什么火灾通量增加是下一层因果问题，可能涉及气象极端、燃料、管理及强迫数据差异，不能直接写“气候变化造成”。

## 5. 建议的下一步

1. 先以四个现有字段生成 NEP、PFT fire、implied decomposing-pool fire、LAND_USE_FLUX、NBP 的同口径逐年小表。
2. 用明确的基期/未来窗口比较绝对通量；RF 避免使用接近零的差值作分母。
3. 在已有或后续小规模验证任务中输出 COL_FIRE_CLOSS，独立检查反推值；遵守 Slurm 规则。
4. 验证火灾相关 forcing 的极端分布和历史烧毁面积；均温、总降水接近不能保证非线性火灾响应正确。
5. 更新结果解释时明确区分：本次已核实的源码漏项、待重算的贡献百分比、仍待验证的火灾物理合理性。

## 6. 0.5° 全情景重算结果

诊断脚本以 commit `3817fe3` 同步到 Pathfinder，并通过 Slurm job `530640`
运行；作业状态 `COMPLETED`、exit code `0`、运行 4 分 04 秒，峰值内存约
2.7 GB。下表使用 2024–2100 全时段平均，单位均为 PgC/yr：

| 情景 | NEP | 完整 fire loss | LAND_USE_FLUX | NBP |
|---|---:|---:|---:|---:|
| 历史 2014–2023 | 0.1504 | 0.0073 | 0.0724 | 0.0708 |
| SSP1-1.9 | 0.1313 | 0.0671 | 0.0661 | -0.0019 |
| SSP2-4.5 | 0.1849 | 0.0783 | 0.0848 | 0.0218 |
| SSP3-7.0 | 0.1673 | 0.0850 | 0.0731 | 0.0092 |
| SSP5-8.5 | 0.1905 | 0.0978 | 0.0809 | 0.0118 |
| SSP3-7.0 RF | 0.1960 | 0.1043 | 0.0150 | 0.0767 |
| SSP3-7.0 DF | 0.0182 | 0.0171 | 0.1232 | -0.1221 |
| SSP3-7.0 RH | 0.1608 | 0.0888 | 0.0494 | 0.0225 |

默认 SSP 相对历史十年的 NBP 缺口可精确写为：

| 情景 | NBP 缺口 | NEP 变化贡献 | fire 变化贡献 | 土地利用变化贡献 |
|---|---:|---:|---:|---:|
| SSP1-1.9 | 0.0727 | 0.0191 (26%) | 0.0598 (82%) | -0.0062 (-9%) |
| SSP2-4.5 | 0.0490 | -0.0345 (-70%) | 0.0710 (145%) | 0.0125 (26%) |
| SSP3-7.0 | 0.0616 | -0.0169 (-27%) | 0.0777 (126%) | 0.0007 (1%) |
| SSP5-8.5 | 0.0591 | -0.0401 (-68%) | 0.0906 (153%) | 0.0086 (15%) |

正百分比表示使未来 NBP 低于历史，负百分比表示抵消这个下降。三项之和为
100%。因此，**完整 fire loss 的上升是所有 Default SSP 中 NBP 降低的首要
预算原因**。在 SSP2-4.5、SSP3-7.0 和 SSP5-8.5 中，未来 NEP 其实高于历史
十年，抵消了部分火灾损失；只有 SSP1-1.9 同时出现 NEP 降低。土地利用通量
对历史差值的贡献较小或中等，不能解释 SSP3-7.0 的下降。

此前遗漏的分解池 fire loss 在未来均值为 0.0181–0.0253 PgC/yr，约占完整
fire loss 的四分之一。这说明此前所谓的未来“残差”主要具有明确的火灾物理
含义，而不是质量守恒误差。

累计核算进一步支持上述结论。若只在预算中移除 fire loss，四个 Default SSP
的 2024–2100 累计 NBP 分别为 5.02、7.70、7.25 和 8.44 PgC；加入 fire loss
后变为 -0.15、1.68、0.71 和 0.91 PgC。这是预算反事实，不是可实现的无火情景。

RF 相对 SSP3-7.0 Default 的 NBP 增益为 0.0675 PgC/yr：更低的土地利用/产品
库损失贡献约 0.0581，更高的 NEP 贡献约 0.0287，而更高的火灾损失抵消约
0.0193。RH 的小幅增益也来自更低的 LAND_USE_FLUX。DF 的 2024 年存在一次
极大的转换冲击，不能解释成平滑、持续的年度毁林响应。

四个时期的均值和逐年极值都表明 NBP 不是单调衰减。强火灾年份与 NBP 的
深度负异常同步，例如 SSP5-8.5 的 2094 年 fire loss 为 0.859 PgC、NBP 为
-1.335 PgC。下一层机制仍需检查燃烧面积、火险气象和燃料负荷，当前预算分解
不能单独判定火灾增加由气候、燃料、管理还是 forcing 偏差造成。
