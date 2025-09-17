from __future__ import annotations

from datetime import datetime, timedelta, date, time as dtime
from typing import Dict, List, Optional, Tuple
import logging

from .data_processor import DataProcessor
from .travel_service import TravelService
from ..database import DatabaseManager
from ..models.schemas import Employee, Patient, QualificationEnum, ServiceType

logger = logging.getLogger(__name__)


class SchedulerCore:
    """Core, non-AI weekly rota scheduler.

    Strategy (daily, per employee):
    - Start at employee earliest start, current location = employee address
    - While time remains and there is patient demand:
      - Choose nearest feasible patient by travel time
      - Place visit block (travel + service) within shift, avoiding overlaps
      - Write assignment to DB with ISO datetimes
    """

    def __init__(
        self,
        data_processor: DataProcessor,
        travel_service: TravelService,
        db_manager: DatabaseManager,
    ) -> None:
        self.data_processor = data_processor
        self.travel_service = travel_service
        self.db_manager = db_manager

    def generate_weekly_rota(self, start_date: Optional[date] = None, task_id: Optional[str] = None) -> Dict[str, int]:
        """Generate assignments for the next 7 days.

        Returns summary counts.
        """
        if start_date is None:
            start_date = self._next_monday(date.today())

        # Seed weekly minutes per employee from DB existing assignments
        week_start_iso = datetime.combine(start_date, dtime(0, 0)).isoformat()
        week_end_iso = datetime.combine(start_date + timedelta(days=6), dtime(23, 59)).isoformat()
        employee_week_minutes: Dict[str, int] = {}
        try:
            for emp in self.data_processor.employees:
                total = 0
                rows = self.db_manager.get_employee_assignments_for_week(emp.EmployeeID, week_start_iso, week_end_iso)
                for r in rows:
                    dur = r.get('duration') or 0
                    try:
                        dur = int(dur)
                    except Exception:
                        dur = 0
                    total += max(0, dur)
                employee_week_minutes[emp.EmployeeID] = total
        except Exception:
            # Fail-safe: start at 0 if query fails
            for emp in self.data_processor.employees:
                employee_week_minutes[emp.EmployeeID] = 0

        total_created = 0
        for day_offset in range(7):
            day_date = start_date + timedelta(days=day_offset)
            # Respect SatSunSupport override: if patient has SatSunSupport == 'N', zero out demand on Sat/Sun
            weekday = day_date.weekday()  # 0=Mon..6=Sun
            created = self._generate_daily_rota_with_overrides(day_date, employee_week_minutes, disable_weekend=(weekday in (5,6)))
            total_created += created
            logger.info(f"SchedulerCore: created {created} assignments on {day_date.isoformat()}")

        return {"created": total_created}

    def _days_supports_weekend(self, patient: Patient) -> bool:
        try:
            days = (getattr(patient, 'DaysOfSupport', '') or '').replace(' ', '').split(',')
            days = [d.strip().lower() for d in days if d.strip() != '']
            # Accept F,S,S or Fri,Sat,Sun etc.
            has_fri = any(d in ('f','fri','friday') for d in days)
            sats = any(d in ('s','sa','sat','saturday') for d in days)
            suns = days.count('s') >= 2 or any(d in ('su','sun','sunday') for d in days)
            return has_fri and sats and suns
        except Exception:
            return False

    def generate_weekend_block(self, start_date: date) -> int:
        """Create Fri evening to Sun evening grouped assignments for eligible patients."""
        created = 0
        # Determine next Friday of the given week start
        # start_date is Monday by design
        fri = start_date + timedelta(days=4)
        sat = start_date + timedelta(days=5)
        sun = start_date + timedelta(days=6)

        for pat in self.data_processor.patients:
            try:
                if not ((getattr(pat, 'SatSunSupport', '') or '').strip().lower() in ('y','yes','true','1')):
                    continue
                if not self._days_supports_weekend(pat):
                    continue
                # Pick best employee: max remaining weekly capacity and language match
                candidates: List[Tuple[Employee, int]] = []
                for emp in self.data_processor.employees:
                    if not self._employee_can_serve(emp, pat):
                        continue
                    role = (getattr(emp, 'RoleLevel', '') or '').strip()
                    cap = getattr(emp, 'weekly_capacity_minutes', None)
                    cap = cap if isinstance(cap, int) and cap > 0 else (1200 if role == 'Junior' else 2160)
                    candidates.append((emp, cap))
                if not candidates:
                    continue
                # Sort by capacity desc
                candidates.sort(key=lambda x: x[1], reverse=True)
                employee = candidates[0][0]
                # Define three blocks and persist with shared group_id
                group_id = f"WEEKEND-{pat.PatientID}-{fri.isoformat()}"
                blocks = [
                    (datetime.combine(fri, dtime(18,0)), datetime.combine(fri, dtime(22,0))),
                    (datetime.combine(sat, dtime(8,0)), datetime.combine(sat, dtime(20,0))),
                    (datetime.combine(sun, dtime(8,0)), datetime.combine(sun, dtime(20,0))),
                ]
                for start_dt, end_dt in blocks:
                    start_iso = start_dt.replace(second=0, microsecond=0).isoformat()
                    end_iso = end_dt.replace(second=0, microsecond=0).isoformat()
                    if self.db_manager.has_overlap_for_employee(employee.EmployeeID, start_iso, end_iso):
                        continue
                    travel_minutes = self.travel_service.get_travel_time(
                        origin=f"{employee.Address}, {employee.PostCode}" if employee.PostCode and employee.PostCode not in employee.Address else employee.Address,
                        destination=f"{pat.Address}, {pat.PostCode}" if pat.PostCode and pat.PostCode not in pat.Address else pat.Address,
                        mode=getattr(employee.TransportMode, 'value', str(employee.TransportMode))
                    )
                    self.db_manager.log_assignment({
                        "employee_id": employee.EmployeeID,
                        "employee_name": employee.Name,
                        "patient_id": pat.PatientID,
                        "patient_name": pat.PatientName,
                        "service_type": self._infer_service_type(pat),
                        "assigned_time": start_iso,
                        "start_time": start_iso,
                        "end_time": end_iso,
                        "estimated_duration": int((end_dt - start_dt).total_seconds() // 60),
                        "travel_time": travel_minutes,
                        "priority_score": 5.0,
                        "assignment_reason": "Weekend grouped support",
                        "group_id": group_id,
                    })
                    created += 1
            except Exception as e:
                try:
                    logger.warning(f"Weekend grouping error for patient {getattr(pat, 'PatientID', '?')}: {e}")
                except Exception:
                    pass
                continue
        return created

    def _generate_daily_rota_with_overrides(self, day_date: date, employee_week_minutes: Dict[str, int], disable_weekend: bool) -> int:
        """Greedy chaining per employee for a single day."""
        # Operation log: start
        try:
            self.db_manager.log_operation(
                "daily_schedule",
                "Starting daily schedule",
                {"date": day_date.isoformat(), "employees": len(self.data_processor.employees), "patients": len(self.data_processor.patients)}
            )
        except Exception:
            pass
        # Prepare patient daily demands (in minutes) using DataProcessor helpers
        patient_daily_minutes: Dict[str, int] = {}
        for patient in self.data_processor.patients:
            try:
                daily = self.data_processor.derive_patient_daily_demand(patient)
                # If SatSunSupport is 'N' and this is Sat/Sun, suppress demand
                if disable_weekend:
                    sss = (getattr(patient, 'SatSunSupport', '') or '').strip().lower()
                    if sss in ('n','no','false','0'):
                        daily = 0
            except Exception:
                daily = self._estimate_patient_daily_minutes(patient)
            if daily > 0:
                patient_daily_minutes[patient.PatientID] = daily

        created_count = 0

        # Track how many meal-prep visits each patient has received today
        meal_visits_done: Dict[str, int] = {}

        for employee in self.data_processor.employees:
            earliest, latest = self._parse_shift(employee)
            # Support overnight shifts: if latest <= earliest, assume next-day end
            current_time = datetime.combine(day_date, earliest)
            shift_end = datetime.combine(day_date, latest)
            if latest <= earliest:
                shift_end = shift_end + timedelta(days=1)
            current_location = f"{employee.Address}, {employee.PostCode}" if employee.PostCode and employee.PostCode not in employee.Address else employee.Address

            # Limit visits to a reasonable number per day
            max_visits = getattr(employee, "max_patients_per_day", 8) or 8
            visits_done = 0

            while current_time < shift_end and visits_done < max_visits:
                # Build candidate list of feasible patients
                candidates: List[Tuple[Patient, int]] = []  # (patient, travel_minutes)
                for patient in self.data_processor.patients:
                    if patient_daily_minutes.get(patient.PatientID, 0) <= 0:
                        continue
                    if not self._employee_can_serve(employee, patient):
                        continue

                    mode = getattr(employee.TransportMode, "value", str(employee.TransportMode))
                    travel_minutes = self.travel_service.get_travel_time(
                        origin=current_location,
                        destination=f"{patient.Address}, {patient.PostCode}" if patient.PostCode and patient.PostCode not in patient.Address else patient.Address,
                        mode=mode,
                    )
                    candidates.append((patient, travel_minutes))

                if not candidates:
                    break

                # Choose nearest by travel time
                candidates.sort(key=lambda x: x[1])
                chosen_patient, travel_minutes = candidates[0]

                # Decide service duration for this visit (based on inferred service type defaults)
                remaining = patient_daily_minutes.get(chosen_patient.PatientID, 0)
                inferred_str = self._infer_service_type(chosen_patient)
                try:
                    inferred_enum = ServiceType(inferred_str)
                except Exception:
                    inferred_enum = ServiceType.PERSONAL_CARE
                # Use entire daily remaining minutes for single-visit policy
                # Priority: RequiredHoursOfSupport minutes computed earlier in daily demand
                default_minutes = self.data_processor.get_default_service_duration(inferred_enum)
                service_minutes = remaining if (remaining and remaining > 0) else default_minutes
                # Enforce minimum on-site duration of 30 minutes
                service_minutes = max(service_minutes, 30)

                # Compute proposed times
                proposed_start = current_time + timedelta(minutes=travel_minutes)
                proposed_end = proposed_start + timedelta(minutes=service_minutes)

                # If meal prep, align once into a meal window but do not create more than one visit per day
                is_meal = self._patient_requires_meal_prep(chosen_patient)
                if is_meal:
                    # Force single daily visit: use full remaining minutes (>=90 from demand), align to next available window
                    win_list = self._get_meal_windows(chosen_patient, day_date)
                    arrival = current_time + timedelta(minutes=travel_minutes)
                    aligned = False
                    for ws, we in win_list:
                        start_cand = arrival if arrival > ws else ws
                        end_cand = start_cand + timedelta(minutes=service_minutes)
                        if end_cand <= we and end_cand <= shift_end:
                            proposed_start = start_cand
                            proposed_end = end_cand
                            aligned = True
                            break
                    if not aligned:
                        # Could not align in a window now; advance and retry next loop
                        current_time = current_time + timedelta(minutes=5)
                        continue

                # Ensure fit in shift; shrink if needed
                if proposed_end > shift_end:
                    # shrink to fit
                    fit_minutes = int((shift_end - proposed_start).total_seconds() // 60)
                    if fit_minutes < 30:
                        break  # too small to schedule
                    service_minutes = fit_minutes
                    proposed_end = proposed_start + timedelta(minutes=service_minutes)

                # Overlap check
                start_iso = proposed_start.replace(second=0, microsecond=0).isoformat()
                end_iso = proposed_end.replace(second=0, microsecond=0).isoformat()
                if self.db_manager.has_overlap_for_employee(employee.EmployeeID, start_iso, end_iso):
                    # push time forward slightly and retry
                    current_time = current_time + timedelta(minutes=5)
                    continue

                # Skip any duplicate same-day visits
                if self.db_manager.has_employee_patient_assignment_on_date(
                    employee.EmployeeID, chosen_patient.PatientID, proposed_start.isoformat()
                ):
                    # Try next candidate if available
                    next_candidate = None
                    for patient, tmin in candidates[1:]:
                        if patient_daily_minutes.get(patient.PatientID, 0) <= 0:
                            continue
                        if not self._employee_can_serve(employee, patient):
                            continue
                        next_candidate = (patient, tmin)
                        break
                    if next_candidate is not None:
                        chosen_patient, travel_minutes = next_candidate
                        remaining = patient_daily_minutes.get(chosen_patient.PatientID, 0)
                        inferred_str = self._infer_service_type(chosen_patient)
                        try:
                            inferred_enum = ServiceType(inferred_str)
                        except Exception:
                            inferred_enum = ServiceType.PERSONAL_CARE
                        default_minutes = self.data_processor.get_default_service_duration(inferred_enum)
                        service_minutes = min(default_minutes, remaining)
                        proposed_start = current_time + timedelta(minutes=travel_minutes)
                        proposed_end = proposed_start + timedelta(minutes=service_minutes)
                        start_iso = proposed_start.replace(second=0, microsecond=0).isoformat()
                        end_iso = proposed_end.replace(second=0, microsecond=0).isoformat()
                        if self.db_manager.has_overlap_for_employee(employee.EmployeeID, start_iso, end_iso):
                            current_time = current_time + timedelta(minutes=5)
                            continue
                    else:
                        # No alternative, advance time slightly
                        current_time = current_time + timedelta(minutes=5)
                        continue

                # Weekly capacity enforcement
                try:
                    eid = employee.EmployeeID
                    cap = getattr(employee, 'weekly_capacity_minutes', None)
                    if not isinstance(cap, int) or cap <= 0:
                        role = (getattr(employee, 'RoleLevel', None) or '').strip()
                        cap = 1200 if role == 'Junior' else 2160
                    used = employee_week_minutes.get(eid, 0)
                    remaining_cap = max(0, cap - used)
                    if remaining_cap < 30:
                        # No meaningful capacity left for the week
                        break
                    if service_minutes > remaining_cap:
                        # shrink to remaining capacity if still >=30
                        if remaining_cap < 30:
                            # Just in case; already handled above
                            break
                        service_minutes = remaining_cap
                        proposed_end = proposed_start + timedelta(minutes=service_minutes)
                        end_iso = proposed_end.replace(second=0, microsecond=0).isoformat()
                except Exception:
                    pass

                # Persist assignment
                service_type = self._infer_service_type(chosen_patient)
                self.db_manager.log_assignment({
                    "employee_id": employee.EmployeeID,
                    "employee_name": employee.Name,
                    "patient_id": chosen_patient.PatientID,
                    "patient_name": chosen_patient.PatientName,
                    "service_type": service_type,
                    "assigned_time": start_iso,
                    "start_time": start_iso,
                    "end_time": end_iso,
                    "estimated_duration": service_minutes,
                    "travel_time": travel_minutes,
                    "priority_score": 5.0,
                    "assignment_reason": "Scheduled by core engine",
                })

                created_count += 1
                visits_done += 1
                patient_daily_minutes[chosen_patient.PatientID] = max(0, remaining - service_minutes)
                current_time = proposed_end
                current_location = f"{chosen_patient.Address}, {chosen_patient.PostCode}" if chosen_patient.PostCode and chosen_patient.PostCode not in chosen_patient.Address else chosen_patient.Address
                # Update weekly usage
                try:
                    employee_week_minutes[eid] = employee_week_minutes.get(eid, 0) + int(service_minutes)
                except Exception:
                    pass
                # Track meal-prep count
                if is_meal:
                    meal_visits_done[chosen_patient.PatientID] = meal_visits_done.get(chosen_patient.PatientID, 0) + 1

        # Operation log: end
        try:
            self.db_manager.log_operation(
                "daily_schedule",
                "Completed daily schedule",
                {"date": day_date.isoformat(), "assignments_created": created_count}
            )
        except Exception:
            pass

        return created_count

    def _employee_can_serve(self, employee: Employee, patient: Patient) -> bool:
        # Medicine requires nurse
        if "medicine" in (patient.RequiredSupport or "").lower():
            if employee.Qualification != QualificationEnum.NURSE:
                return False

        # Language preference basic check (allow if English default)
        pref = (patient.LanguagePreference or "English").strip().lower()
        if pref and pref != "english":
            langs = (employee.LanguageSpoken or "").lower()
            if pref not in langs:
                return False

        return True

    def _parse_shift(self, employee: Employee) -> Tuple[dtime, dtime]:
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

        earliest = _parse(getattr(employee, "EarliestStart", ""), dtime(9, 0))
        latest = _parse(getattr(employee, "LatestEnd", ""), dtime(17, 0))
        return earliest, latest

    def _estimate_patient_daily_minutes(self, patient: Patient) -> int:
        # If weekly hours provided, distribute across 7 days; else default 60
        weekly_hours = patient.RequiredHoursOfSupport
        if isinstance(weekly_hours, int) and weekly_hours and weekly_hours > 0:
            return max(15, int((weekly_hours * 60) / 7))
        return 60

    def _infer_service_type(self, patient: Patient) -> str:
        supports = (patient.RequiredSupport or "").lower()
        if "medicine" in supports:
            return "medicine"
        if "meal_prep" in supports or "meal prep" in supports:
            return "meal_prep"
        if "exercise" in supports:
            return "exercise"
        if "compan" in supports:
            return "companionship"
        if "personal" in supports or "care" in supports:
            return "personal_care"
        return "personal_care"

    def _patient_requires_meal_prep(self, patient: Patient) -> bool:
        try:
            s = (patient.RequiredSupport or '').lower()
            return ('meal_prep' in s) or ('meal prep' in s) or bool(getattr(patient, 'MealPrepRequired', False))
        except Exception:
            return False

    def _parse_time_str(self, hhmm: Optional[str], default: dtime) -> dtime:
        try:
            if not hhmm:
                return default
            parts = hhmm.strip().split(":")
            h = int(parts[0])
            m = int(parts[1]) if len(parts) > 1 else 0
            return dtime(h, m)
        except Exception:
            return default

    def _get_meal_windows(self, patient: Patient, day_date: date) -> List[Tuple[datetime, datetime]]:
        """Return 3 meal windows for the day: Breakfast, Lunch, Dinner.
        If patient-specific times exist, center a 1-hour window around them; otherwise use defaults.
        Defaults: [07:00–09:00], [12:00–14:00], [17:00–19:00].
        """
        windows: List[Tuple[datetime, datetime]] = []
        # Defaults
        default_windows = [
            (dtime(7, 0), dtime(9, 0)),
            (dtime(12, 0), dtime(14, 0)),
            (dtime(17, 0), dtime(19, 0)),
        ]

        bt = getattr(patient, 'BreakfastTime', None)
        lt = getattr(patient, 'LunchTime', None)
        dt = getattr(patient, 'DinnerTime', None)

        custom_times = [
            self._parse_time_str(bt, None) if bt else None,
            self._parse_time_str(lt, None) if lt else None,
            self._parse_time_str(dt, None) if dt else None,
        ]

        for idx, pair in enumerate(default_windows):
            if custom_times[idx] is not None:
                center = custom_times[idx]
                start = datetime.combine(day_date, center) - timedelta(minutes=30)
                end = datetime.combine(day_date, center) + timedelta(minutes=30)
            else:
                start = datetime.combine(day_date, pair[0])
                end = datetime.combine(day_date, pair[1])
            windows.append((start, end))

        return windows

    def _next_monday(self, today: date) -> date:
        # Monday is 0; if today is Monday, use today
        days_ahead = (0 - today.weekday()) % 7
        return today + timedelta(days=days_ahead)


