# -*- coding: utf-8 -*-
"""
文件名：短线选股软件_v6.6.2.py
版本：v6.6.2（保留V6.5东财K线；修复东财VOL量比兜底；修复920北交所CSS后缀；保存完整控制台日志）
日期：2026-05-11
基于：短线选股软件_v6.0.py 复制并改入口

【v6.6.2 修复摘要】
  - 修复东财 css 中 920xxx 北交所代码被拼成 .SZ，导致整批行业补全失败的问题。
  - 将东财 css 名称/行业批量降到更稳的小批量，并兼容 SECURITYNAME / SECURITY_NAME 字段。
  - 东财 K 线保留 v6.5 可用路径；若 VOL 缺失/不可用，则用 AMOUNT/CLOSE 作为量能代理，避免全量“量能缺失”。
  - 对 K 线 open/high/low/close/volume/amount 做统一数值清洗，兼容逗号字符串和空值。

【v6.6.1 修复摘要】
  - 回滚 v6.6 中对东财 K 线解析路径的改动，保留 v6.5 已验证可用的 EMQuantAPI K 线逻辑。
  - 修复成交量/量比 NaN 导致量能状态全部误判为“正常”的问题。
  - 输出新增“成交量”“5日均量”，量比缺失时输出 null，并标注“量能缺失”。
  - 增强东财 css 失败日志，打印 fields/options/ErrorCode/ErrorMsg/codes_sample。
  - 自动保存完整控制台日志到 选股结果/console_logs/，便于后续排查问题。

【与 v6.0 的分工（务必读）】
  - v6.0（短线选股软件_v6.0.py）：热门候选由程序调用 get_hot_stocks（东财/Tushare/AK 并行择优）自动拉取。
  - v6.5（本文件）：**不再调用 get_hot_stocks**；候选股票仅从本地文件读取（默认 `热门股名单/默认热门名单.txt`，
    多份名单可放在 `热门股名单/` 下，改 `HOT_LIST_FILE` 指向具体文件；也可把 `HOT_LIST_FILE` 设为目录名，程序自动读该目录下 `默认热门名单.txt`）。
    `.txt` 若为「制表符 + 表头（含 代码 或 编号/序号）」表格，会读**代码列**，不会把行号当成证券代码；纯文本仍支持每行一只代码。
    另支持 选股配置.json 的 `HOT_LIST_FILE`、环境变量 `STOCK_HOT_LIST_FILE`、命令行 `--hot-list`。
  - 两版均保留：涨停池 get_limit_up_pool、K 线多源、筛选与 run_meta/报告链。

说明（v6.0 历史摘要，底层逻辑与本分支一致部分仍适用）：
  - CONFIG_PRESET、相对强度占位、config_hash 忽略「_」前缀键等见 DEFAULT_CONFIG 与 选股配置.json.example。
  - 以下含历史版本变更摘要（自 v5.9.x；逻辑在 v6.0/v6.5 延续）：
  - 已整合的增强包括：东财 K 线 DATES/Ispandas=1、sector/.em_cache、css 重试、css 批量名称与行业、
    build_screener_signal_row 抽取、AK 名称补全重试、FINAL_REPORT/Excel 强信号分层、打开本轮报告.txt、
    MAP_DRIVE_FOR_CURSOR.cmd（改善 Cursor 聊天内 file 链接）、等。

v5.9.2 相对 v5.9.1 的主要变更：
  - （补丁）K 线回溯默认改为约 90 交易日量级；指标默认偏短线（MACD/BOLL/RSI/CCI/KDJ/WR/PSY/MTM/DMI/ATR 周期缩短，MA 中期由 MA60 改为可配 MA30）；无交易日历时 `get_last_trade_date` 大跨度回推修正；Tushare 热门/实时报价与选股 `trade_date` 对齐；东财 K 线北交所 8/4 后缀；Python 3.8 下高失败率中止不再使用 `cancel_futures`；裸 `except` 改为 `Exception`。
  - 每次运行结果写入 `选股结果/batch_{K线截止日}_{运行时间戳}/` 子文件夹，便于查找与多轮对比；保留天数清理同时支持该子目录与旧版平铺文件。
  - 默认配置不再内置明文账号/Token；请用 选股配置.json、环境变量 EMQUANT_USER/EMQUANT_PASSWORD/TUSHARE_TOKEN。
  - 登录东财时不打印含密码的 start_options；run_meta 增加「生效配置摘要」（自动脱敏）。
  - 新增可调：DISPLAY_TOP_MIN_SCORE、MIN_VOL_RATIO_STRICT、WR_OVERSOLD_SINGLE、WR_OVERSOLD_FOR_RESONANCE、
    ERROR_ABORT_ON_HIGH_FAILURE_RATE、CACHE_FLUSH_EVERY_N；东财热门股路径按 MIN_PRICE 过滤与 AK 路径一致。
  - 无东财实例时，K 线并行源顺序改为 AKShare 优先于 Tushare，减轻 mass K 线场景的积分/频控压力。
  - 聚宽数据：可选 `jqdatasdk`（`ENABLE_JQDATA` + `JQ_USERNAME`/`JQ_PASSWORD`）；K 线在东财之后、无东财时优先于 AK/Tushare，减轻网页断连。
  - 命令行：--no-em / --top-hot N / --target-date YYYYMMDD / --config 路径。
  - 控制台「高分列表」行数由 DISPLAY_TOP_N 控制（0 表示自动取 min(100,TOP_HOT)）；HTML 热力图表格行数由 HTML_CHART_TOP_N 控制。
  - 每轮 batch 目录内自动生成 FINAL_REPORT_*.md；同时在 选股结果/打开本轮报告.txt 写入可复制路径（避免 Cursor 对聊天内 file://+中文路径报 Unable to resolve resource）。
  - 不含任何券商自动下单接口；非逐日资金曲线回测引擎，一年 walk-forward 需另行开发。
  - 东财：sector 成分列表按交易日缓存至 `选股结果/.em_cache`；css 批量请求有限次重试；css 批量补证券简称与行业（HYBLOCK 等）并复用于 industry_map；选股核心行逻辑抽为 `build_screener_signal_row` 便于后续按日调用。
  - AKShare：名称补全现货接口带可配置重试次数/间隔。

v5.9.1 相对 v5.9 的主要变更：
  - EMQuantAPI：`c.sector` 参考日与选股 K 线日线截止日 `trade_date` 对齐（YYYY-MM-DD）；`css` 的 `TradeDate` 使用官方 demo 的 YYYYMMDD 形式；热门股与涨停池使用不同板块代码（`选股配置.json`：`EM_SECTOR_CODE_HOT` / `EM_SECTOR_CODE_ZT`，默认与官网命令生成器：001071 / 001048）；`sector` 保留第三参 `Ispandas=0`（与官方 Python2/3 demo 一致）；成分代码规范为带 `.SH/.SZ/.BJ` 后缀再批量 `css`。
  - `get_hot_stocks` / `get_limit_up_pool` 增加可选参数 `trade_date`（YYYYMMDD），由 `run_screener` 传入。
  - 板块成分解析：与官方策略示例（如 DemoStrategy_HindenburgOmen 中 `code.Codes`）一致，**优先使用 `sector` 返回对象的 `Codes` 属性**，为空时再回退解析 `Data`。

v5.9 相对 v5.8.2 的主要变更（东方财富客服图示）：
  - EMQuantAPI 登录：`c.start(start_options)` 单参调用，与客服提供的 Python 交互示例一致。
  - `start_options` 格式：`UserName=<账号>, Password=<密码>, ForceLogin=1`（逗号后带空格；密码以客服确认为准，默认与图示一致无 @）。
  - 其余逻辑与 v5.8.2 相同（数据源优先级、名称补全、Tushare 节流、登录失败不重试等）。

默认假设：沪深北 A 股现货 **T+1**（当日买入、最早下一交易日可卖）；不含两融「卖券还款」等当日回转场景。

功能分配：
  1. 东方财富 EMQuantAPI（主）: K线数据、交易日历、行业映射
  2. Tushare（辅）: 热门股、涨停池、实时行情
  3. AKShare（备）: 实时行情、涨停池、大盘数据、资金流向
  4. 聚宽 jqdatasdk（可选）: 日线 K 线（需 `pip install jqdatasdk` 与账号，遵守聚宽数据协议）

数据源选用策略（v5.9）：
  - K 线：并行拉取；有东财时 东财→聚宽(若启用)→Tushare→AKShare；无东财时 聚宽(若启用)→AKShare→Tushare。
  - 热门股 / 涨停池 / 行业映射：并行拉取后按东财→Tushare→AKShare 优先级采纳。
  - 实时行情：优先 AKShare 新浪，其次 Tushare、最后东财。
  - 资金流向：优先东财，再 AKShare、Tushare。
"""

import akshare as ak
import argparse
import pandas as pd
import numpy as np
import hashlib
import json
import re
import time
import warnings
import requests
import os
import shutil
import sys
import threading
from contextlib import contextmanager
from html import escape as html_escape
from datetime import datetime, timedelta
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Iterator, Optional, Tuple

SCAN_CACHE_LOCK = threading.Lock()
AKSHARE_NET_LOCK = threading.Lock()
_JQ_API_LOCK = threading.Lock()
_JQ_AUTH_OK = False

warnings.filterwarnings('ignore')


class _TeeStream:
    """同时输出到屏幕和日志文件。"""
    def __init__(self, *streams):
        self.streams = streams

    def write(self, data):
        for stream in self.streams:
            try:
                stream.write(data)
            except Exception:
                pass

    def flush(self):
        for stream in self.streams:
            try:
                stream.flush()
            except Exception:
                pass

    @property
    def encoding(self):
        return getattr(self.streams[0], "encoding", "utf-8")


_ORIG_STDOUT = sys.stdout
_ORIG_STDERR = sys.stderr
_CONSOLE_LOG_FILE = None


def setup_console_log() -> None:
    """保存完整控制台日志，方便以后定位东财/AKShare/CSS/Traceback 等问题。"""
    global _CONSOLE_LOG_FILE
    if _CONSOLE_LOG_FILE is not None:
        return
    try:
        log_dir = Path("选股结果") / "console_logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / f"控制台日志_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        _CONSOLE_LOG_FILE = open(log_path, "w", encoding="utf-8", buffering=1)
        sys.stdout = _TeeStream(_ORIG_STDOUT, _CONSOLE_LOG_FILE)
        sys.stderr = _TeeStream(_ORIG_STDERR, _CONSOLE_LOG_FILE)
        print(f"[日志] 控制台完整日志保存到：{log_path.resolve()}")
    except Exception as e:
        _CONSOLE_LOG_FILE = None
        print(f"[日志] 控制台日志初始化失败：{e}")


setup_console_log()

# v6.5：用户热门名单默认放在独立子目录，便于存放多份名单文件
DEFAULT_HOT_LIST_DIR = "热门股名单"
DEFAULT_HOT_LIST_FILENAME = "默认热门名单.txt"
DEFAULT_HOT_LIST_RELATIVE = f"{DEFAULT_HOT_LIST_DIR}/{DEFAULT_HOT_LIST_FILENAME}"

# ═════════════════════════════════════════════════════════════════
# 全局配置
# ═════════════════════════════════════════════════════════════════
VERSION = "v6.7_风控评分系统+次日风险评估"

DEFAULT_CONFIG = {
    "TOP_HOT": 10,
    "MAX_POOL": 100,
    # K 线请求起点：run_screener 用 get_last_trade_date(min(HIST_DAYS+30, MAX_KLINE_TRADE_DAYS), trade_date)
    "HIST_DAYS": 90,
    # 单次拉 K 向历史回推的交易日数上限（与 HIST_DAYS+30 取小），控制东财 csd 等流量
    "MAX_KLINE_TRADE_DAYS": 60,
    "MIN_PRICE": 4.5, "MAX_TURNOVER_RATE": 35,
    "THREAD_WORKERS": 8, "BATCH_SIZE": 50, "ERROR_THRESHOLD": 0.35,
    # 控制台「TOP 展示」最低买入评分（与 RESONANCE_BUY_THRESHOLD 解耦，避免语义混淆）
    "DISPLAY_TOP_MIN_SCORE": 4,
    # 控制台高分列表行数；0 时 v6.5 在 run_screener 内改为 min(500, 名单只数)；仍可用正整数固定上限
    "DISPLAY_TOP_N": 0,
    # HTML 热力图表格与柱状图取前 N 只（按买入评分排序后的 df 头部）
    "HTML_CHART_TOP_N": 60,
    # 扫描硬过滤：最新日量比低于该值剔除（原写死 0.5）
    "MIN_VOL_RATIO_STRICT": 0.5,
    # 威廉指标：单项加分阈值 / 超卖共振计数阈值（原分别为 -80 / -85）
    "WR_OVERSOLD_SINGLE": -80,
    "WR_OVERSOLD_FOR_RESONANCE": -85,
    # 失败率超 ERROR_THRESHOLD 时是否终止整次扫描（False=仅告警并继续）
    "ERROR_ABORT_ON_HIGH_FAILURE_RATE": False,
    # 扫描进度缓存写入磁盘间隔（每新增 N 只股票 flush 一次，减轻 IO）
    "CACHE_FLUSH_EVERY_N": 25,
    # 东财 sector 成分代码本地缓存（减轻同日重复 sector 调用）；目录默认在 选股结果/.em_cache
    "EM_SECTOR_CACHE_ENABLED": True,
    "EM_SECTOR_CACHE_MAX_AGE_HOURS": 18,
    "EM_CACHE_DIR": "选股结果/.em_cache",
    "EM_CSS_MAX_RETRIES": 4,
    "EM_CSS_RETRY_SLEEP_SEC": 1.0,
    # 东财 css 批量名称/行业每批代码数；过大时部分账号/终端会失败，v6.6.2 默认降到 50
    "EM_CSS_BATCH_CODES": 50,
    # AKShare 网络失败重试（名称补全、热门等）
    "AKSHARE_REQUEST_RETRIES": 3,
    "AKSHARE_RETRY_SLEEP_SEC": 0.9,
    "MACD_FAST": 10, "MACD_SLOW": 22, "MACD_SIGNAL": 8,
    "KDJ_N": 7, "KDJ_K": 3, "KDJ_D": 3,
    "BOLL_PERIOD": 14, "BOLL_STD": 2,
    "RSI_PERIOD_SHORT": 6, "RSI_PERIOD_LONG": 10, "CCI_PERIOD": 10,
    "WR_PERIOD": 10,
    "PSY_PERIOD": 10,
    "MTM_PERIOD": 10,
    "DMI_PERIOD": 10,
    "ATR_PERIOD": 14,
    "MA_MID_PERIOD": 30,
    "RESONANCE_BUY_THRESHOLD": 5, "RESONANCE_URGENCY_CEILING": 6.5,
    "MARKET_CHECK_ENABLED": True, "MARKET_DROP_THRESHOLD": -1.5,
    "STOP_LOSS_ATR_MULT": 2.0, "STOP_LOSS_MA_MULT": 0.97, "TAKE_PROFIT_RR_RATIO": 2.0,
    "MAX_CONSECUTIVE_LIMIT_UP": 2, "INDUSTRY_MIN_STOCKS": 3,
    "HTML_REPORT_ENABLED": True,
    "ZT_LOCK_SHARE_STRONG": 50000000,
    "ZT_LOCK_SHARE_SUPER": 200000000,
    "FILTER_ST_IN_ZT": True,
    "ENABLE_MONEY_FLOW": False,
    "MIN_KDATA_DAYS": 20,
    # 为 True 时，AKShare 调用东财接口前短暂移除 HTTP(S)_PROXY，解决本机代理失效导致的 ProxyError
    "AKSHARE_IGNORE_SYSTEM_PROXY": True,
    # 多数据源并行查询超时（秒）
    "MULTI_SOURCE_TIMEOUT_SEC": 20,
    # 选股结果目录中，按「文件名里的运行时间戳」自动删除超过该天数的旧文件（0 表示不清理）
    "RESULT_RETENTION_DAYS": 7,
    # 东财 sector 板块代码（官网命令生成器；与官方 Python demo 中 001004 可能并存，以你本地配置为准）
    "EM_SECTOR_CODE_HOT": "001071",
    "EM_SECTOR_CODE_ZT": "001048",
    # ── 东方财富 EMQuantAPI（账号密码请放 选股配置.json 或环境变量；此处默认为空）──
    "ENABLE_EMQUANTAPI": True,
    "EMQUANT_USER": "",
    "EMQUANT_PASSWORD": "",
    # ── Tushare（留空则跳过；环境变量 TUSHARE_TOKEN）──
    "TUSHARE_TOKEN": "",
    # ── 聚宽 jqdatasdk（留空则跳过；环境变量 JQ_USERNAME / JQ_PASSWORD）──
    "ENABLE_JQDATA": True,
    "JQ_USERNAME": "",
    "JQ_PASSWORD": "",
    # 聚宽 get_price：前复权 pre 与 AK qfq 对齐习惯；频控间隔秒（0 表示不 sleep）
    "JQ_KLINE_FQ": "pre",
    "JQ_KLINE_SLEEP_SEC": 0.03,
    # 东财 csd 批量拉 K 时每批最多代码数（过大易失败，过小加速不明显）
    "EM_CSD_BATCH_CODES": 25,
    # v6：CONFIG_PRESET balanced|range|trend（仅对用户 JSON 未写的键补预设）；相对强度占位（默认关）
    "CONFIG_PRESET": "balanced",
    "RELATIVE_STRENGTH_ENABLED": False,
    "RELATIVE_STRENGTH_INDEX": "000300.SH",
    "RELATIVE_STRENGTH_LOOKBACK": 20,
    # ── v6.5：用户热门名单（相对 cwd 或绝对路径；多份名单建议放 热门股名单/ 下并改此键指向具体文件）
    "HOT_LIST_FILE": DEFAULT_HOT_LIST_RELATIVE,
    "HOT_LIST_MAX_CODES": 0,
}

# CONFIG_PRESET: balanced | range | trend
CONFIG_PRESET_OVERLAYS: dict[str, dict] = {
    "balanced": {},
    "range": {
        "RESONANCE_BUY_THRESHOLD": 5.5,
        "WR_OVERSOLD_FOR_RESONANCE": -82,
        "DISPLAY_TOP_MIN_SCORE": 4.5,
    },
    "trend": {
        "RESONANCE_BUY_THRESHOLD": 4.5,
        "MARKET_CHECK_ENABLED": True,
        "DISPLAY_TOP_MIN_SCORE": 3.5,
    },
}

CONFIG_FILE = Path(os.environ.get("STOCK_SCREENER_CONFIG", "选股配置.json"))
config = DEFAULT_CONFIG.copy()
# 用户 JSON 顶层键：用于 CONFIG_PRESET 仅对「未在 JSON 显式写出」的键兜底，避免覆盖手写调参
_config_json_explicit_keys: frozenset[str] = frozenset()
if CONFIG_FILE.exists():
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            _loaded_cfg = json.load(f)
        if isinstance(_loaded_cfg, dict):
            _config_json_explicit_keys = frozenset(str(k) for k in _loaded_cfg.keys())
            config.update(_loaded_cfg)
    except Exception as e:
        print(f"[配置] 读取失败: {e}，使用默认参数")
else:
    print(f"[配置] 未找到 {CONFIG_FILE}，使用内置默认（无密钥）。可复制 选股配置.json.example 为 选股配置.json 后填写。")

# 兼容旧版选股配置.json：补上新增字段默认值
for _cfg_key, _cfg_val in DEFAULT_CONFIG.items():
    config.setdefault(_cfg_key, _cfg_val)

# CONFIG_PRESET 非 balanced 时：仅对用户 JSON 中未出现的键应用预设（用户明写优先；完全自定义用 balanced）
_preset = str(config.get("CONFIG_PRESET", "balanced") or "balanced").strip().lower()
if _preset not in CONFIG_PRESET_OVERLAYS:
    _preset = "balanced"
_ov = CONFIG_PRESET_OVERLAYS.get(_preset) or {}
if _ov:
    for _ok, _ovv in _ov.items():
        if _ok not in _config_json_explicit_keys:
            config[_ok] = _ovv


def _sanitize_config_for_meta(cfg: dict) -> dict:
    """写入 run_meta 的配置快照（脱敏）。"""
    out = {}
    for k, v in cfg.items():
        if k in ("EMQUANT_PASSWORD", "TUSHARE_TOKEN", "JQ_PASSWORD"):
            s = str(v or "")
            out[k] = "（已配置）" if s.strip() else "（空）"
            continue
        if k in ("EMQUANT_USER", "JQ_USERNAME"):
            s = str(v or "").strip()
            out[k] = s[:3] + "****" if len(s) > 3 else ("（空）" if not s else "****")
            continue
        out[k] = v
    return out


def hydrate_globals_from_config() -> None:
    """根据全局 config 刷新模块级运行参数（供 CLI 改参后调用）。"""
    global TOP_HOT, MAX_POOL, HIST_DAYS, MAX_KLINE_TRADE_DAYS, MIN_PRICE, MAX_TURNOVER_RATE, THREAD_WORKERS, BATCH_SIZE, ERROR_THRESHOLD
    global DISPLAY_TOP_MIN_SCORE, DISPLAY_TOP_N, HTML_CHART_TOP_N, MIN_VOL_RATIO_STRICT, WR_OVERSOLD_SINGLE, WR_OVERSOLD_FOR_RESONANCE
    global ERROR_ABORT_ON_HIGH_FAILURE_RATE, CACHE_FLUSH_EVERY_N
    global MACD_FAST, MACD_SLOW, MACD_SIGNAL, KDJ_N, KDJ_K, KDJ_D, BOLL_PERIOD, BOLL_STD
    global RSI_PERIOD_SHORT, RSI_PERIOD_LONG, CCI_PERIOD, WR_PERIOD, PSY_PERIOD, MTM_PERIOD, DMI_PERIOD, ATR_PERIOD
    global MA_MID_PERIOD, RESONANCE_BUY_THRESHOLD, RESONANCE_URGENCY_CEILING
    global MARKET_CHECK_ENABLED, MARKET_DROP_THRESHOLD, STOP_LOSS_ATR_MULT, STOP_LOSS_MA_MULT, TAKE_PROFIT_RR_RATIO
    global MAX_CONSECUTIVE_LIMIT_UP, INDUSTRY_MIN_STOCKS, HTML_REPORT_ENABLED, ZT_LOCK_SHARE_STRONG, ZT_LOCK_SHARE_SUPER
    global FILTER_ST_IN_ZT, ENABLE_MONEY_FLOW, MIN_KDATA_DAYS, AKSHARE_IGNORE_SYSTEM_PROXY, MULTI_SOURCE_TIMEOUT_SEC
    global RESULT_RETENTION_DAYS, EM_SECTOR_CODE_HOT, EM_SECTOR_CODE_ZT

    TOP_HOT = config["TOP_HOT"]
    MAX_POOL = config["MAX_POOL"]
    HIST_DAYS = config["HIST_DAYS"]
    MAX_KLINE_TRADE_DAYS = max(30, int(config.get("MAX_KLINE_TRADE_DAYS", 100)))
    MIN_PRICE = config["MIN_PRICE"]
    MAX_TURNOVER_RATE = config["MAX_TURNOVER_RATE"]
    THREAD_WORKERS = config["THREAD_WORKERS"]
    BATCH_SIZE = config["BATCH_SIZE"]
    ERROR_THRESHOLD = config["ERROR_THRESHOLD"]
    DISPLAY_TOP_MIN_SCORE = float(config.get("DISPLAY_TOP_MIN_SCORE", 4))
    _dtn = int(config.get("DISPLAY_TOP_N", 0) or 0)
    DISPLAY_TOP_N = min(500, max(1, _dtn if _dtn > 0 else min(100, TOP_HOT)))
    _htn = int(config.get("HTML_CHART_TOP_N", 60) or 60)
    HTML_CHART_TOP_N = min(200, max(5, _htn))
    MIN_VOL_RATIO_STRICT = float(config.get("MIN_VOL_RATIO_STRICT", 0.5))
    WR_OVERSOLD_SINGLE = float(config.get("WR_OVERSOLD_SINGLE", -80))
    WR_OVERSOLD_FOR_RESONANCE = float(config.get("WR_OVERSOLD_FOR_RESONANCE", -85))
    ERROR_ABORT_ON_HIGH_FAILURE_RATE = bool(config.get("ERROR_ABORT_ON_HIGH_FAILURE_RATE", False))
    CACHE_FLUSH_EVERY_N = max(1, int(config.get("CACHE_FLUSH_EVERY_N", 25)))

    MACD_FAST, MACD_SLOW, MACD_SIGNAL = config["MACD_FAST"], config["MACD_SLOW"], config["MACD_SIGNAL"]
    KDJ_N, KDJ_K, KDJ_D = config["KDJ_N"], config["KDJ_K"], config["KDJ_D"]
    BOLL_PERIOD, BOLL_STD = config["BOLL_PERIOD"], config["BOLL_STD"]
    RSI_PERIOD_SHORT = config["RSI_PERIOD_SHORT"]
    RSI_PERIOD_LONG = config["RSI_PERIOD_LONG"]
    CCI_PERIOD = config["CCI_PERIOD"]
    WR_PERIOD = int(config.get("WR_PERIOD", 10))
    PSY_PERIOD = int(config.get("PSY_PERIOD", 10))
    MTM_PERIOD = int(config.get("MTM_PERIOD", 10))
    DMI_PERIOD = int(config.get("DMI_PERIOD", 10))
    ATR_PERIOD = int(config.get("ATR_PERIOD", 14))
    MA_MID_PERIOD = int(config.get("MA_MID_PERIOD", 30))
    RESONANCE_BUY_THRESHOLD = config["RESONANCE_BUY_THRESHOLD"]
    RESONANCE_URGENCY_CEILING = config["RESONANCE_URGENCY_CEILING"]
    MARKET_CHECK_ENABLED = config["MARKET_CHECK_ENABLED"]
    MARKET_DROP_THRESHOLD = config["MARKET_DROP_THRESHOLD"]
    STOP_LOSS_ATR_MULT = config["STOP_LOSS_ATR_MULT"]
    STOP_LOSS_MA_MULT = config["STOP_LOSS_MA_MULT"]
    TAKE_PROFIT_RR_RATIO = config["TAKE_PROFIT_RR_RATIO"]
    MAX_CONSECUTIVE_LIMIT_UP = config["MAX_CONSECUTIVE_LIMIT_UP"]
    INDUSTRY_MIN_STOCKS = config["INDUSTRY_MIN_STOCKS"]
    HTML_REPORT_ENABLED = config["HTML_REPORT_ENABLED"]
    ZT_LOCK_SHARE_STRONG = config["ZT_LOCK_SHARE_STRONG"]
    ZT_LOCK_SHARE_SUPER = config["ZT_LOCK_SHARE_SUPER"]
    FILTER_ST_IN_ZT = config["FILTER_ST_IN_ZT"]
    ENABLE_MONEY_FLOW = config["ENABLE_MONEY_FLOW"]
    MIN_KDATA_DAYS = config.get("MIN_KDATA_DAYS", 15)
    AKSHARE_IGNORE_SYSTEM_PROXY = bool(config.get("AKSHARE_IGNORE_SYSTEM_PROXY", True))
    MULTI_SOURCE_TIMEOUT_SEC = float(config.get("MULTI_SOURCE_TIMEOUT_SEC", 20))
    RESULT_RETENTION_DAYS = int(config.get("RESULT_RETENTION_DAYS", 7))
    EM_SECTOR_CODE_HOT = str(config.get("EM_SECTOR_CODE_HOT", "001071")).strip()
    EM_SECTOR_CODE_ZT = str(config.get("EM_SECTOR_CODE_ZT", "001048")).strip()


hydrate_globals_from_config()

CACHE_FILE = Path("scanning_cache.json")
STOCK_NAMES_CACHE_FILE = Path("stock_names_cache.json")
# run_screener 每轮开始时写入，供 fetch_kline_batch 写进度 JSON 携带 config_hash
RUN_SCREENER_CONFIG_HASH = ""


def _screener_config_hash() -> str:
    """用于扫描进度缓存：配置或程序版本变化则重扫。不含密码/Token 类键。"""
    safe: dict[str, Any] = {}
    for k, v in sorted(config.items()):
        if str(k).startswith("_"):
            continue
        ku = str(k).upper()
        if "PASSWORD" in ku or "TOKEN" in ku:
            continue
        if isinstance(v, (str, int, float, bool)) or v is None:
            safe[str(k)] = v
    safe["_APP_VERSION"] = VERSION
    b = json.dumps(safe, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.md5(b).hexdigest()


# 自 v5.9.2/v5.9.5：扫描缓存每线程递增，满 CACHE_FLUSH_EVERY_N 再写盘
_CACHE_FLUSH_COUNTER = 0


@contextmanager
def _without_http_proxy_env() -> Iterator[None]:
    """短暂移除系统级代理环境变量，避免 requests 走已失效代理（常见于东财 push2 接口）。"""
    removed: dict[str, str] = {}
    try:
        for key in list(os.environ.keys()):
            if key.upper() in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"):
                removed[key] = os.environ.pop(key)
        yield
    finally:
        os.environ.update(removed)


@contextmanager
def _akshare_call_guard() -> Iterator[None]:
    """串行化 AKShare 相关请求，并在需要时临时去掉系统代理环境变量。"""
    with AKSHARE_NET_LOCK:
        if AKSHARE_IGNORE_SYSTEM_PROXY:
            with _without_http_proxy_env():
                yield
        else:
            yield


# ═════════════════════════════════════════════════════════════════
# 1. 交易日历系统
# ═════════════════════════════════════════════════════════════════
CALENDAR_FILE = Path("trade_calendar.json")


def load_trade_calendar() -> list:
    if CALENDAR_FILE.exists():
        try:
            with open(CALENDAR_FILE, 'r') as f:
                data = json.load(f)
                if datetime.now().strftime('%Y') in data.get('update_year', ''):
                    dates = data.get('dates', [])
                    dates.sort()
                    return dates
        except Exception:
            pass

    print("[日历] 本地交易日历不存在或需更新，尝试获取...")
    try:
        with _akshare_call_guard():
            df = ak.tool_trade_date_hist_sina()
        dates = [d.strftime('%Y%m%d') for d in df['trade_date'].tolist()]
        dates.sort()
        with open(CALENDAR_FILE, 'w') as f:
            json.dump({'update_year': datetime.now().strftime('%Y'), 'dates': dates}, f)
        print(f"[日历] 获取成功，共{len(dates)}个交易日，已缓存")
        return dates
    except Exception as e:
        print(f"[日历] 获取失败: {e}，将回退到简易周末判断模式")
        return []


TRADE_DATES_CACHE = load_trade_calendar()


def get_last_trade_date(days_back: int = 1, base_date: str = None) -> str:
    target = base_date if base_date else datetime.now().strftime('%Y%m%d')
    if not TRADE_DATES_CACHE:
        d = datetime.strptime(target, '%Y%m%d')
        found = -1
        # 原逻辑最多回退 10 个自然日，在 HIST_DAYS+30 等大跨度时会错误返回 target，导致 K 线历史过短
        max_steps = max(400, days_back * 3 + 120)
        steps = 0
        while True:
            if d.weekday() < 5:
                found += 1
            if found == days_back:
                return d.strftime('%Y%m%d')
            d -= timedelta(days=1)
            steps += 1
            if steps > max_steps:
                return d.strftime('%Y%m%d')

    valid_dates = [d for d in TRADE_DATES_CACHE if d <= target]
    if not valid_dates: return target
    if len(valid_dates) <= days_back: return valid_dates[0]
    return valid_dates[-days_back - 1]


def normalize_stock_code(code: Any) -> str:
    """将任意常见格式的证券代码规范为 6 位数字字符串（与东财/涨停池对齐）。"""
    s = str(code).strip()
    if "." in s:
        s = s.split(".", 1)[0].strip()
    digits = "".join(ch for ch in s if ch.isdigit())
    if not digits:
        return str(code).zfill(6)[-6:]
    return digits.zfill(6)[-6:]


def _resolve_hot_list_path(rel_or_abs: str) -> Path:
    """
    热门名单路径：绝对路径直接用；否则相对当前工作目录（一般为项目根）。
    若路径存在且为目录，则读取该目录下的「默认热门名单.txt」（与 DEFAULT_HOT_LIST_FILENAME 一致）。
    """
    raw = str(rel_or_abs or "").strip()
    p = Path(raw) if raw else Path(DEFAULT_HOT_LIST_RELATIVE)
    if not p.is_absolute():
        p = Path.cwd() / p
    p = p.resolve()
    if p.is_dir():
        p = (p / DEFAULT_HOT_LIST_FILENAME).resolve()
    return p


_HOT_LIST_CODE_HEADERS = frozenset({"代码", "code", "CODE", "ts_code", "证券代码"})
_HOT_LIST_NAME_HEADERS = frozenset({"名称", "name", "NAME", "股票名称"})
_HOT_LIST_ROWNO_HEADERS = frozenset({"编号", "序号"})


def _split_hot_list_tab_row(line: str) -> list[str]:
    return [c.strip() for c in line.strip().split("\t")]


def _cell_looks_like_stock_code(cell: str) -> bool:
    if not cell or cell.startswith("#"):
        return False
    d = "".join(ch for ch in cell if ch.isdigit())
    if len(d) < 4:
        return False
    c6 = normalize_stock_code(cell)
    return bool(c6) and len(c6) == 6 and c6.isdigit()


def _try_parse_hot_list_text_as_code_table(text: str) -> Optional[pd.DataFrame]:
    """
    识别「制表符分隔」表：表头含 代码/code 列，或首列为 编号/序号 且第二列为证券代码。
    若不满足则返回 None，由 load_manual_hot_universe 回退到「每行首字段为代码」的旧逻辑。
    """
    raw_lines: list[str] = []
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        raw_lines.append(s)
    if len(raw_lines) < 2:
        return None
    tab_line_count = sum(1 for ln in raw_lines if "\t" in ln)
    if tab_line_count < max(2, int(len(raw_lines) * 0.3)):
        return None

    split_rows = [_split_hot_list_tab_row(ln) for ln in raw_lines]
    head = split_rows[0]
    second = split_rows[1] if len(split_rows) > 1 else []

    code_idx: Optional[int] = None
    name_idx: Optional[int] = None
    start = 0

    for i, cell in enumerate(head):
        if cell in _HOT_LIST_CODE_HEADERS:
            code_idx = i
        if cell in _HOT_LIST_NAME_HEADERS:
            name_idx = i
    if code_idx is not None:
        start = 1
    elif len(head) >= 2 and head[0] in _HOT_LIST_ROWNO_HEADERS:
        code_idx = 1
        name_idx = 2 if len(head) > 2 else None
        start = 1
    elif len(second) >= 2 and second[0].isdigit() and _cell_looks_like_stock_code(second[1]):
        code_idx = 1
        name_idx = 2 if len(second) > 2 else None
        start = 0
        if len(head) >= 2 and (not head[0].isdigit()) and head[0] not in _HOT_LIST_ROWNO_HEADERS:
            if not _cell_looks_like_stock_code(head[1] if len(head) > 1 else ""):
                start = 1

    if code_idx is None or code_idx < 0:
        return None

    acc_codes: list[str] = []
    acc_names: list[str] = []
    seen: set[str] = set()
    for row in split_rows[start:]:
        if code_idx >= len(row):
            continue
        raw_code = row[code_idx].strip()
        if not raw_code or raw_code in _HOT_LIST_CODE_HEADERS:
            continue
        c6 = normalize_stock_code(raw_code.split(".")[0] if "." in raw_code else raw_code)
        if not c6.isdigit() or len(c6) != 6:
            continue
        name = ""
        if name_idx is not None and name_idx < len(row):
            name = str(row[name_idx]).strip()
        if c6 in seen:
            continue
        seen.add(c6)
        acc_codes.append(c6)
        acc_names.append(name)

    if len(acc_codes) < 1:
        return None
    print(
        f"[热门名单] 制表符表解析（避免将「编号」列误当代码）："
        f"代码列索引={code_idx}，名称列={name_idx}，有效行={len(acc_codes)}"
    )
    return pd.DataFrame({"代码": acc_codes, "名称": acc_names})


def load_manual_hot_universe(list_path: Path, max_codes: int = 0) -> pd.DataFrame:
    """
    v6.5：从用户文件读取热门候选（不调用东财/Tushare/AK 热门接口）。
    - .csv：需含「代码」或 code/ts_code 等列；可选「名称」列。
    - .txt：优先识别「制表符 + 表头(代码/编号)」表格；否则按每行首字段为代码（600000 / 600000.SH）；# 开头为注释。
    """
    list_path = list_path.resolve()
    if not list_path.is_file():
        print(f"[热门名单] 未找到文件: {list_path}")
        return pd.DataFrame()
    suf = list_path.suffix.lower()
    try:
        if suf == ".csv":
            df = pd.read_csv(list_path, encoding="utf-8-sig")
            col_code = None
            for c in df.columns:
                cs = str(c).strip()
                if cs in ("代码", "code", "CODE", "ts_code", "证券代码"):
                    col_code = c
                    break
            if col_code is None:
                print(f"[热门名单] CSV 缺少代码列，实际列={list(df.columns)}")
                return pd.DataFrame()
            codes = df[col_code].map(
                lambda x: normalize_stock_code(str(x).split(".")[0] if "." in str(x) else str(x))
            )
            name_col = next(
                (c for c in df.columns if str(c).strip() in ("名称", "name", "NAME", "股票名称")),
                None,
            )
            names = df[name_col].astype(str).str.strip() if name_col else pd.Series([""] * len(df))
            out = pd.DataFrame({"代码": codes.astype(str), "名称": names.fillna("").values})
            out = out.drop_duplicates(subset=["代码"], keep="first").reset_index(drop=True)
        else:
            text = list_path.read_text(encoding="utf-8-sig")
            out = _try_parse_hot_list_text_as_code_table(text)
            if out is None or out.empty:
                acc: list[str] = []
                seen: set[str] = set()
                for line in text.splitlines():
                    s = line.strip()
                    if not s or s.startswith("#"):
                        continue
                    token = s.split()[0].split(",")[0].strip()
                    if not token:
                        continue
                    c6 = normalize_stock_code(token.split(".")[0] if "." in token else token)
                    if c6 not in seen:
                        seen.add(c6)
                        acc.append(c6)
                out = pd.DataFrame({"代码": acc, "名称": [""] * len(acc)})
            else:
                out = out.drop_duplicates(subset=["代码"], keep="first").reset_index(drop=True)
        if max_codes and len(out) > int(max_codes):
            out = out.iloc[: int(max_codes)].copy().reset_index(drop=True)
        print(f"[热门名单] 已载入 {len(out)} 只 ← {list_path}")
        return out
    except Exception as e:
        print(f"[热门名单] 解析失败: {e}")
        return pd.DataFrame()


def _em_csd_code(symbol: Any) -> str:
    """东财 csd/css：北交所 8/4 开头及 920xxx（6 位码以 92 开头）；沪 6 开头；其余 .SZ。"""
    code = normalize_stock_code(symbol)
    if code.startswith(("8", "4", "92")):
        return f"{code}.BJ"
    if code.startswith("6"):
        return f"{code}.SH"
    return f"{code}.SZ"


def _trade_date_compact(trade_date: Optional[str]) -> str:
    """trade_date 统一为 YYYYMMDD（可含横线）。"""
    if not trade_date:
        return datetime.now().strftime("%Y%m%d")
    s = str(trade_date).replace("-", "").strip()
    if len(s) >= 8 and s[:8].isdigit():
        return s[:8]
    digits = "".join(ch for ch in s if ch.isdigit())
    return digits.zfill(8)[-8:] if digits else datetime.now().strftime("%Y%m%d")


def _trade_date_yyyy_mm_dd(trade_date: Optional[str]) -> str:
    d = _trade_date_compact(trade_date)
    return f"{d[:4]}-{d[4:6]}-{d[6:8]}"


def _safe_float(value: Any, default: float = np.nan) -> float:
    """安全转 float；None/空串/NaN/非法值统一返回 default。"""
    try:
        out = float(value)
    except (TypeError, ValueError):
        return default
    return default if pd.isna(out) else out


def _round_or_none(value: Any, ndigits: int = 2):
    """输出用：避免 JSON 里写入非标准 NaN。"""
    out = _safe_float(value, np.nan)
    if pd.isna(out):
        return None
    return round(out, ndigits)

def _numeric_series(values: Any) -> pd.Series:
    """更宽松的数值清洗：兼容 Eastmoney 返回的逗号字符串、空串、-- 等。"""
    s = values if isinstance(values, pd.Series) else pd.Series(values)
    if pd.api.types.is_numeric_dtype(s):
        return pd.to_numeric(s, errors="coerce")
    cleaned = (
        s.astype(str)
        .str.replace(",", "", regex=False)
        .str.strip()
        .replace({"": np.nan, "--": np.nan, "None": np.nan, "nan": np.nan, "NaN": np.nan})
    )
    return pd.to_numeric(cleaned, errors="coerce")


def _prepare_kline_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    """
    统一 K 线 OHLCV 列名与数值类型。

    东财 csd 已验证会返回 DATES/OPEN/HIGH/LOW/CLOSE/VOL/AMOUNT，但个别环境中 VOL
    可能为空或字符串化；量比只依赖相对变化，因此在 VOL 不可用时用 AMOUNT/CLOSE
    作为量能代理，避免整批结果全部“量能缺失”。
    """
    if df is None or df.empty:
        return df
    df = df.copy()
    rename_map: dict[Any, str] = {}
    for c in df.columns:
        key = str(c).strip().upper().replace(" ", "_")
        if key == "OPEN":
            rename_map[c] = "open"
        elif key == "HIGH":
            rename_map[c] = "high"
        elif key == "LOW":
            rename_map[c] = "low"
        elif key == "CLOSE":
            rename_map[c] = "close"
        elif key in ("VOL", "VOLUME"):
            rename_map[c] = "volume"
        elif key in ("AMOUNT", "MONEY"):
            rename_map[c] = "amount"
    if rename_map:
        df.rename(columns=rename_map, inplace=True)

    for col in ("open", "high", "low", "close", "volume", "amount", "turnover_rate", "pct_change"):
        if col in df.columns:
            df[col] = _numeric_series(df[col])

    if "volume" not in df.columns:
        df["volume"] = np.nan
    if "amount" not in df.columns:
        df["amount"] = np.nan

    volume_valid = pd.to_numeric(df["volume"], errors="coerce")
    valid_volume_count = int(((volume_valid.replace([np.inf, -np.inf], np.nan)).fillna(0) > 0).sum())
    need_proxy = valid_volume_count < max(5, min(10, len(df) // 3))

    if need_proxy and "amount" in df.columns and "close" in df.columns:
        close_nonzero = pd.to_numeric(df["close"], errors="coerce").replace(0, np.nan)
        proxy_volume = pd.to_numeric(df["amount"], errors="coerce") / close_nonzero
        proxy_count = int(proxy_volume.replace([np.inf, -np.inf], np.nan).notna().sum())
        if proxy_count >= max(5, min(10, len(df) // 3)):
            df["volume"] = proxy_volume.replace([np.inf, -np.inf], np.nan)
            df["_volume_source"] = "AMOUNT/CLOSE代理"
        else:
            df["_volume_source"] = "缺失"
    else:
        df["volume"] = volume_valid.replace([np.inf, -np.inf], np.nan)
        df["_volume_source"] = "VOL"

    if "turnover_rate" not in df.columns:
        df["turnover_rate"] = 0.0
    if "close" in df.columns:
        df["pct_change"] = pd.to_numeric(df["close"], errors="coerce").pct_change() * 100.0
    return df


def _em_code_for_css(sym: Any) -> str:
    """官方 css/csd demo 使用 300059.SZ 形式；将 6 位或带后缀代码规范为东财截面常用写法。"""
    s = str(sym).strip()
    if not s:
        return s
    if "." in s:
        base, suf = s.split(".", 1)[0], s.split(".", 1)[1].strip().upper()
        digits = "".join(ch for ch in base if ch.isdigit()).zfill(6)[-6:]
        # 北交所 920xxx 若上游误带 .SZ，也要强制修正为 .BJ，否则 css 整批报 invalid stock code。
        if digits.startswith(("8", "4", "92")):
            return f"{digits}.BJ"
        if suf in ("SH", "SZ", "BJ"):
            return f"{digits}.{suf}"
        digits = "".join(ch for ch in s if ch.isdigit()).zfill(6)[-6:]
    else:
        digits = "".join(ch for ch in s if ch.isdigit()).zfill(6)[-6:]
    if not digits:
        return s
    if digits.startswith("6"):
        return f"{digits}.SH"
    if digits.startswith(("8", "4", "92")):
        return f"{digits}.BJ"
    return f"{digits}.SZ"


def _sector_constituent_codes(sector_result: Any) -> list[str]:
    """解析 c.sector 返回的代码列表（兼容 Data 为 list 或 dict 的 keys）。"""
    if sector_result is None:
        return []
    d = getattr(sector_result, "Data", None)
    if d is None:
        return []
    if isinstance(d, dict):
        return [str(k) for k in d.keys()]
    try:
        return [str(x) for x in d]
    except TypeError:
        return []


def _emquant_css_dataframe(css_result: Any) -> Optional[pd.DataFrame]:
    """将 c.css 返回统一为带 CODE 列的 DataFrame（兼容 Ispandas=0 时代码在索引、列名大小写不一致）。"""
    if css_result is None:
        return None
    if hasattr(css_result, "ErrorCode") and css_result.ErrorCode != 0:
        return None
    df: Optional[pd.DataFrame] = None
    if isinstance(css_result, pd.DataFrame):
        df = css_result.copy()
    elif hasattr(css_result, "Data") and getattr(css_result, "Indicators", None) is not None:
        try:
            df = pd.DataFrame(css_result.Data, columns=list(css_result.Indicators))
        except Exception:
            return None
    else:
        return None

    def _upper_columns(d: pd.DataFrame) -> pd.DataFrame:
        d = d.copy()
        d.columns = [str(c).upper() for c in d.columns]
        return d

    df = _upper_columns(df)
    if "CODE" not in df.columns:
        df = _upper_columns(df.reset_index())
    if "CODE" not in df.columns and "INDEX" in df.columns:
        sample = df["INDEX"].astype(str).head(3).tolist()
        if sample and any(".SH" in s or ".SZ" in s or ".BJ" in s for s in sample):
            df = df.rename(columns={"INDEX": "CODE"})
    if "CODE" not in df.columns and len(df.columns) >= 1:
        c0 = df.columns[0]
        known = ("AMOUNT", "CLOSE", "CHANGE", "PREVCLOSE", "OPEN", "HIGH", "LOW", "VOL", "PCTCHANGE")
        if c0 not in known:
            df = df.rename(columns={c0: "CODE"})
    if "CODE" not in df.columns:
        return None
    return df


def _sector_result_codes(sector_result: Any) -> list[str]:
    """与官方策略示例一致：DemoStrategy_HindenburgOmen 等使用 `code.Codes` 再 csd/css；优先 Codes，否则解析 Data。"""
    if sector_result is None:
        return []
    raw = getattr(sector_result, "Codes", None)
    if raw is not None and raw != "":
        try:
            if isinstance(raw, str):
                parts = [p.strip() for p in raw.split(",") if p.strip()]
                if parts:
                    return parts
                return []
            seq = list(raw)
            if seq:
                return [str(x) for x in seq]
        except (TypeError, ValueError):
            pass
    return _sector_constituent_codes(sector_result)


def _em_cache_base_dir() -> Path:
    return Path(str(config.get("EM_CACHE_DIR", "选股结果/.em_cache")))


def _em_sector_codes_cache_path(sector_code: str, ref_yyyy_mm_dd: str, kind: str) -> Path:
    ref = ref_yyyy_mm_dd.replace("-", "")
    return _em_cache_base_dir() / f"sector_{kind}_{sector_code}_{ref}.json"


def _em_try_load_sector_codes(path: Path) -> Optional[list]:
    if not bool(config.get("EM_SECTOR_CACHE_ENABLED", True)):
        return None
    try:
        if not path.is_file():
            return None
        max_h = float(config.get("EM_SECTOR_CACHE_MAX_AGE_HOURS", 18))
        age_h = (datetime.now().timestamp() - path.stat().st_mtime) / 3600.0
        if age_h > max_h:
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list) and len(data) > 0:
            print(f"[EM缓存] 使用已缓存 sector 代码列表: {path.name}（约 {age_h:.1f} 小时内）")
            return data
    except Exception:
        return None
    return None


def _em_save_sector_codes(path: Path, codes: list) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(codes, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass


def _em_css_call_with_retry(c, codes_str: str, indicators: str, options: str) -> Any:
    """东财 css 对大批量代码偶发 10000013 等，做有限次重试。"""
    n = max(1, int(config.get("EM_CSS_MAX_RETRIES", 4)))
    delay = float(config.get("EM_CSS_RETRY_SLEEP_SEC", 1.0))
    last: Any = None
    for i in range(n):
        last = c.css(codes_str, indicators, options)
        if hasattr(last, "ErrorCode") and getattr(last, "ErrorCode", -1) == 0:
            _ds_health_inc("em_css_attempt_ok")
            _ds_health_inc("em_css_invocation_ok")
            return last
        _ds_health_inc("em_css_attempt_fail")
        msg = getattr(last, "ErrorMsg", "") if last is not None else ""
        err_code = getattr(last, "ErrorCode", "") if last is not None else ""
        sample_codes = (codes_str[:120] + "...") if len(codes_str) > 120 else codes_str
        print(
            f"[EMQuantAPI] css 第 {i + 1}/{n} 次失败: "
            f"fields={indicators}, options={options}, ErrorCode={err_code}, "
            f"ErrorMsg={msg}, codes_sample={sample_codes}"
        )
        if i < n - 1:
            time.sleep(delay * (1.0 + 0.35 * i))
    _ds_health_inc("em_css_invocation_fail")
    return last


def _akshare_call_with_retries(fn, desc: str = "AKShare"):
    retries = max(1, int(config.get("AKSHARE_REQUEST_RETRIES", 3)))
    gap = float(config.get("AKSHARE_RETRY_SLEEP_SEC", 0.9))
    last_err: Optional[Exception] = None
    for i in range(retries):
        try:
            with _akshare_call_guard():
                out = fn()
            _ds_health_inc("ak_attempt_ok")
            return out
        except Exception as e:
            last_err = e
            _ds_health_inc("ak_attempt_fail")
            print(f"[{desc}] 第 {i + 1}/{retries} 次失败: {e}")
            if i < retries - 1:
                time.sleep(gap * (1 + i))
    if last_err:
        raise last_err
    raise RuntimeError(f"{desc} 调用失败")


# ── run_screener 本轮数据源健康度（写入 run_meta「数据源健康摘要」）──
_DS_HEALTH_LOCK = threading.Lock()
_SCREENER_DS_HEALTH: dict[str, Any] = {}


def _ds_health_reset() -> None:
    """每轮 run_screener 开始时清零。"""
    with _DS_HEALTH_LOCK:
        _SCREENER_DS_HEALTH.clear()
        _SCREENER_DS_HEALTH.update(
            {
                "em_css_attempt_ok": 0,
                "em_css_attempt_fail": 0,
                "em_css_invocation_ok": 0,
                "em_css_invocation_fail": 0,
                "ak_attempt_ok": 0,
                "ak_attempt_fail": 0,
                "em_hot_ok": 0,
                "em_hot_fail": 0,
                "ts_hot_ok": 0,
                "ts_hot_fail": 0,
                "ak_hot_ok": 0,
                "ak_hot_fail": 0,
                "get_hot_winner_class": None,
                "get_limit_up_winner_class": None,
                "manual_hot_list_path": "",
                "manual_hot_list_count": 0,
                "kline_smart_winner": {},
                "kline_em_batch_prefetch_hit": 0,
                "JoinQuantAdapter_kline_ok": 0,
                "JoinQuantAdapter_kline_fail": 0,
                "EMQuantAPIAdapter_kline_ok": 0,
                "EMQuantAPIAdapter_kline_fail": 0,
                "TushareAdapter_kline_ok": 0,
                "TushareAdapter_kline_fail": 0,
                "AKShareAdapter_kline_ok": 0,
                "AKShareAdapter_kline_fail": 0,
                "name_enrich_trace": [],
                "name_enrich_all_named": None,
                "screener_scan_success_rows": 0,
                "screener_scan_error_rows": 0,
            }
        )


def _ds_health_inc(key: str, n: int = 1) -> None:
    with _DS_HEALTH_LOCK:
        _SCREENER_DS_HEALTH[key] = int(_SCREENER_DS_HEALTH.get(key, 0)) + int(n)


def _ds_health_set(key: str, val: Any) -> None:
    with _DS_HEALTH_LOCK:
        _SCREENER_DS_HEALTH[key] = val


def _ds_health_append_trace(msg: str) -> None:
    if not msg:
        return
    with _DS_HEALTH_LOCK:
        t = _SCREENER_DS_HEALTH.setdefault("name_enrich_trace", [])
        if not t or t[-1] != msg:
            t.append(msg)


def _ds_health_inc_kline_winner(cls_name: str) -> None:
    with _DS_HEALTH_LOCK:
        d = _SCREENER_DS_HEALTH.setdefault("kline_smart_winner", {})
        d[cls_name] = int(d.get(cls_name, 0)) + 1


def _mark_hot_health(adapter_key: str, df: Optional[pd.DataFrame]) -> pd.DataFrame:
    """各适配器 get_hot_stocks 出口（并行时三者各计一次）。"""
    if df is not None and isinstance(df, pd.DataFrame) and not df.empty:
        _ds_health_inc(f"{adapter_key}_hot_ok")
        return df
    _ds_health_inc(f"{adapter_key}_hot_fail")
    return pd.DataFrame()


def _mark_kline_health(cls_name: str, df: Optional[pd.DataFrame]) -> pd.DataFrame:
    """各适配器 get_kline 出口统计。"""
    if df is not None and isinstance(df, pd.DataFrame) and not df.empty:
        _ds_health_inc(f"{cls_name}_kline_ok")
        return df
    _ds_health_inc(f"{cls_name}_kline_fail")
    return pd.DataFrame()


def _ds_health_export_summary(
    hot_nonempty: bool,
    scan_total: int,
    scan_success_rows: int,
    scan_error_rows: int,
) -> dict[str, Any]:
    """生成写入 run_meta 的中文摘要（结构化）。"""
    with _DS_HEALTH_LOCK:
        snap = dict(_SCREENER_DS_HEALTH)
    winner = snap.get("get_hot_winner_class")
    manual_path = str(snap.get("manual_hot_list_path") or "").strip()
    manual_cnt = int(snap.get("manual_hot_list_count") or 0)
    if manual_path:
        winner = "UserHotListFile"
        hot_src = f"用户名单文件：{manual_path}（载入{manual_cnt}只）"
    else:
        hot_src = _ds_health_hot_source_cn(winner)
    zt_w = snap.get("get_limit_up_winner_class")
    zt_src = _ds_health_cls_display(zt_w) if zt_w else "（无）"

    jq_ok = int(snap.get("JoinQuantAdapter_kline_ok", 0))
    jq_fail = int(snap.get("JoinQuantAdapter_kline_fail", 0))
    em_ok = int(snap.get("EMQuantAPIAdapter_kline_ok", 0))
    em_fail = int(snap.get("EMQuantAPIAdapter_kline_fail", 0))
    ts_ok = int(snap.get("TushareAdapter_kline_ok", 0))
    ts_fail = int(snap.get("TushareAdapter_kline_fail", 0))
    ak_ok = int(snap.get("AKShareAdapter_kline_ok", 0))
    ak_fail = int(snap.get("AKShareAdapter_kline_fail", 0))

    prefetch_n = int(snap.get("kline_em_batch_prefetch_hit", 0))
    smart_w: dict[str, int] = {str(k): int(v) for k, v in (snap.get("kline_smart_winner") or {}).items()}
    smart_total = sum(smart_w.values())
    denom = prefetch_n + smart_total
    kline_main = _ds_health_kline_main_label(prefetch_n, smart_w, denom)

    trace = snap.get("name_enrich_trace") or []
    all_named = snap.get("name_enrich_all_named")
    name_ok = bool(all_named) if all_named is not None else None
    name_src = "、".join(trace) if trace else "（未触发补全或仅原始名称）"

    return {
        "热门股来源": hot_src,
        "热门股拉取成功": bool(hot_nonempty),
        "热门采纳适配器类名": winner or "",
        "东财css_尝试成功次数": int(snap.get("em_css_attempt_ok", 0)),
        "东财css_尝试失败次数": int(snap.get("em_css_attempt_fail", 0)),
        "东财css_整次调用成功次数": int(snap.get("em_css_invocation_ok", 0)),
        "东财css_整次调用失败次数": int(snap.get("em_css_invocation_fail", 0)),
        "AKShare_尝试成功次数": int(snap.get("ak_attempt_ok", 0)),
        "AKShare_尝试失败次数": int(snap.get("ak_attempt_fail", 0)),
        "东财热门接口_成功次数": int(snap.get("em_hot_ok", 0)),
        "东财热门接口_失败次数": int(snap.get("em_hot_fail", 0)),
        "Tushare热门接口_成功次数": int(snap.get("ts_hot_ok", 0)),
        "Tushare热门接口_失败次数": int(snap.get("ts_hot_fail", 0)),
        "AKShare热门接口_成功次数": int(snap.get("ak_hot_ok", 0)),
        "AKShare热门接口_失败次数": int(snap.get("ak_hot_fail", 0)),
        "涨停池采纳": zt_src,
        "聚宽K线_成功次数": jq_ok,
        "聚宽K线_失败次数": jq_fail,
        "东财逐只K线_成功次数": em_ok,
        "东财逐只K线_失败次数": em_fail,
        "TushareK线_成功次数": ts_ok,
        "TushareK线_失败次数": ts_fail,
        "AKShareK线_成功次数": ak_ok,
        "AKShareK线_失败次数": ak_fail,
        "K线_东财csd批量命中股票次数": prefetch_n,
        "K线_Smart源采纳次数按类": smart_w,
        "K线主来源": kline_main,
        "名称补全成功": name_ok,
        "名称补全路径": name_src,
        "扫描线程_成功处理股票数": int(scan_success_rows),
        "扫描线程_失败或跳过股票数": int(scan_error_rows),
        "扫描计划股票数": int(scan_total),
        "说明": (
            "热门/涨停/K 线为并行多源：「接口成功/失败」为各适配器实际调用次数；"
            "「K线主来源」按本批成功拿到 K 线的路径（东财批量预取 vs Smart 采纳的逐只源）估算占比。"
            "聚宽/Tushare/AK 失败多而东财成功时，结论更偏东财截面。"
        ),
    }


def _ds_health_cls_display(cls_name: Optional[str]) -> str:
    if not cls_name:
        return ""
    return {
        "EMQuantAPIAdapter": "东财EMQuantAPI",
        "TushareAdapter": "Tushare",
        "AKShareAdapter": "AKShare",
        "JoinQuantAdapter": "聚宽jqdatasdk",
    }.get(str(cls_name), str(cls_name))


def _ds_health_hot_source_cn(winner_class: Optional[str]) -> str:
    base = _ds_health_cls_display(winner_class) or "（无）"
    detail = {
        "EMQuantAPIAdapter": "东财：板块成分+当日 css 成交额(AMOUNT)排序",
        "TushareAdapter": "Tushare：全市场 daily 按 amount 排序",
        "AKShareAdapter": "AKShare：现货表按成交额排序",
    }.get(str(winner_class or ""), "")
    return f"{base}（{detail}）" if detail else base


def _ds_health_kline_main_label(prefetch_n: int, smart_w: dict[str, int], denom: int) -> str:
    if denom <= 0:
        return "无有效K线样本（本批未计入批量命中与逐只采纳）"
    parts: list[tuple[str, int]] = []
    if prefetch_n > 0:
        parts.append(("东财csd批量预取", prefetch_n))
    for cls, n in sorted(smart_w.items(), key=lambda x: -int(x[1])):
        parts.append((_ds_health_cls_display(cls), int(n)))
    top_lab, top_n = parts[0]
    pct = round(100.0 * float(top_n) / float(denom), 1)
    if len(parts) == 1:
        return f"{top_lab}（{pct}%）"
    sec = parts[1]
    return f"{top_lab}（{pct}%）; 其次{sec[0]}（{round(100.0 * sec[1] / denom, 1)}%）"


# ═════════════════════════════════════════════════════════════════
# 2. 工具函数与辅助判定
# ═════════════════════════════════════════════════════════════════
def get_limit_up_threshold(code: str) -> float:
    code = str(code).zfill(6)
    if code.startswith(('688', '300', '301')):
        return 19.8
    elif code.startswith(('8', '4')):
        return 30.0
    else:
        return 9.8


market_check_fail_count = 0


def check_market_environment(target_date: Optional[str] = None) -> Tuple[bool, str]:
    global market_check_fail_count
    if not MARKET_CHECK_ENABLED: return True, "大盘检查已禁用"

    try:
        with _akshare_call_guard():
            df = ak.stock_zh_index_daily(symbol="sh000001")
        if df.empty or len(df) < 10:
            market_check_fail_count = 0
            return True, "大盘数据不足"
        df['date'] = pd.to_datetime(df['date'])
        if target_date:
            df = df[df["date"] <= pd.Timestamp(str(target_date))]
        if len(df) < 65:
            market_check_fail_count = 0
            return True, f"大盘检查：指数历史不足65日(len={len(df)})，跳过MA60/MA20空头规则"

        latest = df.iloc[-1]
        prev = df.iloc[-2]
        pct_change = (float(latest['close']) - float(prev['close'])) / float(prev['close']) * 100.0
        closes = df['close'].astype(float)
        ma20_s = closes.rolling(20, min_periods=20).mean()
        ma60_s = closes.rolling(60, min_periods=60).mean()
        ma20_now = float(ma20_s.iloc[-1])
        ma20_5d_ago = float(ma20_s.iloc[-6])
        ma60_now = float(ma60_s.iloc[-1])
        close = float(latest['close'])
        if ma20_5d_ago <= 0 or np.isnan(ma20_now) or np.isnan(ma20_5d_ago) or np.isnan(ma60_now):
            market_check_fail_count = 0
            return True, "大盘检查：MA20/MA60未就绪，跳过空头规则"
        ma20_drop_pct = (ma20_5d_ago - ma20_now) / ma20_5d_ago * 100.0
        if ma20_drop_pct > 1.0 and close < ma60_now:
            market_check_fail_count = 0
            return False, f"空头环境：MA20近5交易日回落{ma20_drop_pct:.2f}%且收盘低于MA60"

        market_check_fail_count = 0
        return True, f"大盘正常（上证{pct_change:+.1f}%，MA20 5日回落{ma20_drop_pct:.2f}%）"
    except Exception as e:
        market_check_fail_count += 1
        print(f"\r[大盘] 获取指数失败(连续{market_check_fail_count}次): {e}")
        if market_check_fail_count >= 3:
            return False, "大盘数据连续失败>=3次，停止扫描"
        return True, f"大盘检查降级：数据暂不可用（{market_check_fail_count}/3），继续扫描 — {e!s}"


def calc_stop_loss_take_profit(df: pd.DataFrame, current_price: float) -> dict:
    candidates = {}
    if 'ATR' in df.columns and not pd.isna(df.iloc[-1]['ATR']) and df.iloc[-1]['ATR'] > 0:
        sl = round(current_price - df.iloc[-1]['ATR'] * STOP_LOSS_ATR_MULT, 2)
        if sl < current_price: candidates['ATR止损'] = sl
    if 'MA20' in df.columns and not pd.isna(df.iloc[-1]['MA20']) and df.iloc[-1]['MA20'] > 0:
        sl = round(df.iloc[-1]['MA20'] * STOP_LOSS_MA_MULT, 2)
        if sl < current_price: candidates['MA20止损'] = sl
    if 'BOLL_DOWN' in df.columns and not pd.isna(df.iloc[-1]['BOLL_DOWN']) and df.iloc[-1]['BOLL_DOWN'] > 0:
        sl = round(df.iloc[-1]['BOLL_DOWN'], 2)
        if sl < current_price: candidates['BOLL止损'] = sl

    if not candidates:
        sl = round(current_price * 0.98, 2); basis = '固定2%止损'
    else:
        sl = max(candidates.values()); basis = max(candidates, key=candidates.get)

    risk_pct = (current_price - sl) / current_price * 100
    tp = round(current_price + (current_price - sl) * TAKE_PROFIT_RR_RATIO, 2)
    return {'stop_loss': sl, 'take_profit': tp, 'basis': basis, 'rr_ratio': round(TAKE_PROFIT_RR_RATIO, 1),
            'risk_pct': round(risk_pct, 2)}


def check_consecutive_limit_up(
    df: pd.DataFrame,
    today_code: str,
    zt_codes_set: set,
    zt_pool_df: pd.DataFrame,
) -> bool:
    """连板过滤：官方连板数与 K 线回溯取 max，避免重复累加；zt_codes_set 保留以兼容旧调用。"""
    _ = zt_codes_set
    code_norm = normalize_stock_code(today_code)
    zt_board_days: Optional[int] = None
    if not zt_pool_df.empty and "代码" in zt_pool_df.columns:
        norm_series = zt_pool_df["代码"].map(normalize_stock_code)
        for col in ["连板数", "连续板数", "连板", "连续涨停"]:
            if col not in zt_pool_df.columns:
                continue
            row = zt_pool_df.loc[norm_series == code_norm]
            if row.empty:
                continue
            try:
                zt_board_days = int(float(row.iloc[0][col]))
            except (TypeError, ValueError):
                continue
            if zt_board_days >= MAX_CONSECUTIVE_LIMIT_UP:
                return True
            break

    threshold = get_limit_up_threshold(today_code)
    kline_streak = 0
    for i in range(1, min(len(df), 10)):
        pct = float(df.iloc[-i].get("pct_change", 0) or 0)
        if pct >= threshold - 0.5:
            kline_streak += 1
        else:
            break
    effective = max(zt_board_days or 0, kline_streak)
    return effective >= MAX_CONSECUTIVE_LIMIT_UP


def classify_volume_status(row) -> tuple:
    vol_ratio = _safe_float(row.get('VOL_RATIO', np.nan), np.nan)
    if pd.isna(vol_ratio):
        return '量能缺失', 0.0
    close = _safe_float(row.get('close', 0), 0);
    open_price = _safe_float(row.get('open', close), close)
    if vol_ratio > 2.0 and close < open_price:
        return '放量滞涨', -1.5
    elif vol_ratio > 1.5 and close >= open_price:
        return '放量上涨', 0.5
    elif vol_ratio < 0.7:
        return '缩量', -0.5
    else:
        return '正常', 0.0


def get_lock_amount(code: str, zt_pool_df: pd.DataFrame, current_price: float = 10.0) -> float:
    if zt_pool_df.empty or '代码' not in zt_pool_df.columns: return 0.0
    code_n = normalize_stock_code(code)
    zt_row = zt_pool_df[zt_pool_df["代码"].map(normalize_stock_code) == code_n]
    if zt_row.empty: return 0.0

    for col in ['涨停封单量', '封单量']:
        if col in zt_row.columns:
            try:
                return float(zt_row.iloc[0][col])
            except Exception:
                pass

    for col in ['封单金额', '封单额', '封单资金']:
        if col in zt_row.columns:
            try:
                lock_val = float(zt_row.iloc[0][col])
                price_col = '涨停价' if '涨停价' in zt_pool_df.columns else '最新价' if '最新价' in zt_pool_df.columns else None
                if price_col:
                    zt_price = float(zt_row.iloc[0][price_col])
                    if zt_price > 0: return lock_val / zt_price
                if current_price > 0: return lock_val / current_price
                return lock_val / 10.0
            except Exception:
                pass
    return 0.0


def check_volume_pattern(df: pd.DataFrame) -> tuple:
    if len(df) < 5: return "无", 0.0
    latest = df.iloc[-1]
    prev_3_days = df.iloc[-4:-1]

    if 'VOL_RATIO' in prev_3_days.columns:
        if (prev_3_days['VOL_RATIO'] < 0.8).all() and latest['VOL_RATIO'] > 2.0:
            return "底部启动", 1.5

    if 'MA20' in df.columns and len(df) >= 20:
        ma20_today = df.iloc[-1].get('MA20', 0);
        ma20_5d_ago = df.iloc[-6].get('MA20', 0)
        if ma20_today > ma20_5d_ago and latest.get('pct_change', 0) < 0 and latest['VOL_RATIO'] < 0.7:
            return "缩量回踩", 1.0

    return "无", 0.0


def calc_profit_ratio(df: pd.DataFrame) -> float:
    if len(df) < 20: return 50.0
    recent = df.tail(min(len(df), 60))
    close = recent['close'].values
    current = df['close'].iloc[-1]
    profit_ratio = (close <= current).sum() / len(close) * 100
    return round(profit_ratio, 1)


def check_gap_support(df: pd.DataFrame) -> bool:
    if len(df) < 3: return False
    yesterday = df.iloc[-2];
    day_before = df.iloc[-3]
    today_low = df.iloc[-1]['low']
    if yesterday['low'] > day_before['high']:
        if today_low > day_before['high']:
            return True
    return False


# ═════════════════════════════════════════════════════════════════
# 3. 数据源适配器
# ═════════════════════════════════════════════════════════════════
class DataSourceAdapter:
    def get_hot_stocks(self, top_n: int, trade_date: Optional[str] = None) -> pd.DataFrame: raise NotImplementedError

    def get_kline(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame: raise NotImplementedError

    def get_realtime_quote(self, symbol: str) -> dict: raise NotImplementedError

    def get_limit_up_pool(self, date_str: str, trade_date: Optional[str] = None) -> pd.DataFrame: raise NotImplementedError

    def get_industry_map(self) -> dict: raise NotImplementedError

    def get_money_flow(self, symbol: str) -> dict: raise NotImplementedError


# --- EMQuantAPI 适配器（主：K线数据） ---
_EM_LOGIN_LOCK = threading.Lock()


class EMQuantAPIAdapter(DataSourceAdapter):
    """东方财富 EMQuantAPI 适配器（负责K线数据）"""

    def __init__(self, user: str, password: str):
        try:
            from EmQuantAPI import c
            self.c = c
        except ImportError:
            raise ImportError("请先安装 EMQuantAPI：pip install emquantapi")
        self.user = user
        self.password = password
        self._sector_hot = EM_SECTOR_CODE_HOT
        self._sector_zt = EM_SECTOR_CODE_ZT
        self._logged_in = False
        # 登录失败（如 code 90）后不再对每只股票重复 start，避免多线程打爆接口与 SDK 状态错乱
        self._skip_login = False
        self._industry_map = None
        self._login()

    def _login(self):
        with _EM_LOGIN_LOCK:
            if self._logged_in:
                return
            if self._skip_login:
                return
            try:
                # 根据官方demo.py，使用c.start()进行登录
                if self.user and self.password:
                    # 东方财富客服图示：`c.start("UserName=..., Password=..., ForceLogin=1")` — 单字符串、逗号后空格、ForceLogin 在最后
                    start_options = f"UserName={self.user}, Password={self.password}, ForceLogin=1"
                    print("[EMQuantAPI] 正在登录（已隐藏密码）")
                    try:
                        result = self.c.start(start_options)
                    except TypeError:
                        result = self.c.start(start_options, "", None)
                else:
                    print("[EMQuantAPI] 无 UserName/Password，使用 c.start() 无参调用")
                    result = self.c.start()

                if result.ErrorCode != 0:
                    self._skip_login = True
                    raise ConnectionError(f"EMQuantAPI 登录失败: {result.ErrorMsg}")
                self._logged_in = True
                print("[EMQuantAPI] 登录成功")
            except Exception as e:
                self._logged_in = False
                self._skip_login = True
                print(f"[EMQuantAPI] 登录异常（本进程内不再重试 start）: {e}")

    def _ensure_login(self):
        if self._logged_in:
            return
        if self._skip_login:
            return
        self._login()

    def get_hot_stocks(self, top_n: int = TOP_HOT, trade_date: Optional[str] = None) -> pd.DataFrame:
        """使用EMQuantAPI获取成交额最高的股票作为热门股"""
        self._ensure_login()
        if not self._logged_in:
            return _mark_hot_health("em", pd.DataFrame())
        try:
            td = trade_date or get_last_trade_date(1)
            td_compact = _trade_date_compact(td)
            td_y = _trade_date_yyyy_mm_dd(td)
            print(f"[EMQuantAPI] 热门股 sector 板块代码={self._sector_hot} | sector参考日=K线日线截止 trade_date={td_compact} ({td_y}) | sector三参含 Ispandas=0（与官方 demo 一致）")
            cache_path = _em_sector_codes_cache_path(self._sector_hot, td_y, "hot")
            codes = _em_try_load_sector_codes(cache_path)
            if codes is None:
                sector_result = self.c.sector(self._sector_hot, td_y, "Ispandas=0")
                # 检查返回类型
                if hasattr(sector_result, 'ErrorCode'):
                    if sector_result.ErrorCode != 0:
                        print(f"[EMQuantAPI] 获取板块成分股失败: {sector_result.ErrorMsg}")
                        return _mark_hot_health("em", pd.DataFrame())
                    codes = _sector_result_codes(sector_result)
                else:
                    # 如果是DataFrame，直接使用
                    if isinstance(sector_result, pd.DataFrame):
                        codes = sector_result['CODE'].astype(str).tolist()
                    else:
                        print(f"[EMQuantAPI] 获取板块成分股返回未知类型: {type(sector_result)}")
                        return _mark_hot_health("em", pd.DataFrame())
                if codes:
                    _em_save_sector_codes(cache_path, codes)

            if not codes:
                return _mark_hot_health("em", pd.DataFrame())
            codes = [_em_code_for_css(c) for c in codes]
            # 单次 css 请求体量：与 TOP 相关，且不超过 2000（东财限制）；过小会漏掉真·成交额前 N 名
            css_cap = min(len(codes), 2000, max(top_n * 80, 200))
            codes = codes[:css_cap]
            codes_str = ','.join(codes)
            # 获取成交额 AMOUNT 和最新价 CLOSE（官方 demo：TradeDate=YYYYMMDD）；先试 Ispandas=1 便于得到规范列名
            print(f"[EMQuantAPI] 热门股 css TradeDate={td_compact} (YYYYMMDD) | 本次请求代码数={len(codes)}")
            df: Optional[pd.DataFrame] = None
            css_last: Any = None
            for isp in ("1", "0"):
                css_last = _em_css_call_with_retry(
                    self.c, codes_str, "AMOUNT,CLOSE", f"TradeDate={td_compact},Ispandas={isp}"
                )
                if hasattr(css_last, "ErrorCode") and css_last.ErrorCode != 0:
                    continue
                df = _emquant_css_dataframe(css_last)
                if df is not None and "AMOUNT" in df.columns and "CLOSE" in df.columns:
                    break
                df = None
            if df is None:
                if css_last is not None and hasattr(css_last, "ErrorCode") and css_last.ErrorCode != 0:
                    print(f"[EMQuantAPI] 获取成交额失败: {getattr(css_last, 'ErrorMsg', '')}")
                else:
                    print("[EMQuantAPI] 获取成交额失败: 无法解析 css 返回（列不满足 CODE/AMOUNT/CLOSE）")
                return _mark_hot_health("em", pd.DataFrame())
            # 按成交额降序排序；低价过滤与 AKShare 热门路径一致（MIN_PRICE）
            df = df.sort_values("AMOUNT", ascending=False)
            df.rename(columns={"CODE": "代码", "CLOSE": "close", "AMOUNT": "amount"}, inplace=True)
            try:
                df = df[pd.to_numeric(df["close"], errors="coerce") >= float(MIN_PRICE)]
            except Exception:
                pass
            df = df.head(top_n)
            if '代码' in df.columns:
                df['代码'] = df['代码'].astype(str).map(lambda x: normalize_stock_code(x.split('.')[0] if '.' in str(x) else x))
            # 添加其他必要列
            df['名称'] = ''
            df['pct_change'] = 0.0
            df['turnover_rate'] = 0.0
            return _mark_hot_health("em", df[['代码', '名称', 'close', 'pct_change', 'amount', 'turnover_rate']])
        except Exception as e:
            print(f"[EMQuantAPI] 获取热门股异常: {e}")
            import traceback
            traceback.print_exc()
            return _mark_hot_health("em", pd.DataFrame())

    def get_kline(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """EMQuantAPI 提供K线数据（主力功能）"""
        self._ensure_login()
        if not self._logged_in:
            return _mark_kline_health("EMQuantAPIAdapter", pd.DataFrame())
        try:
            em_code = _em_csd_code(symbol)
            # 将日期格式从YYYYMMDD转换为YYYY-MM-DD
            try:
                start_date_fmt = datetime.strptime(start_date, "%Y%m%d").strftime("%Y-%m-%d")
            except Exception:
                start_date_fmt = start_date  # 如果转换失败，使用原格式
            try:
                end_date_fmt = datetime.strptime(end_date, "%Y%m%d").strftime("%Y-%m-%d")
            except Exception:
                end_date_fmt = end_date
            
            # Ispandas=1 时多为带日期列/索引的标准 DataFrame；=0 时偶发无 DATE 列导致解析失败
            csd_result = self.c.csd(
                em_code,
                "OPEN,HIGH,LOW,CLOSE,VOL,AMOUNT",
                start_date_fmt,
                end_date_fmt,
                "period=1,adjustflag=1,Ispandas=1",
            )
            
            # 处理返回结果
            if hasattr(csd_result, 'ErrorCode'):
                if csd_result.ErrorCode != 0:
                    print(f"[EMQuantAPI] K线获取失败 {symbol}: {csd_result.ErrorMsg}")
                    return _mark_kline_health("EMQuantAPIAdapter", pd.DataFrame())
                # 将数据转换为DataFrame
                df = pd.DataFrame(csd_result.Data, columns=csd_result.Indicators)
            else:
                # 如果是DataFrame，直接使用
                if isinstance(csd_result, pd.DataFrame):
                    df = csd_result
                else:
                    print(f"[EMQuantAPI] K线获取返回未知类型: {type(csd_result)}")
                    return _mark_kline_health("EMQuantAPIAdapter", pd.DataFrame())

            if df.empty:
                return _mark_kline_health("EMQuantAPIAdapter", pd.DataFrame())

            # 东财 csd：部分版本/路径返回的 DataFrame 无 DATE 列，日期在索引或列名变体（TRADE_DATE 等）
            df = df.copy()
            date_col = None
            for c in df.columns:
                cu = str(c).upper().replace(" ", "_")
                # 东财 Ispandas=1 常见为 DATES（复数），与旧版 DATE 并存
                if cu in ("DATE", "DATES", "TRADEDATE", "TRADE_DATE", "TIME", "DATETIME") or str(c) in ("日期", "时间"):
                    date_col = c
                    break
            if date_col is not None:
                df["date"] = pd.to_datetime(df[date_col], errors="coerce")
                if date_col != "date":
                    df.drop(columns=[date_col], inplace=True, errors="ignore")
            elif isinstance(df.index, pd.DatetimeIndex):
                df.insert(0, "date", pd.to_datetime(df.index))
                df = df.reset_index(drop=True)
            else:
                c0 = df.columns[0]
                try_ts = pd.to_datetime(df[c0], errors="coerce")
                ohlc_like = {str(x).upper() for x in df.columns}
                if try_ts.notna().sum() >= max(3, len(df) // 2) and not ohlc_like.intersection(
                    {"OPEN", "HIGH", "LOW", "CLOSE", "VOL", "AMOUNT"}
                ):
                    df["date"] = try_ts
                    df.drop(columns=[c0], inplace=True, errors="ignore")
                else:
                    print(f"[EMQuantAPI] K线无法解析日期列，列={list(df.columns)[:12]} index类型={type(df.index).__name__}")
                    return _mark_kline_health("EMQuantAPIAdapter", pd.DataFrame())

            df.rename(columns={
                'OPEN': 'open', 'HIGH': 'high', 'LOW': 'low',
                'CLOSE': 'close', 'VOL': 'volume', 'AMOUNT': 'amount'
            }, inplace=True)
            if "close" not in df.columns:
                print(f"[EMQuantAPI] K线缺少 CLOSE 列，实际列={list(df.columns)}")
                return _mark_kline_health("EMQuantAPIAdapter", pd.DataFrame())
            return _mark_kline_health("EMQuantAPIAdapter", df.sort_values('date').reset_index(drop=True))
        except Exception as e:
            print(f"[EMQuantAPI] K线获取失败 {symbol}: {e}")
            import traceback
            traceback.print_exc()
            return _mark_kline_health("EMQuantAPIAdapter", pd.DataFrame())

    def get_klines_batch(
        self, codes: list[str], start_date: str, end_date: str
    ) -> dict[str, pd.DataFrame]:
        """批量 csd 拉 K 线；返回 {normalize_code: df}。解析失败或接口报错时返回空 dict，由调用方逐只回退。"""
        self._ensure_login()
        if not self._logged_in or not codes:
            return {}
        try:
            start_date_fmt = datetime.strptime(start_date, "%Y%m%d").strftime("%Y-%m-%d")
        except Exception:
            start_date_fmt = start_date
        try:
            end_date_fmt = datetime.strptime(end_date, "%Y%m%d").strftime("%Y-%m-%d")
        except Exception:
            end_date_fmt = end_date

        batch_n = max(5, min(80, int(config.get("EM_CSD_BATCH_CODES", 25) or 25)))
        out: dict[str, pd.DataFrame] = {}
        printed_csd_cols = False
        for i in range(0, len(codes), batch_n):
            chunk = [normalize_stock_code(str(c)) for c in codes[i : i + batch_n]]
            em_str = ",".join(_em_csd_code(c) for c in chunk)
            try:
                csd_result = self.c.csd(
                    em_str,
                    "OPEN,HIGH,LOW,CLOSE,VOL,AMOUNT",
                    start_date_fmt,
                    end_date_fmt,
                    "period=1,adjustflag=1,Ispandas=1",
                )
            except Exception:
                continue
            if hasattr(csd_result, "ErrorCode") and getattr(csd_result, "ErrorCode", -1) != 0:
                continue
            if hasattr(csd_result, "Data") and hasattr(csd_result, "Indicators"):
                raw = pd.DataFrame(csd_result.Data, columns=csd_result.Indicators)
            elif isinstance(csd_result, pd.DataFrame):
                raw = csd_result
            else:
                continue
            if raw is None or raw.empty:
                continue
            if not printed_csd_cols:
                cols = list(raw.columns)
                print(f"[EMQuantAPI] get_klines_batch 解析后列名（首个非空 csd 片段）: {cols}")
                printed_csd_cols = True
            parsed = self._split_csd_multistock_frame(raw)
            for k, sdf in parsed.items():
                if sdf is None or sdf.empty:
                    continue
                if (not str(k).strip()) and len(chunk) == 1:
                    out[normalize_stock_code(chunk[0])] = sdf
                else:
                    out[normalize_stock_code(k)] = sdf
        return out

    def _split_csd_multistock_frame(self, raw: pd.DataFrame) -> dict[str, pd.DataFrame]:
        """将东财批量 csd 返回宽/长表拆成单股 OHLC DataFrame。"""
        df = raw.copy()
        code_col = None
        for c in df.columns:
            cu = str(c).upper()
            if cu in ("CODE", "CODES", "SYMBOL", "TS_CODE", "SECID") or "代码" in str(c):
                code_col = c
                break
        if code_col is None:
            if len(df.columns) >= 6:
                one = self._em_normalize_single_csd_df(df.copy())
                return {"": one} if one is not None and not one.empty else {}
            return {}

        out: dict[str, pd.DataFrame] = {}
        for ckey, g in df.groupby(code_col, sort=False):
            sub = g.drop(columns=[code_col], errors="ignore").copy()
            key = normalize_stock_code(str(ckey).split(".")[0] if "." in str(ckey) else str(ckey))
            sdf = self._em_normalize_single_csd_df(sub)
            if sdf is not None and not sdf.empty:
                out[key] = sdf
        return out

    def _em_normalize_single_csd_df(self, df: pd.DataFrame) -> Optional[pd.DataFrame]:
        if df is None or df.empty:
            return None
        date_col = None
        for c in df.columns:
            cu = str(c).upper().replace(" ", "_")
            if cu in ("DATE", "DATES", "TRADEDATE", "TRADE_DATE", "TIME", "DATETIME") or str(c) in ("日期", "时间"):
                date_col = c
                break
        if date_col is not None:
            df["date"] = pd.to_datetime(df[date_col], errors="coerce")
            if date_col != "date":
                df.drop(columns=[date_col], inplace=True, errors="ignore")
        elif isinstance(df.index, pd.DatetimeIndex):
            df.insert(0, "date", pd.to_datetime(df.index))
            df = df.reset_index(drop=True)
        else:
            c0 = df.columns[0]
            try_ts = pd.to_datetime(df[c0], errors="coerce")
            ohlc_like = {str(x).upper() for x in df.columns}
            if try_ts.notna().sum() >= max(3, len(df) // 2) and not ohlc_like.intersection(
                {"OPEN", "HIGH", "LOW", "CLOSE", "VOL", "AMOUNT"}
            ):
                df["date"] = try_ts
                df.drop(columns=[c0], inplace=True, errors="ignore")
            else:
                return None
        df.rename(
            columns={
                "OPEN": "open",
                "HIGH": "high",
                "LOW": "low",
                "CLOSE": "close",
                "VOL": "volume",
                "AMOUNT": "amount",
            },
            inplace=True,
        )
        if "close" not in df.columns:
            return None
        df["turnover_rate"] = 0.0
        df["pct_change"] = df["close"].astype(float).pct_change() * 100.0
        return df.sort_values("date").reset_index(drop=True)

    def get_realtime_quote(self, symbol: str) -> dict:
        """使用EMQuantAPI获取实时行情"""
        self._ensure_login()
        if not self._logged_in:
            return {}
        try:
            em_code = _em_csd_code(symbol)
            # 获取实时行情数据
            tradedate = datetime.now().strftime("%Y-%m-%d")
            css_result = self.c.css(em_code, "OPEN,HIGH,LOW,CLOSE,VOL,AMOUNT,CHANGE,PCTCHANGE,PREVCLOSE", f"TradeDate={tradedate},Ispandas=0")
            
            # 处理返回结果
            if hasattr(css_result, 'ErrorCode'):
                if css_result.ErrorCode != 0:
                    print(f"[EMQuantAPI] 实时行情获取失败 {symbol}: {css_result.ErrorMsg}")
                    return {}
                # 将数据转换为DataFrame
                df = pd.DataFrame(css_result.Data, columns=css_result.Indicators)
            else:
                # 如果是DataFrame，直接使用
                if isinstance(css_result, pd.DataFrame):
                    df = css_result
                else:
                    print(f"[EMQuantAPI] 实时行情返回未知类型: {type(css_result)}")
                    return {}
            
            if df.empty:
                return {}
            # 提取第一行数据
            row = df.iloc[0]
            return {
                'current': row.get('CLOSE', 0),
                'open': row.get('OPEN', 0),
                'high': row.get('HIGH', 0),
                'low': row.get('LOW', 0),
                'close': row.get('CLOSE', 0),
                'volume': row.get('VOL', 0),
                'amount': row.get('AMOUNT', 0),
                'pct_change': row.get('PCTCHANGE', 0),
                'prev_close': row.get('PREVCLOSE', 0),
                'change': row.get('CHANGE', 0)
            }
        except Exception as e:
            print(f"[EMQuantAPI] 实时行情异常 {symbol}: {e}")
            import traceback
            traceback.print_exc()
            return {}

    def get_limit_up_pool(self, date_str: str, trade_date: Optional[str] = None) -> pd.DataFrame:
        """使用EMQuantAPI获取涨停股票池"""
        self._ensure_login()
        if not self._logged_in:
            return pd.DataFrame()
        try:
            td_k = trade_date or date_str
            td_compact_k = _trade_date_compact(td_k)
            td_y = _trade_date_yyyy_mm_dd(td_k)
            zt_compact = _trade_date_compact(date_str)
            print(f"[EMQuantAPI] 涨停池 sector 板块代码={self._sector_zt} | sector参考日=K线日线截止 trade_date={td_compact_k} ({td_y}) | sector三参含 Ispandas=0（与官方 demo 一致）")
            zcache = _em_sector_codes_cache_path(self._sector_zt, td_y, "zt")
            codes = _em_try_load_sector_codes(zcache)
            if codes is None:
                sector_result = self.c.sector(self._sector_zt, td_y, "Ispandas=0")
                # 检查返回类型
                if hasattr(sector_result, 'ErrorCode'):
                    if sector_result.ErrorCode != 0:
                        print(f"[EMQuantAPI] 获取板块成分股失败: {sector_result.ErrorMsg}")
                        return pd.DataFrame()
                    codes = _sector_result_codes(sector_result)
                else:
                    # 如果是DataFrame，直接使用
                    if isinstance(sector_result, pd.DataFrame):
                        codes = sector_result['CODE'].astype(str).tolist()
                    else:
                        print(f"[EMQuantAPI] 获取板块成分股返回未知类型: {type(sector_result)}")
                        return pd.DataFrame()
                if codes:
                    _em_save_sector_codes(zcache, codes)

            if not codes:
                return pd.DataFrame()
            codes = [_em_code_for_css(c) for c in codes]
            css_cap = min(len(codes), 2000, 1200)
            codes = codes[:css_cap]
            codes_str = ','.join(codes)
            # 获取涨跌幅 CHANGE 和最新价 CLOSE；css 使用涨停日 zt_pool_date（YYYYMMDD，与官方 demo 一致）
            print(f"[EMQuantAPI] 涨停池 css TradeDate=涨停日 zt_pool_date={zt_compact} (YYYYMMDD) | 本次请求代码数={len(codes)}")
            df: Optional[pd.DataFrame] = None
            css_last: Any = None
            for isp in ("1", "0"):
                css_last = _em_css_call_with_retry(
                    self.c, codes_str, "CHANGE,CLOSE,PREVCLOSE", f"TradeDate={zt_compact}, Ispandas={isp}"
                )
                if hasattr(css_last, "ErrorCode") and css_last.ErrorCode != 0:
                    continue
                df = _emquant_css_dataframe(css_last)
                if df is not None and all(x in df.columns for x in ("CHANGE", "CLOSE", "PREVCLOSE")):
                    break
                df = None
            if df is None:
                if css_last is not None and hasattr(css_last, "ErrorCode") and css_last.ErrorCode != 0:
                    print(f"[EMQuantAPI] 获取涨跌幅失败: {getattr(css_last, 'ErrorMsg', '')}")
                else:
                    print("[EMQuantAPI] 获取涨跌幅失败: 无法解析 css 返回（列不满足 CODE/CHANGE/CLOSE/PREVCLOSE）")
                return pd.DataFrame()
            # 计算涨幅百分比 (CHANGE可能是涨跌额，需要除以PREVCLOSE)
            df["pct_change"] = df["CHANGE"] / df["PREVCLOSE"] * 100
            # 筛选涨停股票 (涨幅 >= 9.9%)
            limit_up = df[df["pct_change"] >= 9.9].copy()
            limit_up.rename(columns={"CODE": "代码", "CLOSE": "close", "CHANGE": "change", "PREVCLOSE": "prev_close"}, inplace=True)
            if '代码' in limit_up.columns:
                limit_up['代码'] = limit_up['代码'].astype(str).map(lambda x: normalize_stock_code(x.split('.')[0] if '.' in str(x) else x))
            limit_up['名称'] = ''
            limit_up['limit_up_price'] = limit_up['close']
            limit_up['limit_up_time'] = ''
            return limit_up[['代码', '名称', 'close', 'pct_change', 'limit_up_price', 'limit_up_time']]
        except Exception as e:
            print(f"[EMQuantAPI] 获取涨停池异常: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()

    def batch_stock_display_fields(self, codes_norm: list[str], trade_date_compact: str) -> dict[str, dict[str, str]]:
        """
        东财 css 批量取证券简称与行业/板块字段（减轻对 AK 现货补名称的依赖）。
        codes_norm: 6 位 normalize_stock_code；trade_date_compact: YYYYMMDD。
        返回 {code6: {"名称": str, "行业": str}}。
        """
        self._ensure_login()
        out: dict[str, dict[str, str]] = {}
        if not self._logged_in or not codes_norm:
            return out
        td_compact = _trade_date_compact(trade_date_compact)
        seen: set[str] = set()
        uniq: list[str] = []
        for c in codes_norm:
            c6 = normalize_stock_code(c)
            if c6 not in seen:
                seen.add(c6)
                uniq.append(c6)
        chunk = max(10, min(50, int(config.get("EM_CSS_BATCH_CODES", 50) or 50)))
        for i in range(0, len(uniq), chunk):
            part = uniq[i : i + chunk]
            em_codes = [_em_code_for_css(x) for x in part]
            codes_str = ",".join(em_codes)
            df: Optional[pd.DataFrame] = None
            for fields in ("NAME,HYBLOCK", "NAME,INDUSTRY", "SECURITYNAME,HYBLOCK", "SECURITY_NAME,HYBLOCK", "NAME"):
                css_r = _em_css_call_with_retry(
                    self.c, codes_str, fields, f"TradeDate={td_compact},Ispandas=1"
                )
                df = _emquant_css_dataframe(css_r)
                if df is not None and not df.empty:
                    cols = set(df.columns)
                    name_col = next((x for x in ("NAME", "SECURITYNAME", "SECURITY_NAME") if x in cols), None)
                    if name_col is None:
                        continue
                    for _, row in df.iterrows():
                        rawc = str(row.get("CODE", "") or "")
                        base = rawc.split(".")[0] if "." in rawc else "".join(ch for ch in rawc if ch.isdigit())
                        c6 = normalize_stock_code(base) if base else ""
                        if not c6:
                            continue
                        nm = str(row.get(name_col, "") or "").strip()
                        hy = ""
                        for hk in ("HYBLOCK", "INDUSTRY", "SW2021L1NAME", "BLOCKNAME"):
                            if hk in cols:
                                v = row.get(hk)
                                if v is not None and str(v).strip():
                                    hy = str(v).strip()
                                    break
                        out[c6] = {"名称": nm, "行业": hy}
                    break
        if out:
            print(f"[EMQuantAPI] css 批量名称/行业: {len(out)} 条")
        return out

    def get_industry_map(self) -> dict:
        if self._industry_map is None:
            try:
                self._ensure_login()
                if not self._logged_in:
                    self._industry_map = {}
                    return self._industry_map
                # 尝试从EMQuant获取行业数据
                data = self.c.csec(query="sectorid=100", field="sectorid,sectorname,stockcode")
                if data.ErrorCode == 0:
                    industry_map = {}
                    for item in data.Data:
                        industry_map[str(item[2]).split('.')[0]] = str(item[1])
                    self._industry_map = industry_map
                else:
                    self._industry_map = {}
            except Exception:
                self._industry_map = {}
        return self._industry_map

    def get_money_flow(self, symbol: str) -> dict:
        """使用EMQuantAPI获取资金流向数据"""
        self._ensure_login()
        if not self._logged_in:
            return {'net_amount_3d': 0}
        try:
            em_code = _em_csd_code(symbol)
            
            # 首先尝试获取当日资金流数据
            indicators_to_try = [
                "NETAMOUNTIN", "NETAMOUNTOUT", "MAINNETIN", "MAINNETOUT",
                "NETINFLOW", "NETOUTFLOW", "AMOUNTIN", "AMOUNTOUT"
            ]
            
            for indicator in indicators_to_try:
                try:
                    css_result = self.c.css(em_code, indicator, f"TradeDate={tradedate},Ispandas=0")
                    
                    # 处理返回结果
                    value = None
                    if hasattr(css_result, 'ErrorCode'):
                        if css_result.ErrorCode == 0:
                            # 提取数据值
                            if hasattr(css_result, 'Data') and css_result.Data:
                                value = float(css_result.Data[0][0])
                    else:
                        # 如果是DataFrame，直接使用
                        if isinstance(css_result, pd.DataFrame) and not css_result.empty:
                            value = float(css_result.iloc[0, 0])
                    
                    if value is not None:
                        # 如果是流入指标，返回正值；流出指标返回负值
                        if indicator in ["NETAMOUNTIN", "MAINNETIN", "NETINFLOW", "AMOUNTIN"]:
                            return {'net_amount_3d': value}
                        elif indicator in ["NETAMOUNTOUT", "MAINNETOUT", "NETOUTFLOW", "AMOUNTOUT"]:
                            return {'net_amount_3d': -value}
                except Exception:
                    continue
            
            # 如果无法获取当日数据，尝试获取最近3日的成交额变化作为替代
            try:
                end_date = datetime.now().strftime("%Y-%m-%d")
                start_date = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
                csd_result = self.c.csd(em_code, "AMOUNT", start_date, end_date, "period=1,adjustflag=1,Ispandas=0")
                
                # 处理返回结果
                if hasattr(csd_result, 'ErrorCode'):
                    if csd_result.ErrorCode == 0:
                        # 将数据转换为DataFrame
                        df = pd.DataFrame(csd_result.Data, columns=csd_result.Indicators)
                    else:
                        df = pd.DataFrame()
                else:
                    # 如果是DataFrame，直接使用
                    df = csd_result if isinstance(csd_result, pd.DataFrame) else pd.DataFrame()
                
                if not df.empty and len(df) >= 3:
                    # 计算最近3日的平均成交额变化
                    recent_avg = df['AMOUNT'].tail(3).mean()
                    prev_avg = df['AMOUNT'].head(max(len(df)-3, 0)).mean() if len(df) > 3 else recent_avg
                    net_change = recent_avg - prev_avg
                    return {'net_amount_3d': net_change}
            except Exception:
                pass
                
        except Exception as e:
            print(f"[EMQuantAPI] 资金流向获取失败 {symbol}: {e}")
            import traceback
            traceback.print_exc()
        
        return {'net_amount_3d': 0}


# Tushare daily 免费档约 50 次/分钟：多线程拉 K 线时做简单节流，避免整批被限流
_TS_DAILY_LOCK = threading.Lock()
_TS_DAILY_MONO_TIMES: list[float] = []


def _tushare_throttle_daily():
    with _TS_DAILY_LOCK:
        now = time.monotonic()
        _TS_DAILY_MONO_TIMES[:] = [t for t in _TS_DAILY_MONO_TIMES if now - t < 62.0]
        if len(_TS_DAILY_MONO_TIMES) >= 45:
            wait_sec = 62.0 - (now - _TS_DAILY_MONO_TIMES[0]) + 0.15
            if 0 < wait_sec < 90:
                time.sleep(wait_sec)
            now = time.monotonic()
            _TS_DAILY_MONO_TIMES[:] = [t for t in _TS_DAILY_MONO_TIMES if now - t < 62.0]
        _TS_DAILY_MONO_TIMES.append(time.monotonic())


# --- Tushare 适配器（辅：热门股、涨停池） ---
class TushareAdapter(DataSourceAdapter):
    """Tushare 适配器（负责热门股、涨停池）"""

    def __init__(self, token: str):
        import tushare as ts
        ts.set_token(token)
        self.pro = ts.pro_api()
        self._industry_map = None

    @staticmethod
    def _to_ts_code(symbol: str) -> str:
        """Tushare ts_code：沪/深/北交所后缀区分（北交所常见 8/4 开头）。"""
        code = str(symbol).zfill(6)
        if code.startswith("6"):
            return f"{code}.SH"
        if code.startswith(("8", "4")):
            return f"{code}.BJ"
        return f"{code}.SZ"

    def get_hot_stocks(self, top_n: int = TOP_HOT, trade_date: Optional[str] = None) -> pd.DataFrame:
        """Tushare 获取热门股（按成交额排序），支持非交易日回退"""
        try:
            anchor = _trade_date_compact(trade_date) if trade_date else None
            # 按最近交易日回退：当日非交易日或权限导致 daily 为空时继续尝试前一交易日
            df: Optional[pd.DataFrame] = None
            seen_dates: set[str] = set()
            for dback in range(0, 15):
                td = get_last_trade_date(dback, anchor) if anchor else get_last_trade_date(dback)
                if td in seen_dates:
                    continue
                seen_dates.add(td)
                df = self.pro.daily(trade_date=td)
                if df is not None and not df.empty:
                    break
            if df is None or df.empty:
                return _mark_hot_health("ts", pd.DataFrame())
            df = df.sort_values('amount', ascending=False).head(top_n)
            df["代码"] = df["ts_code"].str.split(".").str[0].map(normalize_stock_code)
            try:
                names = self.pro.stock_basic(exchange='', list_status='L',
                                             fields='ts_code,name').set_index('ts_code')
                # 未映射到时勿用代码冒充名称，否则名称补全无法识别为「待补全」且报表里像「没名称」
                df['名称'] = df['ts_code'].map(names['name']).fillna('')
            except Exception:
                df['名称'] = ''
            df = df[['代码', '名称']].copy()
            return _mark_hot_health("ts", df)
        except Exception as e:
            print(f"[Tushare] 热门股获取失败: {e}")
            return _mark_hot_health("ts", pd.DataFrame())

    def get_kline(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Tushare K线数据（备用，不作为主力）"""
        try:
            _tushare_throttle_daily()
            ts_code = self._to_ts_code(symbol)
            df = self.pro.daily(ts_code=ts_code,
                                start_date=start_date.replace('-', ''),
                                end_date=end_date.replace('-', ''))
            if df is None or df.empty:
                return _mark_kline_health("TushareAdapter", pd.DataFrame())
            df = df.rename(columns={
                'trade_date': 'date', 'vol': 'volume', 'amount': 'amount',
                'pct_chg': 'pct_change'
            })
            df['date'] = pd.to_datetime(df['date'])
            df['turnover_rate'] = 0.0
            df = df.sort_values('date').reset_index(drop=True)
            return _mark_kline_health("TushareAdapter", df)
        except Exception as e:
            print(f"[Tushare] K线获取失败 {symbol}: {e}")
            return _mark_kline_health("TushareAdapter", pd.DataFrame())

    def get_realtime_quote(self, symbol: str) -> dict:
        """Tushare 实时行情"""
        try:
            _tushare_throttle_daily()
            ts_code = self._to_ts_code(symbol)
            td_ctx = getattr(self, "_screen_trade_date", None)
            td_quote = get_last_trade_date(0, td_ctx) if td_ctx else get_last_trade_date(0)
            df = self.pro.daily(ts_code=ts_code, trade_date=td_quote)
            if df is None or df.empty:
                return {}
            return {'name': symbol, 'open': float(df.iloc[0]['open']), 'close': float(df.iloc[0]['close'])}
        except Exception:
            return {}

    def get_limit_up_pool(self, date_str: str, trade_date: Optional[str] = None) -> pd.DataFrame:
        """Tushare 涨停池数据"""
        try:
            df = self.pro.limit_list(trade_date=date_str, limit_type='U')
            if df is None or df.empty:
                return pd.DataFrame()
            df["代码"] = df["ts_code"].str.split(".").str[0].map(normalize_stock_code)
            return df
        except Exception as e:
            print(f"[Tushare] 涨停池获取失败: {e}")
            return pd.DataFrame()

    def get_industry_map(self) -> dict:
        """Tushare 行业映射（备用）"""
        if self._industry_map is None:
            try:
                df = self.pro.stock_basic(exchange='', list_status='L',
                                          fields='ts_code,symbol,industry')
                df["代码"] = df["symbol"].astype(str).map(normalize_stock_code)
                self._industry_map = dict(zip(df["代码"], df["industry"].fillna("未知")))
            except Exception:
                self._industry_map = {}
        return self._industry_map

    def get_money_flow(self, symbol: str) -> dict:
        return {'net_amount_3d': 0}


# --- AKShare 适配器（备：实时行情、涨停池、大盘数据） ---
class AKShareAdapter(DataSourceAdapter):
    """AKShare 适配器（备用数据源，负责大盘检查、实时行情）"""

    def __init__(self):
        self._industry_map = None

    def get_hot_stocks(self, top_n: int = TOP_HOT, trade_date: Optional[str] = None) -> pd.DataFrame:
        """AKShare 获取热门股（按成交额排序）"""
        try:
            df = pd.DataFrame()
            last_err: Optional[Exception] = None
            for attempt in range(1, 4):
                try:
                    with _akshare_call_guard():
                        df = ak.stock_zh_a_spot_em()
                    if df is not None and not df.empty:
                        break
                except Exception as e:
                    last_err = e
                    time.sleep(1.2 * attempt)
            if last_err is not None and df.empty:
                print(f"\n[AKShare] 热门股获取失败（已重试3次）: {last_err}")
            if df.empty:
                print("\n[警告] 获取到 0 条热门股数据，可能接口异常或非交易日！")
                return _mark_hot_health("ak", pd.DataFrame())
            df = df[~df['名称'].str.contains('ST|退', na=False)]
            df = df.sort_values('成交额', ascending=False).head(top_n)
            _hot_cols = ["代码", "名称", "最新价"]
            _missing = [c for c in _hot_cols if c not in df.columns]
            if _missing:
                print(f"\n[AKShare] 热门股接口返回缺少列 {_missing}，跳过本次热门股")
                return _mark_hot_health("ak", pd.DataFrame())
            if "所属行业" not in df.columns:
                df = df[_hot_cols].copy()
                df["所属行业"] = "未知"
            else:
                df = df[_hot_cols + ["所属行业"]].copy()
            df["代码"] = df["代码"].map(normalize_stock_code)
            df = df[df['最新价'] >= MIN_PRICE]
            self._industry_map = dict(zip(df['代码'], df['所属行业']))
            return _mark_hot_health("ak", df)
        except Exception as e:
            print(f"\n[AKShare] 热门股获取失败: {e}")
            return _mark_hot_health("ak", pd.DataFrame())

    def get_kline(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """AKShare K线数据（备用）"""
        try:
            with _akshare_call_guard():
                df = ak.stock_zh_a_hist(symbol=str(symbol).zfill(6), period="daily",
                                        start_date=start_date, end_date=end_date, adjust="qfq")
            if df.empty:
                return _mark_kline_health("AKShareAdapter", pd.DataFrame())
            df = df.rename(columns={'日期': 'date', '开盘': 'open', '收盘': 'close', '最高': 'high', '最低': 'low',
                                    '成交量': 'volume', '成交额': 'amount', '换手率': 'turnover_rate',
                                    '涨跌幅': 'pct_change'})
            df['date'] = pd.to_datetime(df['date'])
            return _mark_kline_health("AKShareAdapter", df.sort_values('date').reset_index(drop=True))
        except Exception as e:
            print(f"[AKShare] K线获取失败 {symbol}: {e}")
            return _mark_kline_health("AKShareAdapter", pd.DataFrame())

    def get_realtime_quote(self, symbol: str) -> dict:
        """AKShare 实时行情（sina接口）"""
        try:
            code = str(symbol).zfill(6)
            sina_sym = f"sh{code}" if code.startswith('6') else f"sz{code}"
            url = f"https://hq.sinajs.cn/list={sina_sym}"
            headers = {'Referer': 'https://finance.sina.com.cn'}
            with _akshare_call_guard():
                r = requests.get(url, headers=headers, timeout=10)
            r.encoding = 'gbk'
            if 'hq_str_' in r.text:
                parts = r.text.split('"')[1].split(',')
                if len(parts) > 30:
                    return {'name': parts[0], 'open': float(parts[1] or 0), 'close': float(parts[3] or 0)}
        except Exception:
            pass
        return {}

    def get_limit_up_pool(self, date_str: str, trade_date: Optional[str] = None) -> pd.DataFrame:
        """AKShare 涨停池数据（备用）"""
        try:
            with _akshare_call_guard():
                df = ak.stock_zt_pool_em(date=date_str)
            if df.empty:
                print(f"\n[警告] {date_str} 涨停池数据为空，可能无涨停或接口异常。")
                return pd.DataFrame()
            if '代码' not in df.columns:
                for c in df.columns:
                    if '代码' in c or 'code' in c.lower():
                        df = df.rename(columns={c: '代码'})
                        break
            if "代码" in df.columns:
                df = df.copy()
                df["代码"] = df["代码"].map(normalize_stock_code)
            return df
        except Exception as e:
            print(f"[AKShare] 涨停池获取失败: {e}")
            return pd.DataFrame()

    def get_industry_map(self) -> dict:
        """AKShare 行业映射"""
        if self._industry_map is None:
            try:
                with _akshare_call_guard():
                    df = ak.stock_zh_a_spot_em()
                if df.empty or "代码" not in df.columns:
                    self._industry_map = {}
                else:
                    df = df.copy()
                    df["代码"] = df["代码"].map(normalize_stock_code)
                    if "所属行业" in df.columns:
                        self._industry_map = dict(zip(df["代码"], df["所属行业"]))
                    else:
                        self._industry_map = dict.fromkeys(df["代码"].tolist(), "未知")
            except Exception:
                self._industry_map = {}
        return self._industry_map

    def get_money_flow(self, symbol: str) -> dict:
        """AKShare 资金流向"""
        try:
            code = str(symbol).zfill(6)
            market = "sh" if code.startswith('6') else "sz"
            with _akshare_call_guard():
                df = ak.stock_individual_fund_flow(stock=code, market=market)
            if df.empty: return {'net_amount_3d': 0}
            latest_3d = df.tail(3)
            net_amount = latest_3d['大单净流入'].sum() if '大单净流入' in latest_3d.columns else 0
            return {'net_amount_3d': net_amount}
        except Exception:
            return {'net_amount_3d': 0}


def _compact_yyyymmdd(d: str) -> str:
    s = re.sub(r"\D", "", str(d))
    return s.zfill(8)[-8:] if len(s) >= 8 else s


def _yyyy_mm_dd(d: str) -> str:
    c = _compact_yyyymmdd(d)
    if len(c) < 8:
        return str(d)
    return f"{c[:4]}-{c[4:6]}-{c[6:8]}"


# --- 聚宽 jqdatasdk 适配器（日线 K 线；需 pip install jqdatasdk，账号见聚宽「数据」页）---
class JoinQuantAdapter(DataSourceAdapter):
    """聚宽本地数据：get_price 日线，与 AK/Tushare 输出列对齐（date/open/high/low/close/volume/amount/pct_change/turnover_rate）。"""

    def __init__(self, username: str, password: str):
        self._username = (username or "").strip()
        self._password = (password or "").strip()
        try:
            import jqdatasdk as jq  # type: ignore
            self._jq = jq
        except ImportError as e:
            raise ImportError("请安装聚宽数据 SDK：pip install jqdatasdk") from e

    @staticmethod
    def _to_jq_security(symbol: str) -> str:
        c = normalize_stock_code(symbol)
        if c.startswith(("8", "4", "92")):
            return f"{c}.BJ"
        if c.startswith("6") or c.startswith("688") or c.startswith("689"):
            return f"{c}.XSHG"
        return f"{c}.XSHE"

    def _ensure_auth(self) -> bool:
        global _JQ_AUTH_OK
        if _JQ_AUTH_OK:
            return True
        with _JQ_API_LOCK:
            if _JQ_AUTH_OK:
                return True
            try:
                self._jq.auth(self._username, self._password)
                _JQ_AUTH_OK = True
                print("[聚宽] jqdatasdk 登录成功")
                return True
            except Exception as e:
                print(f"[聚宽] jqdatasdk 登录失败: {e}")
                return False

    def get_hot_stocks(self, top_n: int = TOP_HOT, trade_date: Optional[str] = None) -> pd.DataFrame:
        return pd.DataFrame()

    def get_kline(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        if not self._ensure_auth():
            return _mark_kline_health("JoinQuantAdapter", pd.DataFrame())
        sec = self._to_jq_security(symbol)
        sd = _yyyy_mm_dd(start_date)
        ed = _yyyy_mm_dd(end_date)
        fq = str(config.get("JQ_KLINE_FQ", "pre") or "pre")
        sleep_sec = float(config.get("JQ_KLINE_SLEEP_SEC", 0) or 0)
        try:
            with _JQ_API_LOCK:
                if sleep_sec > 0:
                    time.sleep(sleep_sec)
                raw = self._jq.get_price(
                    sec,
                    start_date=sd,
                    end_date=ed,
                    frequency="daily",
                    fields=["open", "close", "high", "low", "volume", "money"],
                    skip_paused=False,
                    fq=fq,
                )
            if raw is None or (isinstance(raw, pd.DataFrame) and raw.empty):
                return _mark_kline_health("JoinQuantAdapter", pd.DataFrame())
            df = raw.reset_index()
            time_col = df.columns[0]
            df = df.rename(columns={time_col: "date"})
            df["date"] = pd.to_datetime(df["date"])
            if "money" in df.columns:
                df = df.rename(columns={"money": "amount"})
            elif "amount" not in df.columns:
                df["amount"] = 0.0
            df["pct_change"] = df["close"].astype(float).pct_change() * 100.0
            df["turnover_rate"] = 0.0
            cols = ["date", "open", "high", "low", "close", "volume", "amount", "turnover_rate", "pct_change"]
            for c in cols:
                if c not in df.columns:
                    df[c] = 0.0 if c != "date" else df["date"]
            return _mark_kline_health("JoinQuantAdapter", df[cols].sort_values("date").reset_index(drop=True))
        except Exception as e:
            print(f"[聚宽] K线获取失败 {symbol}: {e}")
            return _mark_kline_health("JoinQuantAdapter", pd.DataFrame())

    def get_realtime_quote(self, symbol: str) -> dict:
        return {}

    def get_limit_up_pool(self, date_str: str, trade_date: Optional[str] = None) -> pd.DataFrame:
        return pd.DataFrame()

    def get_industry_map(self) -> dict:
        return {}

    def get_money_flow(self, symbol: str) -> dict:
        return {"net_amount_3d": 0}


# --- 智能分工数据源适配器 ---
class SmartSourceAdapter(DataSourceAdapter):
    """智能分工数据源：并行拉取后按业务优先级采纳（东财优先历史/截面；实时优先新浪）。"""

    def __init__(self, em_user: str, em_pass: str, ts_token: str, jq_user: str = "", jq_pass: str = ""):
        self.adapters = {}
        
        # 初始化各数据源适配器
        self.em_adapter = None
        self.ts_adapter = None
        self.jq_adapter = None
        self.ak_adapter = AKShareAdapter()  # AKShare 作为默认备用
        
        # 初始化 EMQuantAPI（K线主力）
        if em_user and em_pass and em_user != "your_emquantapi_account":
            try:
                self.em_adapter = EMQuantAPIAdapter(em_user, em_pass)
                print("[智能源] EMQuantAPI 初始化成功（负责K线数据）")
            except Exception as e:
                print(f"[智能源] EMQuantAPI 初始化失败: {e}")
        
        # 初始化 Tushare（热门股、涨停池）
        if ts_token:
            try:
                self.ts_adapter = TushareAdapter(ts_token)
                print("[智能源] Tushare 初始化成功（负责热门股、涨停池）")
            except Exception as e:
                print(f"[智能源] Tushare 初始化失败: {e}")

        # 聚宽 jqdatasdk（日线 K 线）
        if bool(config.get("ENABLE_JQDATA", True)) and jq_user and jq_pass:
            try:
                self.jq_adapter = JoinQuantAdapter(jq_user, jq_pass)
                print("[智能源] 聚宽 jqdatasdk 初始化成功（日线 K 线）")
            except Exception as e:
                print(f"[智能源] 聚宽初始化失败: {e}")
        
        # AKShare 始终可用
        self.ak_adapter = AKShareAdapter()
        self._em_active = self.em_adapter is not None
        print("[智能源] AKShare 就绪（备用/大盘数据）")
        self._stock_name_map: dict[str, str] = {}
        self._load_stock_name_map_cache()

    def _load_stock_name_map_cache(self) -> None:
        """全市场代码→简称：优先读 stock_names_cache.json，否则一次性拉现货表写入内存与文件。"""
        if self._stock_name_map:
            return
        if STOCK_NAMES_CACHE_FILE.is_file():
            try:
                raw = json.loads(STOCK_NAMES_CACHE_FILE.read_text(encoding="utf-8"))
                if isinstance(raw, dict):
                    self._stock_name_map = {
                        normalize_stock_code(str(k)): str(v).strip()
                        for k, v in raw.items()
                        if str(v).strip()
                    }
                    if self._stock_name_map:
                        print(f"[智能源] 已载入本地证券简称缓存 {STOCK_NAMES_CACHE_FILE.name}（{len(self._stock_name_map)} 条）")
                        return
            except Exception as e:
                print(f"[智能源] 读取 {STOCK_NAMES_CACHE_FILE.name} 失败: {e}")
        try:
            spot = _akshare_call_with_retries(lambda: ak.stock_zh_a_spot_em(), "AKShare现货(名称缓存)")
        except Exception as e:
            print(f"[智能源] 构建证券简称内存缓存失败: {e}")
            return
        if spot is None or spot.empty or "代码" not in spot.columns:
            return
        name_col = "名称" if "名称" in spot.columns else next(
            (c for c in spot.columns if "名称" in str(c)), None
        )
        if not name_col:
            return
        spot = spot.copy()
        spot["代码"] = spot["代码"].astype(str).map(normalize_stock_code)
        mp = dict(
            zip(
                spot["代码"].astype(str),
                spot[name_col].astype(str).str.strip(),
            )
        )
        self._stock_name_map = {k: v for k, v in mp.items() if v and k}
        try:
            STOCK_NAMES_CACHE_FILE.write_text(
                json.dumps(self._stock_name_map, ensure_ascii=False, indent=0),
                encoding="utf-8",
            )
            print(f"[智能源] 已构建证券简称缓存并写入 {STOCK_NAMES_CACHE_FILE.name}（{len(self._stock_name_map)} 条）")
        except Exception as e:
            print(f"[智能源] 写入 {STOCK_NAMES_CACHE_FILE.name} 失败（仍保留内存缓存）: {e}")

    def bind_screen_trade_date(self, trade_date: Optional[str]) -> None:
        """与子线程内 Tushare 等对齐本轮 K 线截止日（ThreadPoolExecutor 工作线程不继承 ContextVar）。"""
        compact = _trade_date_compact(trade_date) if trade_date else None
        if self.ts_adapter is not None:
            setattr(self.ts_adapter, "_screen_trade_date", compact)

    def _adapters_for_method(self, method_name: str):
        """返回适配器列表（顺序即采纳优先级）。历史/截面类优先东财；实时行情优先新浪。"""
        if method_name == "get_realtime_quote":
            return [self.ak_adapter, self.ts_adapter, self.em_adapter]
        if method_name == "get_money_flow":
            return [self.em_adapter, self.ak_adapter, self.ts_adapter]
        if method_name == "get_kline":
            jq, em, ts, ak = self.jq_adapter, self.em_adapter, self.ts_adapter, self.ak_adapter
            if em is not None:
                return [x for x in [em, jq, ts, ak] if x is not None]
            return [x for x in [jq, ak, ts, em] if x is not None]
        return [self.em_adapter, self.ts_adapter, self.ak_adapter]

    @staticmethod
    def _result_usable(method_name: str, result) -> bool:
        if isinstance(result, pd.DataFrame):
            return not result.empty
        if isinstance(result, dict):
            if method_name == "get_industry_map":
                return len(result) > 0
            if method_name == "get_money_flow":
                return True
            return bool(result)
        return result is not None

    def _parallel_query(self, method_name: str, *args, **kwargs):
        """并行请求各源，在超时内尽量等齐已发起的任务，再按业务优先级采纳结果（非先到先得）。"""
        from concurrent.futures import ThreadPoolExecutor, wait

        timeout_sec = max(5.0, float(MULTI_SOURCE_TIMEOUT_SEC))
        adapters = [a for a in self._adapters_for_method(method_name) if a is not None]
        if not adapters:
            return self._empty_result(method_name)
        priority_names = [a.__class__.__name__ for a in adapters]

        with ThreadPoolExecutor(max_workers=len(adapters)) as executor:
            future_to_adapter = {}
            for adp in adapters:
                try:
                    fut = executor.submit(getattr(adp, method_name), *args, **kwargs)
                    future_to_adapter[fut] = adp
                except Exception:
                    continue
            if not future_to_adapter:
                return self._empty_result(method_name)

            done, not_done = wait(future_to_adapter.keys(), timeout=timeout_sec)
            for f in not_done:
                try:
                    f.cancel()
                except Exception:
                    pass

            by_cls: dict[str, tuple[Any, Any]] = {}
            for fut in done:
                adp = future_to_adapter.get(fut)
                if adp is None:
                    continue
                try:
                    res = fut.result(timeout=0)
                except Exception:
                    continue
                by_cls[adp.__class__.__name__] = (adp, res)

            for cls_name in priority_names:
                if cls_name not in by_cls:
                    continue
                _, res = by_cls[cls_name]
                if self._result_usable(method_name, res):
                    print(f"[智能源] 使用 {cls_name} 获取 {method_name}")
                    if method_name == "get_hot_stocks":
                        _ds_health_set("get_hot_winner_class", cls_name)
                    elif method_name == "get_kline":
                        _ds_health_inc_kline_winner(cls_name)
                    elif method_name == "get_limit_up_pool":
                        _ds_health_set("get_limit_up_winner_class", cls_name)
                    return res

        for adp in adapters:
            try:
                res = getattr(adp, method_name)(*args, **kwargs)
                if self._result_usable(method_name, res):
                    c2 = adp.__class__.__name__
                    print(f"[智能源] 回退到 {c2} 获取 {method_name}")
                    if method_name == "get_hot_stocks":
                        _ds_health_set("get_hot_winner_class", c2)
                    elif method_name == "get_kline":
                        _ds_health_inc_kline_winner(c2)
                    elif method_name == "get_limit_up_pool":
                        _ds_health_set("get_limit_up_winner_class", c2)
                    return res
            except Exception:
                continue

        return self._empty_result(method_name)

    def _empty_result(self, method_name):
        """返回对应方法的空结果"""
        if method_name in ['get_hot_stocks', 'get_kline', 'get_limit_up_pool']:
            return pd.DataFrame()
        elif method_name == 'get_realtime_quote':
            return {}
        elif method_name == 'get_industry_map':
            return {}
        elif method_name == 'get_money_flow':
            return {'net_amount_3d': 0}
        return None

    def get_hot_stocks(self, top_n: int = TOP_HOT, trade_date: Optional[str] = None) -> pd.DataFrame:
        return self._parallel_query('get_hot_stocks', top_n, trade_date)

    def get_kline(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        return self._parallel_query('get_kline', symbol, start_date, end_date)

    def get_realtime_quote(self, symbol: str) -> dict:
        return self._parallel_query('get_realtime_quote', symbol)

    def get_limit_up_pool(self, date_str: str, trade_date: Optional[str] = None) -> pd.DataFrame:
        return self._parallel_query('get_limit_up_pool', date_str, trade_date)

    def get_industry_map(self) -> dict:
        return self._parallel_query('get_industry_map')

    def get_money_flow(self, symbol: str) -> dict:
        return self._parallel_query('get_money_flow', symbol)


# ═════════════════════════════════════════════════════════════════
# 4. 技术指标计算
# ═════════════════════════════════════════════════════════════════
def calc_macd(close, fast=MACD_FAST, slow=MACD_SLOW, signal=MACD_SIGNAL):
    ema_fast = close.ewm(span=fast, adjust=False).mean();
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    dif = ema_fast - ema_slow;
    dea = dif.ewm(span=signal, adjust=False).mean();
    hist = 2 * (dif - dea)
    return dif, dea, hist


def calc_kdj(high, low, close, n=KDJ_N, k=KDJ_K, d=KDJ_D):
    low_min = low.rolling(n).min();
    high_max = high.rolling(n).max()
    rsv = (close - low_min) / (high_max - low_min + 1e-9) * 100
    k_val = rsv.ewm(alpha=1 / k, adjust=False).mean();
    d_val = k_val.ewm(alpha=1 / d, adjust=False).mean()
    return k_val, d_val, 3 * k_val - 2 * d_val


def calc_rsi(close, period):
    delta = close.diff();
    gain = delta.clip(lower=0);
    loss = (-delta).clip(lower=0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean();
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()
    rs = avg_gain / (avg_loss + 1e-9);
    return 100 - (100 / (1 + rs))


def calc_boll(close, period=BOLL_PERIOD, num_std=BOLL_STD):
    mid = close.rolling(period).mean();
    std = close.rolling(period).std()
    return mid + num_std * std, mid, mid - num_std * std, (2 * num_std * std) / (mid + 1e-9) * 100


def calc_cci(high, low, close, period=CCI_PERIOD):
    tp = (high + low + close) / 3;
    sma = tp.rolling(period).mean();
    mad = (tp - sma).abs().rolling(period).mean()
    return (tp - sma) / (0.015 * mad + 1e-9)


def calc_atr(high, low, close, period=20):
    tr = pd.concat([high - low, (high - close.shift(1)).abs(), (low - close.shift(1)).abs()], axis=1).max(axis=1)
    return tr.rolling(period).mean()


def calc_wr(high, low, close, period=14):
    return (high.rolling(period).max() - close) / (high.rolling(period).max() - low.rolling(period).min() + 1e-9) * -100


def calc_psy(close, period=12): return (close.diff() > 0).rolling(period).sum() / period * 100


def calc_mtm(close, period=12): return close - close.shift(period)


def calc_obv(close, volume): return (close.diff().fillna(0).apply(np.sign) * volume).cumsum()


def calc_dmi_adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14):
    """DMI 简化实现：+DI / -DI / ADX（Wilder 平滑近似，用于趋势强度过滤）。"""
    high = high.astype(float)
    low = low.astype(float)
    close = close.astype(float)
    prev_high, prev_low, prev_close = high.shift(1), low.shift(1), close.shift(1)
    tr = pd.concat(
        [high - low, (high - prev_close).abs(), (low - prev_close).abs()],
        axis=1,
    ).max(axis=1)
    up_move = high - prev_high
    down_move = prev_low - low
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    alpha = 1.0 / period
    tr_s = tr.ewm(alpha=alpha, adjust=False).mean()
    plus_dm_s = pd.Series(plus_dm, index=high.index).ewm(alpha=alpha, adjust=False).mean()
    minus_dm_s = pd.Series(minus_dm, index=high.index).ewm(alpha=alpha, adjust=False).mean()
    plus_di = 100.0 * (plus_dm_s / (tr_s + 1e-9))
    minus_di = 100.0 * (minus_dm_s / (tr_s + 1e-9))
    dx = 100.0 * (plus_di - minus_di).abs() / (plus_di + minus_di + 1e-9)
    adx = dx.ewm(alpha=alpha, adjust=False).mean()
    return plus_di, minus_di, adx


def calc_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = _prepare_kline_ohlcv(df)
    if "volume" not in df.columns:
        df["volume"] = np.nan
    close = df['close'];
    high = df['high'];
    low = df['low'];
    volume = pd.to_numeric(df['volume'], errors='coerce')
    df['MA5'] = close.rolling(5).mean();
    df['MA10'] = close.rolling(10).mean()
    df['MA20'] = close.rolling(20).mean();
    df['MA30'] = close.rolling(MA_MID_PERIOD).mean()
    df['DIF'], df['DEA'], df['MACD_hist'] = calc_macd(close)
    df['K'], df['D'], df['J'] = calc_kdj(high, low, close)
    df['RSI6'] = calc_rsi(close, RSI_PERIOD_SHORT);
    df['RSI14'] = calc_rsi(close, RSI_PERIOD_LONG)
    df['BOLL_UP'], df['BOLL_MID'], df['BOLL_DOWN'], df['BOLL_WIDTH'] = calc_boll(close)
    df['CCI'] = calc_cci(high, low, close);
    df['ATR'] = calc_atr(high, low, close, ATR_PERIOD)
    df['VOL_MA5'] = volume.rolling(5, min_periods=5).mean();
    df['VOL_RATIO'] = np.where(df['VOL_MA5'] > 0, volume / df['VOL_MA5'], np.nan)
    df['BIAS5'] = (close - df['MA5']) / (df['MA5'] + 1e-9) * 100
    df['WR14'] = calc_wr(high, low, close, WR_PERIOD);
    df['PSY12'] = calc_psy(close, PSY_PERIOD)
    df['MTM12'] = calc_mtm(close, MTM_PERIOD);
    df['OBV'] = calc_obv(close, volume)
    df['PLUS_DI'], df['MINUS_DI'], df['ADX'] = calc_dmi_adx(high, low, close, DMI_PERIOD)
    if 'turnover_rate' not in df.columns: df['turnover_rate'] = 0
    _warm = int(
        max(
            MACD_SLOW + MACD_SIGNAL + 10,
            BOLL_PERIOD + 15,
            max(RSI_PERIOD_SHORT, RSI_PERIOD_LONG) + 10,
            KDJ_N + KDJ_K + 10,
            CCI_PERIOD + 15,
            WR_PERIOD + 10,
            max(PSY_PERIOD, MTM_PERIOD) + 5,
            DMI_PERIOD + 15,
            ATR_PERIOD + 10,
            MA_MID_PERIOD + 5,
            40,
        )
    )
    if len(df) > _warm:
        df = df.iloc[_warm:].reset_index(drop=True)
    return df


# ═════════════════════════════════════════════════════════════════
# 5. 买入评分 / 卖出紧迫度 / 操作建议
# ═════════════════════════════════════════════════════════════════
def calc_buy_score(row, prev_row, is_limit_up_yesterday, zt_strength: float = 0.0, extra_signals: dict = None) -> dict:
    score = 0.0;
    details = []
    if extra_signals is None: extra_signals = {}

    vol_ratio = _safe_float(row.get('VOL_RATIO', np.nan), np.nan)
    if not pd.isna(vol_ratio):
        if vol_ratio > 3.0:
            score += 2.0; details.append(f"量比>{vol_ratio:.1f}(+2)")
        elif vol_ratio >= 1.5:
            score += 1.0; details.append(f"量比{vol_ratio:.1f}(+1)")

    ma5 = row.get('MA5', 0) or 0;
    ma10 = row.get('MA10', 0) or 0;
    close = row.get('close', 0) or 0
    ma5_slope = extra_signals.get('ma5_slope', 0) or 0
    if ma5 > ma10 and close > ma5:
        if ma5_slope > 0.01:
            score += 1.5; details.append(f"MA多头发散(斜率{ma5_slope:.2f},+1.5)")
        elif ma5_slope > 0:
            score += 1.0; details.append("MA多头排列(+1.0)")
        else:
            score += 0.5; details.append("MA多头但走平(+0.5)")
    elif ma5_slope < 0 and ma5 < ma10:
        score -= 0.5; details.append("MA空头/下行(-0.5)")

    dif = row.get('DIF', 0) or 0;
    dea = row.get('DEA', 0) or 0
    prev_dif = prev_row.get('DIF', 0) or 0;
    prev_dea = prev_row.get('DEA', 0) or 0
    if (dif > dea and prev_dif <= prev_dea and dif > 0): score += 2.0; details.append("MACD水上金叉(+2)")
    if (dif > dea and prev_dif <= prev_dea and dif <= 0): score += 1.5; details.append("MACD水下金叉(+1.5)")

    k = row.get('K', 50) or 50;
    d = row.get('D', 50) or 50;
    prev_k = prev_row.get('K', 50) or 50;
    prev_d = prev_row.get('D', 50) or 50
    if k > d and prev_k <= prev_d and k < 30:
        score += 1.5; details.append("KDJ超卖金叉(+1.5)")
    elif (row.get('J', 0) or 0) < 0:
        score += 1.0; details.append("J<0极度超卖(+1)")

    rsi6 = row.get('RSI6', 0) or 0
    if rsi6 < 20:
        score += 1.5; details.append("RSI6<20(+1.5)")
    elif rsi6 < 30:
        score += 1.0; details.append("RSI6<30(+1)")

    boll_down = row.get('BOLL_DOWN', 0) or 0
    if close and boll_down and close <= boll_down * 1.01: score += 1.0; details.append("BOLL下轨(+1)")

    if is_limit_up_yesterday:
        turnover = row.get('turnover_rate', 0) or 0
        if 3 <= turnover <= 15:
            if zt_strength >= ZT_LOCK_SHARE_SUPER:
                score += 2.5; details.append("极强封单首板(+2.5)")
            elif zt_strength >= ZT_LOCK_SHARE_STRONG:
                score += 2.0; details.append("强封单首板(+2.0)")
            elif zt_strength > 0:
                score += 1.5; details.append("弱封单首板(+1.5)")
            else:
                score += 1.0; details.append("首板效应(+1.0)")

    cci = row.get('CCI', 0) or 0
    if cci < -100: score += 1.0; details.append("CCI超卖(+1)")

    wr14 = float(row.get('WR14', 0) or 0)
    if wr14 < WR_OVERSOLD_SINGLE:
        score += 0.5; details.append("威廉WR超卖(+0.5)")

    adx = float(row.get('ADX', 0) or 0)
    pdi = float(row.get('PLUS_DI', 0) or 0)
    mdi = float(row.get('MINUS_DI', 0) or 0)
    if adx > 18 and pdi > mdi and pdi > 15:
        score += 0.5; details.append("ADX趋势偏多(+0.5)")

    ma_mid = row.get('MA30', 0) or 0
    if ma_mid and close > ma_mid * 1.002:
        score += 0.5; details.append(f"站上MA{MA_MID_PERIOD}(+0.5)")

    bias5 = row.get('BIAS5', 0) or 0
    if bias5 > 12:
        score -= 2.0; details.append(f"BIAS5={bias5:.1f}%严重偏离(-2)")
    elif bias5 > 8:
        score -= 1.0; details.append(f"BIAS5={bias5:.1f}%明显偏高(-1)")
    elif bias5 > 6:
        score -= 0.5; details.append(f"BIAS5={bias5:.1f}%轻度偏高(-0.5)")

    vol_status, vol_score_delta = classify_volume_status(row)
    if vol_score_delta != 0: score += vol_score_delta; details.append(f"量能{vol_status}({vol_score_delta:+.1f})")

    vol_pattern, vol_pattern_score = extra_signals.get('vol_pattern', ('无', 0))
    if vol_pattern_score > 0: score += vol_pattern_score; details.append(f"{vol_pattern}({vol_pattern_score:+.1f})")

    net_amount_3d = extra_signals.get('net_amount_3d', 0) or 0
    if net_amount_3d > 50000000:
        score += 1.5; details.append("3日大单大幅净流入(+1.5)")
    elif net_amount_3d > 10000000:
        score += 1.0; details.append("3日大单净流入(+1.0)")

    oversold_hits = sum([
        cci < -100,
        rsi6 < 20,
        (boll_down and close and close <= boll_down * 1.01),
        (row.get('J', 0) or 0) < 0,
        wr14 < WR_OVERSOLD_FOR_RESONANCE,
    ])
    if oversold_hits >= 3:
        score += 2.0; details.append("三指标超卖共振(+2)")
    elif oversold_hits >= 2:
        score += 1.0; details.append("双指标超卖共振(+1)")

    profit_ratio = extra_signals.get('profit_ratio', 50) or 50
    if profit_ratio > 80:
        score += 0.3; details.append(f"获利比>{profit_ratio:.0f}%(+0.3)")
    elif profit_ratio < 30:
        score -= 1.0; details.append(f"获利比<{profit_ratio:.0f}%(-1)")

    if extra_signals.get('gap_support', False): score += 1.0; details.append("缺口支撑(+1.0)")

    if extra_signals.get('obv_bull'):
        score += 0.5; details.append("OBV抬升配合价(+0.5)")

    mad10 = extra_signals.get("ma10_above_days_10")
    if mad10 is not None:
        try:
            mad10_i = int(mad10)
        except (TypeError, ValueError):
            mad10_i = -1
        if mad10_i >= 0:
            if mad10_i >= 6:
                score += 0.75
                details.append(f"10日内{mad10_i}日收盘站上MA10(+0.75)")
            elif mad10_i <= 4:
                score -= 0.75
                details.append(f"10日内仅{mad10_i}日收盘站上MA10(-0.75)")

    return {'score': round(max(score, 0), 1), 'details': "; ".join(details) if details else "无得分"}


def calc_next_day_risk(latest, prev, extra_signals=None) -> dict:
    """v6.7 新增：计算次日风险分，用于调整买入评分。返回 {score, penalty, reasons}。"""
    extra_signals = extra_signals or {}
    risk = 0.0
    penalty = 0.0
    reasons = []
    pct = _safe_float(latest.get("pct_change", 0), 0)
    prev_pct = _safe_float(prev.get("pct_change", 0), 0)
    vol_ratio = _safe_float(latest.get("VOL_RATIO", np.nan), np.nan)
    rsi6 = _safe_float(latest.get("RSI6", 50), 50)
    cci = _safe_float(latest.get("CCI", 0), 0)
    wr = _safe_float(latest.get("WR14", -50), -50)
    bias5 = _safe_float(latest.get("BIAS5", 0), 0)
    profit_ratio = _safe_float(extra_signals.get("profit_ratio", 0), 0)
    change_5d = _safe_float(extra_signals.get("change_5d", 0), 0)

    # 1. 昨日涨停后今日转弱
    if prev_pct >= 9.5 and pct <= -5:
        risk += 8; penalty += 4.0
        reasons.append("昨日涨停后今日大跌，接力失败/资金兑现")
    elif prev_pct >= 9.5 and pct < 0:
        risk += 5; penalty += 2.5
        reasons.append("昨日涨停后今日收跌，接力失败风险")

    # 2. 当日涨幅过大
    if pct >= 9.5:
        risk += 5; penalty += 2.5
        reasons.append("当日涨停/接近涨停，次日兑现风险")
    elif pct >= 7:
        risk += 4; penalty += 2.0
        reasons.append("当日大涨超7%，追高风险")
    elif pct >= 5:
        risk += 2; penalty += 1.0
        reasons.append("当日涨幅超5%，存在短线兑现风险")

    # 3. CCI 过热
    if cci >= 200:
        risk += 4; penalty += 2.0
        reasons.append("CCI极度过热")
    elif cci >= 150:
        risk += 3; penalty += 2.0
        reasons.append("CCI过热")
    elif cci >= 120 and pct >= 5:
        risk += 2; penalty += 1.0
        reasons.append("CCI偏热且当日上涨")

    # 4. 5 日涨幅过高
    if change_5d >= 20:
        risk += 4; penalty += 2.0
        reasons.append("5日涨幅过大，短线兑现风险")
    elif change_5d >= 12:
        risk += 2; penalty += 1.0
        reasons.append("5日涨幅偏高")
    elif change_5d >= 9 and pct < 0:
        risk += 2; penalty += 1.0
        reasons.append("5日已有涨幅且今日转弱")

    # 5. WR 过热
    if wr >= -3 and pct >= 5:
        risk += 3; penalty += 1.5
        reasons.append("WR接近强势极值，短线过热")
    elif wr >= -10 and pct >= 5:
        risk += 2; penalty += 1.0
        reasons.append("WR偏热")

    # 6. 获利盘过高
    if profit_ratio >= 0.98 and pct >= 5:
        risk += 3; penalty += 1.5
        reasons.append("获利盘极高且当日大涨，兑现压力")
    elif profit_ratio >= 0.95 and pct >= 5:
        risk += 2; penalty += 1.0
        reasons.append("获利盘高且当日上涨")
    elif profit_ratio >= 0.95:
        risk += 1; penalty += 0.5
        reasons.append("获利盘偏高")

    # 7. 放量大涨
    if not pd.isna(vol_ratio):
        if vol_ratio >= 2.0 and pct >= 5:
            risk += 2; penalty += 1.0
            reasons.append("放量大涨，次日分歧风险")
        elif vol_ratio >= 1.5 and pct >= 5:
            risk += 1; penalty += 0.5
            reasons.append("放量上涨，注意次日分歧")

    # 8. 多指标过热共振
    hot_count = 0
    if rsi6 >= 75:
        hot_count += 1
    if cci >= 150:
        hot_count += 1
    if wr >= -5:
        hot_count += 1
    if bias5 >= 6:
        hot_count += 1
    if hot_count >= 3:
        risk += 5; penalty += 2.5
        reasons.append("多指标过热共振")
    elif hot_count == 2:
        risk += 3; penalty += 1.5
        reasons.append("双指标过热")

    return {
        "score": round(min(risk, 10), 1),
        "penalty": round(min(penalty, 6), 1),
        "reasons": "; ".join(reasons) if reasons else "无明显次日风险",
    }


def calc_sell_urgency(row, prev_row, prev2_row) -> dict:
    urgency = 0;
    reasons = []
    vol_ratio = _safe_float(row.get('VOL_RATIO', np.nan), np.nan)
    close = row.get('close', 0) or 0;
    open_price = row.get('open', 0) or 0
    if (not pd.isna(vol_ratio)) and vol_ratio > 5 and close < open_price: urgency += 5; reasons.append("爆量滞涨(+5)")

    dif = row.get('DIF', 0) or 0;
    dea = row.get('DEA', 0) or 0
    prev_dif = prev_row.get('DIF', 0) or 0;
    prev_dea = prev_row.get('DEA', 0) or 0
    k = row.get('K', 50) or 50
    if (dif < dea and prev_dif >= prev_dea and k > 70): urgency += 4; reasons.append("MACD死叉+K>70(+4)")

    ma5 = row.get('MA5', 0) or 0;
    ma10 = row.get('MA10', 0) or 0
    if close < ma5 and ma5 < ma10: urgency += 3; reasons.append("跌破MA5+死叉(+3)")
    if (row.get('J', 0) or 0) > 100: urgency += 3; reasons.append("J>100高位钝化(+3)")
    if (row.get('RSI6', 0) or 0) > 90: urgency += 3; reasons.append("RSI6>90超买(+3)")

    boll_mid = row.get('BOLL_MID', 0) or 0;
    prev_boll_mid = prev_row.get('BOLL_MID', 0) or 0
    if close < boll_mid and prev_row.get('close', 0) >= prev_boll_mid: urgency += 3; reasons.append("BOLL跌破中轨(+3)")

    bias5 = row.get('BIAS5', 0) or 0
    if bias5 > 12:
        urgency += 4; reasons.append(f"BIAS5={bias5:.1f}%严重偏离(+4)")
    elif bias5 > 8:
        urgency += 3; reasons.append(f"BIAS5={bias5:.1f}%明显偏高(+3)")
    elif bias5 > 6:
        urgency += 2; reasons.append(f"BIAS5={bias5:.1f}%轻度偏高(+2)")

    vol = row.get('volume', 0) or 0;
    prev_vol = prev_row.get('volume', 0) or 0;
    prev2_vol = prev2_row.get('volume', 0) or 0
    if vol < prev_vol and prev_vol < prev2_vol: urgency += 2; reasons.append("连续3天缩量(+2)")

    psy12 = float(row.get('PSY12', 50) or 50)
    if psy12 > 75:
        urgency += 2; reasons.append("PSY>75情绪过热(+2)")

    adx_s = float(row.get('ADX', 0) or 0)
    mdi_s = float(row.get('MINUS_DI', 0) or 0)
    pdi_s = float(row.get('PLUS_DI', 0) or 0)
    if adx_s > 25 and mdi_s > pdi_s and mdi_s > 20:
        urgency += 2; reasons.append("ADX偏空趋势(+2)")

    return {'urgency': min(urgency, 10), 'reasons': "; ".join(reasons) if reasons else "无紧迫信号"}


def get_operation_advice(buy_score: float, sell_urgency: int, next_day_risk: float = 0) -> str:
    if sell_urgency >= 9 or next_day_risk >= 9:
        return "高风险回避"
    elif sell_urgency >= 7 or next_day_risk >= 7:
        return "不追高，等待回落"
    elif buy_score >= 8 and next_day_risk <= 3:
        return "高评分低风险，次日关注"
    elif buy_score >= 6 and next_day_risk <= 4:
        return "谨慎关注"
    elif buy_score >= 4:
        return "观察，不追高"
    else:
        return "不操作"


# ═════════════════════════════════════════════════════════════════
# 6. 输出与报告生成
# ═════════════════════════════════════════════════════════════════

def _parse_run_stamp_from_filename(name: str) -> Optional[datetime]:
    """从 buy_signals_YYYYMMDD_YYYYMMDD_HHMMSS.xlsx / run_meta_*.json 等解析本次运行时间（用于按天清理）。"""
    m = re.search(r"_(\d{8}_\d{6})\.(json|xlsx|html)$", name, re.I)
    if m:
        try:
            return datetime.strptime(m.group(1), "%Y%m%d_%H%M%S")
        except ValueError:
            return None
    return None


def _parse_batch_folder_run_time(name: str) -> Optional[datetime]:
    """从子目录名 `batch_{K线截止YYYYMMDD}_{运行YYYYMMDD_HHMMSS}` 解析运行时刻（用于按天清理）。"""
    m = re.match(r"^batch_\d{8}_(\d{8}_\d{6})$", name)
    if not m:
        return None
    try:
        return datetime.strptime(m.group(1), "%Y%m%d_%H%M%S")
    except ValueError:
        return None


def cleanup_old_screener_outputs(output_dir: Path, retention_days: int) -> None:
    """删除选股结果目录中带运行时间戳的旧输出，仅保留最近 retention_days 天（按文件名或 batch 子目录名内时间戳判断）。"""
    if retention_days <= 0 or not output_dir.is_dir():
        return
    cutoff = datetime.now() - timedelta(days=retention_days)
    legacy_re = re.compile(r"^(buy_signals|heatmap)_\d{8}\.(json|xlsx|html)$", re.I)
    for p in output_dir.iterdir():
        if p.is_dir():
            ts_dir = _parse_batch_folder_run_time(p.name)
            if ts_dir is None:
                continue
            if ts_dir >= cutoff:
                continue
            try:
                shutil.rmtree(p, ignore_errors=False)
                print(f"[清理] 已删除过期结果目录（>{retention_days} 天）：{p.name}")
            except OSError as e:
                print(f"[清理] 删除目录失败 {p.name}: {e}")
            continue
        if not p.is_file():
            continue
        name = p.name
        ts = _parse_run_stamp_from_filename(name)
        if ts is None and legacy_re.match(name):
            ts = datetime.fromtimestamp(p.stat().st_mtime)
        if ts is None or ts >= cutoff:
            continue
        try:
            p.unlink()
            print(f"[清理] 已删除过期结果（>{retention_days} 天）：{name}")
        except OSError as e:
            print(f"[清理] 删除失败 {name}: {e}")


def build_screener_run_meta(
    trade_date: str,
    target_date: Optional[str],
    run_started_at: str,
    run_finished_at: str,
) -> dict:
    """生成写入 JSON / Excel / HTML 的说明：以 K 线日线截止日为准，并记录本次运行起止时间。"""
    td_fmt = f"{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:8]}"
    if target_date:
        mode = "指定目标日"
    else:
        mode = "自动（get_last_trade_date(1)）"
    remark_zh = (
        f"K线日线截止日：{td_fmt}（{trade_date}）。本批选股与技术指标均以该日为日线截面；"
        f"目标日：{target_date or '未指定，走自动'}；模式：{mode}。"
        "适用A股现货T+1：当日买入最早下一交易日方可卖出；操作建议中的「次日」类表述与此一致"
        "（不含融资融券当日回转等特殊规则）。"
        "本程序不包含券商报单、撤单等交易接口，输出仅供研究复盘；非资金曲线类逐日回测引擎。"
    )
    meta = {
        "程序版本": VERSION,
        "运行开始时刻": run_started_at,
        "运行结束时刻": run_finished_at,
        "K线日线截止日": td_fmt,
        "K线日线截止日_trade_date": trade_date,
        "目标日参数": target_date or "（未传，走自动）",
        "基准日模式": mode,
        "结果保留天数配置": RESULT_RETENTION_DAYS,
        "备注": remark_zh,
        "生效配置摘要": _sanitize_config_for_meta(config),
        "展示行数_DISPLAY_TOP_N": DISPLAY_TOP_N,
        "HTML图表行数_HTML_CHART_TOP_N": HTML_CHART_TOP_N,
    }
    return meta


def _md_escape_cell(val: Any, max_len: int = 32) -> str:
    s = "" if val is None or (isinstance(val, float) and pd.isna(val)) else str(val)
    s = s.replace("|", "｜").replace("\r", " ").replace("\n", " ")
    if len(s) > max_len:
        s = s[: max_len - 1] + "…"
    return s


def _hint_append_project_root_docs(parts: list[str]) -> None:
    """把项目根目录下的参考 md、映射脚本等绝对路径追加进提示文件。"""
    root = Path.cwd().resolve()
    names = (
        "MAP_DRIVE_FOR_CURSOR.cmd",
        "UNMAP_DRIVE_FOR_CURSOR.cmd",
        "短线优化_外部参考清单.md",
        "STOCK_SCREENER_EXTERNAL_REFERENCES.md",
    )
    found = [root / n for n in names if (root / n).is_file()]
    if not found:
        return
    parts.extend(
        [
            "",
            "---------- 项目根目录（脚本 / 文档；复制路径或双击 .cmd）----------",
            "",
        ]
    )
    for p in found:
        parts.append(str(p.resolve()))


def write_report_open_hint_minimal(output_dir: Path) -> None:
    """尚无 batch 结果时，仍写入「打开本轮报告.txt」，至少包含根目录参考文档路径。"""
    output_dir.mkdir(parents=True, exist_ok=True)
    hint = output_dir / "打开本轮报告.txt"
    parts = [
        "【说明】Cursor 聊天里自动生成的文件链接，对「含中文的磁盘路径」常解析失败，提示 Unable to resolve resource。",
        "这与文件是否存在、是否有权限无关；文件在磁盘上，应用左侧文件树双击打开，或复制路径到「文件 → 打开文件」。",
        "",
        "【想在聊天框里直接点开链接（最可靠）】请在本目录双击运行 MAP_DRIVE_FOR_CURSOR.cmd，",
        "按提示用 Cursor「打开文件夹」选映射出的盘符（如 W:\\），再在该工作区里聊天；无需移动项目文件夹。",
        "解除映射运行 UNMAP_DRIVE_FOR_CURSOR.cmd。",
        "",
        "当前「选股结果」下还没有 batch_* 子目录时，请先运行一次选股；下方为项目内参考文档路径（若有）：",
        "",
    ]
    _hint_append_project_root_docs(parts)
    try:
        hint.write_text("\n".join(parts), encoding="utf-8-sig")
        print(f"[输出] 已写入（仅文档路径）: {hint.resolve()}")
    except OSError as e:
        print(f"[输出] 写入「打开本轮报告.txt」失败: {e}")


def write_report_open_hint(
    output_dir: Path,
    batch_dir: Path,
    report_md: Optional[Path],
    xlsx_path: Path,
    html_path: Optional[Path],
) -> None:
    """
    写入「纯文本本地路径」到 选股结果/打开本轮报告.txt。
    Cursor/聊天中的 file:// 或 URL 编码链接在含中文路径时常报 Unable to resolve resource，用本文件复制路径即可打开。
    """
    hint = output_dir / "打开本轮报告.txt"
    batch_res = str(batch_dir.resolve())
    parts = [
        "【说明】若在 Cursor 或浏览器里点击聊天中的文件链接出现 Unable to resolve resource，",
        "多为 file:// 与中文路径、URL 编码（%5C 等）不兼容，报告文件仍在磁盘上。",
        "（不是权限不足；用资源管理器或左侧文件树可正常打开同一文件。）",
        "",
        "【想在聊天框里直接点开链接（最可靠）】在本项目根目录双击 MAP_DRIVE_FOR_CURSOR.cmd，",
        "然后用 Cursor「文件 → 打开文件夹」选择映射盘符（如 W:\\）；工作区根路径变为纯英文后，聊天内链接通常可点开。",
        "解除映射：UNMAP_DRIVE_FOR_CURSOR.cmd。",
        "",
        "请任选一种方式：",
        "1) 复制下面「整行」路径，粘贴到 Windows 资源管理器地址栏后回车；",
        "2) Cursor：文件 → 打开文件… → 粘贴路径；",
        "3) 在左侧项目树中展开：选股结果 → 对应 batch_… 文件夹 → 双击 FINAL_REPORT_….md 或 .xlsx",
        "",
        "---------- 本轮路径（仅复制路径本身，勿带引号或多余空格）----------",
        "",
        "【结果文件夹】",
        batch_res,
        "",
    ]
    if report_md is not None:
        parts.extend(["【Markdown 总览】", str(report_md.resolve()), ""])
    parts.extend(["【Excel】", str(xlsx_path.resolve()), ""])
    if html_path is not None:
        try:
            if html_path.exists():
                parts.extend(["【热力图 HTML】", str(html_path.resolve()), ""])
        except OSError:
            pass
    _hint_append_project_root_docs(parts)
    try:
        hint.write_text("\n".join(parts), encoding="utf-8-sig")
        print(f"[输出] 可复制路径（聊天链接打不开时用）：{hint.resolve()}")
    except OSError as e:
        print(f"[输出] 写入「打开本轮报告.txt」失败: {e}")


def write_final_report_md(
    batch_dir: Path,
    df_result: pd.DataFrame,
    run_meta: dict,
    trade_date: str,
    run_stamp: str,
    scan_total: int,
    display_top_n: int,
) -> Optional[Path]:
    """本轮选股文字总览（Markdown），与 xlsx/json 同目录。"""
    path = batch_dir / f"FINAL_REPORT_{trade_date}_{run_stamp}.md"
    lines: list[str] = []
    lines.append("# 短线选股 — 本轮总览报告")
    lines.append("")
    lines.append(
        "> **如何打开本文件**：不要用聊天里的 `file://` 链接打开含中文的路径。"
        "请用资源管理器打开文件夹 `选股结果\\batch_…\\`，或打开同目录上一级中的 `打开本轮报告.txt` 复制路径。"
    )
    lines.append("")
    lines.append(f"- **程序版本**: {VERSION}")
    lines.append(f"- **K 线日线截止日**: {trade_date}")
    lines.append(f"- **运行时间戳**: {run_stamp}")
    if run_meta:
        lines.append(f"- **运行起止**: {run_meta.get('运行开始时刻', '')} → {run_meta.get('运行结束时刻', '')}")
    lines.append(f"- **扫描热门股数**: {scan_total}")
    lines.append(f"- **通过筛选行数**: {len(df_result)}")
    lines.append(f"- **控制台高分列表行数上限**: {display_top_n}（评分≥{DISPLAY_TOP_MIN_SCORE:g}）")
    lines.append("")
    hs = run_meta.get("数据源健康摘要") if run_meta else None
    if isinstance(hs, dict) and hs:
        lines.append("## 数据源健康摘要")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(hs, ensure_ascii=False, indent=2))
        lines.append("```")
        lines.append("")
    lines.append("## 重要说明")
    lines.append("")
    lines.append(
        "1. **无自动下单**：本仓库不提供连接券商柜台、报单、撤单、查询委托等功能；"
        "任何「买入/卖出」表述均为模型化**操作建议**，不构成投资建议。"
    )
    lines.append(
        "2. **与「拉一年数据做资金曲线回测」的区别**：当前主流程为**某一 K 线截止日**下，"
        "对当日热门前 N 只做截面扫描；并非按交易日滚动持仓、计佣金/滑点的组合回测。"
        "若要做一年样本外验证，需单独实现按日信号与仓位规则（并注意东财 API 流量与权限）。"
    )
    lines.append("")
    if run_meta and run_meta.get("备注"):
        lines.append("## 运行说明（摘要）")
        lines.append("")
        lines.append(str(run_meta["备注"]))
        lines.append("")
    if df_result is None or df_result.empty:
        lines.append("## 筛选结果")
        lines.append("")
        lines.append("（无数据行）")
    else:
        bs = pd.to_numeric(df_result["买入评分"], errors="coerce")
        lines.append("## 统计摘要")
        lines.append("")
        lines.append(
            f"- **买入评分**: min={bs.min():.2f}, max={bs.max():.2f}, mean={bs.mean():.2f}, median={bs.median():.2f}"
        )
        if "卖出紧迫度" in df_result.columns:
            u = pd.to_numeric(df_result["卖出紧迫度"], errors="coerce")
            lines.append(
                f"- **卖出紧迫度**: min={u.min():.2f}, max={u.max():.2f}, mean={u.mean():.2f}"
            )
        # v6.7 风控分类
        high_low_risk = len(df_result[(df_result['买入评分'] >= 8) & (df_result['次日风险分'] <= 3)])
        mid_attention = len(df_result[(df_result['买入评分'] >= 6) & (df_result['次日风险分'] <= 4)])
        high_risk_strong = len(df_result[(df_result['原始买入评分'] >= 6) & (df_result['次日风险分'] > 4)])
        lines.append(f"- **高评分低风险(评分≥8 且 风险≤3)**: {high_low_risk} 只")
        lines.append(f"- **中等关注(评分≥6 且 风险≤4)**: {mid_attention} 只")
        lines.append(f"- **高风险强势股(原始≥6 但 风险>4)**: {high_risk_strong} 只")
        lines.append("")
        if "操作建议" in df_result.columns:
            lines.append("### 操作建议分布")
            lines.append("")
            for k, v in df_result["操作建议"].value_counts(dropna=False).head(20).items():
                lines.append(f"- {_md_escape_cell(k, 80)}: **{int(v)}**")
            lines.append("")
        if "量能状态" in df_result.columns:
            lines.append("### 量能状态分布（前 12 类）")
            lines.append("")
            for k, v in df_result["量能状态"].value_counts(dropna=False).head(12).items():
                lines.append(f"- {_md_escape_cell(k, 40)}: **{int(v)}**")
            lines.append("")
        lines.append("## 强信号子集（建议优先复盘，与「次日涨跌」无必然对应）")
        lines.append("")
        n_hl = len(df_result[(df_result["买入评分"] >= 8) & (df_result["次日风险分"] <= 3)])
        n_mid = len(df_result[(df_result["买入评分"] >= 6) & (df_result["次日风险分"] <= 4)])
        n_risk = len(df_result[(df_result["原始买入评分"] >= 6) & (df_result["次日风险分"] > 4)])
        lines.append(f"- **高评分低风险(评分≥8 且 风险≤3)**: {n_hl} 只；**中等关注(评分≥6 且 风险≤4)**: {n_mid} 只；**高风险强势股(原始≥6 但 风险>4)**: {n_risk} 只")
        lines.append("")
        for title, sub in (
            ("高评分低风险（前 20）", df_result[(df_result["买入评分"] >= 8) & (df_result["次日风险分"] <= 3)].head(20)),
            ("中等关注（前 20）", df_result[(df_result["买入评分"] >= 6) & (df_result["次日风险分"] <= 4)].head(20)),
        ):
            lines.append(f"### {title}")
            lines.append("")
            cols_t = [c for c in ("代码", "名称", "买入评分", "次日风险分", "原始买入评分", "卖出紧迫度", "操作建议", "所属行业") if c in sub.columns]
            if cols_t and not sub.empty:
                lines.append("| " + " | ".join(cols_t) + " |")
                lines.append("| " + " | ".join(["---"] * len(cols_t)) + " |")
                for _, row in sub.iterrows():
                    cells = [_md_escape_cell(row.get(c), 20) for c in cols_t]
                    lines.append("| " + " | ".join(cells) + " |")
            else:
                lines.append("（本档无数据）")
            lines.append("")
        lines.append("## 评分排序表（前 100 行，完整数据见同目录 xlsx/json）")
        lines.append("")
        head_n = min(100, len(df_result))
        sub = df_result.head(head_n)
        cols = [c for c in ("代码", "名称", "买入评分", "次日风险分", "原始买入评分", "卖出紧迫度", "操作建议", "量能状态", "所属行业") if c in sub.columns]
        if cols:
            lines.append("| " + " | ".join(cols) + " |")
            lines.append("| " + " | ".join(["---"] * len(cols)) + " |")
            for _, row in sub.iterrows():
                cells = [_md_escape_cell(row.get(c), 24) for c in cols]
                lines.append("| " + " | ".join(cells) + " |")
        lines.append("")
    lines.append("---")
    lines.append("*由 短线选股软件_v6.7.py 自动生成*")
    try:
        path.write_text("\n".join(lines), encoding="utf-8")
        print(f"[输出] 文字总览 Markdown：{path.resolve()}")
        return path
    except OSError as e:
        print(f"[输出] Markdown 报告保存失败: {e}")
        return None


def save_excel_with_industry_sheets(df_result: pd.DataFrame, xlsx_path: Path, run_meta: Optional[dict] = None):
    display_cols = [
        '代码', '名称', '最新价', '涨跌幅(%)', '昨日涨跌幅(%)', '5日涨幅(%)',
        '所属行业', '换手率(%)', '量比', '量能状态',
        '原始买入评分', '买入评分', '次日风险分', '次日风险原因',
        '卖出紧迫度', '操作建议',
        '止损价', '止盈价', '盈亏比', '风险%',
        '评分明细', '紧迫原因',
        'RSI6', 'CCI', 'BIAS5', 'WR14', 'ADX', 'BOLL位置', '超卖共振'
    ]
    valid_cols = [c for c in display_cols if c in df_result.columns]

    with pd.ExcelWriter(xlsx_path, engine='openpyxl') as writer:
        if run_meta:
            rows = []
            for k, v in run_meta.items():
                if k == "数据源健康摘要" and isinstance(v, dict):
                    rows.append({"项": k, "值": json.dumps(v, ensure_ascii=False, indent=2)})
                else:
                    rows.append({"项": k, "值": str(v)})
            meta_df = pd.DataFrame(rows)
            meta_df.to_excel(writer, sheet_name='运行说明', index=False)
        df_result[valid_cols].to_excel(writer, sheet_name='候选股票池', index=False)
        # v6.7 风控分级 Sheet
        df_high_low = df_result[(df_result['买入评分'] >= 8) & (df_result['次日风险分'] <= 3)]
        if not df_high_low.empty: df_high_low[valid_cols].to_excel(writer, sheet_name='高评分低风险(≥8且风险≤3)', index=False)
        df_mid = df_result[(df_result['买入评分'] >= 6) & (df_result['次日风险分'] <= 4)]
        if not df_mid.empty: df_mid[valid_cols].to_excel(writer, sheet_name='中等关注(≥6且风险≤4)', index=False)
        df_risk = df_result[(df_result['原始买入评分'] >= 6) & (df_result['次日风险分'] > 4)]
        if not df_risk.empty: df_risk[valid_cols].to_excel(writer, sheet_name='高风险强势股(原始≥6风险>4)', index=False)
        df_ge6 = df_result[df_result["买入评分"] >= 6].sort_values("买入评分", ascending=False)
        if not df_ge6.empty:
            df_ge6[valid_cols].to_excel(writer, sheet_name="评分≥6汇总", index=False)

        if '所属行业' in df_result.columns:
            industry_counts = df_result['所属行业'].value_counts()
            big_industries = industry_counts[industry_counts >= INDUSTRY_MIN_STOCKS].index.tolist()
            small_industries = industry_counts[industry_counts < INDUSTRY_MIN_STOCKS].index.tolist()

            for ind in big_industries:
                ind_df = df_result[df_result['所属行业'] == ind]
                if not ind_df.empty: ind_df[valid_cols].to_excel(writer, sheet_name=ind[:30], index=False)
            if small_industries:
                df_other = df_result[df_result['所属行业'].isin(small_industries)]
                if not df_other.empty: df_other[valid_cols].to_excel(writer, sheet_name='其他行业', index=False)

            industry_stats = df_result.groupby('所属行业').agg({
                '代码': 'count', '买入评分': 'mean',
                '操作建议': lambda x: (x == '高评分低风险，次日关注').sum()
            }).rename(columns={'代码': '股票数', '买入评分': '平均评分', '操作建议': '高评低风险数'})
            industry_stats.sort_values('平均评分', ascending=False).to_excel(writer, sheet_name='行业统计')


def generate_html_heatmap(
    df_result: pd.DataFrame,
    output_path: Path,
    trade_date: str,
    run_meta: Optional[dict] = None,
    html_table_top_n: Optional[int] = None,
):
    if df_result.empty: return
    n_chart = int(html_table_top_n if html_table_top_n is not None else HTML_CHART_TOP_N)
    n_chart = max(5, min(200, n_chart))
    total_count = len(df_result);
    strong_buy = len(df_result[(df_result['买入评分'] >= 8) & (df_result['次日风险分'] <= 3)])
    hold_count = len(df_result[df_result['操作建议'] == '谨慎关注'])
    avg_score = round(df_result['买入评分'].mean(), 2)
    top_chart = df_result.head(min(n_chart, len(df_result)))

    def safe_fmt(val, fmt, suffix=""):
        if pd.isna(val) or val == '-': return '-'
        try:
            return f"{float(val):{fmt}}{suffix}"
        except Exception:
            return '-'

    top30_rows = ""
    for _, row in top_chart.iterrows():
        sc = '#00c853' if row.get('买入评分', 0) >= 8 else '#64dd17' if row.get('买入评分',
                                                                                0) >= 6 else '#fdd835' if row.get(
            '买入评分', 0) >= 4 else '#ff9100' if row.get('买入评分', 0) >= 2 else '#f44336'
        uc = '#f44336' if row.get('卖出紧迫度', 0) >= 8 else '#ff9100' if row.get('卖出紧迫度',
                                                                                  0) >= 6 else '#fdd835' if row.get(
            '卖出紧迫度', 0) >= 4 else '#64dd17' if row.get('卖出紧迫度', 0) >= 2 else '#00c853'
        disp_name = (str(row.get('名称', '') or '').strip()) or "—"
        top30_rows += f"""<tr>
            <td>{row.get('代码', '')}</td><td>{disp_name}</td><td>{safe_fmt(row.get('最新价', '-'), '.2f')}</td>
            <td>{safe_fmt(row.get('涨跌幅(%)', '-'), '.2f', '%')}</td>
            <td style="background:{sc};color:#000;font-weight:bold">{safe_fmt(row.get('买入评分', '-'), '.1f')}</td>
            <td style="color:#f85149;font-weight:bold">{safe_fmt(row.get('次日风险分', '-'), '.1f')}</td>
            <td>{safe_fmt(row.get('原始买入评分', '-'), '.1f')}</td>
            <td style="background:{uc};color:#fff;font-weight:bold">{safe_fmt(row.get('卖出紧迫度', '-'), '.1f')}</td>
            <td>{row.get('操作建议', '-')}</td><td>{row.get('量能状态', '-')}</td>
            <td>{safe_fmt(row.get('止损价', '-'), '.2f')}</td><td>{safe_fmt(row.get('止盈价', '-'), '.2f')}</td>
            <td>{safe_fmt(row.get('盈亏比', '-'), '.1f')}</td><td>{safe_fmt(row.get('风险%', '-'), '.2f', '%')}</td>
            <td>{row.get('共振', '无')}</td>
            <td>{safe_fmt(row.get('RSI6', '-'), '.1f')}</td><td>{safe_fmt(row.get('CCI', '-'), '.1f')}</td>
            <td>{safe_fmt(row.get('BIAS5', '-'), '.1f')}</td><td>{row.get('BOLL位置', '-')}</td></tr>"""

    industry_chart_html = ""
    if '所属行业' in df_result.columns:
        industry_stats = df_result.groupby('所属行业')['买入评分'].mean().nlargest(15).sort_values(ascending=True)
        ind_labels = json.dumps(list(industry_stats.index), ensure_ascii=False)
        ind_values = list(industry_stats.values)
        industry_chart_html = f"""<div class="chart-box"><canvas id="industryChart" height="150"></canvas></div>
        <script>
        new Chart(document.getElementById('industryChart'), {{
            type: 'bar', data: {{ labels: {ind_labels}, datasets: [{{ label: '平均评分', data: {ind_values}, backgroundColor: 'rgba(255,159,64,0.6)', borderRadius: 4 }}] }},
            options: {{ indexAxis: 'y', responsive: true, scales: {{ x: {{ grid: {{ color: '#21262d' }} }} , y: {{ grid: {{ color: '#21262d' }} }} }}, plugins: {{ legend: {{ labels: {{ color: '#8b949e' }} }} }} }}
        }});
        </script>"""

    meta_sub = ""
    if run_meta:
        esc = html_escape(str(run_meta.get("备注", "")))
        rs, rf = run_meta.get("运行开始时刻", ""), run_meta.get("运行结束时刻", "")
        kd = run_meta.get("K线日线截止日", "")
        kraw = run_meta.get("K线日线截止日_trade_date", trade_date)
        meta_sub = (
            f"<div style=\"max-width:920px;margin:8px auto 16px;padding:12px;background:#161b22;border:1px solid #30363d;"
            f"border-radius:8px;font-size:13px;color:#c9d1d9;line-height:1.55;text-align:left\">"
            f"<div style=\"color:#8b949e;font-size:12px;margin-bottom:6px\">运行说明</div>"
            f"<div style=\"color:#e6edf3;margin-bottom:8px\">K线日线截止日：{html_escape(str(kd))}（{html_escape(str(kraw))}）　"
            f"运行开始：{html_escape(str(rs))}　运行结束：{html_escape(str(rf))}</div>"
            f"<div style=\"color:#e6edf3\">{esc}</div></div>"
        )

    html = f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8">
        <title>短线选股热力图 {trade_date}</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
        <style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:'Microsoft YaHei';background:#0d1117;color:#e6edf3;padding:20px}}
        .cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin-bottom:20px}}
        .card{{background:#161b22;border:1px solid #30363d;border-radius:10px;padding:16px;text-align:center}}
        .card .num{{font-size:32px;font-weight:bold;color:#58a6ff}}
        .card .label{{font-size:12px;color:#8b949e;margin-top:4px}}
        table{{width:100%;border-collapse:collapse;font-size:12px}}th{{background:#21262d;color:#8b949e;padding:8px;text-align:center}}td{{padding:7px;text-align:center;border-bottom:1px solid #21262d}}
        .table-wrap{{max-height:600px;overflow-y:auto;border:1px solid #30363d;border-radius:8px}}
        .chart-box{{background:#161b22;border:1px solid #30363d;border-radius:10px;padding:16px;margin-bottom:16px}}</style></head><body>
        <h1 style="text-align:center;color:#58a6ff">短线选股系统 热力图报告</h1>
        <div style="text-align:center;color:#8b949e;margin-bottom:8px">{VERSION} | K线日线截止日：{trade_date}</div>
        {meta_sub}
        <div class="cards">
          <div class="card"><div class="num">{total_count}</div><div class="label">候选股票数</div></div>
          <div class="card"><div class="num" style="color:#3fb950">{strong_buy}</div><div class="label">高评低风险</div></div>
          <div class="card"><div class="num" style="color:#d29922">{hold_count}</div><div class="label">谨慎关注</div></div>
          <div class="card"><div class="num">{avg_score}</div><div class="label">平均评分</div></div>
        </div>
        <div class="chart-box"><canvas id="barChart" height="100"></canvas></div>
        <div class="chart-box">
          <div class="table-wrap"><table><thead><tr><th>代码</th><th>名称</th><th>最新价</th><th>涨跌幅</th>
          <th>买入评分</th><th>风险分</th><th>原始评分</th><th>卖出紧迫度</th><th>操作建议</th><th>量能状态</th><th>止损价</th><th>止盈价</th><th>盈亏比</th><th>风险%</th><th>共振</th>
          <th>RSI6</th><th>CCI</th><th>BIAS5</th><th>BOLL位置</th></tr></thead>
          <tbody>{top30_rows}</tbody></table></div>
        </div>
        <h3 style="color:#58a6ff;margin-top:20px;margin-bottom:10px">行业平均评分 Top 15</h3>
        {industry_chart_html}
        <script>
        const TOP30_LABELS = {json.dumps(list(top_chart['名称'].values), ensure_ascii=False)};
        const TOP30_SCORES = {list(top_chart['买入评分'].values)};
        const TOP30_URGENCY = {list(top_chart['卖出紧迫度'].values)};
        new Chart(document.getElementById('barChart'), {{
            type: 'bar',
            data: {{ labels: TOP30_LABELS, datasets: [{{ label: '买入评分', data: TOP30_SCORES, backgroundColor: 'rgba(0,200,83,0.6)', borderRadius: 4 }}, {{ label: '卖出紧迫度', data: TOP30_URGENCY, backgroundColor: 'rgba(244,67,54,0.6)', borderRadius: 4 }}] }},
            options: {{ responsive: true, scales: {{ y: {{ max: 10, grid: {{ color: '#21262d' }} }}, x: {{ grid: {{ color: '#21262d' }} }} }}, plugins: {{ legend: {{ labels: {{ color: '#8b949e' }} }} }} }}
        }});
        </script></body></html>"""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"\n[HTML] 热力图已保存：{output_path}")


def build_screener_signal_row(
    data_source: DataSourceAdapter,
    code: str,
    name: str,
    df: pd.DataFrame,
    zt_codes: set[str],
    zt_pool_df: pd.DataFrame,
    industry_map: dict,
) -> Optional[dict]:
    """
    由已通过 calc_all_indicators 且 len>=3 的 K 线 df 生成一行选股结果。
    调用方需已处理 check_consecutive_limit_up 与 MIN_KDATA_DAYS；本函数内做换手/量比硬过滤。
    """
    if len(df) < 3:
        return None
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    prev2 = df.iloc[-3]
    if latest["turnover_rate"] > MAX_TURNOVER_RATE:
        return None
    latest_vol_ratio = _safe_float(latest.get("VOL_RATIO", np.nan), np.nan)
    # v6.6.2：量比缺失时不误当 1 或“正常”；VOL 不可用时已在 K 线清洗阶段尝试 AMOUNT/CLOSE 代理。
    if (not pd.isna(latest_vol_ratio)) and latest_vol_ratio < MIN_VOL_RATIO_STRICT:
        return None

    is_zt = normalize_stock_code(code) in zt_codes
    current_price = float(latest["close"])
    zt_strength = get_lock_amount(code, zt_pool_df, current_price) if is_zt else 0.0

    extra_signals: dict[str, Any] = {}
    if len(df) >= 6 and not pd.isna(df.iloc[-6].get("MA5", np.nan)) and df.iloc[-6]["MA5"] > 0:
        extra_signals["ma5_slope"] = (latest["MA5"] - df.iloc[-6]["MA5"]) / df.iloc[-6]["MA5"]
    else:
        extra_signals["ma5_slope"] = 0.0

    vol_pattern, vol_pattern_score = check_volume_pattern(df)
    extra_signals["vol_pattern"] = (vol_pattern, vol_pattern_score)

    if ENABLE_MONEY_FLOW:
        flow_data = data_source.get_money_flow(code)
        extra_signals["net_amount_3d"] = flow_data.get("net_amount_3d", 0)
    else:
        extra_signals["net_amount_3d"] = 0

    extra_signals["profit_ratio"] = calc_profit_ratio(df)
    extra_signals["gap_support"] = check_gap_support(df)

    obv_bull = False
    if len(df) >= 6 and not pd.isna(latest.get("OBV", np.nan)) and not pd.isna(df.iloc[-6].get("OBV", np.nan)):
        ma5v = float(latest.get("MA5", 0) or 0)
        obv_bull = float(latest["OBV"]) > float(df.iloc[-6]["OBV"]) and current_price > ma5v > 0
    extra_signals["obv_bull"] = obv_bull

    tail10 = df.tail(10)
    if len(tail10) >= 10 and "MA10" in tail10.columns:
        extra_signals["ma10_above_days_10"] = int(
            (tail10["close"].astype(float) > tail10["MA10"].astype(float)).sum()
        )
    else:
        extra_signals["ma10_above_days_10"] = None

    # v6.7：先算 5日涨幅，加入 extra_signals 供 calc_next_day_risk 使用
    if len(df) >= 6 and df.iloc[-6]["close"] > 0:
        change_5d = round((current_price / df.iloc[-6]["close"] - 1) * 100, 2)
    else:
        change_5d = 0
    extra_signals["change_5d"] = change_5d

    # v6.7：先算次日风险，再算原始买入评分，用风险惩罚调整
    next_risk = calc_next_day_risk(latest, prev, extra_signals)
    buy_result = calc_buy_score(latest, prev, is_zt, zt_strength, extra_signals)
    raw_buy_score = buy_result["score"]
    adjusted_buy_score = max(0, round(raw_buy_score - next_risk["penalty"], 1))
    sell_result = calc_sell_urgency(latest, prev, prev2)
    adjusted_sell_urgency = min(
        10,
        round(sell_result["urgency"] + max(0, next_risk["score"] - 6) * 0.5, 1)
    )
    advice = get_operation_advice(
        adjusted_buy_score,
        int(adjusted_sell_urgency),
        next_risk["score"],
    )
    sltp = calc_stop_loss_take_profit(df, current_price)
    vol_status, _ = classify_volume_status(latest)

    yesterday_change = round(float(prev.get("pct_change", 0) or 0), 2)

    boll_loc = "下轨" if (latest.get("BOLL_DOWN", 0) and current_price <= latest["BOLL_DOWN"] * 1.01) else (
        "上轨" if (latest.get("BOLL_UP", 0) and current_price >= latest["BOLL_UP"]) else "中轨附近")

    nm_out = (str(name).strip() if name is not None else "")
    if not nm_out or normalize_stock_code(nm_out) == code:
        nm_out = "（简称未获取）"

    volume_out = _round_or_none(latest.get("volume", np.nan), 2)
    vol_ma5_out = _round_or_none(latest.get("VOL_MA5", np.nan), 2)
    vol_ratio_out = _round_or_none(latest.get("VOL_RATIO", np.nan), 2)

    return {
        "代码": code,
        "名称": nm_out,
        "最新价": round(current_price, 2),
        "涨跌幅(%)": round(float(latest.get("pct_change", 0) or 0), 2),
        "昨日涨跌幅(%)": yesterday_change,
        "5日涨幅(%)": change_5d,
        "所属行业": industry_map.get(code, "未知"),
        "换手率(%)": round(float(latest.get("turnover_rate", 0) or 0), 2),
        "成交量": volume_out,
        "5日均量": vol_ma5_out,
        "量比": vol_ratio_out,
        "量能状态": vol_status,
        "原始买入评分": raw_buy_score,
        "买入评分": adjusted_buy_score,
        "次日风险分": next_risk["score"],
        "次日风险原因": next_risk["reasons"],
        "卖出紧迫度": adjusted_sell_urgency,
        "操作建议": advice,
        "止损价": sltp["stop_loss"],
        "止盈价": sltp["take_profit"],
        "盈亏比": sltp["rr_ratio"],
        "风险%": sltp["risk_pct"],
        "评分明细": buy_result["details"],
        "紧迫原因": sell_result["reasons"],
        "RSI6": round(float(latest.get("RSI6", 0) or 0), 1),
        "CCI": round(float(latest.get("CCI", 0) or 0), 1),
        "BIAS5": round(float(latest.get("BIAS5", 0) or 0), 1),
        "WR14": round(float(latest.get("WR14", 0) or 0), 1),
        "ADX": round(float(latest.get("ADX", 0) or 0), 1),
        "BOLL位置": boll_loc,
        "超卖共振": "三指标" if "三指标超卖共振" in buy_result["details"] else (
            "双指标" if "双指标超卖共振" in buy_result["details"] else "无"),
    }


# ═════════════════════════════════════════════════════════════════
# 7. 多线程K线获取
# ═════════════════════════════════════════════════════════════════
def fetch_kline_batch(data_source, code_name_pairs, start_date, end_date, zt_codes, industry_map, zt_pool_df,
                      scanned_cache):
    results = [];
    success_count = 0;
    error_count = 0
    prefetch: dict[str, pd.DataFrame] = {}
    if isinstance(data_source, SmartSourceAdapter) and data_source.em_adapter is not None:
        data_source.em_adapter._ensure_login()
        if getattr(data_source.em_adapter, "_logged_in", False):
            cods = [normalize_stock_code(str(c)) for c, _ in code_name_pairs]
            prefetch = data_source.em_adapter.get_klines_batch(cods, start_date, end_date)
            if prefetch:
                print(f"\n[批量K线] 东财 csd 本批预取成功 {len(prefetch)}/{len(cods)} 只，其余将逐只回退")
    for code, name in code_name_pairs:
        with SCAN_CACHE_LOCK:
            if code in scanned_cache:
                success_count += 1
                continue

        try:
            time.sleep(0.05)
            df = prefetch.get(code) if prefetch else None
            if df is not None and not df.empty:
                _ds_health_inc("kline_em_batch_prefetch_hit")
            if df is None or df.empty:
                df = data_source.get_kline(code, start_date, end_date)
            if df.empty or len(df) < MIN_KDATA_DAYS:
                error_count += 1
                if df.empty: print(f"\r[警告] {code} K线获取为空", end="")
                continue

            if check_consecutive_limit_up(df, code, zt_codes, zt_pool_df):
                continue
            df = calc_all_indicators(df)
            if len(df) < 3:
                error_count += 1
                continue

            row = build_screener_signal_row(
                data_source, code, name, df, zt_codes, zt_pool_df, industry_map,
            )
            if row is None:
                continue

            with SCAN_CACHE_LOCK:
                if code in scanned_cache:
                    continue
                scanned_cache.add(code)
                global _CACHE_FLUSH_COUNTER
                _CACHE_FLUSH_COUNTER += 1
                if _CACHE_FLUSH_COUNTER % CACHE_FLUSH_EVERY_N == 0:
                    try:
                        with open(CACHE_FILE, "w", encoding="utf-8") as f:
                            json.dump(
                                {
                                    "v": 1,
                                    "config_hash": RUN_SCREENER_CONFIG_HASH,
                                    "codes": list(scanned_cache),
                                },
                                f,
                                ensure_ascii=False,
                            )
                    except Exception:
                        pass

            results.append(row)
            success_count += 1

        except Exception:
            error_count += 1
            continue
    return results, success_count, error_count


def enrich_candidates_stock_names(
    candidates: pd.DataFrame,
    trade_date: Optional[str] = None,
    smart: Any = None,
) -> pd.DataFrame:
    """东财 EM 热门股路径常把「名称」留空；优先东财 css 批量简称，其次 AK 现货（带重试）。"""
    if candidates.empty:
        return candidates
    df = candidates.copy()
    if "代码" not in df.columns:
        return df
    if "名称" not in df.columns:
        df["名称"] = ""
    df["代码"] = df["代码"].map(normalize_stock_code)
    nm = df["名称"].fillna("").astype(str).str.strip()
    bad = nm.eq("") | nm.eq(df["代码"].astype(str))
    if not bad.any():
        _ds_health_append_trace("原始名称已完整")
        _ds_health_set("name_enrich_all_named", True)
        return df
    if smart is not None and getattr(smart, "_stock_name_map", None):
        mmap: dict[str, str] = getattr(smart, "_stock_name_map", {}) or {}
        if mmap:
            n0 = int(bad.sum())
            for idx in df.loc[bad].index:
                c6 = normalize_stock_code(str(df.at[idx, "代码"]))
                hit = mmap.get(c6, "").strip()
                if hit:
                    df.at[idx, "名称"] = hit
            nm = df["名称"].fillna("").astype(str).str.strip()
            bad = nm.eq("") | nm.eq(df["代码"].astype(str))
            if int(bad.sum()) < n0:
                _ds_health_append_trace("内存缓存简称")
    if not bad.any():
        _ds_health_set("name_enrich_all_named", True)
        return df
    td_c = _trade_date_compact(trade_date) if trade_date else get_last_trade_date(1)
    if smart is not None and getattr(smart, "em_adapter", None) is not None:
        em = smart.em_adapter
        em._ensure_login()
        if em._logged_in:
            try:
                need_list = df.loc[bad, "代码"].astype(str).map(normalize_stock_code).tolist()
                bd = em.batch_stock_display_fields(need_list, td_c)
                for idx in df.loc[bad].index:
                    c6 = normalize_stock_code(str(df.at[idx, "代码"]))
                    rec = bd.get(c6) or {}
                    if rec.get("名称"):
                        df.at[idx, "名称"] = rec["名称"]
                if smart is not None:
                    setattr(smart, "_last_em_display_fields", bd)
                nm = df["名称"].fillna("").astype(str).str.strip()
                bad = nm.eq("") | nm.eq(df["代码"].astype(str))
                if bd:
                    _ds_health_append_trace("东财css批量简称")
            except Exception as e:
                print(f"\n[候选] 东财 css 名称补全异常（继续尝试 AK）: {e}")
    if not bad.any():
        _ds_health_set("name_enrich_all_named", True)
        return df
    try:
        spot = _akshare_call_with_retries(lambda: ak.stock_zh_a_spot_em(), "AKShare现货")
        if spot is None or spot.empty or "代码" not in spot.columns:
            raise ValueError("现货表为空")
        name_col = "名称" if "名称" in spot.columns else next((c for c in spot.columns if "名称" in str(c)), None)
        if not name_col:
            raise ValueError("无名称列")
        spot = spot.copy()
        spot["代码"] = spot["代码"].map(normalize_stock_code)
        code2name = dict(zip(spot["代码"].astype(str), spot[name_col].astype(str).str.strip()))
        filled = df.loc[bad, "代码"].astype(str).map(code2name)
        df.loc[bad, "名称"] = filled.fillna("").astype(str)
        nm2 = df["名称"].fillna("").astype(str).str.strip()
        still = nm2.eq("") | nm2.eq(df["代码"].astype(str))
        if still.any():
            df.loc[still, "名称"] = "（简称未获取）"
        print(f"\n[候选] 已为 {int(bad.sum())} 只股票尝试补全名称（东财/Ak 现货）")
        _ds_health_append_trace("AK现货简称")
    except Exception as e:
        print(f"\n[候选] 名称补全失败（不影响继续扫描）: {e}")
    nm_f = df["名称"].fillna("").astype(str).str.strip()
    still_f = nm_f.eq("") | nm_f.eq(df["代码"].astype(str))
    _ds_health_set("name_enrich_all_named", bool(not still_f.any()))
    return df


# ═════════════════════════════════════════════════════════════════
# 8. 主筛选逻辑
# ═════════════════════════════════════════════════════════════════
def run_screener(data_source: DataSourceAdapter, target_date: str = None):
    global _CACHE_FLUSH_COUNTER, RUN_SCREENER_CONFIG_HASH, DISPLAY_TOP_N
    _CACHE_FLUSH_COUNTER = 0
    RUN_SCREENER_CONFIG_HASH = _screener_config_hash()
    _ds_health_reset()
    run_started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("=" * 60)
    print(f"  短线选股系统 {VERSION}")
    print(f"  运行开始：{run_started_at} | 目标日期：{target_date or '最新交易日'}")
    print("=" * 60)

    scanned_cache = set()
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                raw = json.load(f)
            if isinstance(raw, list):
                print("\n[缓存] 旧版 scanning_cache 无 config_hash，已忽略（将重新扫描）")
            elif isinstance(raw, dict):
                if raw.get("config_hash") != RUN_SCREENER_CONFIG_HASH:
                    print("\n[缓存] 配置或版本与当前不一致，已忽略旧扫描进度")
                else:
                    scanned_cache = set(str(x) for x in (raw.get("codes") or []))
                    if scanned_cache:
                        print(f"\n[缓存] 发现上次扫描进度（{len(scanned_cache)}只股票），自动续跑...")
        except Exception:
            scanned_cache = set()

    print(f"\n[大盘] 检查大盘环境...")
    market_ok, market_reason = check_market_environment(target_date)
    if not market_ok:
        print(f"[大盘] 环境不佳或数据异常：{market_reason}\n[大盘] 今日不宜开仓，程序终止")
        return pd.DataFrame()
    print(f"[大盘] 环境正常：{market_reason}")

    trade_date = get_last_trade_date(0, target_date) if target_date else get_last_trade_date(1)
    if isinstance(data_source, SmartSourceAdapter):
        data_source.bind_screen_trade_date(trade_date)
    _kline_span = min(HIST_DAYS + 30, MAX_KLINE_TRADE_DAYS)
    start_date = get_last_trade_date(_kline_span, trade_date)
    end_date = trade_date
    print(f"\n[日期] K线日线截止日：{trade_date}（{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:8]}）")
    print(f"[日期] K线请求起点：{start_date}（相对截止日回溯参数={_kline_span} 个交易日，"
          f"min(HIST_DAYS+30={HIST_DAYS + 30}, MAX_KLINE_TRADE_DAYS={MAX_KLINE_TRADE_DAYS})）")

    hot_rel = str(
        os.environ.get("STOCK_HOT_LIST_FILE") or config.get("HOT_LIST_FILE") or DEFAULT_HOT_LIST_RELATIVE
    ).strip()
    hot_path = _resolve_hot_list_path(hot_rel)
    max_n = int(config.get("HOT_LIST_MAX_CODES", 0) or 0)
    print(f"\n[候选] v6.5 从用户名单加载（文件={hot_path}；HOT_LIST_MAX_CODES={max_n or '不限制'}）")
    candidates = load_manual_hot_universe(hot_path, max_codes=max_n if max_n > 0 else 0)
    _ds_health_set("manual_hot_list_path", str(hot_path))
    _ds_health_set("manual_hot_list_count", int(len(candidates)))
    if candidates.empty:
        print("[错误] 热门名单为空或文件不可读"); return pd.DataFrame()
    if int(config.get("DISPLAY_TOP_N", 0) or 0) == 0:
        DISPLAY_TOP_N = min(500, max(1, len(candidates)))
    candidates = enrich_candidates_stock_names(
        candidates,
        trade_date=trade_date,
        smart=data_source if isinstance(data_source, SmartSourceAdapter) else None,
    )

    industry_map = dict(data_source.get_industry_map())
    if isinstance(data_source, SmartSourceAdapter) and data_source.em_adapter is not None:
        try:
            extra_ind = getattr(data_source, "_last_em_display_fields", None)
            if not extra_ind:
                data_source.em_adapter._ensure_login()
                if data_source.em_adapter._logged_in:
                    c_list = [normalize_stock_code(x) for x in candidates["代码"].tolist()]
                    extra_ind = data_source.em_adapter.batch_stock_display_fields(c_list, trade_date)
            if extra_ind:
                for c6, rec in extra_ind.items():
                    hy = (rec.get("行业") or "").strip()
                    if hy:
                        industry_map[c6] = hy
        except Exception as e:
            print(f"[行业] 东财 css 行业补充失败（沿用原 industry_map）: {e}")

    zt_pool_date = get_last_trade_date(1, trade_date)
    print(f"\n[涨停] 获取涨停池：涨停日 zt_pool_date={zt_pool_date}（{_trade_date_yyyy_mm_dd(zt_pool_date)}）；"
          f"东财 sector 参考日仍=K线日线截止 trade_date={trade_date}（{_trade_date_yyyy_mm_dd(trade_date)}）")
    zt_pool = data_source.get_limit_up_pool(zt_pool_date, trade_date=trade_date)

    if FILTER_ST_IN_ZT and not zt_pool.empty and '名称' in zt_pool.columns:
        original_len = len(zt_pool)
        zt_pool = zt_pool[~zt_pool['名称'].str.contains('ST', na=False)]
        print(f"[涨停] 过滤ST股：{original_len} -> {len(zt_pool)}")

    zt_codes: set[str] = (
        {normalize_stock_code(x) for x in zt_pool["代码"].tolist()}
        if not zt_pool.empty and "代码" in zt_pool.columns
        else set()
    )
    print(f"[涨停] 有效涨停股：{len(zt_codes)} 只")
    print(
        "[规则] v6.6.2 扫描候选仅来自用户名单文件（见 HOT_LIST_FILE / STOCK_HOT_LIST_FILE），"
        "不以涨停池合并进扫描名单；涨停池仅用于昨日涨停/连板/封单等评分加权。"
    )

    all_pairs = list(zip(candidates['代码'].tolist(), candidates['名称'].tolist()))
    batches = [all_pairs[i:i + BATCH_SIZE] for i in range(0, len(all_pairs), BATCH_SIZE)]
    all_results = [];
    total = len(all_pairs);
    total_success = 0;
    total_errors = 0
    start_time = time.time()

    print(f"\n[扫描] 多线程筛选（{THREAD_WORKERS}线程）...")
    with ThreadPoolExecutor(max_workers=THREAD_WORKERS) as executor:
        futures = {executor.submit(fetch_kline_batch, data_source, batch, start_date, end_date, zt_codes, industry_map,
                                   zt_pool, scanned_cache): len(batch) for batch in batches}

        completed_count = 0
        for future in as_completed(futures):
            batch_size = futures[future]
            try:
                batch_results, batch_success, batch_errors = future.result()
                all_results.extend(batch_results);
                total_success += batch_success;
                total_errors += batch_errors

                completed_count += batch_size
                elapsed = time.time() - start_time
                speed = completed_count / elapsed if elapsed > 0 else 0
                remain_sec = (total - completed_count) / speed if speed > 0 else 0
                print(f"\r[扫描中] {completed_count}/{total} ({speed:.1f} it/s), 预计剩余 {remain_sec / 60:.1f} min",
                      end="")

                if total_success + total_errors > 50 and total_errors / (
                        total_success + total_errors) > ERROR_THRESHOLD:
                    msg = (
                        f"\n[警告] 数据源失败率 {total_errors / (total_success + total_errors):.0%} "
                        f"高于阈值 {ERROR_THRESHOLD:.0%}（success={total_success}, errors={total_errors}）"
                    )
                    if ERROR_ABORT_ON_HIGH_FAILURE_RATE:
                        print(msg + "，程序终止（ERROR_ABORT_ON_HIGH_FAILURE_RATE=True）")
                        if sys.version_info >= (3, 9):
                            executor.shutdown(wait=False, cancel_futures=True)
                        else:
                            executor.shutdown(wait=False)
                        return pd.DataFrame()
                    print(msg + "，继续扫描（ERROR_ABORT_ON_HIGH_FAILURE_RATE=False）")
            except Exception as e:
                total_errors += batch_size
                completed_count += batch_size

    print("\n")
    if CACHE_FILE.exists(): os.remove(CACHE_FILE)

    if not all_results: print("[结果] 无符合条件的股票"); return pd.DataFrame()

    df_result = pd.DataFrame(all_results).sort_values('买入评分', ascending=False).reset_index(drop=True)
    if "代码" in df_result.columns:
        df_result = df_result.drop_duplicates(subset=["代码"], keep="first").reset_index(drop=True)

    output_dir = Path("选股结果")
    output_dir.mkdir(exist_ok=True)

    run_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_finished_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    run_meta = build_screener_run_meta(trade_date, target_date, run_started_at, run_finished_at)
    run_meta["数据源健康摘要"] = _ds_health_export_summary(
        hot_nonempty=not candidates.empty,
        scan_total=int(total),
        scan_success_rows=int(total_success),
        scan_error_rows=int(total_errors),
    )

    cleanup_old_screener_outputs(output_dir, RESULT_RETENTION_DAYS)

    # 每轮独立子目录：batch_{K线截止日}_{本机运行时间戳}，便于对照多轮 Excel/HTML
    batch_dir = output_dir / f"batch_{trade_date}_{run_stamp}"
    batch_dir.mkdir(parents=True, exist_ok=True)
    run_meta["结果子文件夹"] = batch_dir.name
    run_meta["筛选结果多轮可能不一致的常见原因"] = (
        "① K线截止日 trade_date 或命令行 --target-date 不同则技术面不同；② v6.5 候选完全由名单文件决定，"
        "换文件/改行顺序即换池子；③ 部分股票 K 线拉取失败会被跳过；④ scanning_cache 续跑会跳过已扫代码直至本轮结束删缓存；"
        "⑤ MAX_POOL、MIN_PRICE 等配置变更；⑥ HOT_LIST_FILE 或 STOCK_HOT_LIST_FILE 路径变化。"
    )

    json_path = batch_dir / f"buy_signals_{trade_date}_{run_stamp}.json"
    meta_path = batch_dir / f"run_meta_{trade_date}_{run_stamp}.json"
    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump({"run_meta": run_meta, "signals": df_result.to_dict(orient="records")}, f, ensure_ascii=False, indent=2)
        print(f"[输出] JSON已保存：{json_path}")
    except Exception as e:
        print(f"[输出] JSON 保存失败: {e}")
    try:
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(run_meta, f, ensure_ascii=False, indent=2)
        print(f"[输出] 运行说明 JSON：{meta_path}")
    except Exception as e:
        print(f"[输出] run_meta 保存失败: {e}")

    xlsx_path = batch_dir / f"buy_signals_{trade_date}_{run_stamp}.xlsx"
    save_excel_with_industry_sheets(df_result, xlsx_path, run_meta)
    print(f"[输出] Excel已保存：{xlsx_path.resolve()}")
    if HTML_REPORT_ENABLED:
        generate_html_heatmap(
            df_result,
            batch_dir / f"heatmap_{trade_date}_{run_stamp}.html",
            trade_date,
            run_meta,
            html_table_top_n=HTML_CHART_TOP_N,
        )

    report_path = write_final_report_md(
        batch_dir,
        df_result,
        run_meta,
        trade_date,
        run_stamp,
        scan_total=total,
        display_top_n=DISPLAY_TOP_N,
    )
    html_path = (batch_dir / f"heatmap_{trade_date}_{run_stamp}.html") if HTML_REPORT_ENABLED else None
    write_report_open_hint(output_dir, batch_dir, report_path, xlsx_path, html_path)

    print(f"[输出] 本轮结果目录：{batch_dir.resolve()}")
    print(f"[输出] K线日线截止日 trade_date={trade_date}；运行 {run_started_at} → {run_finished_at}")
    print(f"[输出] {run_meta.get('备注', '')}")
    print(f"[输出] 子目录与旧版平铺文件均按文件名/目录名内时间戳保留约 {RESULT_RETENTION_DAYS} 天，便于对比。")

    print(f"\n{'=' * 70}")
    print(f"[TOP{DISPLAY_TOP_N}] 短线买入信号（评分≥{DISPLAY_TOP_MIN_SCORE:g}分，与操作建议阈值独立）")
    print(f"{'=' * 70}")
    display_df = df_result[df_result['买入评分'] >= DISPLAY_TOP_MIN_SCORE].head(DISPLAY_TOP_N)
    if not display_df.empty:
        for _, row in display_df.iterrows():
            resonance_flag = " [共振]" if row.get('超卖共振', '无') != '无' else ""
            vol_flag = f" [{row.get('量能状态', '')}]" if row.get('量能状态', '') not in ('-', '正常', '') else ""
            risk_flag = f" 风险{row.get('次日风险分', 0)}" if row.get('次日风险分', 0) > 0 else ""
            print(f"  {row['代码']} {row['名称']:<8} [{row.get('所属行业', '')}] "
                  f"评分{row['买入评分']:>5.1f}(原始{row.get('原始买入评分', 0):>4.1f}) | 紧迫{row['卖出紧迫度']:>4.1f} |"
                  f"{risk_flag} |"
                  f"止损{row.get('止损价', '-'):>6} | {row['操作建议']}{resonance_flag}{vol_flag}")
    else:
        print("  无符合条件的买入信号")

    print(f"\n{'=' * 70}")
    print(f"[统计] 摘要")
    print(f"{'=' * 70}")
    print(f"  扫描总数：{total}")
    print(f"  符合条件：{len(df_result)}")
    # v6.7 风控分类统计
    hl = len(df_result[(df_result['买入评分'] >= 8) & (df_result['次日风险分'] <= 3)])
    md = len(df_result[(df_result['买入评分'] >= 6) & (df_result['次日风险分'] <= 4)])
    hr = len(df_result[(df_result['原始买入评分'] >= 6) & (df_result['次日风险分'] > 4)])
    print(f"  高评分低风险(≥8且风险≤3)：{hl}")
    print(f"  中等关注(≥6且风险≤4)：{md}")
    print(f"  高风险强势股(原始≥6但风险>4)：{hr}")

    if '量能状态' in df_result.columns:
        print(f"\n  量能状态分布：")
        for status, cnt in df_result['量能状态'].value_counts().items():
            print(f"    {status}：{cnt}只")

    return df_result


# ═════════════════════════════════════════════════════════════════
# 9. 主程序入口
# ═════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="短线选股 v6.7（风控评分系统+次日风险评估；保留东财K线+修复VOL量比兜底+修复920CSS后缀）")
    parser.add_argument("--no-em", action="store_true", help="禁用东财 EMQuantAPI（仅用 Tushare/AKShare/聚宽）")
    parser.add_argument("--no-jq", action="store_true", help="禁用聚宽 jqdatasdk（即使配置中有账号）")
    parser.add_argument(
        "--hot-list",
        type=str,
        default=None,
        help="v6.6.2：名单文件路径，或「热门股名单」目录（则读目录内 默认热门名单.txt）；覆盖 HOT_LIST_FILE / STOCK_HOT_LIST_FILE",
    )
    parser.add_argument(
        "--top-hot",
        type=int,
        default=None,
        help="v6.5 下忽略（候选以名单为准）；保留仅为与 v6.0 命令行兼容",
    )
    parser.add_argument("--max-pool", type=int, default=None, help="涨停池相关上限 MAX_POOL（覆盖配置）")
    parser.add_argument("--target-date", type=str, default=None, help="基准日 YYYYMMDD（传给 run_screener）")
    parser.add_argument("--config", type=str, default=None, help="配置文件路径（默认 选股配置.json 或环境变量 STOCK_SCREENER_CONFIG）")
    parser.add_argument(
        "--display-top-n",
        type=int,
        default=None,
        help="控制台高分列表最多行数（覆盖 DISPLAY_TOP_N；0 表示配置中的自动规则）",
    )
    args = parser.parse_args()

    if args.config:
        CONFIG_FILE = Path(args.config)
        if CONFIG_FILE.exists():
            try:
                config.clear()
                config.update(DEFAULT_CONFIG.copy())
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    config.update(json.load(f))
                for _k, _v in DEFAULT_CONFIG.items():
                    config.setdefault(_k, _v)
            except Exception as e:
                print(f"[配置] --config 读取失败: {e}")
        else:
            print(f"[配置] 未找到 {CONFIG_FILE}，沿用已加载配置")

    if args.hot_list:
        config["HOT_LIST_FILE"] = str(args.hot_list).strip()
    if args.top_hot is not None:
        print("[提示] v6.6.2 忽略 --top-hot：候选股票以名单文件为准（HOT_LIST_FILE）")
    if args.max_pool is not None:
        config["MAX_POOL"] = int(args.max_pool)
    if args.display_top_n is not None:
        config["DISPLAY_TOP_N"] = int(args.display_top_n)

    hydrate_globals_from_config()

    # ==================== 数据源（优先 选股配置.json，其次环境变量）====================
    em_enabled = bool(config.get("ENABLE_EMQUANTAPI", True))
    if args.no_em:
        em_enabled = False
        config["ENABLE_EMQUANTAPI"] = False

    em_user = str(config.get("EMQUANT_USER") or os.environ.get("EMQUANT_USER", "") or "").strip()
    em_pass = str(config.get("EMQUANT_PASSWORD") or os.environ.get("EMQUANT_PASSWORD", "") or "").strip()
    ts_token = str(config.get("TUSHARE_TOKEN") or os.environ.get("TUSHARE_TOKEN", "") or "").strip()
    jq_user = str(config.get("JQ_USERNAME") or os.environ.get("JQ_USERNAME", "") or "").strip()
    jq_pass = str(config.get("JQ_PASSWORD") or os.environ.get("JQ_PASSWORD", "") or "").strip()

    if not em_enabled:
        em_user, em_pass = "", ""
    if args.no_jq:
        config["ENABLE_JQDATA"] = False
        jq_user, jq_pass = "", ""

    data_source = SmartSourceAdapter(em_user, em_pass, ts_token, jq_user, jq_pass)

    td_arg = args.target_date.replace("-", "") if args.target_date else None
    result_df = run_screener(data_source, target_date=td_arg)