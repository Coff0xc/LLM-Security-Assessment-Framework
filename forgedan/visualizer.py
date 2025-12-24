# -*- coding: utf-8 -*-
"""
可视化模块
提供攻击结果的图表展示功能
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime


class Visualizer:
    """
    可视化生成器

    功能:
    - 生成HTML可视化报告
    - 适应度进化曲线
    - 攻击成功率统计图
    - 类别分布饼图
    """

    def __init__(self, output_dir: str = "reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_html_report(
        self,
        records: List[Dict],
        history: List[Dict],
        model_name: str = "",
        title: str = "FORGEDAN 安全评估报告"
    ) -> str:
        """生成完整的HTML可视化报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"visual_report_{timestamp}.html"
        filepath = self.output_dir / filename

        # 统计数据
        total = len(records)
        success = len([r for r in records if r.get("success", False)])
        success_rate = success / total * 100 if total > 0 else 0
        avg_fitness = sum(r.get("fitness", 0) for r in records) / total if total > 0 else 0

        # 类别统计
        category_stats = {}
        for r in records:
            cat = r.get("category", "unknown")
            if cat not in category_stats:
                category_stats[cat] = {"total": 0, "success": 0}
            category_stats[cat]["total"] += 1
            if r.get("success", False):
                category_stats[cat]["success"] += 1

        # 进化历史数据
        generations = [h.get("generation", i) for i, h in enumerate(history)]
        fitness_values = [h.get("best_fitness", 0) for h in history]

        html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #eee;
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        .header {{
            text-align: center;
            padding: 30px;
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            margin-bottom: 30px;
        }}
        .header h1 {{ font-size: 2.5em; margin-bottom: 10px; color: #00d4ff; }}
        .header .meta {{ color: #888; font-size: 0.9em; }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: rgba(255,255,255,0.08);
            padding: 25px;
            border-radius: 12px;
            text-align: center;
            transition: transform 0.3s;
        }}
        .stat-card:hover {{ transform: translateY(-5px); }}
        .stat-card .value {{
            font-size: 2.5em;
            font-weight: bold;
            color: #00d4ff;
        }}
        .stat-card .label {{ color: #888; margin-top: 5px; }}
        .stat-card.success .value {{ color: #00ff88; }}
        .stat-card.danger .value {{ color: #ff4757; }}
        .chart-container {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 30px;
            margin-bottom: 30px;
        }}
        .chart-box {{
            background: rgba(255,255,255,0.05);
            padding: 25px;
            border-radius: 15px;
        }}
        .chart-box h3 {{
            margin-bottom: 20px;
            color: #00d4ff;
            font-size: 1.2em;
        }}
        .records-table {{
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            overflow: hidden;
        }}
        .records-table h3 {{
            padding: 20px;
            background: rgba(0,212,255,0.1);
            color: #00d4ff;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            padding: 15px;
            text-align: left;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}
        th {{ background: rgba(255,255,255,0.05); color: #00d4ff; }}
        tr:hover {{ background: rgba(255,255,255,0.03); }}
        .badge {{
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: bold;
        }}
        .badge.success {{ background: rgba(0,255,136,0.2); color: #00ff88; }}
        .badge.fail {{ background: rgba(255,71,87,0.2); color: #ff4757; }}
        .progress-bar {{
            height: 8px;
            background: rgba(255,255,255,0.1);
            border-radius: 4px;
            overflow: hidden;
        }}
        .progress-bar .fill {{
            height: 100%;
            background: linear-gradient(90deg, #00d4ff, #00ff88);
            transition: width 0.5s;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛡️ {title}</h1>
            <div class="meta">
                <p>模型: {model_name or 'N/A'} | 生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            </div>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="value">{total}</div>
                <div class="label">总测试数</div>
            </div>
            <div class="stat-card success">
                <div class="value">{success}</div>
                <div class="label">成功突破</div>
            </div>
            <div class="stat-card danger">
                <div class="value">{success_rate:.1f}%</div>
                <div class="label">突破率</div>
            </div>
            <div class="stat-card">
                <div class="value">{avg_fitness:.3f}</div>
                <div class="label">平均适应度</div>
            </div>
        </div>

        <div class="chart-container">
            <div class="chart-box">
                <h3>📈 适应度进化曲线</h3>
                <canvas id="fitnessChart"></canvas>
            </div>
            <div class="chart-box">
                <h3>📊 类别分布</h3>
                <canvas id="categoryChart"></canvas>
            </div>
        </div>

        <div class="records-table">
            <h3>📋 攻击记录详情</h3>
            <table>
                <thead>
                    <tr>
                        <th>#</th>
                        <th>目标</th>
                        <th>类别</th>
                        <th>适应度</th>
                        <th>状态</th>
                        <th>迭代</th>
                    </tr>
                </thead>
                <tbody>
                    {"".join(self._generate_table_rows(records))}
                </tbody>
            </table>
        </div>
    </div>

    <script>
        // 适应度进化曲线
        new Chart(document.getElementById('fitnessChart'), {{
            type: 'line',
            data: {{
                labels: {json.dumps(generations)},
                datasets: [{{
                    label: '最佳适应度',
                    data: {json.dumps(fitness_values)},
                    borderColor: '#00d4ff',
                    backgroundColor: 'rgba(0,212,255,0.1)',
                    fill: true,
                    tension: 0.4
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{ legend: {{ labels: {{ color: '#eee' }} }} }},
                scales: {{
                    x: {{ ticks: {{ color: '#888' }}, grid: {{ color: 'rgba(255,255,255,0.1)' }} }},
                    y: {{ ticks: {{ color: '#888' }}, grid: {{ color: 'rgba(255,255,255,0.1)' }}, min: 0, max: 1 }}
                }}
            }}
        }});

        // 类别分布饼图
        new Chart(document.getElementById('categoryChart'), {{
            type: 'doughnut',
            data: {{
                labels: {json.dumps(list(category_stats.keys()))},
                datasets: [{{
                    data: {json.dumps([v["total"] for v in category_stats.values()])},
                    backgroundColor: ['#00d4ff', '#00ff88', '#ff4757', '#ffa502', '#a55eea', '#2ed573']
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{ legend: {{ position: 'bottom', labels: {{ color: '#eee' }} }} }}
            }}
        }});
    </script>
</body>
</html>"""

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)

        return str(filepath)

    def _generate_table_rows(self, records: List[Dict]) -> List[str]:
        """生成表格行HTML"""
        rows = []
        for i, r in enumerate(records, 1):
            status = "success" if r.get("success", False) else "fail"
            status_text = "突破" if r.get("success", False) else "拦截"
            goal = r.get("goal", "")[:50] + ("..." if len(r.get("goal", "")) > 50 else "")
            rows.append(f"""
                <tr>
                    <td>{i}</td>
                    <td>{goal}</td>
                    <td>{r.get("category", "N/A")}</td>
                    <td>{r.get("fitness", 0):.4f}</td>
                    <td><span class="badge {status}">{status_text}</span></td>
                    <td>{r.get("generation", 0)}</td>
                </tr>
            """)
        return rows

    def generate_fitness_chart_data(self, history: List[Dict]) -> Dict:
        """生成适应度图表数���"""
        return {
            "labels": [h.get("generation", i) for i, h in enumerate(history)],
            "datasets": [{
                "label": "最佳适应度",
                "data": [h.get("best_fitness", 0) for h in history]
            }]
        }

    def generate_summary_card(self, stats: Dict) -> str:
        """生成摘要卡片HTML"""
        return f"""
        <div class="summary-card">
            <h2>评估摘要</h2>
            <p>总测试: {stats.get('total', 0)}</p>
            <p>成功: {stats.get('success', 0)}</p>
            <p>成功率: {stats.get('rate', 0):.1f}%</p>
        </div>
        """
