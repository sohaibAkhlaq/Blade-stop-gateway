import random
random.seed(7)
N = 10000

# Assumed placeholders (NOT measured)
T_CONTACT = 1.5          # s from hazard appearing to blade reaching a person
AUTO_DETECT_LAT = 0.1    # s for safety layer to detect + command
BLADE_BRAKE_T = 0.5      # s to reach zero blade speed
ALERT_NET_LAT = (0.3, 3.0)   # s notification delivery (uniform)
# Inattentive owner: app open, eyes elsewhere. Notice time lognormal, median ~6 s; 15% never look in 30 s
def owner_notice_time():
    if random.random() < 0.15: return float("inf")
    return random.lognormvariate(1.8, 0.8)   # median ~6 s

def run(auto_stop):
    protected = 0; alert_in_time = 0; owner_acted_in_time = 0
    for _ in range(N):
        alert_arrives = random.uniform(*ALERT_NET_LAT)
        notice = alert_arrives + owner_notice_time()
        if alert_arrives < T_CONTACT: alert_in_time += 1
        if notice + BLADE_BRAKE_T < T_CONTACT: owner_acted_in_time += 1
        if auto_stop:
            stopped = AUTO_DETECT_LAT + BLADE_BRAKE_T < T_CONTACT
        else:
            stopped = notice + BLADE_BRAKE_T < T_CONTACT
        protected += stopped
    return protected/N*100, alert_in_time/N*100, owner_acted_in_time/N*100

for name, auto in [("App-only (waits for owner)", False), ("Our design (auto-stop)", True)]:
    p, a, o = run(auto)
    print(f"{name:28} blade stopped before contact: {p:5.1f}% | alert arrived in time: {a:5.1f}% | owner acted in time: {o:5.1f}%")
