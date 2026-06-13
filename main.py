"""One-shot generator for contracts/FlushClawAI.sol — claw-flush lane mixer ledger."""
from __future__ import annotations

import secrets
from pathlib import Path

try:
    from eth_utils import to_checksum_address as _cs
except ImportError:  # pragma: no cover
    import hashlib

    def _keccak(data: bytes) -> bytes:
        k = hashlib.new("sha3_256")
        k.update(data)
        return k.digest()

    def _cs(addr_hex: str) -> str:
        addr = addr_hex.lower().replace("0x", "")
        digest = _keccak(addr.encode("ascii"))
        out = ["0x"]
        for i, ch in enumerate(addr):
            if ch in "0123456789":
                out.append(ch)
                continue
            nibble = digest[i // 2]
            nibble = (nibble >> 4) if i % 2 == 0 else (nibble & 0x0F)
            out.append(ch.upper() if nibble >= 8 else ch.lower())
        return "".join(out)


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "contracts" / "FlushClawAI.sol"

TARGET_LO = 500
TARGET_HI = 5000
TARGET_LINES = secrets.randbelow(TARGET_HI - TARGET_LO + 1) + TARGET_LO

LANE_COUNT = secrets.randbelow(11) + 21  # 21–31
CYCLE_SLOTS = secrets.randbelow(18) + 32  # 32–49
TICKET_VIEWS = secrets.randbelow(42) + 48  # 48–89
LANE_VIEWS = secrets.randbelow(16) + 26  # 26–41
CASCADE_VIEWS = secrets.randbelow(14) + 19  # 19–32
BURST_VIEWS = secrets.randbelow(12) + 15  # 15–26
FLUSHER_PINGS = secrets.randbelow(9) + 13  # 13–21
CASCADE_BATCHES = secrets.randbelow(11) + 12  # 12–22
LINE_FAULTS = secrets.randbelow(16) + 36  # 36–51


def rand_addr() -> str:
    return _cs("0x" + secrets.token_hex(20))


