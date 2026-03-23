# -*- coding: utf-8 -*-
"""
网站测试 API Blueprint

提供 URL 爬取、Web 安全扫描和 LLM 驱动交互测试端点。
"""

import threading
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from .auth import require_api_key

webscan_bp = Blueprint('webscan', __name__, url_prefix='/api/webscan')


def _get_task_manager():
    return current_app.extensions['task_manager']


@webscan_bp.route('/crawl', methods=['POST'])
@require_api_key
def crawl_url():
    """URL 爬取"""
    data = request.get_json() or {}
    url = data.get('url', '')
    max_depth = data.get('max_depth', 2)
    max_pages = data.get('max_pages', 50)

    if not url:
        return jsonify({'error': 'Missing url parameter', 'code': 'MISSING_URL'}), 400

    task_manager = _get_task_manager()
    params = {'url': url, 'max_depth': max_depth, 'max_pages': max_pages}
    task_id, is_new = task_manager.create_task('crawl', params)

    if not is_new:
        return jsonify({'task_id': task_id, 'message': 'Duplicate crawl running', 'is_duplicate': True})

    def _run():
        try:
            task_manager.update_task(task_id, status='running')

            try:
                from forgedan.web_scanner import WebCrawler
                crawler = WebCrawler(max_depth=max_depth, max_pages=max_pages)
                result = crawler.crawl(url)
                task_manager.update_task(task_id, status='completed', result={
                    'url': url,
                    'pages_found': len(result.get('pages', [])),
                    'forms_found': len(result.get('forms', [])),
                    'links': result.get('links', [])[:100],
                    'pages': result.get('pages', []),
                })
            except ImportError:
                task_manager.update_task(task_id, status='completed', result={
                    'url': url,
                    'message': 'Web scanner module not available. Install forgedan[webscan] for full support.',
                    'pages_found': 0,
                })
        except Exception as e:
            task_manager.update_task(task_id, status='failed', error=str(e))

    threading.Thread(target=_run, daemon=True).start()
    return jsonify({'task_id': task_id, 'message': 'Crawl started', 'is_duplicate': False})


@webscan_bp.route('/scan', methods=['POST'])
@require_api_key
def web_scan():
    """Web 安全扫描"""
    data = request.get_json() or {}
    url = data.get('url', '')
    scan_type = data.get('scan_type', 'basic')

    if not url:
        return jsonify({'error': 'Missing url parameter', 'code': 'MISSING_URL'}), 400

    task_manager = _get_task_manager()
    params = {'url': url, 'scan_type': scan_type}
    task_id, is_new = task_manager.create_task('webscan', params)

    if not is_new:
        return jsonify({'task_id': task_id, 'message': 'Duplicate scan running', 'is_duplicate': True})

    def _run():
        try:
            task_manager.update_task(task_id, status='running')

            try:
                from forgedan.web_scanner import WebSecurityScanner
                scanner = WebSecurityScanner()
                result = scanner.scan(url, scan_type=scan_type)
                task_manager.update_task(task_id, status='completed', result=result)
            except ImportError:
                task_manager.update_task(task_id, status='completed', result={
                    'url': url,
                    'message': 'Web scanner module not available.',
                    'vulnerabilities': [],
                })
        except Exception as e:
            task_manager.update_task(task_id, status='failed', error=str(e))

    threading.Thread(target=_run, daemon=True).start()
    return jsonify({'task_id': task_id, 'message': 'Scan started', 'is_duplicate': False})


@webscan_bp.route('/llm-test', methods=['POST'])
@require_api_key
def llm_interaction_test():
    """LLM 驱动交互测试"""
    data = request.get_json() or {}
    url = data.get('url', '')
    model = data.get('model', 'mock:test-model')
    test_scenarios = data.get('scenarios', ['xss', 'sqli', 'prompt_injection'])

    if not url:
        return jsonify({'error': 'Missing url parameter', 'code': 'MISSING_URL'}), 400

    task_manager = _get_task_manager()
    params = {'url': url, 'model': model, 'scenarios': test_scenarios}
    task_id, is_new = task_manager.create_task('llm_webscan', params)

    if not is_new:
        return jsonify({'task_id': task_id, 'message': 'Duplicate test running', 'is_duplicate': True})

    def _run():
        try:
            task_manager.update_task(task_id, status='running')

            try:
                from forgedan.web_scanner import LLMWebTester
                tester = LLMWebTester(model=model)
                result = tester.test(url, scenarios=test_scenarios)
                task_manager.update_task(task_id, status='completed', result=result)
            except ImportError:
                task_manager.update_task(task_id, status='completed', result={
                    'url': url,
                    'message': 'LLM web tester module not available.',
                    'findings': [],
                })
        except Exception as e:
            task_manager.update_task(task_id, status='failed', error=str(e))

    threading.Thread(target=_run, daemon=True).start()
    return jsonify({'task_id': task_id, 'message': 'LLM test started', 'is_duplicate': False})


@webscan_bp.route('/status/<task_id>', methods=['GET'])
def scan_status(task_id):
    """扫描状态"""
    task = _get_task_manager().get_task(task_id)
    if not task:
        return jsonify({'error': 'Task not found', 'code': 'TASK_NOT_FOUND'}), 404
    return jsonify(task.to_dict())
