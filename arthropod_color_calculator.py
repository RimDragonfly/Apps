#!/usr/bin/env python3
"""
Arthropod Color Calculator
Project Gorgon Genetics Research — Kaskrim & Azizah
Compiled by AI Lumière

Given a CR1 (body) or CR3 (wing) genome, calculates the minimum changes
needed to reach a target color.

Usage:
    python3 arthropod_color_calculator.py

Then follow the prompts.

Notation: o = recessive, x/X/t = mixed, D/d = dominant
All non-recessive positions count as dominant or mixed for hue purposes.
"""

# ============================================================
# GENE MAPS
# ============================================================

# Locked dominant positions — can never be changed through breeding
LOCKED_DOMINANT_CR1 = {"1F2", "1G3", "1I1", "1I2", "1I4"}
LOCKED_DOMINANT_CR3 = {"3F3", "3G3", "3G4", "3I2", "3I3", "3I4"}

# Stat genes on CR1 (coord: (stat_name, point_value))
# Locked dominant stat genes are included for reference but marked
STAT_GENES_CR1 = {
    "1A2": ("Toughness", 2),
    "1B1": ("Friendliness", 3),
    "1B2": ("Ruggedness", 5),
    "1B3": ("Ferocity", 5),
    "1C1": ("Enthusiasm", 4),
    "1C2": ("Virility", 3),
    "1D1": ("Toughness", 3),
    "1D3": ("Friendliness", 0),   # locked recessive — always contributes
    "1E2": ("Intelligence", 3),
    "1E3": ("Enthusiasm", 5),
    "1F1": ("Intelligence", 4),
    "1F3": ("Virility", 2),
    "1F4": ("Ruggedness", 5),
    "1G1": ("Enthusiasm", 5),
    "1G2": ("Toughness", 6),
    "1G3": ("Virility", 0),       # locked dominant — never contributes
    "1H1": ("Friendliness", 5),
    "1H3": ("Ferocity", 3),
    "1H4": ("Ruggedness", 3),
    "1I1": ("Ferocity", 0),       # locked dominant — never contributes
    "1J1": ("Virility", 5),
    "1J2": ("Intelligence", 3),
}

# Stat genes on CR3
STAT_GENES_CR3 = {
    "3A1": ("Virility", 6),
    "3A4": ("Ferocity", 0),       # locked recessive
    "3B3": ("Ferocity", 0),       # locked recessive
    "3B4": ("Toughness", 0),      # locked recessive
    "3C1": ("Ruggedness", 6),
    "3C2": ("Enthusiasm", 1),
    "3D1": ("Friendliness", 0),   # locked recessive
    "3D3": ("Ferocity", 0),       # locked recessive
    "3E1": ("Toughness", 3),
    "3E3": ("Intelligence", 4),
    "3E4": ("Ruggedness", 4),
    "3F2": ("Toughness", 5),
    "3F3": ("Ruggedness", 0),     # locked dominant
    "3G1": ("Ferocity", 2),
    "3G2": ("Virility", 4),
    "3G4": ("Enthusiasm", 0),     # locked dominant
    "3H2": ("Friendliness", 4),
    "3H3": ("Friendliness", 3),
    "3I2": ("Intelligence", 0),   # locked dominant
    "3I4": ("Virility", 0),       # locked dominant
    "3J1": ("Ferocity", 3),
    "3J4": ("Intelligence", 7),
}

# Color ladder: color name -> (min F-J dom/mixed, max F-J dom/mixed)
# F-J has 20 positions total
COLOR_LADDER_CR1 = {
    "red":          (7,  10),
    "orange":       (11, 11),
    "yellow":       (12, 13),
    "green":        (12, 14),
    "turquoise":    (14, 14),
    "blue":         (15, 16),
    "blue-violet":  (17, 17),
    "purple":       (17, 19),
    "violet":       (17, 19),
}

COLOR_LADDER_CR3 = {
    "red":          (10, 10),
    "orange":       (11, 11),
    "yellow":       (12, 13),
    "green":        (12, 14),
    "turquoise":    (14, 14),
    "blue":         (15, 16),
    "blue-violet":  (15, 17),
    "purple":       (17, 19),
    "violet":       (17, 19),
}

LABELS = list("ABCDEFGHIJ")

# ============================================================
# PARSING
# ============================================================

def parse_genome(raw, chromosome):
    """Parse a genome string into groups and states."""
    cleaned = raw.replace(" ", "")
    if len(cleaned) != 40:
        raise ValueError(f"Expected 40 positions, got {len(cleaned)}. Check input.")
    groups = [cleaned[i:i+4] for i in range(0, 40, 4)]
    positions = {}
    for i, label in enumerate(LABELS):
        for pos in range(4):
            coord = f"{chromosome}{label}{pos+1}"
            state = cleaned[i*4 + pos]
            positions[coord] = state
    return positions, groups

def is_dominant_or_mixed(state):
    """Returns True if the position counts as dominant or mixed (non-recessive)."""
    return state.lower() not in ("o", "r")

def fj_dom_count(positions, chromosome):
    """Count dominant or mixed positions in groups F-J."""
    count = 0
    for label in "FGHIJ":
        for pos in range(1, 5):
            coord = f"{chromosome}{label}{pos}"
            if coord in positions and is_dominant_or_mixed(positions[coord]):
                count += 1
    return count

def ae_dom_count(positions, chromosome):
    """Count dominant or mixed positions in groups A-E."""
    count = 0
    for label in "ABCDE":
        for pos in range(1, 5):
            coord = f"{chromosome}{label}{pos}"
            if coord in positions and is_dominant_or_mixed(positions[coord]):
                count += 1
    return count

# ============================================================
# COLOR DETECTION
# ============================================================

def detect_color(fj_dom, ae_dom, chromosome):
    """Estimate current color based on F-J and A-E dominant or mixed counts."""
    ladder = COLOR_LADDER_CR1 if chromosome == 1 else COLOR_LADDER_CR3
    matches = []
    for color, (lo, hi) in ladder.items():
        if lo <= fj_dom <= hi:
            matches.append(color)
    if not matches:
        # Below the ladder minimum — approaching from counterclockwise (all-recessive) end
        min_fj = min(lo for lo, hi in ladder.values())
        if fj_dom < min_fj:
            return f"below ladder (F-J={fj_dom}) — counterclockwise from red, approaching violet"
        return "unknown"
    if len(matches) == 1:
        return matches[0]
    # Multiple matches — use A-E to narrow down
    if fj_dom in (12, 13, 14):
        if ae_dom <= 2:
            return "turquoise"
        elif ae_dom <= 4:
            return "green"
        else:
            return "yellow"
    return "/".join(matches)

# ============================================================
# CHANGE CALCULATOR
# ============================================================

def calculate_changes(positions, chromosome, target_color):
    """Calculate minimum changes to reach target color."""
    cr = chromosome
    locked = LOCKED_DOMINANT_CR1 if cr == 1 else LOCKED_DOMINANT_CR3
    stat_genes = STAT_GENES_CR1 if cr == 1 else STAT_GENES_CR3
    ladder = COLOR_LADDER_CR1 if cr == 1 else COLOR_LADDER_CR3

    if target_color not in ladder:
        print(f"\nUnknown color '{target_color}'.")
        print(f"Valid colors: {', '.join(sorted(ladder.keys()))}")
        return

    target_lo, target_hi = ladder[target_color]
    current_fj = fj_dom_count(positions, cr)
    current_ae = ae_dom_count(positions, cr)

    print(f"\nCurrent F-J dominant or mixed: {current_fj}/20")
    print(f"Current A-E dominant or mixed: {current_ae}/20")
    print(f"Target color: {target_color} (F-J dom/mixed {target_lo}-{target_hi})")

    # Determine direction
    if target_lo <= current_fj <= target_hi:
        print(f"\nAlready in {target_color} zone by F-J count.")
        print("A-E dominant or mixed may still need adjustment for exact shade.")
        return

    changes_needed = []
    total_stat_cost = {}

    if current_fj < target_lo:
        # Need MORE dominant or mixed in F-J — flip recessive → dominant
        needed = target_lo - current_fj
        direction = "recessive → dominant"
        candidates = []
        for label in "FGHIJ":
            for pos in range(1, 5):
                coord = f"{cr}{label}{pos}"
                if coord in positions and not is_dominant_or_mixed(positions[coord]):
                    if coord not in locked:
                        is_stat = coord in stat_genes and stat_genes[coord][1] > 0
                        stat_name = stat_genes[coord][0] if coord in stat_genes else None
                        stat_val = stat_genes[coord][1] if coord in stat_genes else 0
                        candidates.append((coord, is_stat, stat_name, stat_val))
        # Sort: cosmetic first, then by smallest stat cost
        candidates.sort(key=lambda x: (x[1], x[3]))

    else:
        # Need FEWER dominant or mixed in F-J — flip dominant → recessive
        needed = current_fj - target_hi
        direction = "dominant → recessive"
        candidates = []
        for label in "FGHIJ":
            for pos in range(1, 5):
                coord = f"{cr}{label}{pos}"
                if coord in positions and is_dominant_or_mixed(positions[coord]):
                    if coord not in locked:
                        is_stat = coord in stat_genes and stat_genes[coord][1] > 0
                        stat_name = stat_genes[coord][0] if coord in stat_genes else None
                        stat_val = stat_genes[coord][1] if coord in stat_genes else 0
                        candidates.append((coord, is_stat, stat_name, stat_val))
        # Sort: cosmetic first, then by smallest stat cost
        candidates.sort(key=lambda x: (x[1], x[3]))

    if needed <= 0:
        print("No F-J changes needed.")
        return

    print(f"\nNeed to flip {needed} F-J position(s) {direction}.")

    if len(candidates) < needed:
        print(f"WARNING: Only {len(candidates)} eligible positions available — not enough to reach target.")

    print(f"\nRecommended changes (fewest rolls, smallest stat cost):")
    print("-" * 50)
    for i, (coord, is_stat, stat_name, stat_val) in enumerate(candidates[:needed]):
        if is_stat and stat_val > 0:
            sign = "-" if direction == "dominant → recessive" else "+"
            note = f"costs {sign}{stat_val} {stat_name}"
        else:
            note = "cosmetic — no stat cost"
        print(f"  {i+1}. {coord}: {direction}  [{note}]")
        if is_stat and stat_val > 0:
            if direction == "dominant → recessive":
                total_stat_cost[stat_name] = total_stat_cost.get(stat_name, 0) - stat_val
            else:
                total_stat_cost[stat_name] = total_stat_cost.get(stat_name, 0) + stat_val

    if total_stat_cost:
        print(f"\nTotal stat impact:")
        for stat, delta in sorted(total_stat_cost.items()):
            sign = "+" if delta > 0 else ""
            print(f"  {stat}: {sign}{delta}")
    else:
        print(f"\nNo stat cost.")

    # Show remaining candidates if stat cost is involved
    if any(c[1] for c in candidates[:needed]):
        remaining = candidates[needed:]
        if remaining:
            print(f"\nAlternative positions (higher stat cost or more rolls):")
            for coord, is_stat, stat_name, stat_val in remaining[:5]:
                note = f"{stat_val} {stat_name}" if is_stat and stat_val > 0 else "cosmetic"
                print(f"  {coord}: {note}")

# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 55)
    print("  Arthropod Color Calculator")
    print("  Project Gorgon Genetics Research")
    print("  Kaskrim & Azizah — Lumière")
    print("=" * 55)
    print()
    print("Chromosome options:")
    print("  1 = CR1 (body color hue)")
    print("  3 = CR3 (wing color hue)")
    print()

    while True:
        cr_input = input("Chromosome (1 or 3): ").strip()
        if cr_input in ("1", "3"):
            chromosome = int(cr_input)
            break
        print("  Please enter 1 or 3.")

    print()
    print("Enter the 40-position genome string.")
    print("Spaces are fine. o=recessive, x/X/t/D=dominant or mixed.")
    raw = input("Genome: ").strip()

    try:
        positions, groups = parse_genome(raw, chromosome)
    except ValueError as e:
        print(f"\nError: {e}")
        return

    fj = fj_dom_count(positions, chromosome)
    ae = ae_dom_count(positions, chromosome)
    current_color = detect_color(fj, ae, chromosome)

    print(f"\nParsed successfully.")
    print(f"F-J dominant or mixed: {fj}/20")
    print(f"A-E dominant or mixed: {ae}/20")
    print(f"Estimated current color: {current_color}")

    print()
    print("Available target colors:")
    ladder = COLOR_LADDER_CR1 if chromosome == 1 else COLOR_LADDER_CR3
    for color, (lo, hi) in sorted(ladder.items(), key=lambda x: x[1][0]):
        rng = f"{lo}" if lo == hi else f"{lo}-{hi}"
        marker = " (current)" if lo <= fj <= hi else ""
        print(f"  {color:<14} (F-J dom/mixed {rng}){marker}")

    print()
    target = input("Target color: ").strip().lower()
    calculate_changes(positions, chromosome, target)

    print()
    input("Press Enter to exit.")

if __name__ == "__main__":
    main()
