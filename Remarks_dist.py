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
scores_4o = [-3, -4, -1, 1, 0, 2, 1, -4, -6, -2, 6, 2, 0, 5, -4, 3, -5, 6, -5, 0, 0, -1, -3, -3, -4]
scores_o4 = [0, 0, -3, 7, 7, 6, 1, 0, 0, 4, 3, 5, 5, 6, 2, 5, 4, 8, 1, 4, -3, 7, 3, 7]
# Plot instellingen
fig, ax = plt.subplots(figsize=(10, 6))
bins = range(min(scores_4o + scores_o4), max(scores_4o + scores_o4) + 2)  # gezamenlijke binrange
# # Plot beide distributies
# sns.histplot(scores_4o, bins=bins, color='blue', label='4o-mini',
#              kde=False, discrete=False, alpha=1, ax=ax, multiple='dodge')

# # sns.histplot(scores_o4, bins=bins, color='orange', label='o4-mini',
# #              kde=False, discrete=False, alpha=1, ax=ax, multiple='dodge')

ax.axvspan(-6, -2, facecolor='red',    alpha=0.35, zorder=0)
ax.axvspan(-2,  0, facecolor='orange', alpha=0.35, zorder=0)
ax.axvspan( 0,  2, facecolor='yellow', alpha=0.35, zorder=0)
ax.axvspan( 2,  9, facecolor='green',  alpha=0.35, zorder=0)


ax.hist(scores_4o, bins=bins, alpha=1, label='4o-mini', color='blue', edgecolor='black')
#ax.hist(scores_o4, bins=bins, alpha=1, label='o4-mini', color='orange', edgecolor='black')
# Labels en titel
plt.title("Remarks distribution")
plt.xlabel("Score")
plt.ylabel("Frequency")
plt.legend()
plt.tight_layout()

# Plot tonen
plt.show()

