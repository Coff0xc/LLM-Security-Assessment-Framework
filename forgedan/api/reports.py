# -*- coding: utf-8 -*-
"""
报告 API Blueprint

提供报告列表、详情、对比和导出端点。
"""

import json
import csv
import io
from pathlib import Path
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app, send_from_directory
from .auth import require_api_key

reports_bp = Blueprint('reports', __name__, url_prefix='/api/reports')


@reports_bp.route('', methods=['GET'])
def list_reports():
    """报告列表"""
    report_dir = Path(current_app.config['REPORT_DIR'])
    reports = []

    if report_dir.exists():
        for f in sorted(report_dir.glob('*.html'), reverse=True):
            stats = f.stat()
            reports.append({
                'id': f.stem,
                'name': f.name,
                'size': stats.st_size,
                'created': datetime.fromtimestamp(stats.st_ctime).isoformat(),
            })

    return jsonify(reports)


@reports_bp.route('/<report_id>', methods=['GET'])
def get_report(report_id):
    """获取报告详情/内容"""
    report_dir = current_app.config['REPORT_DIR']
    filename = report_id if '.' in report_id else f"{report_id}.html"

    # 路径遍历防护
    if '..' in filename or filename.startswith(('/', '\\')):
        return jsonify({'error': 'Invalid filename', 'code': 'INVALID_FILENAME'}), 400
    safe_name = Path(filename).name
    if safe_name != filename:
        return jsonify({'error': 'Invalid filename', 'code': 'INVALID_FILENAME'}), 400

    try:
        return send_from_directory(report_dir, safe_name)
    except FileNotFoundError:
        return jsonify({'error': 'Report not found', 'code': 'REPORT_NOT_FOUND'}), 404


@reports_bp.route('/compare', methods=['GET'])
def compare_reports():
    """对比两份报告"""
    report_a = request.args.get('a', '')
    report_b = request.args.get('b', '')

    if not report_a or not report_b:
        return jsonify({'error': 'Provide both a and b report IDs', 'code': 'MISSING_PARAMS'}), 400

    log_dir = Path(current_app.config['LOG_DIR'])

    def _load_report_data(report_id):
        """从日志目录加载与报告关联的数据"""
        for f in log_dir.glob('*.json'):
            if report_id in f.stem:
                try:
                    with open(f, 'r', encoding='utf-8') as fh:
                        return json.load(fh)
                except Exception:
                    pass
        return None

    data_a = _load_report_data(report_a)
    data_b = _load_report_data(report_b)

    if not data_a or not data_b:
        return jsonify({'error': 'Could not load report data', 'code': 'REPORT_DATA_MISSING'}), 404

    def _summarize(data):
        records = data if isinstance(data, list) else data.get('records', [])
        total = len(records)
        success = sum(1 for r in records if r.get('success', False))
        return {
            'total': total, 'success': success,
            'rate': success / total * 100 if total > 0 else 0,
        }

    return jsonify({
        'report_a': {'id': report_a, 'summary': _summarize(data_a)},
        'report_b': {'id': report_b, 'summary': _summarize(data_b)},
    })


@reports_bp.route('/export', methods=['POST'])
@require_api_key
def export_report():
    """导出报告为 JSON 或 CSV"""
    data = request.get_json() or {}
    fmt = data.get('format', 'json')

    log_dir = Path(current_app.config['LOG_DIR'])
    all_records = []

    for f in sorted(log_dir.glob('*.json'), reverse=True):
        try:
            with open(f, 'r', encoding='utf-8') as fh:
                raw = json.load(fh)
                records = raw if isinstance(raw, list) else raw.get('records', [])
                all_records.extend(records)
        except Exception:
            continue

    if fmt == 'json':
        return jsonify({
            'export_time': datetime.now().isoformat(),
            'total_records': len(all_records),
            'records': all_records,
        })
    elif fmt == 'csv':
        output = io.StringIO()
        if all_records:
            writer = csv.DictWriter(output, fieldnames=all_records[0].keys())
            writer.writeheader()
            writer.writerows(all_records)
        response = current_app.response_class(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=forgedan_report.csv'},
        )
        return response
    else:
        return jsonify({'error': f'Unsupported format: {fmt}', 'code': 'INVALID_FORMAT'}), 400
