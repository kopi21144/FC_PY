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
    w(la, "        if (openCascades >= FCA_OPEN_CASCADE_CAP) revert FCA_CapHit();")
    w(la, "        FcaLane storage ln = lanes[laneId];")
    w(la, "        if (ln.status != FcaLaneStatus.Running) revert FCA_LaneDrained();")
    w(la, "        cascadeIdUsed[cascadeId] = true;")
    w(la, "        cascades[cascadeId] = FcaCascade({")
    w(la, "            laneId: laneId,")
    w(la, "            proposer: msg.sender,")
    w(la, "            flushTag: flushTag,")
    w(la, "            stage: FcaCascadeStage.Waiting,")
    w(la, "            outcomeHash: bytes32(0),")
    w(la, "            flushRating: 0,")
    w(la, "            queuedAt: uint64(block.timestamp)")
    w(la, "        });")
    w(la, "        unchecked {")
    w(la, "            openCascades += 1;")
    w(la, "            ln.cascadeCount += 1;")
    w(la, "        }")
    w(la, "        escrowWei += msg.value;")
    w(la, "        emit Queued(cascadeId, laneId, flushTag, block.timestamp);")
    w(la, "    }")
    w(la, "")
    w(la, "    function flushCascade(bytes32 cascadeId, bytes32 outcomeHash, uint16 flushRating) external onlyFlusher {")
    w(la, "        FcaCascade storage c = cascades[cascadeId];")
    w(la, "        if (c.stage != FcaCascadeStage.Waiting && c.stage != FcaCascadeStage.Active) revert FCA_CascadeDone();")
    w(la, "        if (flushRating < FCA_RATING_FLOOR) revert FCA_RatingLow();")
    w(la, "        if (flushRating > FCA_RATING_CEIL) revert FCA_RatingHigh();")
    w(la, "        c.stage = FcaCascadeStage.Finalized;")
    w(la, "        c.outcomeHash = outcomeHash;")
    w(la, "        c.flushRating = flushRating;")
    w(la, "        if (openCascades > 0) unchecked { openCascades -= 1; }")
    w(la, "        emit Flushed(cascadeId, outcomeHash, flushRating, activeCycle);")
    w(la, "    }")
    w(la, "")
    w(la, "    function emitBurst(")
    w(la, "        bytes32 burstId,")
    w(la, "        uint256 laneId,")
    w(la, "        bytes32 burstTag,")
    w(la, "        bytes32 ductHash,")
    w(la, "        uint16 pressureBand")
    w(la, "    ) external onlyFlusher whenRunning {")
    w(la, "        if (burstIdUsed[burstId]) revert FCA_FlusherOld();")
    w(la, "        if (pressureBand < FCA_FLUSH_FLOOR) revert FCA_RatingLow();")
    w(la, "        if (pressureBand > FCA_FLUSH_CEIL) revert FCA_RatingHigh();")
    w(la, "        FcaLane storage ln = lanes[laneId];")
    w(la, "        if (ln.status != FcaLaneStatus.Running) revert FCA_LaneDrained();")
    w(la, "        burstIdUsed[burstId] = true;")
    w(la, "        bursts[burstId] = FcaBurst({")
    w(la, "            laneId: laneId,")
    w(la, "            burstTag: burstTag,")
    w(la, "            ductHash: ductHash,")
    w(la, "            pressureBand: pressureBand,")
    w(la, "            stampedAt: uint64(block.timestamp)")
    w(la, "        });")
    w(la, "        emit Burst(burstId, laneId, pressureBand, block.timestamp);")
    w(la, "    }")
    w(la, "")
    w(la, "    function fundLane() external payable whenRunning {")
    w(la, "        if (msg.value == 0) revert FCA_ZeroWei();")
    w(la, "        emit NativeReceived(msg.sender, msg.value, block.number);")
    w(la, "        emit Ripple_1(rippleSerial, msg.sender, msg.value, activeCycle);")
    w(la, "        unchecked { rippleSerial += 1; }")
    w(la, "    }")
    w(la, "")
    w(la, "    function redeemTicket(bytes32 ticketId, address payable to) external nonReentrant whenRunning {")
    w(la, "        FcaTicket storage t = tickets[ticketId];")
    w(la, "        if (!t.open) revert FCA_TicketGone();")
    w(la, "        if (t.runner != msg.sender) revert FCA_SelfRoute();")
    w(la, "        if (to == address(0)) revert FCA_ZeroAddr();")
    w(la, "        uint256 amt = t.lockedWei;")
    w(la, "        if (amt == 0) revert FCA_ZeroWei();")
    w(la, "        t.open = false;")
    w(la, "        t.lockedWei = 0;")
    w(la, "        escrowWei -= amt;")
    w(la, "        _pushNative(to, amt);")
    w(la, "    }")
    w(la, "")


def emit_internal(la: list[str]) -> None:
    w(la, "    function _pushNative(address to, uint256 amt) internal {")
    w(la, '        (bool ok, ) = payable(to).call{value: amt}("");')
    w(la, "        if (!ok) revert FCA_SendFail();")
    w(la, "    }")
    w(la, "")
    w(la, "    function _beginCycle(uint256 cycleId) internal {")
    w(la, "        FcaCycleRing storage ring = cycleRings[cycleId];")
    w(la, "        ring.openedAt = uint64(block.timestamp);")
    w(la, "        ring.ticketMass = _cycleTicketMass();")
    w(la, "        ring.cascadeMass = openCascades;")
    w(la, "        ring.ringDigest = _ringDigest(cycleId, ring.ticketMass, ring.cascadeMass);")
    w(la, "    }")
    w(la, "")
    w(la, "    function _ringDigest(uint256 cycleId, uint256 tm, uint256 cm) internal view returns (bytes32) {")
    w(la, "        return keccak256(abi.encode(")
    w(la, "            FCA_DOMAIN,")
    w(la, "            cycleId,")
    w(la, "            tm,")
    w(la, "            cm,")
    w(la, "            ADDRESS_A,")
    w(la, "            ADDRESS_B,")
    w(la, "            ADDRESS_C,")
    w(la, "            _SALT_0,")
    w(la, "            FCA_CYCLE_BLOCKS,")
    w(la, "            bornBlock")
    w(la, "        ));")
    w(la, "    }")
    w(la, "")
    w(la, "    function ticketDigest(bytes32 ticketId) public view returns (bytes32) {")
    w(la, "        FcaTicket storage t = tickets[ticketId];")
    w(la, "        return keccak256(abi.encode(")
    w(la, "            ticketId,")
    w(la, "            t.laneId,")
    w(la, "            t.runner,")
    w(la, "            t.lockedWei,")
    w(la, "            t.clawSeal,")
    w(la, "            _SALT_1,")
    w(la, "            activeCycle")
    w(la, "        ));")
    w(la, "    }")
    w(la, "")
    w(la, "    function _cycleTicketMass() internal view returns (uint256 mass) {")
    w(la, "        for (uint256 i = 1; i <= FCA_LANE_COUNT; ++i) {")
    w(la, "            mass += lanes[i].massSum;")
    w(la, "        }")
    w(la, "    }")
    w(la, "")


def emit_boot_lanes(la: list[str]) -> None:
    w(la, "    function _bootLanes() internal {")
    tiers = [4, 6, 5, 7, 3, 8, 5, 6]
    for lid in range(1, LANE_COUNT + 1):
        tier = tiers[(lid - 1) % len(tiers)]
        salt = HEX32[lid % len(HEX32)]
        w(la, f"        lanes[{lid}] = FcaLane({{")
        w(la, "            status: FcaLaneStatus.Running,")
        w(la, f"            flushTier: uint8({tier}),")
        w(la, "            startedAt: uint64(block.timestamp),")
        w(la, "            ticketCount: 0,")
        w(la, "            cascadeCount: 0,")
        w(la, f"            massSum: {lid * 41 + 23},")
        w(la, f"            laneSalt: {salt}")
        w(la, "        });")
        w(la, f"        emit Opened({lid}, {salt}, uint8({tier}), {lid * 41 + 23});")
    w(la, "    }")
    w(la, "")


def emit_views(la: list[str]) -> None:
    w(la, "    // lane readers")
    for n in range(TICKET_VIEWS):
        w(la, f"    function readTicket_{n}(bytes32 ticketId) external view returns (")
        w(la, "        uint256 laneId,")
        w(la, "        address runner,")
        w(la, "        uint8 tier,")
        w(la, "        uint256 locked,")
        w(la, "        bytes32 digest")
        w(la, "    ) {")
        w(la, "        FcaTicket storage t = tickets[ticketId];")
        w(la, "        laneId = t.laneId;")
        w(la, "        runner = t.runner;")
        w(la, "        tier = t.flushTier;")
        w(la, "        locked = t.lockedWei;")
        w(la, f"        digest = keccak256(abi.encode(ticketId, locked, _SALT_{n % len(HEX32)}));")
        w(la, "    }")
        w(la, "")
    for n in range(LANE_VIEWS):
        w(la, f"    function readLane_{n}(uint256 laneId) external view returns (")
        w(la, "        uint32 tickets,")
        w(la, "        uint32 cascades,")
        w(la, "        uint256 mass,")
        w(la, "        uint8 tier,")
        w(la, "        bytes32 salt")
        w(la, "    ) {")
        w(la, "        FcaLane storage ln = lanes[laneId];")
        w(la, "        tickets = ln.ticketCount;")
        w(la, "        cascades = ln.cascadeCount;")
        w(la, "        mass = ln.massSum;")
        w(la, "        tier = ln.flushTier;")
        w(la, "        salt = ln.laneSalt;")
        w(la, f"        mass = mass ^ (uint256(_SALT_{n % len(HEX32)}) & 0);")
        w(la, "    }")
        w(la, "")
    w(la, "    function cycleRing(uint256 cycleId) external view returns (bytes32 digest, uint256 tm, uint256 cm) {")
    w(la, f"        if (cycleId == 0 || cycleId > {CYCLE_SLOTS}) revert FCA_CycleOff();")
    w(la, "        FcaCycleRing storage ring = cycleRings[cycleId];")
    w(la, "        return (ring.ringDigest, ring.ticketMass, ring.cascadeMass);")
    w(la, "    }")
    w(la, "")
    w(la, "    function anchorCheck(uint8 slot, address candidate) external view returns (bool) {")
    w(la, "        if (slot == 0) return candidate == ADDRESS_A;")
    w(la, "        if (slot == 1) return candidate == ADDRESS_B;")
    w(la, "        if (slot == 2) return candidate == ADDRESS_C;")
    w(la, "        revert FCA_CycleOff();")
    w(la, "    }")
    w(la, "")
    w(la, "    function nativePool() external view returns (uint256) {")
    w(la, "        return address(this).balance;")
    w(la, "    }")
    w(la, "")
    w(la, "    function escrowPool() external view returns (uint256) {")
    w(la, "        return escrowWei;")
    w(la, "    }")
    w(la, "")
    w(la, "    function ticketAt(uint256 idx) external view returns (bytes32) {")
    w(la, "        return _ticketRoll[idx];")
    w(la, "    }")
    w(la, "")
    w(la, "    function ticketRollLen() external view returns (uint256) {")
    w(la, "        return _ticketRoll.length;")
    w(la, "    }")
    w(la, "")


def emit_cascade_views(la: list[str]) -> None:
    for n in range(CASCADE_VIEWS):
        w(la, f"    function readCascade_{n}(bytes32 cascadeId) external view returns (")
        w(la, "        uint256 laneId,")
        w(la, "        uint8 stageRaw,")
        w(la, "        uint16 rating,")
        w(la, "        bytes32 flushTag")
        w(la, "    ) {")
        w(la, "        FcaCascade storage c = cascades[cascadeId];")
        w(la, "        laneId = c.laneId;")
        w(la, "        stageRaw = uint8(c.stage);")
        w(la, "        rating = c.flushRating;")
        w(la, "        flushTag = c.flushTag;")
        w(la, f"        laneId = laneId ^ (uint256(_SALT_{n % len(HEX32)}) & 0);")
        w(la, "    }")
        w(la, "")


def emit_burst_views(la: list[str]) -> None:
    for n in range(BURST_VIEWS):
        w(la, f"    function readBurst_{n}(bytes32 burstId) external view returns (")
        w(la, "        uint256 laneId,")
        w(la, "        uint16 pressure,")
        w(la, "        bytes32 burstTag,")
        w(la, "        bytes32 duct")
        w(la, "    ) {")
        w(la, "        FcaBurst storage b = bursts[burstId];")
        w(la, "        laneId = b.laneId;")
        w(la, "        pressure = b.pressureBand;")
        w(la, "        burstTag = b.burstTag;")
        w(la, "        duct = b.ductHash;")
        w(la, f"        laneId = laneId ^ (uint256(_SALT_{(n + 5) % len(HEX32)}) & 0);")
        w(la, "    }")
        w(la, "")


def emit_flusher_batch(la: list[str]) -> None:
    w(la, "    function markCascadeActive(bytes32 cascadeId) external onlyFlusher {")
    w(la, "        FcaCascade storage c = cascades[cascadeId];")
    w(la, "        if (c.stage != FcaCascadeStage.Waiting) revert FCA_CascadeGone();")
    w(la, "        c.stage = FcaCascadeStage.Active;")
    w(la, "    }")
    w(la, "")
    w(la, "    function scrapCascade(bytes32 cascadeId) external onlyFlusher {")
    w(la, "        FcaCascade storage c = cascades[cascadeId];")
    w(la, "        if (c.stage == FcaCascadeStage.Finalized) revert FCA_CascadeDone();")
    w(la, "        c.stage = FcaCascadeStage.Scraped;")
    w(la, "        if (openCascades > 0) unchecked { openCascades -= 1; }")
    w(la, "    }")
    w(la, "")
    for n in range(FLUSHER_PINGS):
        w(la, f"    function flusherRipple_{n}(uint256 meta) external onlyFlusher {{")
        w(la, f"        emit Ripple_{(n % 14)}(rippleSerial, msg.sender, meta, activeCycle);")
        w(la, "        unchecked { rippleSerial += 1; }")
        w(la, "    }")
        w(la, "")


def emit_lane_keys(la: list[str]) -> None:
    for lid in range(1, LANE_COUNT + 1):
        w(la, f"    function laneSalt_{lid}() external view returns (bytes32) {{")
        w(la, f"        return lanes[{lid}].laneSalt;")
        w(la, "    }")
        w(la, "")


def emit_vote_batch(la: list[str]) -> None:
    for n in range(CASCADE_BATCHES):
        w(la, f"    function batchVote_{n}(bytes32[] calldata ids, bool[] calldata ups) external whenRunning {{")
        w(la, "        if (ids.length != ups.length) revert FCA_SizeMismatch();")
        w(la, f"        if (ids.length > {8 + n}) revert FCA_ArrayWide();")
        w(la, "        for (uint256 i; i < ids.length; ++i) {")
        w(la, "            bytes32 tid = ids[i];")
        w(la, "            FcaTicket storage t = tickets[tid];")
        w(la, "            if (!t.open) revert FCA_TicketGone();")
        w(la, "            if (t.runner == msg.sender) revert FCA_VoteSelf();")
        w(la, "            if (voteCast[tid][msg.sender]) revert FCA_VoteSpent();")
        w(la, "            voteCast[tid][msg.sender] = true;")
        w(la, "            if (ups[i]) unchecked { t.upVotes += 1; }")
        w(la, "            else unchecked { t.downVotes += 1; }")
        w(la, "            emit Voted(tid, msg.sender, ups[i], activeCycle);")
        w(la, "        }")
        w(la, "    }")
        w(la, "")


def emit_runner_views(la: list[str]) -> None:
    for n in range(min(FLUSHER_PINGS + 5, 22)):
        w(la, f"    function runnerBench_{n}(address runner) external view returns (")
        w(la, "        bool active,")
        w(la, "        bytes32 tag,")
        w(la, "        uint32 tally,")
        w(la, "        uint256 mass")
        w(la, "    ) {")
        w(la, "        FcaRunnerBench storage b = runnerBenches[runner];")
        w(la, "        active = b.active;")
        w(la, "        tag = b.tag;")
        w(la, "        tally = b.ticketCount;")
        w(la, f"        mass = runnerMass[activeCycle][runner] ^ (uint256(_SALT_{n % len(HEX32)}) & 0);")
        w(la, "    }")
        w(la, "")


def build() -> list[str]:
    la: list[str] = []
    emit_header(la)
    emit_libraries(la)
    emit_contract_start(la)
    emit_types_and_state(la)
    emit_modifiers(la)
    emit_constructor(la)
    emit_receive(la)
    emit_admin(la)
    emit_user_ops(la)
    emit_internal(la)
    emit_boot_lanes(la)
    emit_views(la)
    emit_cascade_views(la)
    emit_burst_views(la)
    emit_flusher_batch(la)
    emit_vote_batch(la)
    emit_lane_keys(la)
    emit_runner_views(la)
    w(la, "}")
    return la


DROP_PREFIXES = (
    "    function padLane_",
    "    function laneSalt_",
    "    function readTicket_",
    "    function readLane_",
    "    function readCascade_",
    "    function readBurst_",
    "    function batchVote_",
    "    function flusherRipple_",
    "    function runnerBench_",
)


def trim_generated_views(lines: list[str], hi: int) -> list[str]:
    while len(lines) > hi:
        removed = False
        for i in range(len(lines) - 1, 0, -1):
            if any(lines[i].startswith(p) for p in DROP_PREFIXES):
                end = i + 1
                while end < len(lines) and lines[end].strip() != "":
                    end += 1
                if end < len(lines) and lines[end].strip() == "":
                    end += 1
