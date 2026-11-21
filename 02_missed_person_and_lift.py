# Assumed placeholders (NOT real mower specs)
SPEED = 0.5          # m/s mower ground speed
WHEEL_STOP_DIST = 0.03  # m to halt wheels once commanded
BLADE_BRAKE_T = 0.5  # s active brake to zero
BLADE_PASSIVE_T = 3.0   # s coast-down with no brake
BLADE_BEHIND_BUMPER = 0.20  # m from front bumper to blade edge
HAND_REACH_T = 0.4   # s for a hand to reach blade after deck is lifted
LIFT_LATENCY = 0.02  # s lift sensor to command

log = []
def L(case, event): log.append((case, event))

def run(case, detected, backup):
    # backup: None | "bumper" | "lift" | "lift_no_sensor"
    if case.startswith("A"):   # normal detection, person 1.0 m ahead
        t_cmd = 0.1
        gap_left = 1.0 - SPEED*t_cmd - WHEEL_STOP_DIST
        safe = gap_left > BLADE_BEHIND_BUMPER*0  # stopped before reaching person
        blade_zero = BLADE_BRAKE_T
        L(case, "primary detection -> cut_blade+halt_wheels")
        return safe, f"person never reached; blade zero in {blade_zero}s"
    if case.startswith("B"):   # camera misses, bumper contact at 0 m
        L(case, "MISS: contact with no prior detection (primary detector failed)")
        L(case, "backup bumper -> cut_blade+halt_wheels")
        travel = WHEEL_STOP_DIST
        person_reached_blade = travel >= BLADE_BEHIND_BUMPER
        return (not person_reached_blade), f"mower rolled {travel:.2f}m after contact; blade edge is {BLADE_BEHIND_BUMPER}m behind bumper"
    if case.startswith("C"):   # unsafe lift, lift sensor works
        L(case, "lift sensor -> cut_blade+halt_wheels")
        blade_speed_at_reach = max(0, 1 - (HAND_REACH_T-LIFT_LATENCY)/BLADE_BRAKE_T)
        return blade_speed_at_reach == 0, f"blade at {blade_speed_at_reach*100:.0f}% speed when hand reaches it ({HAND_REACH_T}s)"
    if case.startswith("D"):   # undetected, no backup fires
        return False, "no sensor fired: nothing to stop, nothing to log"

cases = [("A. Person detected normally", True, None),
         ("B. Undetected, bumper backup", False, "bumper"),
         ("C. Unsafe lift, lift sensor on", True, "lift"),
         ("D. Undetected, no backup fires", False, None)]
print(f"{'Case':34}{'Safe?':7} Detail")
for c, d, b in cases:
    ok, detail = run(c, d, b)
    print(f"{c:34}{'YES' if ok else 'NO':7} {detail}")
print("\nAudit log:")
for c, e in log: print(f"  [{c[:1]}] {e}")
