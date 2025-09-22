from __future__ import annotations

from datetime import datetime, date, time as dtime, timedelta
from typing import List, Tuple, Optional, Union, Dict

from .data_processor import DataProcessor
from ..database import DatabaseManager
from ..models.schemas import ServiceType, QualificationEnum


class AssignmentValidator:
    """
    DB-first validator for proposed assignments. Used by both the core scheduler and ad-hoc flow.
    """

    def __init__(self, db_manager: DatabaseManager, data_processor: DataProcessor):
        self.db = db_manager
        self.dp = data_processor

    # ---- Public API ----
    def validate_proposed_assignment(
        self,
        employee_id: str,
        patient_id: str,
        service_type: Union[ServiceType, str],
        start_iso: str,
        end_iso: str,
        duration_minutes: int,
        allow_same_day_dup_for_meal_prep: bool = False,
    ) -> List[str]:
        """Return list of violations (empty when valid)."""
        violations: List[str] = []

        employee = self.dp.get_employee_by_id(employee_id)
        patient = self.dp.get_patient_by_id(patient_id)
        if not employee or not patient:
            return ["Employee or patient not found"]

        svc = service_type.value if isinstance(service_type, ServiceType) else str(service_type)
        svc = (svc or "").strip().lower()

        # Parse datetimes
        try:
            start_dt = datetime.fromisoformat(start_iso)
            end_dt = datetime.fromisoformat(end_iso)
        except Exception:
            return ["Start or end time is not ISO format"]

        # Rule 10: DaysOfSupport gating
        if not self._is_day_supported(patient.DaysOfSupport, start_dt.date()):
            violations.append("Patient not scheduled for support on this day (DaysOfSupport)")

        # Rule 3: min on-site duration
        if duration_minutes < 30:
            violations.append("Minimum on-site duration is 30 minutes")

        # Shift bounds (with overnight wrap support)
        if not self._within_shift_bounds(employee.EarliestStart, employee.LatestEnd, start_dt, end_dt):
            violations.append("Assignment outside employee shift bounds")

        # Rule 1: Qualification for medication
        if svc == ServiceType.MEDICINE.value:
            if employee.Qualification != QualificationEnum.NURSE:
                violations.append("Medicine services require a qualified nurse")

        # Rule 9: Gender preference
        pref = (getattr(patient, 'PreferenceOfCarer', '') or '').strip().lower()
        if pref in ("male", "female"):
            if employee.Gender.value.strip().lower() != pref:
                violations.append(f"Gender preference mismatch ({pref})")

        # Language preference (enforce if non-English)
        lang_pref = (patient.LanguagePreference or "English").strip().lower()
        if lang_pref and lang_pref != "english":
            langs = (employee.LanguageSpoken or "").strip().lower()
            if lang_pref not in langs:
                violations.append("Employee does not speak patient's preferred language")

        # No overlap for employee
        if self.db.has_overlap_for_employee(employee.EmployeeID, start_iso, end_iso):
            violations.append("Employee has overlapping assignment")

        # Weekly capacity (Rule 1 caps)
        wk_start, wk_end = self._week_bounds(start_dt.date())
        used = self.db.sum_employee_minutes_for_week(employee.EmployeeID, wk_start.isoformat(), wk_end.isoformat())
        cap = self._role_capacity_minutes(getattr(employee, 'RoleLevel', None), getattr(employee, 'weekly_capacity_minutes', None))
        if used + max(0, int(duration_minutes)) > cap:
            violations.append("Weekly capacity would be exceeded")

        # Same-day E↔P duplicate (blocked unless meal_prep)
        if not (allow_same_day_dup_for_meal_prep and svc == ServiceType.MEAL_PREP.value):
            if self.db.has_employee_patient_assignment_on_date(employee.EmployeeID, patient.PatientID, start_iso):
                violations.append("Employee already assigned to this patient today")

        # Rule 8: Patient concurrency <= RequiredCarerSupport
        try:
            req_support = int(getattr(patient, 'RequiredCarerSupport', 1) or 1)
        except Exception:
            req_support = 1
        current_overlaps = self.db.count_patient_overlaps(patient.PatientID, start_iso, end_iso)
        if current_overlaps + 1 > max(1, req_support):
            violations.append("Patient concurrency limit exceeded (RequiredCarerSupport)")

        return violations

    def validate_with_details(
        self,
        employee_id: str,
        patient_id: str,
        service_type: Union[ServiceType, str],
        start_iso: str,
        end_iso: str,
        duration_minutes: int,
        allow_same_day_dup_for_meal_prep: bool = False,
    ) -> List[str]:
        """Return detailed violation strings including IDs and context for verification."""
        base = self.validate_proposed_assignment(
            employee_id=employee_id,
            patient_id=patient_id,
            service_type=service_type,
            start_iso=start_iso,
            end_iso=end_iso,
            duration_minutes=duration_minutes,
            allow_same_day_dup_for_meal_prep=allow_same_day_dup_for_meal_prep,
        )

        detailed: List[str] = []

        # Fetch models once
        employee = self.dp.get_employee_by_id(employee_id)
        patient = self.dp.get_patient_by_id(patient_id)
        svc = service_type.value if isinstance(service_type, ServiceType) else str(service_type)
        svc = (svc or '').strip().lower()

        # Precompute helpful context
        try:
            wk_start, wk_end = self._week_bounds(datetime.fromisoformat(start_iso).date())
            used = self.db.sum_employee_minutes_for_week(employee_id, wk_start.isoformat(), wk_end.isoformat())
            cap = self._role_capacity_minutes(getattr(employee, 'RoleLevel', None), getattr(employee, 'weekly_capacity_minutes', None))
        except Exception:
            used, cap = 0, 0

        for msg in base:
            m = msg.lower()
            if 'overlapping assignment' in m:
                overlaps = self.db.get_overlapping_assignments_for_employee(employee_id, start_iso, end_iso)
                if overlaps:
                    for r in overlaps[:3]:  # limit fanout
                        detailed.append(
                            f"Employee has overlapping assignment: conflicts with assignment #{r.get('id')} "
                            f"({r.get('start_time')}→{r.get('end_time')}, patient {r.get('patient_id')} {r.get('patient_name')})"
                        )
                else:
                    detailed.append(msg)
            elif 'already assigned to this patient today' in m:
                same = self.db.get_employee_patient_assignments_on_date(employee_id, patient_id, start_iso)
                if same:
                    ids = [str(r.get('id')) for r in same]
                    times = [f"{r.get('start_time')}→{r.get('end_time')}" for r in same]
                    detailed.append(
                        f"Duplicate employee↔patient on date: existing assignment(s) #{', '.join(ids)} at {', '.join(times)}"
                    )
                else:
                    detailed.append(msg)
            elif 'concurrency limit exceeded' in m:
                try:
                    overlaps = self.db.get_overlapping_assignments_for_patient(patient_id, start_iso, end_iso)
                except Exception:
                    overlaps = []
                if overlaps:
                    parts = []
                    for r in overlaps[:4]:
                        parts.append(
                            f"#{r.get('id')} ({r.get('start_time')}→{r.get('end_time')}, emp {r.get('employee_id')} {r.get('employee_name')})"
                        )
                    detailed.append(
                        f"Patient concurrency exceeded (RequiredCarerSupport): overlaps with {', '.join(parts)}"
                    )
                else:
                    detailed.append(msg)
            elif 'weekly capacity' in m:
                detailed.append(
                    f"Weekly capacity would be exceeded: used {used} min, requested {max(0, int(duration_minutes))} min, cap {cap} min"
                )
            elif 'outside employee shift bounds' in m:
                try:
                    e = getattr(employee, 'EarliestStart', None)
                    l = getattr(employee, 'LatestEnd', None)
                except Exception:
                    e, l = None, None
                detailed.append(
                    f"Assignment outside shift bounds: proposed {start_iso}→{end_iso}, shift {e or '09:00'}–{l or '17:00'}"
                )
            elif 'days of support' in m.lower():
                try:
                    dos = getattr(patient, 'DaysOfSupport', None)
                except Exception:
                    dos = None
                detailed.append(
                    f"Patient not scheduled this day (DaysOfSupport={dos or 'n/a'}), proposed window {start_iso}→{end_iso}"
                )
            elif 'gender preference mismatch' in m:
                try:
                    pref = (getattr(patient, 'PreferenceOfCarer', '') or '').strip()
                    emp_gender = getattr(employee.Gender, 'value', str(getattr(employee, 'Gender', '')))
                except Exception:
                    pref, emp_gender = '', ''
                detailed.append(f"Gender preference mismatch: patient={pref or 'n/a'}, employee={emp_gender or 'n/a'}")
            elif "does not speak" in m or 'language' in m:
                try:
                    pref_lang = (getattr(patient, 'LanguagePreference', '') or '').strip()
                    emp_langs = (getattr(employee, 'LanguageSpoken', '') or '').strip()
                except Exception:
                    pref_lang, emp_langs = '', ''
                detailed.append(f"Language mismatch: patient_pref={pref_lang or 'English'}, employee_langs={emp_langs or '-'}")
            elif 'medicine services require' in m:
                detailed.append("Medicine requires nurse: employee not qualified")
            else:
                detailed.append(msg)

        return detailed

    # ---- Helpers ----
    def _within_shift_bounds(self, earliest: str, latest: str, start_dt: datetime, end_dt: datetime) -> bool:
        e, l = self._parse_shift_bounds(earliest, latest)
        shift_start = start_dt.replace(hour=e.hour, minute=e.minute, second=0, microsecond=0)
        shift_end = start_dt.replace(hour=l.hour, minute=l.minute, second=0, microsecond=0)
        if l <= e:
            # overnight wrap
            shift_end = shift_end + timedelta(days=1)
        return start_dt >= shift_start and end_dt <= shift_end

    def _parse_shift_bounds(self, earliest: str, latest: str) -> Tuple[dtime, dtime]:
        def _parse(t: str, default: dtime) -> dtime:
            try:
                if not t:
                    return default
                parts = t.strip().split(":")
                hour = int(parts[0])
                minute = int(parts[1]) if len(parts) > 1 else 0
                return dtime(hour, minute)
            except Exception:
                return default
        return _parse(earliest, dtime(9, 0)), _parse(latest, dtime(17, 0))

    def _is_day_supported(self, days_str: Optional[str], on_date: date) -> bool:
        if not days_str:
            return True
        raw = (days_str or '').replace(' ', '')
        tokens = [t.strip().lower() for t in raw.split(',') if t.strip() != '']
        if not tokens:
            return True
        # Accept initials or names
        weekday = on_date.weekday()  # 0=Mon..6=Sun
        name_map = {
            0: ("m", "mon", "monday"),
            1: ("t", "tu", "tue", "tues", "tuesday"),
            2: ("w", "wed", "wednesday"),
            3: ("th", "thu", "thurs", "thursday"),
            4: ("f", "fri", "friday"),
            5: ("sa", "sat", "saturday"),
            6: ("su", "sun", "sunday"),
        }
        aliases = name_map.get(weekday, ())
        return any(t in aliases for t in tokens)

    def _week_bounds(self, on_date: date) -> Tuple[datetime, datetime]:
        # Monday 00:00:00 to Sunday 23:59:59
        days_to_monday = (on_date.weekday() - 0) % 7
        monday = datetime.combine(on_date - timedelta(days=days_to_monday), dtime(0, 0))
        sunday = monday + timedelta(days=6, hours=23, minutes=59)
        return monday, sunday

    def _role_capacity_minutes(self, role_level: Optional[str], configured_minutes: Optional[int]) -> int:
        if isinstance(configured_minutes, int) and configured_minutes > 0:
            return configured_minutes
        rl = (role_level or '').strip().lower()
        if rl == 'junior':
            return 20 * 60
        return 36 * 60


