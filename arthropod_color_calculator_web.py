"""
Arthropod Color Calculator — Streamlit Web Version
Project Gorgon Genetics Research — Kaskrim & Azizah
Compiled by AI Lumière

Run locally:  streamlit run arthropod_color_calculator_web.py
Host on:      Streamlit Community Cloud (streamlit.io)
"""

import streamlit as st

# ============================================================
# GENE MAPS
# ============================================================

LOCKED_DOMINANT_CR1 = {"1F2", "1G3", "1I1", "1I2", "1I4"}
LOCKED_DOMINANT_CR3 = {"3F3", "3G3", "3G4", "3I2", "3I3", "3I4"}

STAT_GENES_CR1 = {
    "1A2": ("Toughness", 2),
    "1B1": ("Friendliness", 3),
    "1B2": ("Ruggedness", 5),
    "1B3": ("Ferocity", 5),
    "1C1": ("Enthusiasm", 4),
    "1C2": ("Virility", 3),
    "1D1": ("Toughness", 3),
    "1E2": ("Intelligence", 3),
    "1E3": ("Enthusiasm", 5),
    "1F1": ("Intelligence", 4),
    "1F3": ("Virility", 2),
    "1F4": ("Ruggedness", 5),
    "1G1": ("Enthusiasm", 5),
    "1G2": ("Toughness", 6),
    "1H1": ("Friendliness", 5),
    "1H3": ("Ferocity", 3),
    "1H4": ("Ruggedness", 3),
    "1J1": ("Virility", 5),
    "1J2": ("Intelligence", 3),
}

STAT_GENES_CR3 = {
    "3C1": ("Ruggedness", 6),
    "3C2": ("Enthusiasm", 1),
    "3E1": ("Toughness", 3),
    "3E3": ("Intelligence", 4),
    "3E4": ("Ruggedness", 4),
    "3F2": ("Toughness", 5),
    "3G1": ("Ferocity", 2),
    "3G2": ("Virility", 4),
    "3H2": ("Friendliness", 4),
    "3H3": ("Friendliness", 3),
    "3J1": ("Ferocity", 3),
    "3J4": ("Intelligence", 7),
}

COLOR_LADDER_CR1 = {
    "Red":         (7,  9),
    "Yellow-green": (10, 10),
    "Green-yellow":  (10, 10),
    "Orange":      (11, 13),
    "Orange":        (11, 13),
    "Green":       (11, 13),
    
    "Blue":        (14, 16),
    "Blue-violet": (17, 17),
    "Teal":  (17, 19),
    "Purple":      (17, 19),
}

COLOR_LADDER_CR3 = {
    "Red":         (10, 10),
    "Orange":      (11, 13),
    "Orange":        (11, 13),
    "Green":       (9,  13),
    
    "Blue":        (14, 16),
    "Blue-violet": (15, 17),
    "Purple":      (17, 19),
}

LABELS = list("ABCDEFGHIJ")

# ============================================================
# CORE LOGIC
# ============================================================

def parse_genome(raw, chromosome):
    cleaned = raw.replace(" ", "")
    if len(cleaned) != 40:
        return None, f"Expected 40 positions, got {len(cleaned)}. Check input."
    unknown = sum(1 for c in cleaned if c == "?")
    if unknown > 0:
        return None, (f"Genome contains {unknown} unknown position(s) marked as '?'. "
                      f"This tool requires Genetics skill uncapped at level 100 so all "
                      f"positions are visible. Unknown genes cannot be read correctly.")
    positions = {}
    for i, label in enumerate(LABELS):
        for pos in range(4):
            coord = f"{chromosome}{label}{pos+1}"
            state = cleaned[i*4 + pos]
            positions[coord] = state
    return positions, None

def is_dom(state):
    return state.lower() not in ("o", "r")

def fj_dom_count(positions, cr):
    return sum(1 for label in "FGHIJ" for pos in range(1,5)
               if is_dom(positions.get(f"{cr}{label}{pos}", "o")))

def ae_dom_count(positions, cr):
    return sum(1 for label in "ABCDE" for pos in range(1,5)
               if is_dom(positions.get(f"{cr}{label}{pos}", "o")))

def detect_color(fj, ae, cr):
    if fj >= 17:
        if ae >= 7: return "Teal"
        elif ae >= 4: return "Blue-violet"
        else: return "Purple"
    if fj in (14, 15, 16):
        return "Teal" if ae >= 5 else "Blue"
    if fj == 10:
        return "Green-yellow" if ae >= 4 else "Yellow-green"
    if fj == 9:
        if cr == 3:
            return "Green" if ae <= 4 else "Orange"
        else:  # CR1
            if ae <= 4: return "Green"
            elif ae <= 8: return "Yellow"
            else: return "Orange"
    if fj in (11, 12, 13):
        if ae <= 2:
            return "Teal" if fj in (12, 13) else "Green"
        elif ae <= 4:
            return "Green"
        elif ae <= 8:
            return "Yellow"
        else:
            return "Orange"
    if fj <= 8:
        return "Red"
    ladder = COLOR_LADDER_CR1 if cr == 1 else COLOR_LADDER_CR3
    min_fj = min(lo for lo, hi in ladder.values())
    if fj < min_fj:
        return "Below ladder — possible counterclockwise approach to violet/purple"
    return "Unknown"

def get_candidates(positions, cr, direction):
    """Get eligible F-J positions for flipping in a given direction."""
    locked = LOCKED_DOMINANT_CR1 if cr == 1 else LOCKED_DOMINANT_CR3
    stat_genes = STAT_GENES_CR1 if cr == 1 else STAT_GENES_CR3
    candidates = []
    for label in "FGHIJ":
        for pos in range(1, 5):
            coord = f"{cr}{label}{pos}"
            if coord not in positions: continue
            if coord in locked: continue
            state = positions[coord]
            if direction == "recessive → dominant" and is_dom(state): continue
            if direction == "dominant → recessive" and not is_dom(state): continue
            is_stat = coord in stat_genes
            stat_name = stat_genes[coord][0] if is_stat else None
            stat_val = stat_genes[coord][1] if is_stat else 0
            candidates.append((coord, is_stat, stat_name, stat_val))
    candidates.sort(key=lambda x: (x[1], x[3]))
    return candidates

def calc_cost(selected, direction):
    """Calculate total stat cost for a set of changes.
    For arthropods: stats express at recessive (o).
    recessive → dominant = stat turns OFF = loss (negative)
    dominant → recessive = stat turns ON = gain (positive)
    """
    cost = {}
    for coord, is_stat, stat_name, stat_val in selected:
        if is_stat and stat_val > 0:
            delta = stat_val if direction == "dominant → recessive" else -stat_val
            cost[stat_name] = cost.get(stat_name, 0) + delta
    return cost

def calculate_changes(positions, cr, target_color):
    ladder = COLOR_LADDER_CR1 if cr == 1 else COLOR_LADDER_CR3
    target_lo, target_hi = ladder[target_color]
    current_fj = fj_dom_count(positions, cr)

    if target_lo <= current_fj <= target_hi:
        return "already_there", None, None

    results = {}

    # --- Path A: direct (counterclockwise if going down, clockwise if going up) ---
    if current_fj < target_lo:
        dir_a = "recessive → dominant"
        needed_a = target_lo - current_fj
    else:
        dir_a = "dominant → recessive"
        needed_a = current_fj - target_hi

    cands_a = get_candidates(positions, cr, dir_a)
    selected_a = cands_a[:needed_a]
    cost_a = calc_cost(selected_a, dir_a)
    pts_a = sum(abs(v) for v in cost_a.values())
    results["path_a"] = {
        "label": "Direct path",
        "direction": dir_a,
        "needed": needed_a,
        "selected": selected_a,
        "cost": cost_a,
        "pts": pts_a,
        "feasible": len(selected_a) >= needed_a,
    }

    # --- Path B: clockwise wrap to red (only when target is Red and current_fj is high) ---
    if target_color == "Red" and current_fj > target_hi:
        dir_b = "recessive → dominant"
        # Flip all remaining recessive F-J positions to dominant — wraps around to red
        cands_b = get_candidates(positions, cr, dir_b)
        needed_b = len(cands_b)  # flip everything recessive in F-J
        selected_b = cands_b
        cost_b = calc_cost(selected_b, dir_b)
        pts_b = sum(abs(v) for v in cost_b.values())
        results["path_b"] = {
            "label": "Clockwise wrap",
            "direction": dir_b,
            "needed": needed_b,
            "selected": selected_b,
            "cost": cost_b,
            "pts": pts_b,
            "feasible": True,
        }

    return "paths", results, target_color

# ============================================================
# STREAMLIT UI
# ============================================================

st.set_page_config(
    page_title="Arthropod Color Calculator",
    page_icon="🐝",
    layout="centered"
)

st.title("🐝 Arthropod Color Calculator")
st.caption("Project Gorgon Genetics Research · Kaskrim & Azizah · Lumière")

st.markdown("""
Calculate the minimum changes needed to reach a target body or wing color.
Paste your genome export directly from the game.

**Notation:** `o` or `R` = recessive · everything else = dominant or mixed
""")

st.warning("⚠️ **Genetics skill must be uncapped at level 100.** Do not use this tool with a genome that contains ? marks.")

st.divider()

col1, col2 = st.columns(2)
with col1:
    cr_choice = st.radio(
        "Chromosome",
        options=["CR 1 — Body color", "CR 3 — Wing color"],
        index=0
    )
    cr = 1 if "CR 1" in cr_choice else 3

with col2:
    ladder = COLOR_LADDER_CR1 if cr == 1 else COLOR_LADDER_CR3
    target_color = st.selectbox(
        "Target color",
        options=list(ladder.keys()),
        index=0
    )

genome_input = st.text_input(
    "Genome string (40 positions, spaces OK)",
    placeholder="e.g. oooo Xooo ooXo oooo oooX XoXo XoXX XXXX XXXX Xooo"
)

if genome_input.strip():
    positions, error = parse_genome(genome_input.strip(), cr)

    if error:
        st.error(f"⚠️ {error}")
    else:
        fj = fj_dom_count(positions, cr)
        ae = ae_dom_count(positions, cr)
        current_color = detect_color(fj, ae, cr)

        st.divider()

        m1, m2, m3 = st.columns(3)
        m1.metric("F-J dominant or mixed", f"{fj} / 20")
        m2.metric("A-E dominant or mixed", f"{ae} / 20")
        m3.metric("Estimated color", current_color)

        # Show low F-J note when genome is below ladder or targeting red with very low F-J
        if "Below ladder" in current_color or (target_color == "Red" and fj <= 6):
            st.info("""ℹ️ **Low F-J zone — bottom of the wheel**

The color wheel is circular. Red appears at both ends of the ladder.
All-recessive on CR 1 is confirmed to produce red by wrapping clockwise past violet.

What other colors may exist in this low F-J zone (F-J=0–6) is **untested**.
Other colors may be achievable here. Until data points confirm what lives in this zone,
this app defaults to Red for any genome below F-J=7.

If your bee has an unusual color at very low F-J, that is valuable research data.
Please share it with Kaskrim.""")

        st.divider()

        target_lo, target_hi = ladder[target_color]
        status, paths, _ = calculate_changes(positions, cr, target_color)

        if status == "already_there":
            st.success(f"✅ Already in the **{target_color}** zone (F-J dom/mixed = {fj}).")
            st.info("A-E dominant or mixed fine-tunes the exact shade within this zone.")
        else:
            def show_path(path, label):
                direction = path["direction"]
                needed = path["needed"]
                selected = path["selected"]
                cost = path["cost"]
                pts = path["pts"]
                feasible = path["feasible"]

                if not feasible:
                    st.warning(f"⚠️ {label}: Only {len(selected)} eligible positions found — not enough.")
                    return

                # Calculate net stat change for summary
                net = sum(cost.values())
                if pts == 0:
                    st.success(f"**{label}:** {needed} change(s) — 🟢 no stat cost")
                elif net > 0:
                    st.success(f"**{label}:** {needed} change(s) — 🟢 {pts} stat point(s) gained")
                else:
                    st.warning(f"**{label}:** {needed} change(s) — 🔴 {pts} stat point(s) lost")

                st.markdown(f"*Direction: {direction}*")
                for i, (coord, is_stat, stat_name, stat_val) in enumerate(selected):
                    if is_stat and stat_val > 0:
                        # dominant→recessive = stat ON = gain; recessive→dominant = stat OFF = loss
                        if direction == "dominant → recessive":
                            st.markdown(f"**{i+1}.** `{coord}` · gains **+{stat_val} {stat_name}**")
                        else:
                            st.markdown(f"**{i+1}.** `{coord}` · costs **−{stat_val} {stat_name}**")
                    else:
                        st.markdown(f"**{i+1}.** `{coord}` · cosmetic, no stat cost")

                if cost:
                    for stat, delta in sorted(cost.items()):
                        sign = "+" if delta > 0 else ""
                        color_str = "🟢" if delta > 0 else "🔴"
                        st.markdown(f"{color_str} **{stat}:** {sign}{delta}")
                else:
                    st.markdown("🟢 **No stat impact.**")

            path_a = paths.get("path_a")
            path_b = paths.get("path_b")

            if path_b:
                # Show both paths, recommend cheaper one
                pts_a = path_a["pts"] if path_a else 999
                pts_b = path_b["pts"]

                if pts_a <= pts_b:
                    st.markdown("### ✅ Recommended: Direct path")
                    show_path(path_a, path_a["label"])
                    st.divider()
                    st.markdown(f"### Alternative: {path_b['label']}")
                    st.caption(f"Costs {pts_b} stat points — more expensive than direct path.")
                    show_path(path_b, path_b["label"])
                else:
                    st.markdown(f"### ✅ Recommended: {path_b['label']}")
                    st.caption("Cheaper in stat cost than the direct path.")
                    show_path(path_b, path_b["label"])
                    st.divider()
                    st.markdown("### Alternative: Direct path")
                    st.caption(f"Costs {pts_a} stat points — more expensive.")
                    show_path(path_a, path_a["label"])
            else:
                show_path(path_a, path_a["label"])

st.divider()
st.markdown("""
<small>
Color ladder based on research by Kaskrim and Azizah, 2021–2026.
F-J dominant or mixed sets broad hue position (more F-J = clockwise = toward purple/blue).
A-E dominant or mixed fine-tunes within the zone (more A-E = counterclockwise = toward warmer colors).
The two axes push in opposite directions.
</small>
""", unsafe_allow_html=True)

# ============================================================
# CR5 GLOW + CR9 PARTICLES & TAIL LIGHT
# ============================================================

# ---- CR5 STAT GENE MAP ----
# Position: (stat_name, point_value)
# A1, A3, C1 are cosmetic (_)
STAT_GENES_CR5 = {
    "5A2": ("Friendliness", 4),
    "5A4": ("Enthusiasm",   4),
    "5B1": ("Intelligence", 4),
    "5B2": ("Intelligence", 2),
    "5B3": ("Friendliness", 3),
    "5B4": ("Ferocity",     1),
    "5C2": ("Toughness",    7),
}

# CR5 glow-on patterns (normalized, 10 chars)
# Anything not in this set = glow off
GLOW_ON_PATTERNS = {
    "oooooXXXXo",  # glow on
    "oooooXXooo",  # glow on
    "oooooXXoXo",  # glow on
    "oooooXoXoo",  # glow on
}

# ---- CR9 PARTICLE LOOKUP ----
# Uses first 10 positions of CR9 (A1-A4, B1-B4, C1-C2)
# Key: 10-char normalized string
# Value: "Tail" | "Wing" | "None"
PARTICLE_LOOKUP = {
    # Tail particles
    "XXXXXooXXX": "Tail",
    "XXXXXoXoXX": "Tail",
    "XXXXXXooXX": "Tail",
    "XXXXoooXXX": "Tail",
    "XXXoXoXoXo": "Tail",
    "XXXoXooXXX": "Tail",
    "XXXoXoooXX": "Tail",
    "XXXoooooXX": "Tail",
    "XXoXXoooXX": "Tail",
    "XXooXoooоX": "Tail",
    "XoXXXoooXX": "Tail",
    # Wing particles
    "XooXXXXXXX": "Wing",
    "oXoXXXXXXX": "Wing",
    "ooXXXXXXXX": "Wing",
    # No particles (sample — not exhaustive, used as fallback)
}

# ---- CR9 TAIL LIGHT LOOKUP ----
# Uses last 10 positions of CR9 (C3-C4, D1-D4, E1-E4)
# Key: 10-char normalized string
# Value: color name string
# Tail light lookup: key -> list of possible colors
# Entries with multiple colors mean the pattern is ambiguous — needs more data
TAILLIGHT_LOOKUP = {
    "oXXooXooXo": ["Wave Teal"],
    "oXXoXoooоX": ["Wave Teal"],
    "oXXXoooXoo": ["Poison Green"],
    "ooooXoXooo": ["Poison Green"],
    "ooXXXooXoo": ["Poison Green"],
    "ooooXXoXoX": ["Golden Yellow"],
    "ooooXoXXoX": ["Golden Yellow"],
    "ooooXoXoXX": ["Golden Yellow"],
    "ooooXooXoX": ["Golden Yellow", "Firey Pink"],  # ambiguous — needs more data
    "oXooooooоX": ["Aqua Blue"],
    "oXoXooXooX": ["Aqua Blue"],
    "ooooXooooX": ["Aqua Blue", "None"],            # ambiguous — needs more data
    "oXooooXoXX": ["Aqua Blue"],
    "ooooоXXooX": ["Aqua Blue"],
    "oXooooooXX": ["Red Orange"],
    "oXoXoXXXXX": ["Red Orange"],
    "oXXoXoXXoX": ["Firey Pink"],
    "oXoXoXXXXo": ["Firey Pink"],
    "oXoXoXXXoX": ["Firey Pink"],
    "ooooXoooXX": ["Firey Pink", "None"],           # ambiguous — needs more data
    "oXoXXXXooX": ["Galaxy Purple"],
    "oXoXXoooоX": ["Galaxy Purple"],
    "oXoXXooooo": ["Galaxy Purple"],
    "ooooXoXXXX": ["Galaxy Purple", "White Frosty"], # ambiguous — needs more data
    "ooooXoXXoX": ["Galaxy Purple"],
    "ooooXooXXX": ["Galaxy Purple"],
    "ooooooooXX": ["Galaxy Purple"],
    "oXooooooоX": ["White/Purp/Teal"],
    "ooooXooooo": ["White/Purp/Teal"],
    "XXooooXooX": ["White/Purp/Teal"],
    "oXooXooXoo": ["White/Purp/Teal"],
    "ooooXXoooX": ["White Noise"],
    "ooooXoXooX": ["White Noise"],
    "ooooXoooоX": ["White Noise"],
    "ooooooooоX": ["None"],
    "oXooooooXo": ["None"],
    "oXooooXoXo": ["None"],
    "oXooXooXXo": ["None"],
}

def normalize_genome_str(raw, expected_len):
    """Normalize a genome string to o/X notation, strip spaces."""
    cleaned = raw.replace(" ", "")
    if len(cleaned) != expected_len:
        return None, f"Expected {expected_len} positions, got {len(cleaned)}."
    result = ""
    for c in cleaned:
        if c.lower() in ("o", "r"):
            result += "o"
        else:
            result += "X"
    return result, None

def analyze_cr5(raw):
    """Parse CR5, determine glow on/off, and calculate stat contributions."""
    norm, err = normalize_genome_str(raw, 10)
    if err:
        return None, err

    labels_sizes = [("A", 4), ("B", 4), ("C", 2)]
    positions = {}
    idx = 0
    for label, size in labels_sizes:
        for pos in range(1, size + 1):
            coord = f"5{label}{pos}"
            positions[coord] = norm[idx]
            idx += 1

    glow_on = norm in GLOW_ON_PATTERNS

    stat_totals = {}
    expressing = []
    not_expressing = []
    for coord, state in positions.items():
        if coord in STAT_GENES_CR5:
            stat_name, stat_val = STAT_GENES_CR5[coord]
            if state == "o":
                stat_totals[stat_name] = stat_totals.get(stat_name, 0) + stat_val
                expressing.append((coord, stat_name, stat_val))
            else:
                not_expressing.append((coord, stat_name, stat_val))

    return {
        "glow": glow_on,
        "norm": norm,
        "positions": positions,
        "stat_totals": stat_totals,
        "expressing": expressing,
        "not_expressing": not_expressing,
    }, None

def glow_on_paths(positions, norm):
    """Calculate paths to reach each known glow-on pattern from current CR5 state.
    Returns list of path dicts sorted by (flips_needed, net_stat_loss).
    Only positions that differ between current and target are flipped.
    CR5 has no locked positions so all flips are always available.
    """
    coords = [f"5{l}{p}" for l, sz in [("A",4),("B",4),("C",2)] for p in range(1, sz+1)]

    paths = []
    for target_norm in sorted(GLOW_ON_PATTERNS):
        flips = []
        net_stat = {}  # stat_name -> delta (positive = gain, negative = loss)
        for i, coord in enumerate(coords):
            current = norm[i]
            target  = target_norm[i]
            if current == target:
                continue
            # This position needs to flip
            direction = "recessive → dominant" if target == "X" else "dominant → recessive"
            stat_info = STAT_GENES_CR5.get(coord)
            if stat_info:
                stat_name, stat_val = stat_info
                if stat_val > 0:
                    # dominant→recessive = stat turns ON = gain
                    # recessive→dominant = stat turns OFF = loss
                    delta = stat_val if direction == "dominant → recessive" else -stat_val
                    net_stat[stat_name] = net_stat.get(stat_name, 0) + delta
            flips.append({"coord": coord, "direction": direction, "stat": stat_info})

        total_loss = sum(v for v in net_stat.values() if v < 0)
        total_gain = sum(v for v in net_stat.values() if v > 0)
        paths.append({
            "target": target_norm,
            "flips": flips,
            "flips_count": len(flips),
            "net_stat": net_stat,
            "total_loss": total_loss,
            "total_gain": total_gain,
            "net_total": total_gain + total_loss,  # combined net (loss is negative)
        })

    # Sort by fewest flips, then by best net stat (highest net = least loss / most gain)
    paths_by_speed = sorted(paths, key=lambda p: (p["flips_count"], -p["net_total"]))
    paths_by_stat  = sorted(paths, key=lambda p: (-p["net_total"], p["flips_count"]))
    return paths_by_speed, paths_by_stat


def lookup_cr9(raw):
    norm, err = normalize_genome_str(raw, 20)
    if err:
        return None, err
    particle_key = norm[:10]
    taillight_key = norm[10:]

    # Particle result
    if particle_key in PARTICLE_LOOKUP:
        particle = PARTICLE_LOOKUP[particle_key]
    elif all(c == "X" for c in particle_key[:2]) and particle_key[8:10] == "XX":
        particle = "Tail"
    else:
        particle = "Unknown"

    # Tail light result — returns a list; multiple entries = ambiguous
    taillight_results = TAILLIGHT_LOOKUP.get(taillight_key, None)
    if taillight_results is None:
        taillight = ["Unknown"]
        ambiguous = False
    else:
        taillight = taillight_results
        ambiguous = len(taillight_results) > 1

    return {"particle": particle, "taillight": taillight, "taillight_ambiguous": ambiguous}, None


def particle_paths(particle_key):
    """For each known particle type (Tail, Wing, None), find the cheapest path
    from the current particle_key pattern. Returns dict keyed by type."""
    # Group all known patterns by type
    by_type = {"Tail": [], "Wing": [], "None": []}
    for pattern, ptype in PARTICLE_LOOKUP.items():
        if ptype in by_type:
            by_type[ptype].append(pattern)

    # Also include no-particle heuristic: if none in lookup, treat any non-Tail/Wing as None
    # (We only compute paths to patterns we actually know)

    results = {}
    for target_type, patterns in by_type.items():
        best = None
        for target_pattern in patterns:
            flips = []
            for i, (c, t) in enumerate(zip(particle_key, target_pattern)):
                if c != t:
                    coord = ["9A1","9A2","9A3","9A4","9B1","9B2","9B3","9B4","9C1","9C2"][i]
                    direction = "recessive → dominant" if t == "X" else "dominant → recessive"
                    flips.append({"coord": coord, "direction": direction})
            path = {"target": target_pattern, "flips_count": len(flips), "flips": flips}
            if best is None or len(flips) < best["flips_count"]:
                best = path
        results[target_type] = best
    return results


# ============================================================
# CR5 / CR9 UI SECTION
# ============================================================

st.divider()
st.header("🐝 Visual Traits — CR5 & CR9")
st.caption("Glow (CR5) · Particles & Tail Light (CR9)")
st.markdown("""
Paste your CR5 and CR9 genome strings to look up glow, particle type, and tail light color.
These are lookup tables — results not in the research data will show as **Unknown** or **Glow off**.
""")

col_cr5, col_cr9 = st.columns(2)

with col_cr5:
    st.subheader("CR5 — Glow (10 positions)")
    cr5_input = st.text_input(
        "CR5 genome string",
        placeholder="e.g. oooo oXXX Xo",
        key="cr5_input"
    )
    if cr5_input.strip():
        result, err = analyze_cr5(cr5_input.strip())
        if err:
            st.error(f"⚠️ {err}")
        else:
            if result["glow"]:
                st.success("✨ **Glow: ON**")
            else:
                st.info("🔘 **Glow: Off**")

            st.markdown("**CR5 stat contributions (recessive positions):**")
            if result["expressing"]:
                for coord, stat_name, stat_val in sorted(result["expressing"]):
                    st.markdown(f"  `{coord}` → +{stat_val} {stat_name}")
                st.markdown("**Totals from CR5:**")
                for stat, total in sorted(result["stat_totals"].items()):
                    st.markdown(f"  🟢 {stat}: +{total}")
            else:
                st.markdown("  No stat genes expressing on CR5.")

            if result["not_expressing"]:
                with st.expander("Stat genes not expressing (dominant)"):
                    for coord, stat_name, stat_val in sorted(result["not_expressing"]):
                        st.markdown(f"  `{coord}` → {stat_val} {stat_name} (off)")

            # ---- Glow-off: show paths to reach glow-on ----
            if not result["glow"]:
                st.divider()
                st.markdown("**Paths to turn glow on:**")
                paths_speed, paths_stat = glow_on_paths(result["positions"], result["norm"])

                def show_glow_path(path, label):
                    flips = path["flips"]
                    net = path["net_stat"]
                    net_total = path["net_total"]
                    if not flips:
                        st.success(f"**{label}:** Already matches a glow-on pattern — no flips needed.")
                        return
                    if net_total > 0:
                        summary = f"{path['flips_count']} flip(s) — 🟢 net +{net_total} stat points"
                    elif net_total < 0:
                        summary = f"{path['flips_count']} flip(s) — 🔴 net {net_total} stat points"
                    else:
                        summary = f"{path['flips_count']} flip(s) — no net stat change"
                    st.markdown(f"**{label}:** {summary}")
                    st.caption(f"Target pattern: `{path['target']}`")
                    for f in flips:
                        coord = f["coord"]
                        direction = f["direction"]
                        stat_info = f["stat"]
                        if stat_info and stat_info[1] > 0:
                            stat_name, stat_val = stat_info
                            delta = stat_val if "dominant → recessive" in direction else -stat_val
                            sign = "+" if delta > 0 else ""
                            icon = "🟢" if delta > 0 else "🔴"
                            st.markdown(f"  `{coord}` {direction} → {icon} {sign}{delta} {stat_name}")
                        else:
                            st.markdown(f"  `{coord}` {direction} → cosmetic")
                    if net:
                        for stat, delta in sorted(net.items()):
                            sign = "+" if delta > 0 else ""
                            icon = "🟢" if delta > 0 else "🔴"
                            st.markdown(f"  {icon} **{stat}:** {sign}{delta}")

                # Show fastest and best stat — collapse duplicates if they're the same path
                fastest = paths_speed[0]
                best_stat = paths_stat[0]

                st.markdown("##### ⚡ Fewest flips")
                show_glow_path(fastest, "Fastest path")

                if best_stat["target"] != fastest["target"]:
                    st.markdown("##### 📈 Best stat outcome")
                    show_glow_path(best_stat, "Best stat path")
                else:
                    st.caption("The fastest path is also the best stat outcome.")

                # Show remaining options collapsed
                remaining = [p for p in paths_speed[1:] if p["target"] != best_stat["target"]]
                if remaining:
                    with st.expander(f"Other options ({len(remaining)} more)"):
                        for p in remaining:
                            show_glow_path(p, f"Pattern `{p['target']}`")

with col_cr9:
    st.subheader("CR9 — Particles & Tail Light (20 positions)")
    cr9_input = st.text_input(
        "CR9 genome string",
        placeholder="e.g. XXXo Xooo XX oo Xooo oXoo",
        key="cr9_input"
    )
    if cr9_input.strip():
        result, err = lookup_cr9(cr9_input.strip())
        if err:
            st.error(f"⚠️ {err}")
        else:
            p = result["particle"]
            tl = result["taillight"]
            ambiguous = result["taillight_ambiguous"]

            p_icon = {"Tail": "🐝", "Wing": "🪽", "None": "⬜", "Unknown": "❓"}.get(p, "❓")
            st.markdown(f"**Particles:** {p_icon} {p}")

            if tl == ["Unknown"]:
                st.markdown("**Tail light:** ❓ Unknown")
                st.caption("This pattern isn't in the research data yet. If you know what tail light color this bee has, please share the genome with Kaskrim at twitch.tv/kaskrim.")
            elif ambiguous:
                colors_str = " or ".join(tl)
                st.warning(f"**Tail light:** ⚠️ {colors_str}")
                st.caption(
                    f"This genome pattern matches multiple tail light colors in the research data "
                    f"({colors_str}). The decode for this pattern is not yet confirmed. "
                    f"If you can confirm which color your bee actually has, please share it with "
                    f"Kaskrim at twitch.tv/kaskrim — it will help resolve the ambiguity."
                )
            else:
                st.markdown(f"**Tail light:** 💡 {tl[0]}")

            if p == "Unknown":
                st.caption("Particle result unknown — pattern not in research data. Share with Kaskrim at twitch.tv/kaskrim.")

            # ---- Particle target dropdown ----
            st.divider()
            st.markdown("**Change particle type:**")
            particle_options = ["Tail", "Wing", "None"]
            current_label = p if p in particle_options else None
            default_idx = particle_options.index(current_label) if current_label in particle_options else 0
            target_particle = st.selectbox(
                "Target particle type",
                options=particle_options,
                index=default_idx,
                key="target_particle",
                format_func=lambda x: {"Tail": "🐝 Tail", "Wing": "🪽 Wing", "None": "⬜ None"}.get(x, x)
            )

            norm_full, _ = normalize_genome_str(cr9_input.strip(), 20)
            if norm_full:
                particle_key = norm_full[:10]
                if target_particle == p:
                    st.success(f"Already {target_particle} particles — no flips needed.")
                else:
                    paths = particle_paths(particle_key)
                    best = paths.get(target_particle)
                    if best is None or not best["flips"]:
                        st.info("No known pattern available for this particle type.")
                    else:
                        flips = best["flips"]
                        st.markdown(f"**Fewest flips to {target_particle}:** {len(flips)} flip(s)")
                        st.caption(f"Target pattern: `{best['target']}`")
                        for f in flips:
                            st.markdown(f"  `{f['coord']}` — {f['direction']}")

st.divider()
st.markdown("""
<small>
Glow and particle data: Kaskrim, 2026. Tail light series data: community research.
Lookup tables are incomplete — Unknown = not yet documented, not necessarily absent.
</small>
""", unsafe_allow_html=True)

