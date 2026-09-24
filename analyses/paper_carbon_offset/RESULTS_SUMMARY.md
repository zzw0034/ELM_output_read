# 高分辨率 ELM 森林碳管理论文：结果与证据状态

更新：2026-09-24。

> **2026-09-24 结果目录选择（优先于下文旧表述）：**在
> `/scratch/hpcl-cli185/zw5/cime_output_dirs/20260910_seus_rerun/`
> 下，Default 和 DF 选用 16 个 `cds38000` future 目录；RF、RH
> 选用 16 个不带该后缀的 future 目录；另用 6 个不带该后缀的
> spin-up/transient 目录。具体 38 个名称见第 0 节。
>
> **2026-09-23 其余决定（与上述选择并用）：**
> 1. 论文结果均来自上述 20260910 rerun 根目录。旧
>    [CASE_MATRIX.md](CASE_MATRIX.md) 和 `code/common.py` 尚未更新到
>    2026-09-24 的混合选择，不可直接把其 Default/DF 映射当作本文档清单。
>    下文所有旧版数值（4.79/4.95、9.50/9.88、3–5%、33.6%/57.3% 等）对论文作废，需重算。
> 2. `crit_dayl_stress`：按本节列出的实际目录选择分析，不能再把所有
>    future case 统一描述为 38000 s。实际参数及跨情景配对条件仍须核对。
> 3. 4 km 火灾图的圆形斑块来自 **HDM 人口密度输入**；脆弱性中的火灾分量是 HDM 的粗分辨率，
>    需单独报告，并做去掉火灾分量的选址敏感性检验。
> 4. 分辨率优势统一与“降尺度 0.5°”（0.5° 每 PFT 碳密度 × 4 km PFT 比例）比较；
>    选址的主要粗分辨率对照是“4 km 聚合到 0.5°”。

本文档按用户确定的新主线组织：
**空间可信度 → 区域碳效益 → 空间异质性及机制 → 管理优先区域**。
完整结构见 [MANUSCRIPT_BLUEPRINT.md](MANUSCRIPT_BLUEPRINT.md)，
图表安排见
[manuscript_figure_results_discussion.md](manuscript_figure_results_discussion.md)。

本次为整理已有材料，没有重算模拟输出。下文区分旧图报告值、新版诊断记录和
尚未执行的分析。重复且已被新证据取代的旧版长篇总结已从工作目录移除；
可在 Git 历史中追溯，不能作为当前结论。

## 0. 2026-09-24 选用的 38 个结果目录

下列名称均位于同一结果根目录：
`/scratch/hpcl-cli185/zw5/cime_output_dirs/20260910_seus_rerun/`。
完整路径为“该根目录 + 下列文件夹名”。2026-09-24 对根目录做了只读的一层
目录核对：54 个目录存在；按用户指定规则选用其中 38 个（32 个 future、
6 个 spin-up/transient）。未在本次核对各目录内 h0/h1 文件、年份、参数、
restart 或输出完整性。

### 0.5°：19 个

```text
20260911_seus_halfdeg_ad_spinup_dt3600
20260911_seus_halfdeg_final_spinup_dt3600
20260911_seus_halfdeg_transient_dt3600

20260922_seus_halfdeg_future_ssp119_cds38000_dt3600
20260922_seus_halfdeg_future_ssp119_DF_cds38000_dt3600
20260915_seus_halfdeg_future_ssp119_RF_dt3600
20260915_seus_halfdeg_future_ssp119_RH_dt3600

20260922_seus_halfdeg_future_ssp245_cds38000_dt3600
20260922_seus_halfdeg_future_ssp245_DF_cds38000_dt3600
20260915_seus_halfdeg_future_ssp245_RF_dt3600
20260915_seus_halfdeg_future_ssp245_RH_dt3600

20260922_seus_halfdeg_future_ssp370_cds38000_dt3600
20260922_seus_halfdeg_future_ssp370_DF_cds38000_dt3600
20260911_seus_halfdeg_future_ssp370_RF_dt3600
20260911_seus_halfdeg_future_ssp370_RH_dt3600

20260922_seus_halfdeg_future_ssp585_cds38000_dt3600
20260922_seus_halfdeg_future_ssp585_DF_cds38000_dt3600
20260915_seus_halfdeg_future_ssp585_RF_dt3600
20260915_seus_halfdeg_future_ssp585_RH_dt3600
```

### 4 km：19 个

```text
20260910_Southeast_hires_30n_hdmfix_mapfix_ICB1850CNRDCTCBC_ad_spinup
20260911_Southeast_hires_20n_hdmfix_mapfix_ICB1850CNPRDCTCBC_final_spinup
20260911_Southeast_hires_30n_hdmfix_mapfix_ICB20TRCNPRDCTCBC

20260922_seus_4km_fut_ssp119_cds38000
20260922_seus_4km_fut_ssp119_DF_cds38000
20260915_seus_4km_fut_ssp119_RF
20260915_seus_4km_fut_ssp119_RH

20260922_seus_4km_fut_ssp245_cds38000
20260922_seus_4km_fut_ssp245_DF_cds38000
20260915_seus_4km_fut_ssp245_RF
20260915_seus_4km_fut_ssp245_RH

20260922_seus_4km_fut_ssp370_cds38000
20260922_seus_4km_fut_ssp370_DF_cds38000
20260917_seus_4km_fut_ssp370_RF
20260917_seus_4km_fut_ssp370_RH

20260922_seus_4km_fut_ssp585_cds38000
20260922_seus_4km_fut_ssp585_DF_cds38000
20260915_seus_4km_fut_ssp585_RF
20260915_seus_4km_fut_ssp585_RH
```

其余 16 个不带 `cds38000` 的旧版 Default/DF future 目录仍存在，
但本次分析不选用。因为 RF/RH 与 Default/DF 取自不同批次，管理差值在
解释前需核对实际参数、初始状态和其他配置；本节只固定文件夹选择，
不声称已经完成严格配对验证或重算结果。

## 1. 先锁定结果版本

旧图（common.py 2026-09-23 前的设置）用的是 20260911 的 0.5° dt3600 case 与较早的
20260908 4 km future case，管理对比只列 SSP3-7.0；common.py 现已切到新版 rerun。下面的 4.79/4.95 PgC、3–5%
差异和象限比例属于这一旧图分析组合。

[新版 4 km 配对分析](../20260908_seus_4km/rerun_comparison/FINDINGS.md)
已记录新增管理 SSP 和新版输出变化。不能再把“只有 SSP3-7.0 管理实验”说成
整个项目的现状，也不能把旧表直接标成新版结果。论文采用哪些 case、参数、
restart 和时间窗，需要先建立实际实验矩阵。第 0 节已固定拟使用的目录，
但 `code/common.py` 和 [CASE_MATRIX.md](CASE_MATRIX.md) 尚未同步这一选择。

该配对分析指出 parameter file、restart 等配置同时变化，所以现有跨分辨率
差异尚不能全部解释为纯网格效应。

## 2. 空间可信度：有观测对照，定量优势待检验

Poster 已包含 4 km ELM 与 ESA-CCI AGB、SoilGrids 0–30 cm SOC 的对照，
相邻脚本也能生成 0.5° | 4 km | observation 三列图。原来“没有任何观测
比较、数据位置未知”的描述已经过时。

这些图仍是 illustrative comparison。需要统一掩膜、碳/生物量单位、年份、
SOC 深度和比较尺度，计算 bias、RMSE、空间相关及分布差异，并检验 4 km
在 0.5° 格点内部捕捉的变化是否与观测一致。图像更细不等于预测更准。

此外，已知日长阈值会产生人工空间突变，见第 6 节。真实地理结构与参数
造成的细节必须分开评价。

## 3. 区域效益：旧分析显示跨分辨率相近

SSP3-7.0、2091–2100 平均 TOTECOSYSC 状态差，单位 PgC：

| 定义 | 0.5° | 旧版 4 km |
|---|---:|---:|
| RF−Default：恢复与保护组合 | 4.95 | 4.79 |
| RH−Default：减采伐 | 0.98 | 0.93 |
| Default−DF：理想化避免损失上界 | 9.88 | 9.50 |

这支持“同一模型框架下的区域效益较一致”，不构成独立验证。
约 10:5:1 的大小关系也不是三种同等可行政策的效率排名：DF 是持续全域
森林转草地参照，RF 包括更广范围禁伐，RH 是较小的采伐扰动。

Poster 的 RF 5.9 PgC、DF 10.1 PgC 要追溯变量、时间窗和 case 版本。
年度/十年平均状态差、分项池之和与累计 NBP 不能互换。

四个 Default SSP 给出未来背景，管理效益必须用同一 SSP 内的对照差。
扩大跨 SSP 结论前，接入已经存在的新 case 并核对配对条件，不机械补跑矩阵。

## 4. 空间异质性与机制：论文的中间证据

旧 fig04 检查了 12:1 嵌套与相同区域陆地面积，并比较 native 4 km、
4 km 聚合到 0.5°、native 0.5°。以下是旧 DF avoided-loss 分布的面积占比：

| 阈值 | native 4 km | 4 km → 0.5° | native 0.5° |
|---|---:|---:|---:|
| <1000 gC/m² | 11.3% | 4.3% | 2.5% |
| >12000 gC/m² | 13.6% | 8.8% | 9.2% |
| >18000 gC/m² | 1.60% | 0.55% | 0.92% |

这些结果说明空间平均会压缩分布尾部。它们没有证明 4 km 是现实真值，
也没有直接计算粗网格“漏掉多少真实最佳地点”。需补 RF 分布、格点内部差异、
位置重叠，以及已知阈值人工结构的敏感性。

碳库解释继续保留：旧分项计算的管理增量约 66–70% 在地上，但分项和与
TOTECOSYSC 尚未闭合，比例暂不作最终数值。18–19% 地上占比描述的是
所选碳库存量结构，不能说 AGB 核算遗漏了约 81% 的管理效益。
RF/RH 的 SOC 差值略负是模型结果，不是现实造林普遍损失 SOC 的证据。

### 通量机制：完整 fire 与 PFT fire 必须区分

原生 NBP 的核算关系为：

```text
NBP = NEP - COL_FIRE_CLOSS - LAND_USE_FLUX
LAND_USE_FLUX = land-conversion loss + wood-product-pool loss
```

PFT_FIRE_CLOSS 不包括完整的凋落物/CWD 火灾损失；用原生 NBP 反推
COL_FIRE_CLOSS 按恒等式闭合，不是火灾物理的独立验证。木材进入产品池
的 WOOD_HARVESTC 也不等于当年大气排放。

[NBP 核算记录](supplement/NBP_RESIDUAL_REVIEW_20260915.md) 报告的旧 0.5° 结果：

| 情景/时期 | NEP | 完整 fire loss（反推） | LAND_USE_FLUX | NBP |
|---|---:|---:|---:|---:|
| 历史 2014–2023 | 0.1504 | 0.0073 | 0.0724 | 0.0708 |
| SSP1-1.9，2024–2100 | 0.1313 | 0.0671 | 0.0661 | −0.0019 |
| SSP2-4.5，2024–2100 | 0.1849 | 0.0783 | 0.0848 | 0.0218 |
| SSP3-7.0，2024–2100 | 0.1673 | 0.0850 | 0.0731 | 0.0092 |
| SSP5-8.5，2024–2100 | 0.1905 | 0.0978 | 0.0809 | 0.0118 |
| SSP3-7.0 RF，2024–2100 | 0.1960 | 0.1043 | 0.0150 | 0.0767 |

单位 PgC/yr。完整 fire 增加解释了历史与未来 NBP 缺口的 82–153%，
其中三个 SSP 的 NEP 增加抵消部分缺口。这个预算归因不能单独解释 fire
变化由气候、燃料还是强迫偏差造成。

RF 相对 Default 的年均 NBP 增益约 0.0675 PgC/yr，来自较低土地利用/
产品池损失（+0.0581）、较高 NEP（+0.0287）与较高 fire loss（−0.0193）
的净结果。火灾损失已包含在模型净结果里，不能再从 stock benefit 扣一次。

不能由这些结果推出“所有 SSP 未来都是汇”“气候减排没有用”或“主动管理
必然优于减排”。未来全期均值、末世纪均值、历史延续累计曲线口径不同。

## 5. 管理优先区域：已有象限，等面积比较待做

旧 2091–2100 分类，high-potential AND low-vulnerability 象限：

| 情景/分辨率 | 占区域土地 | 包含潜力 |
|---|---:|---:|
| RF 0.5° | 37.4% | 58.4% |
| RF 4 km | 33.6% | 57.3%（2.75/4.79 PgC） |
| DF 0.5° | 32.4% | 49.4% |
| DF 4 km | 30.4% | 51.2% |

这是两个条件的交集，不是整个低脆弱性的一半土地。结果说明潜力的空间
集中性，尚未证明高分辨率筛选更优，也不支持把某片区域叫“安全地块”。

现有 fig05 使用 PFT fire/总生态系统碳、全年平均 1−BTRAN、十年未去趋势
stock CV。三个分量按格点排名后等权；象限中位数才是面积加权。
图中 fire/stock 只是损失强度，不能解释成项目逆转概率。指标定义、
完整 fire、排序权重与缺测处理需要核对。

优先新分析：同样选取公共 eligible domain 的 20% 或 30% 物理面积，
比较两个分辨率选址的重叠、PgC、每公顷效益和脆弱性；扩展为面积预算
曲线。两个选择都用同一参考场评估，并测试参考场依赖，不能把用 4 km
排序再用同一场评分得到的优势当作现实验证。设计见 blueprint Methods 2.9。

## 6. 新证据：草地物候已从假说推进到参数敏感性

[日长阈值诊断](../CRIT_DAYL_STRESS_ARTIFACT.md) 的 2026-09-21/22 记录
将 30.833°N 附近的 GPP 不连续关联到 crit_dayl_stress=36000 s；
两种分辨率均有这种结构，DF 因草地比例高更明显。

9 月 22 日的四 SSP、0.5° 配对试验同时对 Default 和 DF 使用 38000 s。
记录报告累计 NBP（2024–2100）avoided-loss benefit 增加约 5.3–5.9%，
2100 年末 TOTECOSYSC 差值增加约 5.0–5.7%。这些口径与本目录旧表的
2091–2100 平均 stock benefit 不同，不能直接乘上旧数当修正值。

仅改 DF 仍会留下 Default 的阈值结构。38000 s 虽移走域内阈值，也引入
南部更强冬季休眠；restart 仍来自 36000 s 的历史状态。早期试验是有信息量
的参数敏感性，并非独立生态验证。现按第 0 节选用两种分辨率的
`cds38000` Default/DF，以及不带该后缀的 RF/RH；后两种管理差值涉及
不同批次，不能从早期 0.5° Default/DF 敏感性试验直接外推。

论文必须检验阈值对空间 skill、潜力排序、vulnerability 的影响。高分辨率
揭示额外细节，其中可能既有真实空间信息，也有模型结构的痕迹。

## 7. 当前行动顺序

1. 核对新版和旧版 case/参数/restart，冻结论文实际实验矩阵与参考结果。
2. 完成 AGB/SOC 的跨尺度定量评价，审查日长阈值影响。
3. 补格点内部异质性与等面积优先区域比较。
4. 关闭 pool residual，核对 fire 和 vulnerability 定义，补面积归一化。
5. 按新五图计划重组并重新生成图，记录版本并进行视觉检查。

本轮已更新说明和脚本文字，未运行这些新分析；
[figures/legacy/](figures/legacy/) 的原图仍是旧版。
