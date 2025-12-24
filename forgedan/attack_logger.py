# -*- coding: utf-8 -*-
"""
攻击日志记录模块
记录每次测试评估中攻击成功的详细信息
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict


@dataclass
class AttackRecord:
    """单次攻击记录"""
    timestamp: str
    goal: str
    template: str
    prompt: str
    response: str
    fitness: float
    success: bool
    generation: int
    total_queries: int
    model_name: str = ""
    category: str = ""
    severity: int = 0


class AttackLogger:
    """
    攻击日志记录器

    功能:
    - 记录每次成功/失败的攻击
    - 按日期/模型/类别组织日志
    - 支持JSON��Markdown格式导出
    """

    def __init__(self, log_dir: str = "logs/attacks"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.records: List[AttackRecord] = []
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    def log_attack(
        self,
        goal: str,
        template: str,
        prompt: str,
        response: str,
        fitness: float,
        success: bool,
        generation: int = 0,
        total_queries: int = 0,
        model_name: str = "",
        category: str = "",
        severity: int = 0
    ) -> AttackRecord:
        """记录一次攻击"""
        record = AttackRecord(
            timestamp=datetime.now().isoformat(),
            goal=goal,
            template=template,
            prompt=prompt,
            response=response,
            fitness=fitness,
            success=success,
            generation=generation,
            total_queries=total_queries,
            model_name=model_name,
            category=category,
            severity=severity
        )
        self.records.append(record)

        # 成功攻击立即保存
        if success:
            self._save_success_log(record)

        return record

    def _save_success_log(self, record: AttackRecord):
        """保存成功攻击日志"""
        # 按日期和模型组织目录
        date_str = datetime.now().strftime("%Y-%m-%d")
        model_dir = record.model_name.replace(":", "_").replace("/", "_") or "unknown"

        success_dir = self.log_dir / "success" / date_str / model_dir
        success_dir.mkdir(parents=True, exist_ok=True)

        # 生成文件名
        filename = f"{self.session_id}_{len([r for r in self.records if r.success])}.json"
        filepath = success_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(asdict(record), f, ensure_ascii=False, indent=2)

    def save_session(self, filename: Optional[str] = None) -> str:
        """保存整个会话日志"""
        if not filename:
            filename = f"session_{self.session_id}.json"

        filepath = self.log_dir / filename

        data = {
            "session_id": self.session_id,
            "total_attacks": len(self.records),
            "successful_attacks": len([r for r in self.records if r.success]),
            "records": [asdict(r) for r in self.records]
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return str(filepath)

    def export_markdown_report(self, filename: Optional[str] = None) -> str:
        """导出Markdown格式报告"""
        if not filename:
            filename = f"report_{self.session_id}.md"

        filepath = self.log_dir / filename

        success_records = [r for r in self.records if r.success]
        success_rate = len(success_records) / len(self.records) * 100 if self.records else 0

        md_content = f"""# 攻击日志报告

**会话ID**: {self.session_id}
**生成时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## 统计摘要

| 指标 | 数值 |
|------|------|
| 总攻击次数 | {len(self.records)} |
| 成功次数 | {len(success_records)} |
| 成功率 | {success_rate:.1f}% |
| 平均适应度 | {sum(r.fitness for r in self.records) / len(self.records) if self.records else 0:.4f} |

## 成功攻击详情

"""
        for i, record in enumerate(success_records, 1):
            md_content += f"""### 攻击 #{i}

- **时间**: {record.timestamp}
- **目标**: {record.goal}
- **模型**: {record.model_name or 'N/A'}
- **类别**: {record.category or 'N/A'}
- **适应度**: {record.fitness:.4f}
- **迭代次数**: {record.generation}
- **查询次数**: {record.total_queries}

**攻击提示**:
```
{record.prompt[:500]}{'...' if len(record.prompt) > 500 else ''}
```

**模型响应**:
```
{record.response[:500]}{'...' if len(record.response) > 500 else ''}
```

---

"""

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(md_content)

        return str(filepath)

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        if not self.records:
            return {"total": 0, "success": 0, "rate": 0}

        success_records = [r for r in self.records if r.success]

        # 按类别统计
        category_stats = {}
        for r in self.records:
            cat = r.category or "unknown"
            if cat not in category_stats:
                category_stats[cat] = {"total": 0, "success": 0}
            category_stats[cat]["total"] += 1
            if r.success:
                category_stats[cat]["success"] += 1

        return {
            "total": len(self.records),
            "success": len(success_records),
            "rate": len(success_records) / len(self.records) * 100,
            "avg_fitness": sum(r.fitness for r in self.records) / len(self.records),
            "avg_queries": sum(r.total_queries for r in self.records) / len(self.records),
            "by_category": category_stats
        }
