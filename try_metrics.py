import fake_data
import metrics

lines = fake_data.max_grip_curve(34.0)
readings = []
for line in lines:
    time_str, force_str = line.split(",")
    readings.append({"time_ms": int(time_str), "force_kg": float(force_str)})

print("Onset:", metrics.find_onset(readings))
print("Peak:", metrics.find_peak(readings))
print("Time to peak (ms):", metrics.time_to_peak_ms(readings))
print("RFD (N/s):", metrics.rfd_n_per_s(readings))