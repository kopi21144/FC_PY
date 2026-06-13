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


def rand_bytes32() -> str:
    return "0x" + secrets.token_hex(32)


ADDR = [rand_addr() for _ in range(3)]
HEX32 = [rand_bytes32() for _ in range(8)]

TIER_CAP = secrets.randbelow(5) + 4  # 4–8
MAX_TICKETS = secrets.randbelow(91) + 134  # 134–224
MAX_OPEN_CASCADES = secrets.randbelow(35) + 47  # 47–81
TICKET_FEE = f"0.00{secrets.randbelow(4) + 2} ether"
FLUSHER_BOND = f"0.0{secrets.randbelow(5) + 4} ether"
FLUSH_FLOOR = secrets.randbelow(210) + 390
FLUSH_CEIL = secrets.randbelow(1300) + 7600
CYCLE_BLOCK_SPAN = secrets.randbelow(280) + 310
WEIGHT_CAP = secrets.randbelow(5200) + 12800
RATING_FLOOR = secrets.randbelow(110) + 240
RATING_CEIL = secrets.randbelow(920) + 7400


def w(lines: list[str], s: str = "") -> None:
    lines.append(s)


def emit_header(la: list[str]) -> None:
    w(la, "// SPDX-License-Identifier: MIT")
    w(la, "pragma solidity 0.8.28;")
    w(la, "")
    w(la, "/// @title FlushClawAI — hydraulic ticket cascade for claw-routed mixer lanes.")
    w(la, "/// @dev codename: teal siphon / gasket line nine")


def emit_libraries(la: list[str]) -> None:
    w(la, "")
    w(la, "library FcaGauge {")
    w(la, "    error FCA_GaugeOverflow();")
    w(la, "    uint256 internal constant BPS = 10_000;")
    w(la, "    function clampU24(uint256 v, uint24 lo, uint24 hi) internal pure returns (uint24) {")
    w(la, "        if (v < lo) return lo;")
    w(la, "        if (v > hi) return hi;")
    w(la, "        return uint24(v);")
    w(la, "    }")
    w(la, "    function takeBps(uint256 gross, uint256 bps) internal pure returns (uint256) {")
    w(la, "        unchecked { return (gross * bps) / BPS; }")
    w(la, "    }")
    w(la, "    function safeAdd(uint256 a, uint256 b, uint256 cap) internal pure returns (uint256) {")
    w(la, "        unchecked {")
    w(la, "            uint256 s = a + b;")
    w(la, "            if (s < a || s > cap) revert FCA_GaugeOverflow();")
    w(la, "            return s;")
    w(la, "        }")
    w(la, "    }")
