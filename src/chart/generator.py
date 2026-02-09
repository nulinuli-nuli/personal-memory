"""Chart generation using Plotly."""
from datetime import date
from pathlib import Path
from typing import List, Optional

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS']
    matplotlib.rcParams['axes.unicode_minus'] = False
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

from src.core.schemas_chart import ChartData, ChartDataPoint, ChartRequest


class ChartGenerator:
    """Generate financial charts using Plotly."""

    # Color schemes (hex format for both plotly and matplotlib)
    CATEGORY_COLORS = [
        "#8dd3c7", "#ffffb3", "#bebada", "#fb8072", "#80b1d3",
        "#fdb462", "#b3de69", "#fccde5", "#d9d9d9", "#bc80bd"
    ]
    INCOME_COLOR = "#2ecc71"
    EXPENSE_COLOR = "#e74c3c"

    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize chart generator.

        Args:
            output_dir: Directory to save chart files (defaults to data/charts)
        """
        if not PLOTLY_AVAILABLE:
            raise ImportError(
                "Plotly is not installed. Please install it with: pip install plotly kaleido"
            )

        if output_dir is None:
            from src.config import settings
            output_dir = settings.data_dir / "charts"
        output_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir = output_dir

    def generate(
        self,
        data: List[ChartDataPoint],
        config: ChartRequest,
    ) -> go.Figure:
        """
        Generate a chart based on data and configuration.

        Args:
            data: Chart data points
            config: Chart configuration

        Returns:
            Plotly Figure object
        """
        chart_type = config.chart_type

        if chart_type == "pie":
            return self._generate_pie_chart(data, config)
        elif chart_type == "bar":
            return self._generate_bar_chart(data, config)
        elif chart_type == "line":
            return self._generate_line_chart(data, config)
        elif chart_type == "area":
            return self._generate_area_chart(data, config)
        elif chart_type == "stacked_bar":
            return self._generate_stacked_bar_chart(data, config)
        elif chart_type == "scatter":
            return self._generate_scatter_chart(data, config)
        else:
            raise ValueError(f"Unsupported chart type: {chart_type}")

    def _generate_pie_chart(
        self,
        data: List[ChartDataPoint],
        config: ChartRequest,
    ) -> go.Figure:
        """Generate a pie chart."""
        labels = [d.label for d in data]
        values = [d.value for d in data]

        # Calculate percentages for labels
        total = sum(values)
        text_labels = [
            f"{label}<br>¥{value:.2f} ({value/total*100:.1f}%)"
            for label, value in zip(labels, values)
        ]

        fig = go.Figure(data=[
            go.Pie(
                labels=labels,
                values=values,
                textinfo="label+percent",
                hovertemplate="%{label}<br>金额: ¥%{value:.2f}<br>占比: %{percent}<extra></extra>",
                marker=dict(colors=self.CATEGORY_COLORS[:len(data)]),
            )
        ])

        fig.update_layout(
            title=dict(text=config.chart_title, x=0.5, xanchor="center"),
            font=dict(family="Microsoft YaHei, Arial, sans-serif", size=14),
            showlegend=True,
            height=600,
        )

        return fig

    def _generate_bar_chart(
        self,
        data: List[ChartDataPoint],
        config: ChartRequest,
    ) -> go.Figure:
        """Generate a bar chart."""
        labels = [d.label for d in data]
        values = [d.value for d in data]

        # Apply color scheme
        if config.color_scheme == "type":
            colors = [
                self.INCOME_COLOR if ("收入" in str(d.label) or "income" in str(d.label).lower())
                else self.EXPENSE_COLOR
                for d in data
            ]
        else:
            colors = self.CATEGORY_COLORS[:len(data)]

        fig = go.Figure(data=[
            go.Bar(
                x=labels,
                y=values,
                marker=dict(color=colors),
                text=[f"¥{v:.2f}" for v in values],
                textposition="auto",
                hovertemplate="%{x}<br>金额: ¥%{y:.2f}<extra></extra>",
            )
        ])

        fig.update_layout(
            title=dict(text=config.chart_title, x=0.5, xanchor="center"),
            xaxis_title=config.x_axis_label,
            yaxis_title=config.y_axis_label,
            font=dict(family="Microsoft YaHei, Arial, sans-serif", size=14),
            height=600,
        )

        return fig

    def _generate_line_chart(
        self,
        data: List[ChartDataPoint],
        config: ChartRequest,
    ) -> go.Figure:
        """Generate a line chart."""
        # Sort by date/label for line charts
        sorted_data = sorted(
            data,
            key=lambda d: str(d.date) if d.date else str(d.label)
        )

        labels = [d.label for d in sorted_data]
        values = [d.value for d in sorted_data]

        fig = go.Figure(data=[
            go.Scatter(
                x=labels,
                y=values,
                mode="lines+markers",
                line=dict(width=3, color="#3498db"),
                marker=dict(size=8),
                hovertemplate="%{x}<br>金额: ¥%{y:.2f}<extra></extra>",
            )
        ])

        fig.update_layout(
            title=dict(text=config.chart_title, x=0.5, xanchor="center"),
            xaxis_title=config.x_axis_label,
            yaxis_title=config.y_axis_label,
            font=dict(family="Microsoft YaHei, Arial, sans-serif", size=14),
            height=600,
            hovermode="x unified",
        )

        return fig

    def _generate_area_chart(
        self,
        data: List[ChartDataPoint],
        config: ChartRequest,
    ) -> go.Figure:
        """Generate an area chart."""
        sorted_data = sorted(
            data,
            key=lambda d: str(d.date) if d.date else str(d.label)
        )

        labels = [d.label for d in sorted_data]
        values = [d.value for d in sorted_data]

        fig = go.Figure(data=[
            go.Scatter(
                x=labels,
                y=values,
                fill="tozeroy",
                mode="lines",
                line=dict(width=2, color="#3498db"),
                fillcolor="rgba(52, 152, 219, 0.3)",
                hovertemplate="%{x}<br>金额: ¥%{y:.2f}<extra></extra>",
            )
        ])

        fig.update_layout(
            title=dict(text=config.chart_title, x=0.5, xanchor="center"),
            xaxis_title=config.x_axis_label,
            yaxis_title=config.y_axis_label,
            font=dict(family="Microsoft YaHei, Arial, sans-serif", size=14),
            height=600,
        )

        return fig

    def _generate_stacked_bar_chart(
        self,
        data: List[ChartDataPoint],
        config: ChartRequest,
    ) -> go.Figure:
        """Generate a stacked bar chart (for grouped data)."""
        # Group data by category
        grouped = {}
        for d in data:
            cat = d.category or "默认"
            if cat not in grouped:
                grouped[cat] = []
            grouped[cat].append(d)

        fig = go.Figure()

        for i, (category, items) in enumerate(grouped.items()):
            fig.add_trace(
                go.Bar(
                    name=category,
                    x=[d.label for d in items],
                    y=[d.value for d in items],
                    marker=dict(color=self.CATEGORY_COLORS[i % len(self.CATEGORY_COLORS)]),
                )
            )

        fig.update_layout(
            title=dict(text=config.chart_title, x=0.5, xanchor="center"),
            xaxis_title=config.x_axis_label,
            yaxis_title=config.y_axis_label,
            barmode="stack",
            font=dict(family="Microsoft YaHei, Arial, sans-serif", size=14),
            height=600,
        )

        return fig

    def _generate_scatter_chart(
        self,
        data: List[ChartDataPoint],
        config: ChartRequest,
    ) -> go.Figure:
        """Generate a scatter chart."""
        max_value = max([d.value for d in data]) if data else 1

        fig = go.Figure(data=[
            go.Scatter(
                x=[d.label for d in data],
                y=[d.value for d in data],
                mode="markers",
                marker=dict(
                    size=[max(10, d.value / max_value * 30) for d in data],
                    color=self.CATEGORY_COLORS[:len(data)],
                ),
                hovertemplate="%{x}<br>金额: ¥%{y:.2f}<extra></extra>",
            )
        ])

        fig.update_layout(
            title=dict(text=config.chart_title, x=0.5, xanchor="center"),
            xaxis_title=config.x_axis_label,
            yaxis_title=config.y_axis_label,
            font=dict(family="Microsoft YaHei, Arial, sans-serif", size=14),
            height=600,
        )

        return fig

    def save_html(self, fig: go.Figure, filename: str) -> Path:
        """
        Save chart as HTML file.

        Args:
            fig: Plotly Figure
            filename: Output filename (without extension)

        Returns:
            Path to saved file
        """
        output_path = self.output_dir / f"{filename}.html"
        fig.write_html(str(output_path), include_plotlyjs="cdn")
        return output_path

    def save_png(self, fig: go.Figure, filename: str) -> Path:
        """
        Save chart as PNG image (requires kaleido).

        Args:
            fig: Plotly Figure
            filename: Output filename (without extension)

        Returns:
            Path to saved file
        """
        output_path = self.output_dir / f"{filename}.png"
        try:
            fig.write_image(str(output_path), engine="kaleido", width=1200, height=600)
            return output_path
        except Exception as e:
            raise ImportError(
                f"PNG export failed. Please install kaleido: pip install kaleido. Error: {e}"
            )

    def open_in_browser(self, fig: go.Figure, filename: str) -> None:
        """
        Save chart as HTML and open in default browser.

        Args:
            fig: Plotly Figure
            filename: Output filename (without extension)
        """
        import webbrowser
        output_path = self.save_html(fig, filename)
        webbrowser.open(f"file:///{output_path.absolute()}")

    def show_window(
        self,
        data: List[ChartDataPoint],
        config: ChartRequest,
    ) -> None:
        """
        Display chart in a popup window using matplotlib.

        Args:
            data: Chart data points
            config: Chart configuration
        """
        if not MATPLOTLIB_AVAILABLE:
            raise ImportError(
                "Matplotlib is not installed. Please install it with: pip install matplotlib"
            )

        chart_type = config.chart_type
        labels = [d.label for d in data]
        values = [d.value for d in data]

        # Create figure
        fig, ax = plt.subplots(figsize=(12, 7))

        if chart_type == "pie":
            # Pie chart
            colors = self.CATEGORY_COLORS[:len(data)]
            wedges, texts, autotexts = ax.pie(
                values,
                labels=labels,
                autopct='%1.1f%%',
                colors=colors,
                startangle=90,
            )
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontsize(10)
                autotext.set_fontweight('bold')

        elif chart_type == "bar":
            # Bar chart
            if config.color_scheme == "type":
                colors = [
                    self.INCOME_COLOR if ("收入" in str(d.label) or "income" in str(d.label).lower())
                    else self.EXPENSE_COLOR
                    for d in data
                ]
            else:
                colors = self.CATEGORY_COLORS[:len(data)]

            bars = ax.bar(labels, values, color=colors)
            ax.bar_label(bars, fmt='¥%.2f')

        elif chart_type == "line":
            # Line chart
            sorted_data = sorted(
                data,
                key=lambda d: str(d.date) if d.date else str(d.label)
            )
            labels = [d.label for d in sorted_data]
            values = [d.value for d in sorted_data]

            ax.plot(labels, values, marker='o', linewidth=2, markersize=8, color='#3498db')
            ax.grid(True, alpha=0.3)

        elif chart_type == "area":
            # Area chart
            sorted_data = sorted(
                data,
                key=lambda d: str(d.date) if d.date else str(d.label)
            )
            labels = [d.label for d in sorted_data]
            values = [d.value for d in sorted_data]

            ax.fill_between(labels, values, alpha=0.3, color='#3498db')
            ax.plot(labels, values, marker='o', linewidth=2, markersize=6, color='#3498db')
            ax.grid(True, alpha=0.3)

        elif chart_type == "stacked_bar":
            # Stacked bar chart
            grouped = {}
            for d in data:
                cat = d.category or "默认"
                if cat not in grouped:
                    grouped[cat] = {'labels': [], 'values': []}
                grouped[cat]['labels'].append(d.label)
                grouped[cat]['values'].append(d.value)

            bottom = [0] * len(data)
            for i, (cat, items) in enumerate(grouped.items()):
                values = items['values']
                labels = items['labels']
                ax.bar(labels, values, bottom=bottom, label=cat, color=self.CATEGORY_COLORS[i % len(self.CATEGORY_COLORS)])
                bottom = [b + v for b, v in zip(bottom, values)]
            ax.legend()

        elif chart_type == "scatter":
            # Scatter chart
            max_value = max(values) if values else 1
            sizes = [max(100, v / max_value * 500) for v in values]
            ax.scatter(labels, values, s=sizes, c=self.CATEGORY_COLORS[:len(data)], alpha=0.6)

        # Set labels and title
        ax.set_xlabel(config.x_axis_label, fontsize=12)
        ax.set_ylabel(config.y_axis_label, fontsize=12)
        ax.set_title(config.chart_title, fontsize=14, fontweight='bold', pad=20)

        # Rotate x-axis labels if needed
        if len(labels) > 5 or max(len(str(l)) for l in labels) > 8:
            plt.xticks(rotation=45, ha='right')

        plt.tight_layout()

        # Show window
        plt.show()
