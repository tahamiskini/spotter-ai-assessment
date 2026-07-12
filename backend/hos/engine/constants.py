"""All FMCSA Hours-of-Service numeric limits in one place.

Scope: property-carrying interstate drivers on the 70-hour / 8-day cycle,
no adverse-condition exception, split-sleeper deferred.  Every magic number
the planner relies on lives here so the rules are auditable at a glance.
"""

# --- Driving / shift limits (hours) ---------------------------------------
MAX_DRIVE_HOURS = 11.0          # 11h driving limit after 10h off
MAX_WINDOW_HOURS = 14.0         # 14h on-duty window (wall clock, not extendable)
DRIVE_BEFORE_BREAK_HOURS = 8.0  # 30-min break required after 8h cumulative driving

# --- Rest periods (hours) --------------------------------------------------
BREAK_HOURS = 0.5               # the mandatory 30-minute break
RESET_HOURS = 10.0              # 10 consecutive hours off resets shift + window
RESTART_HOURS = 34.0            # 34 consecutive hours off resets the cycle

# Any non-driving period at least this long satisfies the 30-min break rule.
MIN_BREAK_QUALIFYING_HOURS = 0.5

# --- Cycle (rolling on-duty) ----------------------------------------------
MAX_CYCLE_HOURS = 70.0          # 70h on-duty in any 8 consecutive days
CYCLE_WINDOW_DAYS = 8           # today + prior 7 calendar days

# --- Fuel ------------------------------------------------------------------
FUEL_INTERVAL_MILES = 1000.0    # refuel at least every 1,000 miles
FUEL_STOP_HOURS = 0.5           # modelled as a 30-min on-duty (not driving) stop

# --- Activities at pickup / dropoff ---------------------------------------
PICKUP_HOURS = 1.0              # 1h on-duty loading
DROPOFF_HOURS = 1.0             # 1h on-duty unloading

# Floating-point slack so "== limit" comparisons are robust.
EPS = 1e-6
