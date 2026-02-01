# -*- coding: utf-8 -*-
"""
FORGEDAN Web 应用启动脚本

启动实时监控仪表盘（支持 WebSocket）
"""

import sys
import os

# Windows 控制台编码修复
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from forgedan.web.app import create_app

if __name__ == '__main__':
    app, socketio = create_app()

    print("\n" + "=" * 60)
    print("[*] LLM Black-box Jailbreak - Real-time Dashboard")
    print("=" * 60)
    print("\n[Dashboard]  http://127.0.0.1:5000")
    print("[Test]       http://127.0.0.1:5000/test")
    print("[Reports]    http://127.0.0.1:5000/reports")
    print("[Settings]   http://127.0.0.1:5000/settings")
    if socketio:
        print("[WebSocket]  ws://127.0.0.1:5000/evolution")
    print("\n" + "-" * 60)
    print("Press Ctrl+C to stop the server")
    print("-" * 60 + "\n")

    # 使用 SocketIO 启动（如果可用）
    if socketio:
        socketio.run(
            app,
            debug=True,
            host='127.0.0.1',
            port=5000,
            use_reloader=False
        )
    else:
        app.run(
            debug=True,
            host='127.0.0.1',
            port=5000,
            threaded=True,
            use_reloader=False
        )
