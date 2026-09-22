# 30.833°N 上的 GPP 突变线：`crit_dayl_stress` 物候阈值

查明于 2026-09-21。**影响所有含草本的 SEUS 模拟结果的解读，不限于某一族 case。**
这不是 bug，是参数设置的物理后果——但它在结果里制造了一条人为的空间不连续，
写论文和做区域统计时必须知道。

（英文版见下一节 "English summary"，可直接用于论文 limitations、给合作者的邮件，
或向 E3SM 提 issue。）

---

## English summary

### The symptom

All SEUS 4 km simulations show a perfectly straight, east–west GPP
discontinuity at ~30.83°N that spans the entire model domain. It is most
obvious in the DF (deforestation counterfactual) scenario, where the whole
landscape is converted to grass, and is present in every SSP and in two
independently built case families (`20260908_seus_4km_fut_*` and
`20260915/17_seus_4km_fut_*`), which used different executables, different
initial conditions, and different versions of the land-use input files.

### The cause

ELM's stress-deciduous phenology — which governs **all grass PFTs**
(`natpft` 12, 13, 14) — force-triggers leaf offset (dormancy) whenever
daylength falls to or below the parameter `crit_dayl_stress`
(`PhenologyMod.F90`, the `force offset` branch, and the companion branch
that blocks onset).

This project's parameter file
(`20260910_seus_rerun_inputs/clm_params_SEUS_c260712.nc`) sets

```
crit_dayl_stress = 36000 s = 10.0 hours
```

Winter-solstice daylength equals exactly 10.0 hours at

```
H = 10 h × 15°/h ÷ 2 = 75°
tan(φ) · tan(23.44°) = cos(75°) = 0.25882
φ = arctan(0.25882 / 0.43356) = 30.833°N
```

Therefore:

- **South of 30.833°N** minimum annual daylength never reaches the
  threshold, grass is never forced into dormancy, and it photosynthesises
  through the winter — behaving effectively as evergreen.
- **North of 30.833°N** daylength drops below 10 h every winter, grass is
  force-dormant, and winter GPP collapses.

The model grid rows bracketing the threshold are row 163 (30.813°N) and
row 164 (30.854°N); the predicted threshold falls exactly between them,
and that is precisely where the step is observed.

> ⚠ **The source comment is stale and misleading.** `PhenologyMod.F90`
> annotates this branch as "force offset if daylength is < 6 hrs", because
> the *code default* is `secspqtrday` = 21600 s = 6 h. The parameter file
> overrides it to 36000 s = 10 h. Six hours corresponds to a threshold
> latitude near the Arctic Circle; ten hours corresponds to 30.8°N. Anyone
> reading the source without checking the parameter file will conclude the
> threshold is thousands of kilometres away from where it actually is.
>
> For contrast, season-deciduous PFTs use a different parameter,
> `crit_dayl = 39300 s = 10.92 h`, whose threshold latitude is 18.06°N —
> south of the entire domain, so it applies uniformly and creates no
> within-domain discontinuity.

### Evidence

Four independent, falsifiable predictions were tested; all four hold.

**1. Exact latitude.** Predicted 30.833°N; the step is observed between
grid rows at 30.813°N and 30.854°N.

**2. Magnitude scales with grass fraction.** In the annual mean, the
domain-width row-mean GPP step at row 163→164 is −338 gC m⁻² yr⁻¹ in DF
(~100 % grass after clearing) versus −24 in Default (~15–20 % grass) — a
factor of ~14. Leaf area (ELAI) drops 27 % in DF and 11 % in Default at
the same row. RH ≈ Default (same vegetation composition); RF, which has
the least grass, is weakest.

**3. The step is seasonal.** If it is a daylength threshold it *must*
vanish in summer, when daylength exceeds 10 h everywhere:

| Month | Default | DF |
|---|---|---|
| January | 1562 → 1192 (−370, −24 %) | 2099 → 544 (−1555, **−74 %**) |
| July | 4525 → 4545 (**+20, no step**) | 4427 → 4252 (−175, −4 %) |

Default's step disappears entirely in July; DF's is reduced to 11 % of its
winter magnitude. The small July residual in DF is a legacy effect —
northern grass must regrow from dormancy each spring and therefore carries
less leaf area into summer.

**4. It is confined to stress-deciduous PFTs.** Using PFT-resolved (h1)
output from a *single* simulation, so gridcells, climate, soils and
executable are identical and only the PFT class differs:

| | January (row 163→164) | July |
|---|---|---|
| **Grass** (natpft 12–14, stress-deciduous) | 2350 → 362 (**−85 %**) | 4985 → 4577 (−8 %) |
| **Trees** (natpft 1–8) | 1448 → **1475 (+2 %, no step)** | 4461 → 4521 (+1 %) |

Grass collapses by 85 % at the threshold row in January; trees in the same
cells at the same moment show no step at all. This isolates the mechanism
with no confounding.

### What was ruled out

Every static input field is smooth across the step: land-cover composition
(`PCT_NAT_PFT` forest and grass fractions at 2024/2050/2100), the C3/C4
grass ratio, total forest fraction and `PCT_NATVEG`, the LUH2-downscaled
`HARVEST_*` fields, meteorological forcing (`TBOT`, `TSA`, `RAIN`, `FSDS`,
10-year annual means), soil phosphorus pools (`APATITE_P`, `LABILE_P`,
`OCCLUDED_P`, `SECONDARY_P`), soil texture and organic matter, soil colour
and soil order, `FMAX`, slope, elevation, and the population-density field
driving human fire ignitions. Fire variables (`FAREA_BURNED`,
`PFT_FIRE_CLOSS`) do step at the same row, but as a *consequence* — less
leaf area means less fuel — not a cause.

Two false leads are documented in the Chinese sections below so they are
not re-investigated: (i) a genuine but unrelated numerical fragility in the
DF scenario's grass-routing weight `w_k = p(k,2023) / grass_2023` where
pre-existing grass is near zero (real, worth fixing separately, but
statistically unable to explain this line: Pearson r = 0.09 against the
GPP step); and (ii) the apparent coincidence with the Alabama/Georgia–
Florida state line at 31.00°N, which is 0.17° (~19 km) away and is not the
cause — the step persists when all map overlays are removed.

### Implications for interpretation

1. **Grass carbon fluxes are not comparable across 30.833°N.** South of it
   the model treats grass as winter-active; north of it as winter-dormant.
2. **`Default − DF` carbon-benefit estimates carry an artificial
   discontinuity at this latitude**, which will contaminate any regional
   aggregate or latitudinal-gradient analysis that spans it.
3. Sensitivity to the artifact scales with grass fraction:
   DF ≫ Default ≈ RH > RF.
4. The artifact is present in both 4 km case families **and in the 0.5°
   runs** (all share the same parameter file). At 0.5° the grid rows sit at
   …30.25, 30.75, 31.25, 31.75…, so the 30.833°N threshold falls between
   the 30.75 and 31.25 rows; ELM evaluates daylength at the cell centre, so
   the 30.75 row stays winter-active and the 31.25 row is force-dormant.
   Verified (SSP5-8.5, 2091–2100 mean, 30.75 → 31.25 row step):

   | | January | July |
   |---|---|---|
   | Default | 1578 → 1180 (**−25 %**) | 4491 → 4403 (−2 %) |
   | DF | 2099 → 813 (**−61 %**) | 4452 → 4089 (−8 %) |

   Same signature as 4 km — a large January step at the threshold row
   boundary that nearly vanishes in July, scaling with grass fraction. Only
   the spatial expression differs: a thin line on the 0.042° grid, a single
   coarse row boundary on the 0.5° grid.
5. Removing it would require changing `crit_dayl_stress` (e.g. back to the
   code default of 21600 s) and **re-running**, and should not be done
   before establishing why the value was set to 36000 s in the first place
   — it predates this project (the parameter file's `history` attribute
   records `crit_dayl_stress = crit_dayl_stress*0 + 36000` applied
   2017-09-01).

This is not a code bug. It is the physical consequence of a parameter
choice, but it produces a spatial discontinuity that must be disclosed in
any write-up and accounted for in regional statistics.

### 2026-09-22 update: 0.5° rerun at 38000 s

`crit_dayl_stress = 38000 s` (10.56 h, threshold latitude 23.4°N, south of
the domain) was tested on the 0.5° futures (2024-2100, 4 SSPs), rerunning
DF first and then Default. Each rerun differs from its original only in
the paramfile. Results (2091-2100):

- The step in `Default − DF` at 30.75→31.25°N falls to the profile's own
  row-to-row noise **only when both runs use 38000 s**. January: +639 to +902
  → −59 to −75 against noise of 48-94 gC m⁻² yr⁻¹. Annual: +218 to +287 →
  +14 to +36. Rerunning DF alone leaves Default's own step in the difference,
  reversed in sign, at about 40-55% of the original.
- Cost 1: all stress-deciduous vegetation is now dormant through January
  domain-wide. Annual GPP falls 15-25% south of the old threshold (DF) and
  0-5% north of it. Keeping C3 grass dormant all winter in the far south is a
  strong assumption.
- Cost 2: the parameter lowers GPP more in DF (−6 to −8%, almost all grass)
  than in Default (−3 to −4%). The avoided-deforestation benefit (cumulative
  NBP 2024-2100) therefore grows by **+5.3 to +5.9%** (about 0.6 PgC) with
  both runs at 38000 s, versus +7.3 to +8.4% with DF alone.
- The starting restart was still spun up at 36000 s; the parameter changes
  only from 2024.

Details: the Chinese section "2026-09-22 更新" below, and
`20260910_seus_rerun/20260922_seus_halfdeg_DF_cds38000/`.

---

## 一句话结论

ELM 对胁迫落叶型（stress-deciduous，**所有草本 PFT**）有一个硬阈值：日长 ≤
`crit_dayl_stress` 就**强制落叶**。本项目 paramfile 把它设成 **36000 秒 = 10.0
小时**，而冬至日日长恰好等于 10 小时的纬度是 **30.833°N**。于是：

- **线以南**：冬季日长始终 > 10 小时 → 草本永不被强制休眠 → 全年常绿 → GPP 高
- **线以北**：每年冬天日长跌破 10 小时 → 草本强制落叶 → GPP 低

草本占比越高的情景，这条线越明显——所以 **DF（毁林反事实，景观几乎 100% 变成草）
最突出，Default/RH（草只占 13-22%）弱约 4 倍，RF（草更少）最弱**。

## 证据链

### 参数值

```
$ ncdump -v crit_dayl_stress /projects/hpcl-cli185/proj-shared/zw5/20260910_seus_rerun_inputs/clm_params_SEUS_c260712.nc
crit_dayl_stress = 36000 ;
```

paramfile 的 `history` 属性留着人为设置的痕迹（2017-09-01）：
`ncap2 -s crit_dayl_stress=crit_dayl_stress*0+36000`

### 代码位置

`E3SM/components/elm/src/biogeochem/PhenologyMod.F90`：

```fortran
1207:  ! only allow onset if dayl > 6hrs
1208:  if (onset_flag(p) == 1._r8 .and. dayl(g) <= PhenolParamsInst%crit_dayl_stress) then
1305:  ! force offset if daylength is < 6 hrs
1306:  if (dayl(g) <= PhenolParamsInst%crit_dayl_stress) then
```

**⚠ 源码注释是错的**：注释写"6 hrs"是因为**代码内的默认值**是
`secspqtrday = 86400/4 = 21600 s = 6 小时`（PhenologyMod.F90:121, 174），但
**paramfile 把它覆盖成了 36000 s = 10 小时**。照注释读源码的人会得出完全错误的
阈值纬度（6 小时对应北极圈附近，10 小时对应 30.8°N，差了几千公里）。

（对照：季节落叶型用的是另一个参数 `crit_dayl = 39300 s = 10.92 hr`，对应
18.06°N，整个 SEUS 域都在其以北，所以对树木是均匀生效的，不产生域内不连续。）

### 阈值纬度推导

冬至日 δ = −23.44°，日长 = 10.0 小时：

```
H = 10 × 15/2 = 75°
tan(φ)·tan(23.44°) = cos(75°) = 0.25882
tan(φ) = 0.25882 / 0.43356 = 0.59696
φ = 30.833°N
```

**模型网格行：第 163 行 = 30.813°N，第 164 行 = 30.854°N。阈值正好落在两行之间。**

### 实测跳变（SSP5-8.5，2091-2100，全域宽度行均值）

年均 GPP（gC/m²/yr）：

| row | lat | Default 逐行变化 | DF 逐行变化 |
|---|---|---|---|
| 162→163 | 30.77→30.81 | +12.8 | +9.6 |
| **163→164** | **30.81→30.85** | **−24.4** | **−338.0** |
| 164→165 | 30.85→30.90 | +2.1 | +7.4 |

叶面积（ELAI，近因）：

| row | lat | ELAI_Default | ELAI_DF | DF 逐行变化 |
|---|---|---|---|---|
| 163 | 30.812 | 3.93 | 5.84 | −0.02 |
| **164** | **30.854** | **3.50（−11%）** | **4.26（−27%）** | **−1.58** |
| 165 | 30.896 | 3.48 | 4.25 | −0.01 |

### 决定性验证：冬夏对照

如果是日长阈值，跳变**必须**在夏天消失（夏季日长处处 > 10 小时，无人被强制休眠）。

**1月 GPP**（各月多年平均，按年化速率表示）：

| row | lat | Default | DF |
|---|---|---|---|
| 163 | 30.812 | 1562.2 | 2098.9 |
| **164** | **30.854** | **1192.0（−370.3，−24%）** | **544.3（−1554.6，−74%）** |

**7月 GPP**（对照组）：

| row | lat | Default | DF |
|---|---|---|---|
| 163 | 30.812 | 4525.1 | 4427.2 |
| **164** | **30.854** | **4545.2（+20.1，不降反升）** | **4251.8（−175.4，−4%）** |

- Default 的跳变在 7 月**完全消失**（甚至是上升的）
- DF 的跳变从冬季的 −1554.6 缩到 −175.4（**只剩 11%**）；相对幅度从 −74% 降到 −4.0%，
  **季节性差 18 倍**
- 7 月残留的那点 DF 跌幅是遗留效应：北侧草每年冬天休眠、春天重新长叶，夏季叶面积
  存量本来就低于南侧常绿的

### 决定性验证二：按 PFT 分开看（同一次模拟内部对照）

上面的冬夏对照还混着"情景"这个变量（DF vs Default）。**最干净的检验是只用
Default 这一次模拟**——同一批格点、同样的气候/土壤/可执行文件，唯一变量是
"看哪一类 PFT"：

- **草本**（natpft 12/13/14）是胁迫落叶型 → 受 `crit_dayl_stress` 管 → **应该**跳
- **树木**（natpft 1-8）是常绿或季节落叶型 → 受 `crit_dayl`（39300 s，阈值纬度
  18.06°N，在全域以南）管，域内均匀生效 → **不应该**跳

实测（SSP5-8.5 Default，h1 逐 PFT 输出，2097-2099 平均，第 163→164 行）：

| | 1月 | 7月 |
|---|---|---|
| **草本** | 2349.9 → **361.6（−1988.2，塌 85%）** | 4985.1 → 4576.5（−408.6，−8%） |
| **树木** | 1447.5 → **1475.1（+27.5，不降反升）** | 4460.5 → 4520.7（+60.2，+1%） |

草本 1 月塌 85%，树木在同一行同一时刻**毫无反应**（甚至微升）。两者共处同一次
模拟、同一批格点——除了 PFT 类型没有任何差异。**机制到此完全隔离，无其他解释空间。**

图：`20260910_seus_rerun/20260915_seus_4km_fut_management_scenarios/figure/gpp_pft_jan_jul_daylength.png`

## 排除过的其他解释（**别重复查**）

以下场在第 163→164 行全部**平滑**，都不是成因：

| 检查项 | 结果 |
|---|---|
| landuse `PCT_NAT_PFT` 森林/草地构成（2024/2050/2100） | 平滑 |
| C3/C4 草地比例 `w14 = C4/grass` 行均值 | 平滑（0.147 vs 0.145） |
| 森林总量 `forest_2100`、`PCT_NATVEG` | 平滑（−2.07%，属正常波动） |
| `HARVEST_VH1` 采伐场（LUH2 降尺度） | 平滑 |
| 气象驱动 `TBOT`/`TSA`/`RAIN`/`FSDS`（10年年均） | 全部平滑单调 |
| 土壤磷 `APATITE_P`/`LABILE_P`/`OCCLUDED_P`/`SECONDARY_P` | 平滑 |
| 土壤质地 `PCT_SAND`/`PCT_CLAY`/`ORGANIC`/`SOIL_COLOR`/`SOIL_ORDER` | 平滑 |
| `FMAX`/`SLOPE`/`STD_ELEV` | 平滑 |
| 人口密度 `hdm`（火的人为点火源） | 平滑（双线性，只有斜率拐点无台阶） |
| 火 `FAREA_BURNED`/`PFT_FIRE_CLOSS` | **在同一行跳，但是结果不是原因**（植被少→燃料少） |

另外两个走过的弯路，记下来免得别人再走：

1. **"低草地格点导致 `w_k = p(k,2023)/grass_2023` 除法病态"**——这个机制**真实存在**
   （相邻格点 w14 能差 20 倍，DF 的 C4 占比随之从 0.4% 跳到 13.6%），但**不是这条线
   的成因**：第 164 行全部 325 个格点做散点，`grass_2023` 与 `DF−Default GPP` 的
   Pearson r = **0.091**、Spearman ρ = 0.166，只能解释不到 1% 的方差。它是叠加在这条
   线上的**局部噪声**，值得单独修（见下），但别拿它解释这条线。
2. **"线与州界重合"**——阿拉巴马/佐治亚南界在 31.00°N，这条线在 30.833°N，**差 0.17°
   （约 19 km）**。缩略图上肉眼分不出来，容易误判成行政边界/数据拼接缝。另外画图代码
   如果叠加了 `cfeature.STATES`，那条灰线本身也会加重误判——但**去掉全部叠加线重画，
   这条线依然存在**（已验证），所以它确实在数据里。

## 对结果解读的影响

1. **30.833°N 南北两侧的草本碳循环结果不可直接比较。** 南侧模型把草当成全年常绿
   （冬季仍在光合），北侧每年冬天强制落叶。
2. **`Default − DF` 的碳收益估计在跨越这条线时有人为不连续**，做区域汇总（尤其是
   南北跨线的区域平均、或做纬度梯度分析）时会被这个阈值污染。
3. **草本占比越高的情景受影响越大**：DF ≫ Default ≈ RH > RF。
4. 这条线在**新旧两族 4km 模拟里都存在**（20260908 族与 20260915/17 族），**0.5° 的
   模拟也有**（已于 2026-09-21 验证）——三者共用同一份 paramfile 和同一段代码。

   0.5° 的网格行在 …30.25, 30.75, **31.25**, 31.75…，阈值 30.833°N 正好落在 30.75
   与 31.25 两行之间。ELM 按格点中心纬度算日长，所以 30.75 行冬季保持活跃、31.25 行
   被强制休眠。实测（SSP5-8.5，2091-2100 平均，30.75 → 31.25 行）：

   | | 1月 | 7月 |
   |---|---|---|
   | Default | 1578 → 1180（**−25%**） | 4491 → 4403（−2%） |
   | DF | 2099 → 813（**−61%**） | 4452 → 4089（−8%） |

   签名与 4km 完全一致：1月在阈值行边界上巨幅跳变、7月几乎消失、幅度随草本占比缩放。
   差别只在空间表现形式——4km（0.042° 网格）是一条细线，0.5° 是一个粗行边界。
5. 若要消除，需要改 paramfile 里的 `crit_dayl_stress`（例如改回代码默认的 21600 s），
   但那会改变所有草本的物候行为，**必须重跑**，且需要先确认 36000 s 这个值当初是为
   什么设的（2017 年就在这份 paramfile 里了，早于本项目）。

## 2026-09-22 更新：0.5° 用 `crit_dayl_stress = 38000 s` 重跑的结果

**做了什么。** 38000 s = 10.56 h，冬至日长等于它的纬度是 23.44°N，在整个研究区
以南，所以每个格点每年冬天都会被强制休眠，不再有"南边从不休眠、北边休眠"的分界。
新 paramfile：`/projects/hpcl-cli185/proj-shared/zw5/20260910_seus_rerun_inputs/clm_params_SEUS_c260922_cds38000.nc`
（只改了这一个变量）。分两轮重跑 0.5° future（2024-2100，4 个 SSP），每个新
case 都是原 case 的 `--keepexe` 克隆，`lnd_in` 与原 case 只差 `paramfile` 一行：

| 轮次 | case | 源 case |
|---|---|---|
| 1：只改 DF | `20260922_seus_halfdeg_future_ssp*_DF_cds38000_dt3600` | `2026091{1,5}_..._DF_dt3600` |
| 2：Default 也改（方案 A） | `20260922_seus_halfdeg_future_ssp*_cds38000_dt3600` | `20260911_..._ssp*_dt3600` |

分析：`20260910_seus_rerun/20260922_seus_halfdeg_DF_cds38000/analyze_df_cds38000.py`
（Slurm 作业 555823；第一轮只有 DF 时的输出存在本地 `outputs/round1_DF_only/`）。
以下均为 2091-2100 平均。

**1. 线在 `Default − DF` 里消失了——但只有两边都改才行。** 阈值两行
（30.75 → 31.25°N）上 `Default − DF` 差值曲线的跳变，对比这条曲线在其他相邻行之间
的正常起伏（中位数），格式为 跳变 / 起伏，单位 gC m⁻² yr⁻¹：

| | 两边 36000 | 只改 DF | 两边 38000 |
|---|---|---|---|
| 1 月，SSP1-1.9 … SSP5-8.5 | +639/23 … +902/54 | −304/58 … −416/76 | **−59/69 … −75/75（在噪声内）** |
| 全年 | +218/31 … +287/57 | −34/64 … +1/32 | **+14/51 … +36/35（在噪声内）** |

只改 DF 时，Default 自身的台阶（1 月 −311 到 −423）原封不动地留在差值里，方向反过来，
约为原来的 40-55%。7 月在阈值处 +25 到 +144 的落差在两种 38000 配对里几乎一样，与
阈值无关。

**2. 代价：南部的草冬天也休眠了。** 38000 s 下日长低于阈值的时间段在 25.25°N 为
11/29-1/12，在 30.75°N 为 11/09-1/31，在 35.25°N 为 10/31-2/10，所以全域 1 月基本
都是休眠状态：DF 的草在 30°N 以北 1 月 GPP ≈ 0，佛罗里达南部从 2000-3000 降到约
400。年 GPP 减少集中在旧阈值以南（SSP5-8.5 DF 为 −15% 到 −25%，Default 在南佛罗
里达和路易斯安那沿海最多 −20%），以北只有 0 到 −5%。模式里 DF 的草 85% 是 C3 草，
而现实中东南部的 C3 冷季草冬季是活跃的，所以 38000 s 在南部是一个偏强的休眠假设。

**3. 参数效应（新 − 旧，土地利用相同），全域 GPP：**
- **DF：** −6% 到 −8%（几乎全部来自 stress-deciduous：C3 草为主，作物 −7% 到 −8%，
  BDS 灌木 −8%）
- **Default：** −3% 到 −4%（stress-deciduous 的 PFT 各 −7% 到 −9%，树木不变）
- 作物**不是**干净的对照：`create_crop_landunit = .false.`，作物 PFT 15 与 DF 新增的草
  共用自然植被土壤 column

**4. 碳收益（`Default − DF`）变大，这部分来自参数。** 累计 NBP 2024-2100：两边
36000 为 10.1-11.0 PgC；只改 DF 为 +7.3% 到 +8.4%；**两边 38000 为 +5.3% 到 +5.9%**
（10.7-11.7 PgC，多约 0.55-0.65 PgC）。2100 年底的 TOTECOSYSC 差值结论相同
（两边 38000 为 +5.0% 到 +5.7%）。原因是同一参数对 DF（几乎全是草）的影响比对
Default 大。

**结论。** 要让 `Default − DF` 里没有这条线，Default 和 DF 必须用同一个 38000 s；
只改 DF 不够。代价是碳收益约 +5-6%，以及南部冬季休眠偏强，两者都需要在写作中说明。
起点状态（transient 2024 restart）仍是 36000 s 下 spin-up 出来的，只从 2024 年换参数。

## 复现用的代码

- **按 PFT 分开的冬夏图（决定性证据）**：`20260910_seus_rerun/20260915_seus_4km_fut_management_scenarios/code/plot_pft_seasonal_daylength.py`
- 冬夏空间图（Default vs DF）：`20260910_seus_rerun/20260915_seus_4km_fut_management_scenarios/code/plot_seasonal_daylength_artifact.py`
- 12 情景年均 GPP 图：同目录 `plot_all_scenarios_gpp.py`
- 早期（已被证伪的）低草地假设诊断图：同目录 `diagnose_df_gpp_line.py`
  —— 保留作为"这个解释不成立"的记录，别当成结论
