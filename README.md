# Blade-Stop Gateway: A Stop-Only Safety Layer for Robotic Mowers

> **Not safety software.** This repo documents a design and test *method*, plus small simulations that use **assumed placeholder timings, not measured mower data**. Do not use any code here to control a real blade.

## Project overview

Robotic mowers have a spinning blade, and the controls most owners rely on don't cover every case. The physical STOP button needs someone standing next to the mower. The app needs a phone, a connection and an owner who is watching the screen. Neither acts on its own when a child or pet enters the danger zone while no one is looking.

This project describes an independent safety layer that **cuts and brakes the blade before it can reach a person or animal, without waiting for the app or the button.**

## Challenge approach

**Device and boundary:** Robotic mower. The action stopped is the blade spinning while a person or animal is in the danger zone, or the mower is lifted or tilted. Blade motion stops first, then the wheels, in the same response.

**Where the safeguard acts:** A small command gateway on the mower's own safety controller, between the safety agent and the blade motor driver. It is the only path to the blade.

**Design rules**
- **Stop-only authority:** only `cut_blade`, `brake_blade`, `halt_wheels`. No starting, driving, or reconfiguring.
- **Default deny:** anything not on the allowlist is refused.
- **Stops are instant, restarts are gated:** a restart needs a fresh owner approval tied to that specific stop. Missing, expired, or unverifiable approval (e.g. app offline) means the blade stays off.
- **Fail-safe:** if the safety code crashes or loses its sensors, a watchdog cuts the blade. The blade power line also runs through a hardware relay the physical button and watchdog can open directly.
- **Auditability:** every decision is logged with its sensor reading, and a rolling 5-second buffer is saved on each stop for replay.

**Safe practice:** simulator with virtual sensors and a disconnected motor with an indicator light. Real hardware only after consistent simulator results, and only with the blade removed.

**Gateway rule (pseudocode)**
```
on request(cmd, approval):
    if cmd in {cut_blade, brake_blade, halt_wheels}:
        execute(cmd); log(ALLOW); return
    if cmd == restart_blade:
        if approval is fresh AND tied to current stop AND verifiable:
            execute(cmd); log(ALLOW, "fresh approval")
        else:
            log(DENY, reason)   # blade stays off
        return
    log(DENY, "not on allowlist")
```

## Replay method

1. Load the simulated mower environment.
2. Inject fake sensor events in three groups: **hazards** (child enters danger zone, mower lifted, pet detected, app disconnected), **safe work** (hose or flat toy, passer-by outside the zone, small tilt within range, glare), and a **blind spot** (person enters, no sensor fires). Write the expected outcome for each before running.
3. Run the safety layer read-only first and compare its decisions to expectations, then enable stop commands.
4. Capture the 5-second sensor buffer and decision log.
5. Record blade ramp-down time and restart approval state.

## Supporting evidence

Run any script with `python3 simulations/<file>.py`.

| Script | What it tests | Result (assumed timings) |
|---|---|---|
| `01_restart_gate.py` | Restart with no approval, expired approval, app offline, plus a fresh-approval control | All three bad cases denied, blade stayed at 0 RPM, each denial logged with its reason. Control case allowed |
| `02_missed_person_and_lift.py` | Detected person, camera miss with bumper backup, unsafe lift, undetected with no backup | Backup caught the miss and logged it. **Lift case failed** (blade at 24% speed when a hand could reach it). **No-sensor case failed** (nothing stopped, nothing logged) |
| `03_inattentive_owner.py` | Owner has the app open but isn't watching, 10,000 runs | App-dependent design stopped the blade before contact in 0.1% of runs. Auto-stop design in 100% (for hazards the layer detects). Alert arrived in time in under half of runs |

**Example replay, unsafe lift (a failure).** Input: mower lifted at full blade speed; assumed latency 0.02 s, hand-reach time 0.4 s, brake time 0.5 s. Expected: blade at zero before hand reach. Logged: `lift sensor -> cut_blade+halt_wheels`. Result: blade at 24% speed at hand-reach time. The layer acted correctly, but the blade could not stop fast enough. The fix is a faster brake or physical guarding, not better code.

## Limitations

- **Simulation only.** All timings are assumptions. No hardware testing has been done.
- **Blade stop time must be shorter than hand-reach time.** Our lift test failed this under assumed values.
- **Blind spot:** if no sensor fires, nothing stops and nothing is logged. Independent backup sensors reduce this risk but do not remove it.
- **False stops were not measured.** The tests cover hazards only. The replay method includes safe-work scenarios, but they have not been run.
- **Sample record gaps:** the example run did not capture the 5-second buffer or restart state.
- **Restart friction:** the mower stays idle until someone confirms. The real-world cost of this is unknown.
- The comparison with app-dependent designs is our own simulation, not a measurement of any real product.
