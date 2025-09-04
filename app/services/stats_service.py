from __future__ import annotations

from typing import Dict, List, Any
from datetime import datetime, timedelta
import logging

from ..database import DatabaseManager
from .openai_service import OpenAIService

logger = logging.getLogger(__name__)


class StatsService:
    def __init__(self, db: DatabaseManager, ai: OpenAIService) -> None:
        self.db = db
        self.ai = ai

    def _compute_core_metrics(self, assignments: List[Dict[str, Any]], employees: List[Dict[str, Any]], patients: List[Dict[str, Any]]) -> Dict[str, Any]:
        total_assignments = len(assignments)
        total_travel_minutes = sum(a.get('travel_time') or 0 for a in assignments)
        total_service_minutes = sum((a.get('duration') or a.get('estimated_duration') or 0) for a in assignments)
        avg_service_minutes = (total_service_minutes / total_assignments) if total_assignments else 0
        avg_travel_minutes = (total_travel_minutes / total_assignments) if total_assignments else 0

        # Simple optimization proxies
        # Assume baseline travel 20 min per assignment
        baseline_travel_minutes = 20 * total_assignments
        travel_time_saved = max(0, baseline_travel_minutes - total_travel_minutes)

        # Resource utilization: assignments per employee
        assignments_by_employee: Dict[str, int] = {}
        for a in assignments:
            eid = a.get('employee_id')
            assignments_by_employee[eid] = assignments_by_employee.get(eid, 0) + 1

        # Future required resources: estimate based on patients without assignments
        assigned_patient_ids = {a.get('patient_id') for a in assignments}
        unassigned_patients = [p for p in patients if p.get('patient_id') not in assigned_patient_ids]
        estimated_future_minutes = len(unassigned_patients) * 60  # 60 min each default

        return {
            'generated_at': datetime.now().isoformat(),
            'counts': {
                'assignments': total_assignments,
                'employees': len(employees),
                'patients': len(patients),
                'unassigned_patients': len(unassigned_patients)
            },
            'time': {
                'total_service_minutes': total_service_minutes,
                'total_travel_minutes': total_travel_minutes,
                'avg_service_minutes': round(avg_service_minutes, 2),
                'avg_travel_minutes': round(avg_travel_minutes, 2),
                'travel_time_saved_minutes': travel_time_saved
            },
            'workload': assignments_by_employee,
            'future': {
                'estimated_future_minutes': estimated_future_minutes
            }
        }

    def _filter_assignments(self, assignments: List[Dict[str, Any]], days: List[int] | None, start_date: str | None, end_date: str | None) -> List[Dict[str, Any]]:
        def parse_date(d: str):
            try:
                return datetime.fromisoformat(d).date()
            except Exception:
                return None
        start = parse_date(start_date) if start_date else None
        end = parse_date(end_date) if end_date else None
        dayset = set(days) if days else None

        filtered = []
        for a in assignments:
            ts = a.get('start_time') or a.get('assigned_time')
            if not ts:
                continue
            try:
                dt = datetime.fromisoformat(ts)
                d = dt.date()
                wd = dt.weekday()  # 0=Mon..6=Sun
            except Exception:
                continue
            if start and d < start:
                continue
            if end and d > end:
                continue
            if dayset is not None and wd not in dayset:
                continue
            filtered.append(a)
        return filtered

    async def _ai_summarize(self, metrics: Dict[str, Any]) -> Dict[str, str]:
        try:
            # Use a minimal call to summarize metrics and propose ideas
            client = self.ai.client
            prompt = f"""
            You are an analytics assistant. Given the following rota metrics as JSON, write:
            1) A concise summary (<=120 words) highlighting optimizations and impact
            2) 3 data-backed ideas for further optimization as bullet points
            JSON:\n{metrics}
            """
            resp = client.chat.completions.create(
                model=self.ai.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            text = resp.choices[0].message.content
            # Simple split: first paragraph then ideas
            parts = text.split('\n')
            summary = '\n'.join([p for p in parts if p.strip() and not p.strip().startswith(('-', '*'))][:5])
            ideas = '\n'.join([p for p in parts if p.strip().startswith(('-', '*'))][:10])
            return {"summary": summary, "ideas": ideas}
        except Exception as e:
            logger.warning(f"AI summarize failed: {e}")
            return {"summary": "", "ideas": ""}

    async def get_or_generate_stats(self, force: bool = False, days: List[int] | None = None, start_date: str | None = None, end_date: str | None = None) -> Dict[str, Any]:
        assignments = self.db.get_assignments()
        employees = self.db.get_employees()
        patients = self.db.get_patients()

        # If filters are provided, compute on the fly and do not use cache for metrics
        if days or start_date or end_date:
            subset = self._filter_assignments(assignments, days, start_date, end_date)
            # Build filtered employees/patients based on subset participation
            emp_map = {e.get('employee_id') or e.get('EmployeeID'): e for e in employees}
            pat_map = {p.get('patient_id') or p.get('PatientID'): p for p in patients}
            emp_ids = sorted({a.get('employee_id') for a in subset if a.get('employee_id')})
            pat_ids = sorted({a.get('patient_id') for a in subset if a.get('patient_id')})
            employees_filtered = [emp_map.get(eid, {'employee_id': eid}) for eid in emp_ids]
            patients_filtered = [pat_map.get(pid, {'patient_id': pid}) for pid in pat_ids]
            metrics = self._compute_core_metrics(subset, employees_filtered, patients_filtered)
            # Optional: AI summary for filtered
            ai = await self._ai_summarize(metrics)
            return {
                'id': None,
                'generated_at': metrics['generated_at'],
                'assignments_count': len(subset),
                'metrics': metrics,
                'ai_summary': ai.get('summary'),
                'ai_ideas': ai.get('ideas')
            }

        # Unfiltered: use cache unless forced or assignment count changed
        latest = self.db.get_latest_stats()
        current_assignments = len(assignments)
        if latest and not force and latest.get('assignments_count') == current_assignments:
            return latest

        metrics = self._compute_core_metrics(assignments, employees, patients)
        ai = await self._ai_summarize(metrics)
        self.db.save_stats(assignments_count=current_assignments, metrics=metrics, ai_summary=ai.get('summary'), ai_ideas=ai.get('ideas'))
        return self.db.get_latest_stats()


