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
    w(la, "}")
    w(la, "")


def emit_contract_start(la: list[str]) -> None:
    w(la, "contract FlushClawAI {")
    base_errs = [
        "FCA_NotPitMaster",
        "FCA_NotFlusher",
        "FCA_Halted",
        "FCA_ZeroAddr",
        "FCA_ZeroWei",
        "FCA_Reentered",
        "FCA_LaneDead",
        "FCA_LaneDrained",
        "FCA_TicketTaken",
        "FCA_TicketGone",
        "FCA_TierOff",
        "FCA_CapHit",
        "FCA_CycleOff",
        "FCA_CascadeLive",
        "FCA_CascadeGone",
        "FCA_CascadeDone",
        "FCA_FlusherOld",
        "FCA_RatingLow",
        "FCA_RatingHigh",
        "FCA_SelfRoute",
        "FCA_HashEmpty",
        "FCA_VoteSpent",
        "FCA_VoteSelf",
        "FCA_BondThin",
        "FCA_SendFail",
        "FCA_ArrayWide",
        "FCA_SizeMismatch",
        "FCA_NotRunner",
        "FCA_RunnerKnown",
        "FCA_FallbackBlocked",
        "FCA_PitLocked",
    ]
    for e in base_errs:
        w(la, f"    error {e}();")
    for i in range(len(base_errs), LINE_FAULTS):
        w(la, f"    error FCA_Fault_{i}();")
    w(la, "")
    w(la, "    event Posted(bytes32 indexed ticketId, uint256 indexed laneId, address indexed runner, uint8 tier, uint256 weiLocked);")
    w(la, "    event Voted(bytes32 indexed ticketId, address indexed voter, bool up, uint256 cycleId);")
    w(la, "    event Locked(bytes32 indexed ticketId, address indexed from, uint256 weiAmt, uint256 cycleId);")
    w(la, "    event Queued(bytes32 indexed cascadeId, uint256 indexed laneId, bytes32 flushTag, uint256 queuedAt);")
    w(la, "    event Flushed(bytes32 indexed cascadeId, bytes32 outcomeHash, uint16 flushRating, uint256 cycleId);")
    w(la, "    event Burst(bytes32 indexed burstId, uint256 indexed laneId, uint16 pressureBand, uint256 at);")
    w(la, "    event Opened(uint256 indexed laneId, bytes32 laneSalt, uint8 tier, uint256 seedWeight);")
    w(la, "    event Turned(uint256 indexed cycleId, uint64 wallAt, uint256 ticketMass, uint256 cascadeMass);")
    w(la, "    event Halted(bool halted, address indexed by, uint256 atBlock);")
    w(la, "    event FlusherSet(address indexed flusher, uint256 atBlock);")
    w(la, "    event NativeReceived(address indexed from, uint256 weiAmt, uint256 atBlock);")
    w(la, "    event RunnerJoined(address indexed runner, bytes32 tag, uint256 bondWei);")
    w(la, "    event RunnerLeft(address indexed runner, uint256 atBlock);")
    for i in range(14):
        w(la, f"    event Ripple_{i}(uint256 indexed slot, address indexed actor, uint256 meta, uint256 cycleId);")
    w(la, "")


def emit_types_and_state(la: list[str]) -> None:
    w(la, "    enum FcaLaneStatus { Empty, Running, Drained }")
    w(la, "    enum FcaCascadeStage { Waiting, Active, Finalized, Scraped }")
    w(la, "")
    w(la, "    struct FcaLane {")
    w(la, "        FcaLaneStatus status;")
    w(la, "        uint8 flushTier;")
    w(la, "        uint64 startedAt;")
    w(la, "        uint32 ticketCount;")
    w(la, "        uint32 cascadeCount;")
    w(la, "        uint256 massSum;")
    w(la, "        bytes32 laneSalt;")
    w(la, "    }")
    w(la, "")
    w(la, "    struct FcaTicket {")
    w(la, "        uint256 laneId;")
    w(la, "        address runner;")
    w(la, "        bytes32 clawSeal;")
    w(la, "        uint8 flushTier;")
    w(la, "        uint32 upVotes;")
    w(la, "        uint32 downVotes;")
    w(la, "        uint256 lockedWei;")
    w(la, "        uint64 postedAt;")
    w(la, "        bool open;")
    w(la, "    }")
    w(la, "")
    w(la, "    struct FcaCascade {")
    w(la, "        uint256 laneId;")
    w(la, "        address proposer;")
    w(la, "        bytes32 flushTag;")
    w(la, "        FcaCascadeStage stage;")
    w(la, "        bytes32 outcomeHash;")
    w(la, "        uint16 flushRating;")
    w(la, "        uint64 queuedAt;")
    w(la, "    }")
    w(la, "")
    w(la, "    struct FcaBurst {")
    w(la, "        uint256 laneId;")
    w(la, "        bytes32 burstTag;")
    w(la, "        bytes32 ductHash;")
    w(la, "        uint16 pressureBand;")
    w(la, "        uint64 stampedAt;")
    w(la, "    }")
    w(la, "")
    w(la, "    struct FcaCycleRing {")
    w(la, "        uint64 openedAt;")
    w(la, "        uint256 ticketMass;")
    w(la, "        uint256 cascadeMass;")
    w(la, "        bytes32 ringDigest;")
    w(la, "    }")
    w(la, "")
    w(la, "    struct FcaRunnerBench {")
    w(la, "        bool active;")
    w(la, "        bytes32 tag;")
    w(la, "        uint64 joinedAt;")
    w(la, "        uint32 ticketCount;")
    w(la, "    }")
    w(la, "")
    w(la, f"    uint256 public constant FCA_TIER_CAP = {TIER_CAP};")
    w(la, f"    uint256 public constant FCA_TICKET_FEE = {TICKET_FEE};")
    w(la, f"    uint256 public constant FCA_FLUSHER_BOND = {FLUSHER_BOND};")
    w(la, f"    uint256 public constant FCA_MAX_TICKETS = {MAX_TICKETS};")
    w(la, f"    uint256 public constant FCA_OPEN_CASCADE_CAP = {MAX_OPEN_CASCADES};")
    w(la, f"    uint256 public constant FCA_FLUSH_FLOOR = {FLUSH_FLOOR};")
    w(la, f"    uint256 public constant FCA_FLUSH_CEIL = {FLUSH_CEIL};")
    w(la, f"    uint256 public constant FCA_CYCLE_BLOCKS = {CYCLE_BLOCK_SPAN};")
    w(la, f"    uint256 public constant FCA_MASS_CAP = {WEIGHT_CAP};")
    w(la, f"    uint256 public constant FCA_RATING_FLOOR = {RATING_FLOOR};")
    w(la, f"    uint256 public constant FCA_RATING_CEIL = {RATING_CEIL};")
    w(la, f"    uint256 public constant FCA_LANE_COUNT = {LANE_COUNT};")
    w(la, "")
    for i, h in enumerate(HEX32):
        w(la, f"    bytes32 private constant _SALT_{i} = {h};")
    w(la, '    bytes32 private constant FCA_DOMAIN = keccak256("FlushClawAI.hydraulicLane");')
    w(la, "")
    w(la, "    address public immutable pitMaster;")
    w(la, "    address public immutable ADDRESS_A;")
    w(la, "    address public immutable ADDRESS_B;")
    w(la, "    address public immutable ADDRESS_C;")
    w(la, "")
    w(la, "    address public flusher;")
    w(la, "    bool public halted;")
    w(la, "    uint256 public activeCycle;")
    w(la, "    uint256 public rippleSerial;")
    w(la, "    uint256 public openCascades;")
    w(la, "    uint256 public escrowWei;")
    w(la, "    uint256 public bornBlock;")
    w(la, "    uint256 public laneSerial;")
    w(la, "")
    w(la, "    mapping(uint256 => FcaLane) public lanes;")
    w(la, "    mapping(bytes32 => FcaTicket) public tickets;")
    w(la, "    mapping(bytes32 => FcaCascade) public cascades;")
    w(la, "    mapping(bytes32 => FcaBurst) public bursts;")
    w(la, "    mapping(uint256 => FcaCycleRing) public cycleRings;")
    w(la, "    mapping(uint256 => mapping(address => uint256)) public runnerMass;")
    w(la, "    mapping(bytes32 => mapping(address => bool)) public voteCast;")
    w(la, "    mapping(bytes32 => bool) public ticketIdUsed;")
    w(la, "    mapping(bytes32 => bool) public cascadeIdUsed;")
    w(la, "    mapping(bytes32 => bool) public burstIdUsed;")
    w(la, "    mapping(address => FcaRunnerBench) public runnerBenches;")
    w(la, "    mapping(address => bytes32[]) private _ticketsByRunner;")
    w(la, "    bytes32[] private _ticketRoll;")
    w(la, "    uint256 private _guard;")
    w(la, "")


def emit_modifiers(la: list[str]) -> None:
    w(la, "    modifier nonReentrant() {")
    w(la, "        if (_guard == 2) revert FCA_Reentered();")
    w(la, "        _guard = 2;")
    w(la, "        _;")
    w(la, "        _guard = 1;")
    w(la, "    }")
    w(la, "")
    w(la, "    modifier onlyPitMaster() {")
    w(la, "        if (msg.sender != pitMaster) revert FCA_NotPitMaster();")
    w(la, "        _;")
    w(la, "    }")
    w(la, "")
    w(la, "    modifier onlyFlusher() {")
    w(la, "        if (msg.sender != flusher) revert FCA_NotFlusher();")
    w(la, "        _;")
    w(la, "    }")
    w(la, "")
    w(la, "    modifier whenRunning() {")
    w(la, "        if (halted) revert FCA_Halted();")
    w(la, "        _;")
    w(la, "    }")
    w(la, "")
    w(la, "    modifier onlyActiveRunner() {")
    w(la, "        if (!runnerBenches[msg.sender].active) revert FCA_NotRunner();")
    w(la, "        _;")
    w(la, "    }")
    w(la, "")


def emit_constructor(la: list[str]) -> None:
    w(la, "    constructor() {")
    w(la, "        pitMaster = msg.sender;")
    w(la, f"        ADDRESS_A = {ADDR[0]};")
    w(la, f"        ADDRESS_B = {ADDR[1]};")
    w(la, f"        ADDRESS_C = {ADDR[2]};")
    w(la, "        flusher = ADDRESS_A;")
    w(la, "        _guard = 1;")
    w(la, "        bornBlock = block.number;")
    w(la, "        activeCycle = 1;")
    w(la, "        laneSerial = FCA_LANE_COUNT;")
    w(la, "        _beginCycle(1);")
    w(la, "        _bootLanes();")
    w(la, "    }")
    w(la, "")


def emit_receive(la: list[str]) -> None:
    w(la, "    receive() external payable {")
    w(la, "        emit NativeReceived(msg.sender, msg.value, block.number);")
    w(la, "        emit Ripple_0(rippleSerial, msg.sender, msg.value, activeCycle);")
    w(la, "        unchecked { rippleSerial += 1; }")
    w(la, "    }")
    w(la, "")
    w(la, "    fallback() external payable {")
    w(la, "        revert FCA_FallbackBlocked();")
    w(la, "    }")
    w(la, "")


def emit_admin(la: list[str]) -> None:
    w(la, "    function setFlusher(address next_) external onlyPitMaster {")
    w(la, "        if (next_ == address(0)) revert FCA_ZeroAddr();")
    w(la, "        flusher = next_;")
    w(la, "        emit FlusherSet(next_, block.number);")
    w(la, "    }")
    w(la, "")
    w(la, "    function setHalted(bool on) external onlyPitMaster {")
    w(la, "        halted = on;")
    w(la, "        emit Halted(on, msg.sender, block.number);")
    w(la, "    }")
    w(la, "")
    w(la, "    function turnCycle() external onlyPitMaster whenRunning {")
    w(la, "        uint256 n = activeCycle + 1;")
    w(la, f"        if (n > {CYCLE_SLOTS}) revert FCA_CycleOff();")
    w(la, "        activeCycle = n;")
    w(la, "        _beginCycle(n);")
    w(la, "        emit Turned(n, uint64(block.timestamp), _cycleTicketMass(), openCascades);")
    w(la, "    }")
    w(la, "")
    w(la, "    function drainLane(uint256 laneId) external onlyFlusher {")
    w(la, "        FcaLane storage ln = lanes[laneId];")
    w(la, "        if (ln.status == FcaLaneStatus.Empty) revert FCA_LaneDead();")
    w(la, "        ln.status = FcaLaneStatus.Drained;")
    w(la, "    }")
    w(la, "")
    w(la, "    function enrollRunner(address runner, bytes32 tag) external onlyPitMaster {")
    w(la, "        if (runner == address(0)) revert FCA_ZeroAddr();")
    w(la, "        if (runnerBenches[runner].active) revert FCA_RunnerKnown();")
    w(la, "        runnerBenches[runner] = FcaRunnerBench({")
    w(la, "            active: true,")
    w(la, "            tag: tag,")
    w(la, "            joinedAt: uint64(block.timestamp),")
    w(la, "            ticketCount: 0")
    w(la, "        });")
    w(la, "        emit RunnerJoined(runner, tag, 0);")
    w(la, "    }")
    w(la, "")
    w(la, "    function dropRunner(address runner) external onlyPitMaster {")
    w(la, "        if (!runnerBenches[runner].active) revert FCA_NotRunner();")
    w(la, "        runnerBenches[runner].active = false;")
    w(la, "        emit RunnerLeft(runner, block.number);")
    w(la, "    }")
    w(la, "")
    w(la, "    function skimExcess(uint256 amt, address payable to) external onlyPitMaster nonReentrant {")
    w(la, "        if (to == address(0)) revert FCA_ZeroAddr();")
    w(la, "        if (amt == 0 || amt > address(this).balance) revert FCA_ZeroWei();")
    w(la, "        if (amt > address(this).balance - escrowWei) revert FCA_CapHit();")
    w(la, "        _pushNative(to, amt);")
    w(la, "    }")
    w(la, "")


def emit_user_ops(la: list[str]) -> None:
    w(la, "    function postTicket(")
    w(la, "        bytes32 ticketId,")
    w(la, "        uint256 laneId,")
    w(la, "        bytes32 clawSeal,")
    w(la, "        uint8 flushTier")
    w(la, "    ) external payable nonReentrant whenRunning onlyActiveRunner {")
    w(la, "        if (ticketId == bytes32(0)) revert FCA_HashEmpty();")
    w(la, "        if (ticketIdUsed[ticketId]) revert FCA_TicketTaken();")
    w(la, "        if (msg.value < FCA_TICKET_FEE) revert FCA_BondThin();")
    w(la, "        if (flushTier == 0 || flushTier > FCA_TIER_CAP) revert FCA_TierOff();")
    w(la, "        FcaLane storage ln = lanes[laneId];")
    w(la, "        if (ln.status != FcaLaneStatus.Running) revert FCA_LaneDrained();")
    w(la, "        if (ln.ticketCount >= FCA_MAX_TICKETS) revert FCA_CapHit();")
    w(la, "        ticketIdUsed[ticketId] = true;")
    w(la, "        tickets[ticketId] = FcaTicket({")
    w(la, "            laneId: laneId,")
    w(la, "            runner: msg.sender,")
    w(la, "            clawSeal: clawSeal,")
    w(la, "            flushTier: flushTier,")
    w(la, "            upVotes: 0,")
    w(la, "            downVotes: 0,")
    w(la, "            lockedWei: msg.value,")
    w(la, "            postedAt: uint64(block.timestamp),")
    w(la, "            open: true")
    w(la, "        });")
    w(la, "        unchecked {")
    w(la, "            ln.ticketCount += 1;")
    w(la, "            ln.massSum = FcaGauge.safeAdd(")
    w(la, "                ln.massSum, uint256(flushTier) * 89, FCA_MASS_CAP")
    w(la, "            );")
    w(la, "            runnerBenches[msg.sender].ticketCount += 1;")
    w(la, "        }")
    w(la, "        runnerMass[activeCycle][msg.sender] += uint256(flushTier) * 17;")
    w(la, "        escrowWei += msg.value;")
    w(la, "        _ticketsByRunner[msg.sender].push(ticketId);")
    w(la, "        _ticketRoll.push(ticketId);")
    w(la, "        emit Posted(ticketId, laneId, msg.sender, flushTier, msg.value);")
    w(la, "    }")
    w(la, "")
    w(la, "    function voteTicket(bytes32 ticketId, bool up) external whenRunning {")
    w(la, "        FcaTicket storage t = tickets[ticketId];")
    w(la, "        if (!t.open) revert FCA_TicketGone();")
    w(la, "        if (t.runner == msg.sender) revert FCA_VoteSelf();")
    w(la, "        if (voteCast[ticketId][msg.sender]) revert FCA_VoteSpent();")
    w(la, "        voteCast[ticketId][msg.sender] = true;")
    w(la, "        if (up) unchecked { t.upVotes += 1; }")
    w(la, "        else unchecked { t.downVotes += 1; }")
    w(la, "        emit Voted(ticketId, msg.sender, up, activeCycle);")
    w(la, "    }")
    w(la, "")
    w(la, "    function lockTicket(bytes32 ticketId) external payable nonReentrant whenRunning {")
    w(la, "        if (msg.value == 0) revert FCA_ZeroWei();")
    w(la, "        FcaTicket storage t = tickets[ticketId];")
    w(la, "        if (!t.open) revert FCA_TicketGone();")
    w(la, "        t.lockedWei += msg.value;")
    w(la, "        escrowWei += msg.value;")
    w(la, "        emit Locked(ticketId, msg.sender, msg.value, activeCycle);")
    w(la, "    }")
    w(la, "")
    w(la, "    function joinRunner(bytes32 tag) external payable nonReentrant whenRunning {")
    w(la, "        if (msg.value < FCA_FLUSHER_BOND) revert FCA_BondThin();")
    w(la, "        if (runnerBenches[msg.sender].active) revert FCA_RunnerKnown();")
    w(la, "        runnerBenches[msg.sender] = FcaRunnerBench({")
    w(la, "            active: true,")
    w(la, "            tag: tag,")
    w(la, "            joinedAt: uint64(block.timestamp),")
    w(la, "            ticketCount: 0")
    w(la, "        });")
    w(la, "        escrowWei += msg.value;")
    w(la, "        emit RunnerJoined(msg.sender, tag, msg.value);")
    w(la, "    }")
    w(la, "")
    w(la, "    function queueCascade(bytes32 cascadeId, uint256 laneId, bytes32 flushTag)")
    w(la, "        external")
    w(la, "        payable")
    w(la, "        nonReentrant")
    w(la, "        whenRunning")
    w(la, "        onlyActiveRunner")
    w(la, "    {")
    w(la, "        if (cascadeId == bytes32(0)) revert FCA_HashEmpty();")
    w(la, "        if (cascadeIdUsed[cascadeId]) revert FCA_CascadeLive();")
    w(la, "        if (msg.value < FCA_TICKET_FEE) revert FCA_BondThin();")
