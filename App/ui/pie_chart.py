import matplotlib.pyplot as plt
from datetime import datetime

def draw_pie_chart(stats):
    all_labels = ['Richtig', 'Falsch', 'Unsicher', 'Unbekannt']
    all_colors = ['#4CAF50', '#FFC107', '#F44336', '#9E9E9E']
    all_sizes = [
        stats.get('richtig', 0),
        stats.get('falsch', 0),
        stats.get('unsicher', 0),
        stats.get('unbekannt', 0)
    ]

    if sum(all_sizes) == 0:
        fig, ax = plt.subplots(figsize=(3, 3), dpi=100)
        ax.text(0.5, 0.5, 'Keine Lernstatistikdaten\nvorhanden',
                horizontalalignment='center',
                verticalalignment='center',
                fontsize=12, color='gray', transform=ax.transAxes)
        ax.axis('off')
        return fig

    fig, ax = plt.subplots(figsize=(3, 3), dpi=100)

    wedges, texts, autotexts = ax.pie(
        all_sizes,
        labels=None,
        autopct=lambda pct: f'{pct:.1f}%' if pct > 0 else '',
        colors=all_colors,
        startangle=90
    )
    ax.axis('equal')

    timestamp_str = stats.get('timestamp')
    if timestamp_str:
        try:
            ts = datetime.fromisoformat(timestamp_str)
            date_str = ts.strftime('%d.%m.%Y')
            time_str = ts.strftime('%H:%M')
        except ValueError:
            date_str = ''
            time_str = ''
    else:
        date_str = ''
        time_str = ''

    ax.text(0.5, 1.00, "Letzter Lernfortschritt", transform=ax.transAxes,
            ha='center', va='bottom', fontsize=20, fontweight='bold')
    if date_str and time_str:
        ax.text(0.5, 0.95, f"vom {date_str} um {time_str}", transform=ax.transAxes,
                ha='center', va='bottom', fontsize=16, color='gray')
    else:
        ax.text(0.5, 0.95, "Datum und Uhrzeit nicht verfügbar", transform=ax.transAxes,
                ha='center', va='bottom', fontsize=11, color='gray')

    # Legende direkt unter dem Kreis, innerhalb des Figures
    ax.legend(
        wedges,
        all_labels,
        loc='upper center',
        bbox_to_anchor=(0.5, 0.08), 
        ncol=2,
        frameon=False,
        fontsize=10,
        handlelength=1.0,
        columnspacing=2.5
    )

    return fig


