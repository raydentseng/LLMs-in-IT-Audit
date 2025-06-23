import matplotlib.pyplot as plt
import seaborn as sns
plt.rcParams.update({
    'axes.titlesize': 18,
    'axes.labelsize': 16,
    'xtick.labelsize': 14,
    'ytick.labelsize': 14,
    'legend.fontsize': 14
})
# Gegeven scores
scores_4o = [-3, -2, -3, 2, 0, 1, -2, -4, -2, -1, 2, 0, 0, -2, -2, 3, 0, -4, -4, -2, -3, -3, -3, -4]
scores_o4 = [4, 3, 2, 2, 2, 1, -1, 2, 0, 1, 2, 2, 4, 0, 3, 0, -1, -1, 2, 2, 3, -2, 3, 0]
# Plot instellingen
fig, ax = plt.subplots(figsize=(10, 6))
bins = range(min(scores_4o + scores_o4), max(scores_4o + scores_o4) + 2)  # gezamenlijke binrange

# Plot beide distributies
sns.histplot(scores_4o, bins=bins, color='blue', label='4o-mini', kde=False, discrete=False, alpha=1, ax=ax)
#sns.histplot(scores_o4, bins=bins, color='orange', label='o4-mini', kde=False, discrete=False, alpha=1, ax=ax)


ax.axvspan(-4, -2, facecolor='red',    alpha=0.35, zorder=0)
ax.axvspan(-2,  0, facecolor='orange', alpha=0.35, zorder=0)
ax.axvspan( 0,  2, facecolor='yellow', alpha=0.35, zorder=0)
ax.axvspan( 2,  5, facecolor='green',  alpha=0.35, zorder=0)

# Labels en titel
plt.title("Completeness distribution")
plt.xlabel("Score")
plt.ylabel("Frequency")
plt.legend()
plt.tight_layout()

# Plot tonen
plt.show()