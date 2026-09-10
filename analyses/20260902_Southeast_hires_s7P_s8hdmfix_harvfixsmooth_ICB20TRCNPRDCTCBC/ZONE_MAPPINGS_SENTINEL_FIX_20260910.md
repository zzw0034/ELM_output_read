# zone_mappings.txt 海洋哨兵点修复

日期：2026-09-10　　执行：zw5　　已征得 f9y 同意（`cpl_bypass_full/zone_mappings.txt` 原属 f9y）

> **English summary.** The CPL_BYPASS met reader picks the nearest
> `zone_mappings.txt` entry for each land gridcell and reads that record without
> checking whether it contains data. 107,661 of the 225,625 entries point at
> ocean records holding constant sentinels (`FSDS = -1111.027`, `TBOT = 396 K`,
> `PSRF = -9999.086`). Because the SEUS 4 km model grid is offset half a cell
> from the forcing grid, 194 coastal land cells snapped onto one and produced
> `GPP = 0` for entire runs. The fix deletes the sentinel-pointing rows from
> `zone_mappings.txt`; nothing else is touched, no `.nc` data is modified, and
> the untouched original is preserved beside it as
> `zone_mappings.txt.orig_before_sentinel_fix_20260910`. Reverting is a single
> `cp` back. Details below in Chinese.

---

## 1. 问题

ELM 的 `CPL_BYPASS` 气象读取（`components/elm/src/cpl/lnd_import_export.F90`，约 411–436 行）：

```fortran
open(unit=13, file=trim(metdata_bypass) // '/zone_mappings.txt')
ng = 0
do v=1,500000
  read(13,*, end=10), longxy(v), latixy(v), zone_map(v), grid_map(v)
  ng = ng + 1
end do
...
mindist=99999
do g3 = 1,ng
  thisdist = 100*((latixy(g3) - ldomain%latc(g))**2 + (longxy(g3) - ldomain%lonc(g))**2)**0.5
  if (thisdist .lt. mindist) then
    mindist = thisdist;  ztoget = zone_map(g3);  gtoget = grid_map(g3)
  end if
end do
```

对每个陆地格点在全部条目里找最近邻，**取到就用，从不检查那条记录里有没有有效数据**。

而这套强迫的 225625 个点里，**107661 个是海洋点，存的是常数哨兵值**：

| 变量 | 哨兵值 |
|---|---|
| `FSDS` | −1111.027 |
| `TBOT` | 396.001 K |
| `PRECTmms` | −0.088 |
| `PSRF` | −9999.086 |
| `FLDS` | 1000.989 |

五个变量标记的是同一批点，并集也是 107661，有效点 117964。`PSRF` 的 −9999 是典型缺测标志，说明这些是**刻意留的 no-data 标记**，不是数据损坏。

## 2. 后果

SEUS 4km 的模式网格和这套 4km 强迫网格**错开半个格**（模式格心落在强迫格心 +0.5 处），所以每个格点都要做最近邻，沿海格点完全可能命中隔壁的海洋点。

实测：**194 个陆地格点**（占陆地 0.256%）读到的是哨兵，`GPP` 恒为 0，**在我们所有 4km run 里都是同一批**——AD spin-up、final spin-up、2010 年瞬变一模一样。位置全部贴着海岸线：迈阿密、劳德代尔堡、夏洛特港、加尔维斯顿湾、路易斯安那海岸。

这些格点的 `landfrac` 全部等于 1.000，模式认为它们是 100% 陆地。

> 注：`elm_setup_and_run_guide.md` 第 10 节记过一个类似的沿海坑，但写着"原生分辨率跑该文件本身永远不会触发"。**那句话不成立**，前提是两套网格格心重合，而这里错开半个格。该处已更正。

## 3. 修法

**只删 `zone_mappings.txt` 里指向哨兵记录的行，不动任何 `.nc` 数据。**

安全性依据：`ng` 是读文件时数出来的，`grid_map` 是第 4 列**显式给出的记录索引**，不是行号推的。所以删行既不改条目上限，也不会让索引错位。

更重要的是，**删掉的只可能是"更远或等距"的候选**。一个格点如果原本最近的就是有效点，删完之后最近的还是同一个点。所以：

- **只有那 194 个格点会改映射**
- 其余 75726 个格点的取值**逐比特不变**

实测位移：那 194 个格点到最近**有效**点的距离，中位数、均值、p90、最大值**全部是 3.30 km**，而它们现在用的哨兵点是 3.27 km。也就是从"隔壁的海洋点"改成"隔壁的陆地点"，100% 落在一个格距（4.6 km）以内。

顺带 `ng` 从 225625 降到 117964，那个逐格点的 O(ng) 搜索快一倍。

## 4. 处理了哪些文件

| 目录 | 用途 | 原条目 | 保留 | 删除 |
|---|---|---|---|---|
| `cpl_bypass_full/` | spin-up 和历史 | 225625 | 117964 | 107661 |
| `future_clim/ssp119/` | 4km future 情景 | 225625 | 117964 | 107661 |
| `future_clim/ssp245/` | | 225625 | 117964 | 107661 |
| `future_clim/ssp370/` | | 225625 | 117964 | 107661 |
| `future_clim/ssp585/` | | 225625 | 117964 | 107661 |

## 5. 执行过程

脚本：`ELM_output_read/analyses/20260902_Southeast_hires_s7P_s8hdmfix_harvfixsmooth_ICB20TRCNPRDCTCBC/fix_zone_mappings.py`（在 GitHub `zzw0034/ELM_output_read` 里有版本记录）

每个目录的步骤，全部通过才继续：

1. 从**该目录自己的** `FSDS` 文件探测哨兵集合，采样记录的第 50% 和第 80% 两个时间步，取交集
2. 原文件 `shutil.copy2` 成 `zone_mappings.txt.orig_before_sentinel_fix_20260910`，`filecmp.cmp(shallow=False)` 逐字节校验，不一致则中止
3. 过滤后的表写入同目录临时文件 `zone_mappings.txt.tmp_sentinel_fix`
4. 校验临时文件行数等于预期保留数
5. 校验临时文件里**每一个**索引都指向非哨兵记录
6. `os.replace` 原子替换，备份文件保留不删

**为什么采样第 50% 和 80% 而不是第一个时间步**：`future_clim/*` 的 `DBCCA_Daymet_TESSFA2_FSDS_2023-2100_z01.nc` 开头有一个 dummy 区块，`t = 0..2918`（3 小时步长正好一年）全部 225625 个点都是哨兵。读 `t=0` 会把整张表判成哨兵、删光所有行。第一次干跑正是这样报的，因此改成采样中后段，并且**整条记录全是哨兵的时间步一律丢弃**。这个坑值得记住。

## 6. 如何回退

```bash
cd <目录>
cp zone_mappings.txt.orig_before_sentinel_fix_20260910 zone_mappings.txt
```

备份文件不会被脚本删除。重复执行脚本时，若备份已存在则保留原备份不覆盖，所以最初的原始文件始终安全。

## 7. 如何验证修好了

跑一小段之后，对 `landmask == 1` 的格点统计年均 `FSDS < 1` 的数量，**应该是 0**（修复前是 194）。

```python
land = (landmask == 1)
bad = land & (annual_mean_FSDS < 1.0)
assert bad.sum() == 0
```

建议把这条检查加进任何新 case 的建立流程。已写入 `elm_setup_and_run_guide.md`。

## 8. 影响范围提醒

改动对结果是**严格改善**：原本产出零的沿海格点开始产出合理的碳通量。但它确实会改变结果，所以：

- 修复前跑完的结果，那 194 个格点仍然是零，需要屏蔽或标注
- 若有人正在做跨时间的对比，请注意 2026-09-10 前后的 run 在这些格点上不可直接比较
- 其余 75726 个格点不受任何影响，可以直接比较

## 9. 背景

这个问题是在追查另一件事时发现的：SEUS 4km 历史模拟里常绿 PFT（松树、常绿阔叶灌木）在部分斑块上叶碳趋近于零且永久滞留。完整调查记录见
`ELM_output_read/analyses/20260902_Southeast_hires_s7P_s8hdmfix_harvfixsmooth_ICB20TRCNPRDCTCBC/EVERGREEN_DIEBACK.md`。
哨兵格点是那次调查的副产品，与常绿滞留是**两个独立的问题**。
