# src/utils/memlog.py
import os, resource, tracemalloc, time
_TRACEMALLOC = False

def mem_mb():
    # macOS: ru_maxrss en bytes ; Linux: en KB. On normalise.
    usage_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if os.uname().sysname == "Darwin":
        return usage_kb / (1024*1024)
    return usage_kb / 1024

def start_trace():
    global _TRACEMALLOC
    if not _TRACEMALLOC:
        tracemalloc.start()
        _TRACEMALLOC = True

def log_mem(tag: str):
    m = mem_mb()
    current = peak = None
    if _TRACEMALLOC:
        current, peak = tracemalloc.get_traced_memory()
    now = time.strftime('%H:%M:%S')
    extra = f" tracemalloc_cur_mb={current/1e6:.1f} peak_mb={peak/1e6:.1f}" if current is not None else ""
    print(f"[MEM] {now} {tag} rss_mb={m:.1f}{extra}")
