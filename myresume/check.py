import os
import platform
import psutil

print("CPU Information:")
print(f"Processor: {platform.processor()}")
print(f"Architecture: {platform.machine()}")
print(f"CPU Cores: {os.cpu_count()}")
print(f"CPU Frequency: {psutil.cpu_freq().current} MHz")