#!/usr/bin/env Rscript

# Small-cache companion to plot_comparison.py.  Runs on the local Mac with
# ncdf4 and ggplot2; no Pathfinder job or raw 4 km h0 read is required.

suppressPackageStartupMessages(library(ncdf4))
suppressPackageStartupMessages(library(ggplot2))

script_arg <- grep("^--file=", commandArgs(), value = TRUE)
if (length(script_arg) != 1L) stop("Run this file with Rscript")
root <- dirname(normalizePath(sub("^--file=", "", script_arg)))
cache_dir <- file.path(root, "_cache")
output_dir <- file.path(root, "outputs")
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

cases <- c(
  transient = "Transient",
  ssp119 = "SSP1-1.9",
  ssp245 = "SSP2-4.5",
  ssp370 = "SSP3-7.0",
  ssp370_RF = "SSP3-7.0 RF",
  ssp370_DF = "SSP3-7.0 DF",
  ssp370_RH = "SSP3-7.0 RH",
  ssp585 = "SSP5-8.5"
)

variables <- c(
  "GPP", "NPP", "NBP", "SOC_0_30cm", "TOTSOMC_1m",
  "FAREA_BURNED", "PFT_FIRE_CLOSS", "burned_area_km2",
  "PFT_FIRE_CLOSS_PgC", "NBP_PgC"
)

units <- c(
  GPP = "gC m-2 yr-1",
  NPP = "gC m-2 yr-1",
  NBP = "gC m-2 yr-1 (+ = sink)",
  SOC_0_30cm = "gC m-2",
  TOTSOMC_1m = "gC m-2",
  FAREA_BURNED = "percentage points yr-1",
  PFT_FIRE_CLOSS = "gC m-2 yr-1"
)

rows <- vector("list", length(cases) * length(variables))
index <- 0L
for (key in names(cases)) {
  old_path <- file.path(cache_dir, paste0("20260908__", key, ".nc"))
  new_path <- file.path(cache_dir, paste0("20260910_rerun__", key, ".nc"))
  if (!file.exists(old_path) || !file.exists(new_path)) {
    stop("Missing paired cache for ", key)
  }
  old <- nc_open(old_path)
  new <- nc_open(new_path)
  old_year <- as.integer(ncvar_get(old, "year"))
  new_year <- as.integer(ncvar_get(new, "year"))
  if (!identical(old_year, new_year)) {
    stop("Year coordinates differ for ", key)
  }
  for (variable in variables) {
    a <- as.numeric(ncvar_get(old, variable))
    b <- as.numeric(ncvar_get(new, variable))
    index <- index + 1L
    rows[[index]] <- data.frame(
      case_key = key,
      case_label = unname(cases[[key]]),
      year = old_year,
      variable = variable,
      old = a,
      new = b,
      new_minus_old = b - a
    )
  }
  nc_close(old)
  nc_close(new)
}

annual <- do.call(rbind, rows)
annual$case_label <- factor(annual$case_label, levels = unname(cases))
csv_path <- file.path(output_dir, "annual_series.csv")
write.csv(annual, csv_path, row.names = FALSE, na = "")
message("Wrote ", csv_path, " (", nrow(annual), " rows)")

for (variable in names(units)) {
  plotted <- annual[annual$variable == variable, ]
  fig <- ggplot(plotted, aes(x = year, y = new_minus_old)) +
    geom_hline(yintercept = 0, color = "grey40", linewidth = 0.3) +
    geom_line(color = "#7B3294", linewidth = 0.45) +
    facet_wrap(~case_label, ncol = 2, scales = "free") +
    labs(
      title = paste("SEUS 4 km rerun effect by year:", variable),
      subtitle = "20260910 rerun minus 20260908 simulation",
      x = "Year",
      y = paste("New - old (", units[[variable]], ")", sep = "")
    ) +
    theme_bw(base_size = 10) +
    theme(
      panel.grid.minor = element_blank(),
      strip.background = element_rect(fill = "grey94", color = "grey75")
    )
  out_path <- file.path(output_dir, paste0("delta_timeseries_", variable, ".png"))
  ggsave(out_path, plot = fig, width = 13, height = 12, dpi = 170, bg = "white")
  message("Wrote ", out_path)
}
