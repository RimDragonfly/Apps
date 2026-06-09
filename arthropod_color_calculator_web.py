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
    "Turquoise":   (12, 13),
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
    "Turquoise":   (12, 13),
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
                      f"This tool requires Genetics skill uncapped at level 1000 so all "
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
        return "Blue"
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
            return "Turquoise" if fj in (12, 13) else "Green"
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
            "label": "Clockwise wrap (experimental — red at top of wheel, both body and wings)",
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

st.warning("""⚠️ **Genetics skill must be uncapped at level 1000.**
If your Genetics skill is not at maximum, some gene positions will show as **?** (unknown).
Unknown positions cannot be read correctly and will cause wrong results.
Do not use this tool with a genome that contains ? marks.""")

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

                if pts == 0:
                    st.success(f"**{label}:** {needed} change(s) — 🟢 no stat cost")
                else:
                    st.warning(f"**{label}:** {needed} change(s) — 🔴 {pts} stat point(s) lost")

                st.markdown(f"*Direction: {direction}*")
                for i, (coord, is_stat, stat_name, stat_val) in enumerate(selected):
                    if is_stat and stat_val > 0:
                        sign = "−" if direction == "dominant → recessive" else "+"
                        st.markdown(f"**{i+1}.** `{coord}` · costs **{sign}{stat_val} {stat_name}**")
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
F-J dominant or mixed sets broad hue position. A-E dominant or mixed fine-tunes within the zone.
More dominant or mixed = clockwise on the color wheel. Less = counterclockwise.
</small>
""", unsafe_allow_html=True)
