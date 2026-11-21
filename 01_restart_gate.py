import time, json

class Gateway:
    ALLOW_ALWAYS = {"cut_blade", "brake_blade", "halt_wheels"}
    APPROVAL_TTL = 30  # seconds

    def __init__(self):
        self.blade_rpm = 3000
        self.stop_id = 0
        self.log = []

    def _log(self, cmd, decision, reason):
        self.log.append({"cmd": cmd, "decision": decision, "reason": reason, "blade_rpm": self.blade_rpm})

    def safety_stop(self):
        self.stop_id += 1
        self.blade_rpm = 0
        self._log("cut_blade", "ALLOW", f"hazard detected, stop #{self.stop_id}")

    def request(self, cmd, approval=None, app_online=True):
        if cmd in self.ALLOW_ALWAYS:
            self.blade_rpm = 0
            self._log(cmd, "ALLOW", "stop-only command")
            return
        if cmd != "restart_blade":
            self._log(cmd, "DENY", "not on allowlist (default deny)")
            return
        if approval is None:
            self._log(cmd, "DENY", "missing approval")
        elif not app_online:
            self._log(cmd, "DENY", "approval unverifiable: app offline")
        elif approval["stop_id"] != self.stop_id:
            self._log(cmd, "DENY", "approval tied to a different stop")
        elif time.time() - approval["issued_at"] > self.APPROVAL_TTL:
            self._log(cmd, "DENY", "approval expired")
        else:
            self.blade_rpm = 3000
            self._log(cmd, "ALLOW", "fresh approval for current stop")

cases = [
    ("1. No approval",        dict(approval=None)),
    ("2. Expired approval",   None),   # built per run
    ("3. App offline",        None),
    ("4. CONTROL: fresh approval", None),
]

results = []
for name, kw in cases:
    g = Gateway(); g.safety_stop()
    if name.startswith("1"):
        g.request("restart_blade", approval=None)
    elif name.startswith("2"):
        g.request("restart_blade", approval={"stop_id": g.stop_id, "issued_at": time.time() - 3600})
    elif name.startswith("3"):
        g.request("restart_blade", approval={"stop_id": g.stop_id, "issued_at": time.time()}, app_online=False)
    else:
        g.request("restart_blade", approval={"stop_id": g.stop_id, "issued_at": time.time()})
    last = g.log[-1]
    expect_zero = not name.startswith("4")
    ok = (g.blade_rpm == 0) == expect_zero and (last["decision"] == "DENY") == expect_zero
    results.append((name, g.blade_rpm, last["decision"], last["reason"], "PASS" if ok else "FAIL"))

print(f"{'Case':32}{'Blade RPM':>10}  {'Decision':8} {'Logged reason':42} Result")
for r in results:
    print(f"{r[0]:32}{r[1]:>10}  {r[2]:8} {r[3]:42} {r[4]}")
