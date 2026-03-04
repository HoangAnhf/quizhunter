import sys
from pathlib import Path

# Đảm bảo thư mục gốc (quizhunter/) nằm trong sys.path
_root = str(Path(__file__).parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)
