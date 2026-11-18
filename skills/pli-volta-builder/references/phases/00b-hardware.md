# Phase 0b: Hardware readiness

**Entry:** intake has the card list. Old datacenter cards on used boards, switch cards and risers fail in ways a
software session will not see unless it looks. In the PLI builds a card ran at half its link width until a switch
card was moved, NVLink links raised errors on two cards, every card dropped off the bus after a crash, power supplies
tripped under full load and a power strip failed. Check before blaming the engine.

**Goal:** every card at its expected link, the power budget known, no open fault; and a list of hardware settings
the owner may want to try as measured levers.

## Check (read-only; the owner runs anything that needs root and is not already allowed)

- **PCIe link per card:** `sudo lspci -vv -s <bus>` for each card: `LnkSta` (current speed and width) against
  `LnkCap` (what the card can do). A card at x8 where it can do x16, or at Gen1 speed, is a fault to report.
  `nvidia-smi --query-gpu=index,pcie.link.gen.current,pcie.link.width.current --format=csv` gives a quick view
  (read it under load: idle cards drop their link speed).
- **NVLink:** `nvidia-smi nvlink -s` (link state and speed per link) and `nvidia-smi nvlink -e` (error counters, if
  supported); `nvidia-smi topo -m` for which cards share a board.
- **Faults so far:** `journalctl -k | grep -i xid` (Xid errors, with their numbers), cards missing from
  `nvidia-smi -L` compared with the count expected, ECC counters (`nvidia-smi -q -d ECC`).
- **ACS** on the PCIe switches above the cards (`lspci -vvv | grep -i acsctl`): redirect hangs card-to-card traffic.
- **Power budget:** each card's limit times the number of cards on each power supply and each circuit, against the
  supply's and the circuit's rating, with margin for the host. Old servers on household circuits trip under full
  load: say which combination of cards may run at full load at once.
- **Thermals:** temperature and clock throttle reasons under a short load (`nvidia-smi -q -d PERFORMANCE`).

## Hardware settings as measured levers (gate 1: the owner applies them)

Power caps, clock caps and locked clocks, memory clocks where adjustable, the placement of switch cards and risers,
BIOS settings (PCIe generation, ACS, power profiles), and host memory speed can each change speed. Treat each as a
candidate like any other, with one difference: the agent proposes, the OWNER applies. Write the amendment (what is
changed, the prediction, the lines), the owner applies the setting, and a window measures before and after under the
same everything else. Record losses too: a BIOS change that changed nothing is worth recording so nobody tries it
again. A power cap mostly moves prompt reading (compute-bound); decode (bandwidth-bound) moves less.

## Writes

The hardware table in `BUILD-STATE.md`: per card, index, board, link (current / capable), NVLink state, temperature
under load, faults; the power budget per supply and circuit; the hardware levers proposed, applied and measured.

## Gate to phase 1

Every card at its expected link and visible, no unexplained Xid line, the power budget written down. A fault found
here is reported to the owner and fixed (or accepted in writing) before the first boot.
