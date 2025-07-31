import matplotlib.pyplot as plt
import matplotlib.patches as patches

fig, ax = plt.subplots(figsize=(6, 6))
ax.set_xlim(0.0425, 0.0575)
ax.set_ylim(2.550, 2.425)

# Shaded test
ax.add_patch(patches.Rectangle((0.0425, (2.550+2.425)/2),
                               0.0075, 0.0625,
                               facecolor='lightyellow', alpha=0.3))

ax.add_patch(patches.Rectangle((0.050, (2.550+2.425)/2),
                               0.0075, 0.0625,
                               facecolor='lightblue', alpha=0.3))

plt.show()

