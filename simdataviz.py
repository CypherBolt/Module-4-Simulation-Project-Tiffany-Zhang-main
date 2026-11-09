from math import pi, cos, sin
from itertools import accumulate
from bokeh.plotting import figure, show, output_file
from bokeh.transform import cumsum
from bokeh.models import ColumnDataSource
import random

DATA_FILE = "sim3_data.txt"

#load one infection time (in seconds) per line
with open(DATA_FILE) as f:
    times = [float(line.strip()) for line in f if line.strip()]

#group trials into 5-second-wide infection-time ranges (e.g. "10-15s")
bucket_width = 5
max_bucket_start = (int(max(times) // bucket_width) + 1) * bucket_width

labels = []
counts = []
for low in range(0, max_bucket_start, bucket_width):
    high = low + bucket_width
    count = sum(1 for t in times if low <= t < high)
    if count > 0:
        labels.append(f"{low}-{high}s")
        counts.append(count)

total = len(times)
angles = [count / total * 2 * pi for count in counts]
pcts = [count / total * 100 for count in counts]
colors = [(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)) for i in range(len(labels))]
#each slice will have a different color, matched with the # of slices there are from labels

source = ColumnDataSource(data=dict(label=labels, count=counts, angle=angles, pct=pcts, color=colors))
#this will allow us to easily reference the data in the plot

output_file("sim3_visualization.html", title="Sim 3 Simulation Results")
#output to an HTML file

pie_chart = figure(
    title=f"Sim 3: Trials by Infection Time Range ({total} trials, data: {DATA_FILE})",
    x_range=(-0.5, 1.0),
    width=600,
    height=500,
)
pie_chart.wedge(
    x=0, y=1, radius=0.4,
    start_angle=cumsum("angle", include_zero=True), end_angle=cumsum("angle"),
    line_color="white", fill_color="color", legend_field="label",
    source=source,
)

#place a percentage label at the midpoint angle of each slice
cumulative_angles = list(accumulate(angles, initial=0))
mid_angles = [(cumulative_angles[i] + cumulative_angles[i + 1]) / 2 for i in range(len(angles))]
label_x = [0 + 0.28 * cos(a) for a in mid_angles]
label_y = [1 + 0.28 * sin(a) for a in mid_angles]
label_text = [f"{p:.1f}%" for p in pcts]

pie_chart.text(
    x=label_x, y=label_y, text=label_text,
    text_align="center", text_baseline="middle", text_font_size="10pt",
)

pie_chart.axis.axis_label = None
pie_chart.axis.visible = False
pie_chart.grid.grid_line_color = None

show(pie_chart)
