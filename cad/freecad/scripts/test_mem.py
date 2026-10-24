import ctypes
from ctypes import wintypes

class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
    _fields_ = [
        ('cb', wintypes.DWORD),
        ('PageFaultCount', wintypes.DWORD),
        ('PeakWorkingSetSize', ctypes.c_size_t),
        ('WorkingSetSize', ctypes.c_size_t),
        ('QuotaPeakPagedPoolUsage', ctypes.c_size_t),
        ('QuotaPagedPoolUsage', ctypes.c_size_t),
        ('QuotaPeakNonPagedPoolUsage', ctypes.c_size_t),
        ('QuotaNonPagedPoolUsage', ctypes.c_size_t),
        ('PagefileUsage', ctypes.c_size_t),
        ('PeakPagefileUsage', ctypes.c_size_t),
    ]

fn = ctypes.windll.kernel32.K32GetProcessMemoryInfo
fn.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESS_MEMORY_COUNTERS), wintypes.DWORD]
fn.restype = wintypes.BOOL

counters = PROCESS_MEMORY_COUNTERS()
counters.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS)
handle = ctypes.windll.kernel32.GetCurrentProcess()
success = fn(handle, ctypes.byref(counters), counters.cb)
print("Success:", success)
print("WorkingSetSize MB:", counters.WorkingSetSize / (1024*1024))
print("PeakWorkingSetSize MB:", counters.PeakWorkingSetSize / (1024*1024))
