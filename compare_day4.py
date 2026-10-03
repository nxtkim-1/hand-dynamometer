from statistics import NormalDist

z = -1.44
percentile = NormalDist().cdf(z) * 100
print(f"Estimated percentile: {percentile:.1f}%")
