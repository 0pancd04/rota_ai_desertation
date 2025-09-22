from __future__ import annotations

from datetime import datetime, timedelta, date, time as dtime
from typing import Dict, List, Optional, Tuple, Any
import logging
import re

from .data_processor import DataProcessor
from .travel_service import TravelService
from ..database import DatabaseManager
from ..models.schemas import Employee, Patient, QualificationEnum, ServiceType
from .assignment_validator import AssignmentValidator

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
        validator: AssignmentValidator | None = None,
    ) -> None:
        self.data_processor = data_processor
        self.travel_service = travel_service
        self.db_manager = db_manager
        self.validator = validator or AssignmentValidator(db_manager, data_processor)

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
                    # Validate with shared validator for the primary employee
                    v1 = self.validator.validate_proposed_assignment(
                        employee_id=employee.EmployeeID,
                        patient_id=pat.PatientID,
                        service_type=ServiceType(self._infer_service_type(pat)),
                        start_iso=start_iso,
                        end_iso=end_iso,
                        duration_minutes=int((end_dt - start_dt).total_seconds() // 60),
                        allow_same_day_dup_for_meal_prep=False,
                    )
                    if v1:
                        continue
                    travel_minutes = self.travel_service.get_travel_time(
                        origin=f"{employee.Address}, {employee.PostCode}" if employee.PostCode and employee.PostCode not in employee.Address else employee.Address,
                        destination=f"{pat.Address}, {pat.PostCode}" if pat.PostCode and pat.PostCode not in pat.Address else pat.Address,
                        mode=getattr(employee.TransportMode, 'value', str(employee.TransportMode))
                    )
                    # Handle RequiredCarerSupport >= 2 for the block
                    req_support = 1
                    try:
                        req_support = int(getattr(pat, 'RequiredCarerSupport', 1) or 1)
                    except Exception:
                        req_support = 1
                    if req_support >= 2:
                        # prefer non-junior as second carer
                        second_pool: List[Employee] = []
                        for emp2 in self.data_processor.employees:
                            if emp2.EmployeeID == employee.EmployeeID:
                                continue
                            if not self._employee_can_serve(emp2, pat):
                                continue
                            second_pool.append(emp2)
                        # sort non-junior first, then by travel time
                        ranked_second: List[Tuple[int, int, Employee]] = []
                        for emp2 in second_pool:
                            is_jun = 1 if (getattr(emp2, 'RoleLevel', '') or '').strip().lower() == 'junior' else 0
                            t2 = self._calc_travel_minutes(emp2, pat)
                            v2 = self.validator.validate_proposed_assignment(
                                employee_id=emp2.EmployeeID,
                                patient_id=pat.PatientID,
                                service_type=ServiceType(self._infer_service_type(pat)),
                                start_iso=start_iso,
                                end_iso=end_iso,
                                duration_minutes=int((end_dt - start_dt).total_seconds() // 60),
                                allow_same_day_dup_for_meal_prep=False,
                            )
                            if not v2:
                                ranked_second.append((is_jun, t2, emp2))
                        if not ranked_second:
                            continue
                        ranked_second.sort(key=lambda x: (x[0], x[1]))
                        emp2 = ranked_second[0][2]
                        # Transactionally insert both assignments
                        self.db_manager.begin_transaction()
                        try:
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
                            self.db_manager.log_assignment({
                                "employee_id": emp2.EmployeeID,
                                "employee_name": emp2.Name,
                                "patient_id": pat.PatientID,
                                "patient_name": pat.PatientName,
                                "service_type": self._infer_service_type(pat),
                                "assigned_time": start_iso,
                                "start_time": start_iso,
                                "end_time": end_iso,
                                "estimated_duration": int((end_dt - start_dt).total_seconds() // 60),
                                "travel_time": self._calc_travel_minutes(emp2, pat),
                                "priority_score": 5.0,
                                "assignment_reason": "Weekend grouped support",
                                "group_id": group_id,
                            })
                            self.db_manager.commit()
                            created += 2
                        except Exception:
                            self.db_manager.rollback()
                            continue
                    else:
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
                # Respect DaysOfSupport gate
                if daily > 0 and not self._is_day_supported(getattr(patient, 'DaysOfSupport', ''), day_date):
                    daily = 0
            except Exception:
                daily = self._estimate_patient_daily_minutes(patient)
            if daily > 0:
                patient_daily_minutes[patient.PatientID] = daily

        created_count = 0
        # Collect reasons for patients we fail to assign today
        patient_reasons: Dict[str, set[str]] = {}
        # Track detailed attempt diagnostics per patient/employee for richer unassigned context
        patient_attempts: Dict[str, List[Dict[str, Any]]] = {}
        employee_attempts: Dict[str, List[Dict[str, Any]]] = {}

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

            # Track whether this employee received any assignment today
            employee_got_assignment = False

            while current_time < shift_end and visits_done < max_visits:
                # Build candidate list of feasible patients
                candidates: List[Tuple[Patient, int]] = []  # (patient, travel_minutes)
                for patient in self.data_processor.patients:
                    if patient_daily_minutes.get(patient.PatientID, 0) <= 0:
                        continue
                    if not self._employee_can_serve(employee, patient):
                        continue
                    # Avoid assigning Junior solo when RequiredCarerSupport == 1 (Rule 1 learning)
                    try:
                        rcs = int(getattr(patient, 'RequiredCarerSupport', 1) or 1)
                    except Exception:
                        rcs = 1
                    role_lv = (getattr(employee, 'RoleLevel', '') or '').strip().lower()
                    if rcs == 1 and role_lv == 'junior':
                        continue

                    mode = getattr(employee.TransportMode, "value", str(employee.TransportMode))
                    travel_minutes = self.travel_service.get_travel_time(
                        origin=current_location,
                        destination=f"{patient.Address}, {patient.PostCode}" if patient.PostCode and patient.PostCode not in patient.Address else patient.Address,
                        mode=mode,
                    )
                    candidates.append((patient, travel_minutes))

                if not candidates:
                    # No feasible patients at this time for this employee; try nudging time, or break if no demand remains
                    # Nudge time slightly to see if new windows open; if still nothing after nudge, break
                    current_time = current_time + timedelta(minutes=15)
                    # If after nudge we are past shift end or still no demand, stop
                    if current_time >= shift_end:
                        break
                    # Recompute on next loop iteration
                    continue

                # Choose nearest by travel time
                candidates.sort(key=lambda x: x[1])
                chosen_patient, travel_minutes = candidates[0]

                # Decide service duration and proposed times
                remaining = patient_daily_minutes.get(chosen_patient.PatientID, 0)
                inferred_str = self._infer_service_type(chosen_patient)
                try:
                    inferred_enum = ServiceType(inferred_str)
                except Exception:
                    inferred_enum = ServiceType.PERSONAL_CARE
                is_meal = (inferred_enum == ServiceType.MEAL_PREP)

                if is_meal:
                    # Schedule 3x30 across the day; here we place one 30-min visit per loop aligned to next free meal window
                    service_minutes = 30
                    arrival = current_time + timedelta(minutes=travel_minutes)
                    win_list = self._get_meal_windows(chosen_patient, day_date)
                    # Determine which windows already have a meal_prep assignment (DB-first)
                    patient_rows_today = self.db_manager.get_assignments_for_patient_on_date(chosen_patient.PatientID, arrival.isoformat())
                    filled_windows = []
                    for ws, we in win_list:
                        for r in patient_rows_today:
                            try:
                                if (r.get('service_type') == ServiceType.MEAL_PREP.value
                                    and r.get('start_time') and r.get('end_time')):
                                    st = datetime.fromisoformat(r['start_time'])
                                    en = datetime.fromisoformat(r['end_time'])
                                    # window filled if assignment lies within window
                                    if st >= ws and en <= we:
                                        filled_windows.append((ws, we))
                                        break
                            except Exception:
                                continue
                    # pick first unfilled window that we can align into
                    proposed_start = None
                    proposed_end = None
                    for ws, we in win_list:
                        if (ws, we) in filled_windows:
                            continue
                        start_cand = arrival if arrival > ws else ws
                        end_cand = start_cand + timedelta(minutes=service_minutes)
                        if end_cand <= we and end_cand <= shift_end:
                            proposed_start = start_cand
                            proposed_end = end_cand
                            break
                    if proposed_start is None:
                        # No free window now; nudge time and retry
                        current_time = current_time + timedelta(minutes=5)
                        continue
                else:
                    default_minutes = self.data_processor.get_default_service_duration(inferred_enum)
                    service_minutes = remaining if (remaining and remaining > 0) else default_minutes
                    service_minutes = max(service_minutes, 30)
                    proposed_start = current_time + timedelta(minutes=travel_minutes)
                    proposed_end = proposed_start + timedelta(minutes=service_minutes)

                # Ensure fit in shift; shrink if needed
                if proposed_end > shift_end:
                    # shrink to fit
                    fit_minutes = int((shift_end - proposed_start).total_seconds() // 60)
                    if fit_minutes < 30:
                        break  # too small to schedule
                    service_minutes = fit_minutes
                    proposed_end = proposed_start + timedelta(minutes=service_minutes)

                # Build ISO strings
                start_iso = proposed_start.replace(second=0, microsecond=0).isoformat()
                end_iso = proposed_end.replace(second=0, microsecond=0).isoformat()

                # Validate with shared validator
                allow_dup_meal = is_meal
                # Detailed validation to capture overlapping assignment IDs, caps, etc.
                violations = self.validator.validate_with_details(
                    employee_id=employee.EmployeeID,
                    patient_id=chosen_patient.PatientID,
                    service_type=inferred_enum,
                    start_iso=start_iso,
                    end_iso=end_iso,
                    duration_minutes=int(service_minutes),
                    allow_same_day_dup_for_meal_prep=allow_dup_meal,
                )
                if violations:
                    # Always record detailed violations for the chosen patient attempt
                    try:
                        s = patient_reasons.get(chosen_patient.PatientID)
                        if s is None:
                            s = set()
                            patient_reasons[chosen_patient.PatientID] = s
                        for v in violations:
                            s.add(v)
                    except Exception:
                        pass
                    # Record this failed attempt for richer diagnostics (who/when/why)
                    try:
                        attempt_rec: Dict[str, Any] = {
                            "employee_id": employee.EmployeeID,
                            "employee_name": getattr(employee, 'Name', employee.EmployeeID),
                            "patient_id": chosen_patient.PatientID,
                            "patient_name": getattr(chosen_patient, 'PatientName', chosen_patient.PatientID),
                            "service_type": inferred_enum.value if hasattr(inferred_enum, 'value') else str(inferred_enum),
                            "start_time": start_iso,
                            "end_time": end_iso,
                            "violations": list(violations),
                        }
                        patient_attempts.setdefault(chosen_patient.PatientID, []).append(attempt_rec)
                        employee_attempts.setdefault(employee.EmployeeID, []).append(attempt_rec)
                    except Exception:
                        pass
                    # Try next candidate patient if possible
                    next_candidate = None
                    for p2, tmin in candidates[1:]:
                        if patient_daily_minutes.get(p2.PatientID, 0) <= 0:
                            continue
                        if not self._employee_can_serve(employee, p2):
                            continue
                        next_candidate = (p2, tmin)
                        break
                    if next_candidate is not None:
                        chosen_patient, travel_minutes = next_candidate
                        # restart loop to recompute
                        continue
                    # otherwise nudge time and retry
                    current_time = current_time + timedelta(minutes=5)
                    continue

                # Weekly capacity tracking in-memory to avoid overscheduling beyond cap in this run
                try:
                    eid = employee.EmployeeID
                    used = employee_week_minutes.get(eid, 0)
                    remaining_cap = max(0, 2160 - used)
                    # conservative cap; actual enforcement done in validator
                    if remaining_cap < 30:
                        break
                    if service_minutes > remaining_cap:
                        service_minutes = remaining_cap
                        proposed_end = proposed_start + timedelta(minutes=service_minutes)
                        end_iso = proposed_end.replace(second=0, microsecond=0).isoformat()
                except Exception:
                    pass

                # Handle RequiredCarerSupport (concurrent carers)
                req_support = 1
                try:
                    req_support = int(getattr(chosen_patient, 'RequiredCarerSupport', 1) or 1)
                except Exception:
                    req_support = 1

                if req_support >= 2:
                    # Attempt to find a second employee for the same time window
                    second_candidates = self._get_candidate_employees(start_iso, end_iso, employee.EmployeeID)
                    # Prefer nearest by travel and transport mode (Car > PT > Bicycle > Walking), non-junior first
                    second_ranking: List[Tuple[int, int, int, Employee]] = []
                    for emp2 in second_candidates:
                        t2 = self._calc_travel_minutes(emp2, chosen_patient)
                        # validate emp2
                        v2 = self.validator.validate_proposed_assignment(
                            employee_id=emp2.EmployeeID,
                            patient_id=chosen_patient.PatientID,
                            service_type=inferred_enum,
                            start_iso=start_iso,
                            end_iso=end_iso,
                            duration_minutes=int(service_minutes),
                            allow_same_day_dup_for_meal_prep=is_meal,
                        )
                        if not v2:
                            is_jun = 1 if (getattr(emp2, 'RoleLevel', '') or '').strip().lower() == 'junior' else 0
                            tp = self._transport_priority(getattr(emp2, 'TransportMode', None))
                            second_ranking.append((is_jun, t2, tp, emp2))
                    if not second_ranking:
                        # cannot satisfy concurrency; record reason and try next patient/time
                        try:
                            s = patient_reasons.get(chosen_patient.PatientID)
                            if s is None:
                                s = set()
                                patient_reasons[chosen_patient.PatientID] = s
                            s.add("Cannot satisfy RequiredCarerSupport=2 concurrently")
                        except Exception:
                            pass
                        current_time = current_time + timedelta(minutes=5)
                        continue
                    second_ranking.sort(key=lambda x: (x[0], x[1], x[2]))
                    emp2 = second_ranking[0][3]

                    # Transactionally insert both
                    ok = self.db_manager.begin_transaction()
                    try:
                        aid1 = self.db_manager.log_assignment({
                            "employee_id": employee.EmployeeID,
                            "employee_name": employee.Name,
                            "patient_id": chosen_patient.PatientID,
                            "patient_name": chosen_patient.PatientName,
                            "service_type": inferred_enum.value,
                            "assigned_time": start_iso,
                            "start_time": start_iso,
                            "end_time": end_iso,
                            "estimated_duration": service_minutes,
                            "travel_time": travel_minutes,
                            "priority_score": 5.0,
                            "assignment_reason": "Scheduled by core engine (RCS=2)",
                        })
                        aid2 = self.db_manager.log_assignment({
                            "employee_id": emp2.EmployeeID,
                            "employee_name": emp2.Name,
                            "patient_id": chosen_patient.PatientID,
                            "patient_name": chosen_patient.PatientName,
                            "service_type": inferred_enum.value,
                            "assigned_time": start_iso,
                            "start_time": start_iso,
                            "end_time": end_iso,
                            "estimated_duration": service_minutes,
                            "travel_time": self._calc_travel_minutes(emp2, chosen_patient),
                            "priority_score": 5.0,
                            "assignment_reason": "Scheduled by core engine (RCS=2)",
                        })
                        self.db_manager.commit()
                    except Exception:
                        self.db_manager.rollback()
                        current_time = current_time + timedelta(minutes=5)
                        continue
                else:
                    # Persist single assignment
                    aid = self.db_manager.log_assignment({
                        "employee_id": employee.EmployeeID,
                        "employee_name": employee.Name,
                        "patient_id": chosen_patient.PatientID,
                        "patient_name": chosen_patient.PatientName,
                        "service_type": inferred_enum.value,
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
                employee_got_assignment = True
                # Deduct remaining demand for non-meal services; for meal-prep we want 3x30 total per day
                if is_meal:
                    # reduce demand by 30; initial demand was 90
                    patient_daily_minutes[chosen_patient.PatientID] = max(0, remaining - 30)
                else:
                    patient_daily_minutes[chosen_patient.PatientID] = max(0, remaining - service_minutes)
                current_time = proposed_end
                current_location = f"{chosen_patient.Address}, {chosen_patient.PostCode}" if chosen_patient.PostCode and chosen_patient.PostCode not in chosen_patient.Address else chosen_patient.Address
                # Update weekly usage
                try:
                    employee_week_minutes[eid] = employee_week_minutes.get(eid, 0) + int(service_minutes)
                except Exception:
                    pass
                # Track meal-prep count (in-memory; DB is source-of-truth)
                if is_meal:
                    meal_visits_done[chosen_patient.PatientID] = meal_visits_done.get(chosen_patient.PatientID, 0) + 1

            # After finishing this employee's shift, if they got no assignments today, log unassigned reason for employee
            try:
                todays_rows = self.db_manager.get_employee_assignments_for_date(employee.EmployeeID, day_date.isoformat())
                if (todays_rows is None) or (len(todays_rows) == 0):
                    emp_reasons = self._diagnose_employee_unassigned(employee, day_date, patient_daily_minutes)
                    # Build attempts for this employee against top candidate patients
                    attempts_e: List[Dict[str, Any]] = []
                    try:
                        earliest, latest = self._parse_shift(employee)
                        shift_start = datetime.combine(day_date, earliest)
                        # rank patients with demand by travel time
                        ranked_patients: List[Tuple[int, Patient]] = []
                        for p in self.data_processor.patients:
                            if patient_daily_minutes.get(p.PatientID, 0) <= 0:
                                continue
                            if not self._employee_can_serve(employee, p):
                                continue
                            ranked_patients.append((self._calc_travel_minutes(employee, p), p))
                        ranked_patients.sort(key=lambda x: x[0])
                        for tmin, p in ranked_patients[:5]:
                            try:
                                inferred_str = self._infer_service_type(p)
                                try:
                                    inferred_enum = ServiceType(inferred_str)
                                except Exception:
                                    inferred_enum = ServiceType.PERSONAL_CARE
                                start_iso = (shift_start + timedelta(minutes=int(tmin))).replace(second=0, microsecond=0).isoformat()
                                default_minutes = self.data_processor.get_default_service_duration(inferred_enum)
                                end_iso = (datetime.fromisoformat(start_iso) + timedelta(minutes=int(default_minutes))).replace(second=0, microsecond=0).isoformat()
                                violations = self.validator.validate_with_details(
                                    employee_id=employee.EmployeeID,
                                    patient_id=p.PatientID,
                                    service_type=inferred_enum,
                                    start_iso=start_iso,
                                    end_iso=end_iso,
                                    duration_minutes=int(default_minutes),
                                    allow_same_day_dup_for_meal_prep=(inferred_enum == ServiceType.MEAL_PREP),
                                )
                                attempts_e.append({
                                    "employee_id": employee.EmployeeID,
                                    "employee_name": getattr(employee, 'Name', employee.EmployeeID),
                                    "patient_id": p.PatientID,
                                    "patient_name": getattr(p, 'PatientName', p.PatientID),
                                    "service_type": inferred_enum.value,
                                    "start_time": start_iso,
                                    "end_time": end_iso,
                                    "violations": violations,
                                })
                            except Exception:
                                continue
                    except Exception:
                        pass
                    ctx = {
                        "role_level": getattr(employee, 'RoleLevel', None),
                        "qualification": getattr(employee, 'Qualification', None).value if getattr(employee, 'Qualification', None) else None,
                        "languages": getattr(employee, 'LanguageSpoken', ''),
                        "transport_mode": getattr(employee, 'TransportMode', None).value if getattr(employee, 'TransportMode', None) else None,
                        "earliest_start": getattr(employee, 'EarliestStart', None),
                        "latest_end": getattr(employee, 'LatestEnd', None),
                        "issues": self._build_employee_issues(employee.EmployeeID, day_date.isoformat(), emp_reasons),
                        "attempts": attempts_e,
                    }
                    self.db_manager.log_unassigned('employee', employee.EmployeeID, day_date.isoformat(), emp_reasons or ["No feasible assignments found"], ctx)
            except Exception:
                pass

        # After all employees processed, log unassigned patients for the day
        try:
            for patient in self.data_processor.patients:
                remaining = patient_daily_minutes.get(patient.PatientID, 0)
                if remaining <= 0:
                    continue
                # Confirm none assigned in DB for this date
                todays = self.db_manager.get_assignments_for_patient_on_date(patient.PatientID, day_date.isoformat())
                if not todays:
                    base_reasons = list(patient_reasons.get(patient.PatientID, set()))
                    extra = self._diagnose_patient_unassigned(patient, day_date)
                    # Merge and dedupe
                    reason_set = set(base_reasons)
                    for r in extra:
                        reason_set.add(r)
                    # Build attempts for this patient against top candidate employees
                    attempts_p: List[Dict[str, Any]] = []
                    try:
                        ranked_emps: List[Tuple[int, Employee]] = []
                        for emp in self.data_processor.employees:
                            if not self._employee_can_serve(emp, patient):
                                continue
                            ranked_emps.append((self._calc_travel_minutes(emp, patient), emp))
                        ranked_emps.sort(key=lambda x: x[0])
                        for tmin, emp in ranked_emps[:5]:
                            try:
                                earliest, latest = self._parse_shift(emp)
                                start_dt = datetime.combine(day_date, earliest) + timedelta(minutes=int(tmin))
                                inferred_str = self._infer_service_type(patient)
                                try:
                                    inferred_enum = ServiceType(inferred_str)
                                except Exception:
                                    inferred_enum = ServiceType.PERSONAL_CARE
                                default_minutes = self.data_processor.get_default_service_duration(inferred_enum)
                                start_iso = start_dt.replace(second=0, microsecond=0).isoformat()
                                end_iso = (start_dt + timedelta(minutes=int(default_minutes))).replace(second=0, microsecond=0).isoformat()
                                violations = self.validator.validate_with_details(
                                    employee_id=emp.EmployeeID,
                                    patient_id=patient.PatientID,
                                    service_type=inferred_enum,
                                    start_iso=start_iso,
                                    end_iso=end_iso,
                                    duration_minutes=int(default_minutes),
                                    allow_same_day_dup_for_meal_prep=(inferred_enum == ServiceType.MEAL_PREP),
                                )
                                attempts_p.append({
                                    "employee_id": emp.EmployeeID,
                                    "employee_name": getattr(emp, 'Name', emp.EmployeeID),
                                    "patient_id": patient.PatientID,
                                    "patient_name": getattr(patient, 'PatientName', patient.PatientID),
                                    "service_type": inferred_enum.value,
                                    "start_time": start_iso,
                                    "end_time": end_iso,
                                    "violations": violations,
                                })
                            except Exception:
                                continue
                    except Exception:
                        pass
                    # Build richer context with inline issues for verification
                    ctx = {
                        "required_support": getattr(patient, 'RequiredSupport', None),
                        "required_hours_per_week": getattr(patient, 'RequiredHoursOfSupport', None),
                        "language_preference": getattr(patient, 'LanguagePreference', None),
                        "preference_of_carer": getattr(patient, 'PreferenceOfCarer', None),
                        "required_carer_support": getattr(patient, 'RequiredCarerSupport', None),
                        "meal_prep_required": bool(getattr(patient, 'MealPrepRequired', False)),
                        "days_of_support": getattr(patient, 'DaysOfSupport', None),
                        "sat_sun_support": getattr(patient, 'SatSunSupport', None),
                        # Inline verification artifacts: show overlapping rows and reasons
                        "issues": self._build_patient_issues(patient.PatientID, day_date.isoformat(), reason_set),
                        "attempts": attempts_p,
                    }
                    self.db_manager.log_unassigned('patient', patient.PatientID, day_date.isoformat(), list(reason_set) or ["No feasible employee/time window found"], ctx)
        except Exception:
            pass

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

    def _diagnose_patient_unassigned(self, patient: Patient, day_date: date) -> List[str]:
        reasons: List[str] = []
        try:
            # Eligibility checks across workforce
            employees: List[Employee] = list(self.data_processor.employees)
            if not employees:
                return ["No employees loaded"]

            # DaysOfSupport gate should already exclude, but if present, record
            try:
                if not self._is_day_supported(getattr(patient, 'DaysOfSupport', ''), day_date):
                    reasons.append("Patient not scheduled for support on this day (DaysOfSupport)")
            except Exception:
                pass

            # Medication nurse requirement
            if "medicine" in (getattr(patient, 'RequiredSupport', '') or '').lower():
                nurses = [e for e in employees if getattr(e, 'Qualification', None) == QualificationEnum.NURSE]
                if not nurses:
                    reasons.append("No nurse available for medication")

            # Gender preference
            pref = (getattr(patient, 'PreferenceOfCarer', '') or '').strip().lower()
            if pref in ("male", "female"):
                has_gender = any((getattr(e, 'Gender', None).value or '').strip().lower() == pref for e in employees if getattr(e, 'Gender', None) is not None)
                if not has_gender:
                    reasons.append("No employee matches gender preference")

            # Language preference (non-English)
            lang_pref = (getattr(patient, 'LanguagePreference', 'English') or 'English').strip().lower()
            if lang_pref and lang_pref != 'english':
                has_lang = False
                for e in employees:
                    try:
                        if lang_pref in (getattr(e, 'LanguageSpoken', '') or '').strip().lower():
                            has_lang = True
                            break
                    except Exception:
                        continue
                if not has_lang:
                    reasons.append("No employee speaks patient's preferred language")

            # RequiredCarerSupport availability
            try:
                rcs = int(getattr(patient, 'RequiredCarerSupport', 1) or 1)
            except Exception:
                rcs = 1
            elig = [e for e in employees if self._employee_can_serve(e, patient)]
            if rcs >= 2 and len(elig) < 2:
                reasons.append("Insufficient eligible employees to satisfy RequiredCarerSupport=2")

            # Weekly capacity exhausted for eligible employees
            if elig:
                week_start = self._next_monday(day_date)
                wk_start_iso = datetime.combine(week_start, dtime(0,0)).isoformat()
                wk_end_iso = datetime.combine(week_start + timedelta(days=6), dtime(23,59)).isoformat()
                all_exhausted = True
                for e in elig:
                    used = self.db_manager.sum_employee_minutes_for_week(e.EmployeeID, wk_start_iso, wk_end_iso)
                    role = (getattr(e, 'RoleLevel', '') or '').strip().lower()
                    cap = getattr(e, 'weekly_capacity_minutes', None)
                    cap = cap if isinstance(cap, int) and cap > 0 else (1200 if role == 'junior' else 2160)
                    if used + 30 <= cap:
                        all_exhausted = False
                        break
                if all_exhausted:
                    reasons.append("All eligible employees at or near weekly capacity")

            # Fallback generic reason
            if not reasons:
                reasons.append("Scheduling constraints (overlaps/shift bounds) prevented assignment")
        except Exception:
            reasons = ["No feasible employee/time window found"]
        return reasons

    def _build_patient_issues(self, patient_id: str, date_iso: str, reasons: set[str]) -> List[Dict[str, str]]:
        """Construct a compact issues list with verification artifacts for the unassigned record.

        Each issue is a dict with keys such as 'type', 'details', and optionally 'assignment_ids'.
        """
        issues: List[Dict[str, str]] = []
        # If any reason references concurrency or overlap, attach overlapping patient assignments that day
        try:
            # Build a representative window for the day to scan overlaps: 00:00 to 23:59
            start_iso = f"{date_iso}T00:00:00"
            end_iso = f"{date_iso}T23:59:00"
            overlaps = self.db_manager.get_overlapping_assignments_for_patient(patient_id, start_iso, end_iso)
            if overlaps:
                ids = [str(r.get('id')) for r in overlaps]
                details = ", ".join([f"#{r.get('id')} {r.get('start_time')}→{r.get('end_time')} (emp {r.get('employee_id')})" for r in overlaps[:6]])
                issues.append({
                    "type": "patient_overlaps",
                    "assignment_ids": ",".join(ids),
                    "details": f"Existing overlapping assignments that day: {details}"
                })
        except Exception:
            pass
        # Parse reasons to extract conflicting assignment IDs (from validator details)
        try:
            text_reasons = list(reasons or [])
            id_set: set[str] = set()
            for msg in text_reasons:
                if not isinstance(msg, str):
                    continue
                for m in re.finditer(r"assignment\s*#(\d+)", msg.lower()):
                    id_set.add(m.group(1))
            if id_set:
                details_parts: List[str] = []
                for sid in list(id_set)[:6]:
                    try:
                        row = self.db_manager.get_assignment_by_id(int(sid))
                        if row:
                            details_parts.append(f"#{sid} {row.get('start_time')}→{row.get('end_time')} (emp {row.get('employee_id')})")
                        else:
                            details_parts.append(f"#{sid}")
                    except Exception:
                        details_parts.append(f"#{sid}")
                issues.append({
                    "type": "employee_overlaps",
                    "assignment_ids": ",".join(sorted(id_set)),
                    "details": ", ".join(details_parts)
                })
        except Exception:
            pass

        # Echo raw reasons as separate entries for quick rendering
        try:
            for r in list(reasons or []):
                issues.append({"type": "reason", "details": r})
        except Exception:
            pass
        return issues

    def _build_employee_issues(self, employee_id: str, date_iso: str, reasons: List[str]) -> List[Dict[str, str]]:
        """Construct issues for an employee unassigned record.

        Attaches same-day assignments for the employee and echoes reasons.
        """
        out: List[Dict[str, str]] = []
        try:
            rows = self.db_manager.get_employee_assignments_for_date(employee_id, date_iso)
            if rows:
                ids = [str(r.get('id')) for r in rows if r.get('id') is not None]
                details = ", ".join([f"#{r.get('id')} {r.get('start_time')}→{r.get('end_time')} (pat {r.get('patient_id')})" for r in rows[:6]])
                out.append({
                    "type": "employee_same_day_assignments",
                    "assignment_ids": ",".join(ids),
                    "details": f"Existing assignments that day: {details}"
                })
        except Exception:
            pass
        # Parse reasons for explicit conflicting assignment references
        try:
            id_set: set[str] = set()
            for msg in reasons or []:
                if not isinstance(msg, str):
                    continue
                for m in re.finditer(r"assignment\s*#(\d+)", msg.lower()):
                    id_set.add(m.group(1))
            if id_set:
                details_parts: List[str] = []
                for sid in list(id_set)[:6]:
                    try:
                        row = self.db_manager.get_assignment_by_id(int(sid))
                        if row:
                            details_parts.append(f"#{sid} {row.get('start_time')}→{row.get('end_time')} (pat {row.get('patient_id')})")
                        else:
                            details_parts.append(f"#{sid}")
                    except Exception:
                        details_parts.append(f"#{sid}")
                out.append({
                    "type": "employee_overlaps",
                    "assignment_ids": ",".join(sorted(id_set)),
                    "details": ", ".join(details_parts)
                })
        except Exception:
            pass
        try:
            for r in reasons or []:
                out.append({"type": "reason", "details": r})
        except Exception:
            pass
        return out

    def _diagnose_employee_unassigned(self, employee: Employee, day_date: date, patient_daily_minutes: Dict[str, int]) -> List[str]:
        reasons: List[str] = []
        try:
            # Determine patients with demand today
            patients_with_demand: List[Patient] = []
            for p in self.data_processor.patients:
                if patient_daily_minutes.get(p.PatientID, 0) and patient_daily_minutes.get(p.PatientID, 0) > 0:
                    patients_with_demand.append(p)

            if not patients_with_demand:
                return ["No patients required support today (after gating)"]

            # Eligibility filter
            eligible_patients = [p for p in patients_with_demand if self._employee_can_serve(employee, p)]
            if not eligible_patients:
                # Diagnose which filter likely blocked
                any_medicine = any("medicine" in (getattr(p, 'RequiredSupport', '') or '').lower() for p in patients_with_demand)
                if any_medicine and getattr(employee, 'Qualification', None) != QualificationEnum.NURSE:
                    reasons.append("Not qualified nurse for medication cases")
                # Gender and language cases cannot be summarized easily across multiple patients; provide generic
                reasons.append("No matching patients given gender/language preferences")
                return reasons

            # If eligible exist, then likely time/overlap/capacity
            # Check weekly capacity
            week_start = self._next_monday(day_date)
            wk_start_iso = datetime.combine(week_start, dtime(0,0)).isoformat()
            wk_end_iso = datetime.combine(week_start + timedelta(days=6), dtime(23,59)).isoformat()
            used = self.db_manager.sum_employee_minutes_for_week(employee.EmployeeID, wk_start_iso, wk_end_iso)
            role = (getattr(employee, 'RoleLevel', '') or '').strip().lower()
            cap = getattr(employee, 'weekly_capacity_minutes', None)
            cap = cap if isinstance(cap, int) and cap > 0 else (1200 if role == 'junior' else 2160)
            if used + 30 > cap:
                reasons.append("Weekly capacity exhausted")

            # Overlap/shift bounds generic
            reasons.append("Time windows conflicted with shift bounds or existing assignments")
        except Exception:
            reasons = ["No feasible patients/time windows"]
        return reasons

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

        # Gender preference
        try:
            gp = (getattr(patient, 'PreferenceOfCarer', '') or '').strip().lower()
            if gp in ("male", "female"):
                if (employee.Gender.value or '').strip().lower() != gp:
                    return False
        except Exception:
            pass

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

    def _is_day_supported(self, days_str: str, on_date: date) -> bool:
        try:
            supported = self._normalize_days_of_support(days_str)
            return on_date.weekday() in supported if supported is not None else True
        except Exception:
            return True

    def _normalize_days_of_support(self, days_str: str) -> Optional[set[int]]:
        try:
            if not days_str:
                return None
            raw = (days_str or '').replace(' ', '')
            tokens = [t.strip().lower() for t in raw.split(',') if t.strip() != '']
            if not tokens:
                return None
            # Map tokens to weekday ints
            mapping = {
                'm': 0, 'mon': 0, 'monday': 0,
                't': 1, 'tu': 1, 'tue': 1, 'tues': 1, 'tuesday': 1,
                'w': 2, 'wed': 2, 'wednesday': 2,
                'th': 3, 'thu': 3, 'thurs': 3, 'thursday': 3,
                'f': 4, 'fri': 4, 'friday': 4,
                'sa': 5, 'sat': 5, 'saturday': 5,
                'su': 6, 'sun': 6, 'sunday': 6,
                's': None,  # ambiguous token used twice for weekend sequences; handle separately
            }
            result: list[int] = []
            s_count = tokens.count('s')
            for tok in tokens:
                if tok == 's':
                    # If appears twice, interpret as Sat and Sun
                    if s_count >= 2:
                        if 5 not in result:
                            result.append(5)
                        if 6 not in result:
                            result.append(6)
                    else:
                        # Default single 's' to Saturday
                        if 5 not in result:
                            result.append(5)
                    continue
                val = mapping.get(tok)
                if val is not None and val not in result:
                    result.append(val)
            return set(result) if result else None
        except Exception:
            return None
    def _transport_priority(self, mode) -> int:
        try:
            val = getattr(mode, 'value', str(mode))
            key = (val or '').strip().lower()
        except Exception:
            key = ''
        mapping = {
            'car': 0,
            'public transport': 1,
            'bicycle': 2,
            'walking': 3,
        }
        return mapping.get(key, 5)



    def run_post_generation_diagnostics(self, week_start_iso: str, week_end_iso: str, top_k: Optional[int] = None) -> Dict[str, int]:
        """Enrich unassigned rows after weekly rota generation.

        For each unassigned patient/employee in the given week range:
        - Loop through counterpart candidates ranked by travel time (all by default)
        - Run validate_with_details for a representative timeslot in shift
        - Append attempts and compact issues/suggestions context via log_unassigned

        Returns simple counters for observability.
        """
        enriched_patients = 0
        enriched_employees = 0
        try:
            # Patients
            patient_rows = self.db_manager.get_unassigned_patients_for_week(week_start_iso, week_end_iso)
            for row in patient_rows:
                try:
                    pid = row.get('patient_id')
                    day_iso = row.get('date')
                    pat = self.data_processor.get_patient_by_id(pid)
                    if not pat:
                        continue
                    # Always recompute full attempts set across all employees for this patient
                    # Rank employees by travel time regardless of eligibility; fallback to 0 on travel failure
                    ranked: List[Tuple[int, Employee]] = []
                    for emp in self.data_processor.employees:
                        try:
                            tmin = self._calc_travel_minutes(emp, pat)
                        except Exception:
                            tmin = 0
                        ranked.append((int(tmin) if isinstance(tmin, int) else 0, emp))
                    ranked.sort(key=lambda x: x[0])
                    attempts_p: List[Dict[str, Any]] = []
                    potentials: List[Dict[str, Any]] = []
                    subset = ranked if (top_k is None) else ranked[:max(1, int(top_k))]
                    for tmin, emp in subset:
                        try:
                            earliest, _latest = self._parse_shift(emp)
                            # Representative window: shift start + travel, default duration for inferred service
                            inferred_str = self._infer_service_type(pat)
                            try:
                                inferred_enum = ServiceType(inferred_str)
                            except Exception:
                                inferred_enum = ServiceType.PERSONAL_CARE
                            base_dt = datetime.combine(datetime.fromisoformat(f"{day_iso}T00:00:00").date(), earliest)
                            start_iso = (base_dt + timedelta(minutes=int(tmin))).replace(second=0, microsecond=0).isoformat()
                            default_minutes = self.data_processor.get_default_service_duration(inferred_enum)
                            end_iso = (datetime.fromisoformat(start_iso) + timedelta(minutes=int(default_minutes))).replace(second=0, microsecond=0).isoformat()
                            viols = self.validator.validate_with_details(
                                employee_id=emp.EmployeeID,
                                patient_id=pid,
                                service_type=inferred_enum,
                                start_iso=start_iso,
                                end_iso=end_iso,
                                duration_minutes=int(default_minutes),
                                allow_same_day_dup_for_meal_prep=(inferred_enum == ServiceType.MEAL_PREP),
                            )
                            attempts_p.append({
                                "employee_id": emp.EmployeeID,
                                "employee_name": getattr(emp, 'Name', emp.EmployeeID),
                                "patient_id": pid,
                                "patient_name": getattr(pat, 'PatientName', pid),
                                "service_type": inferred_enum.value,
                                "start_time": start_iso,
                                "end_time": end_iso,
                                "violations": list(viols),
                            })
                            potentials.append({
                                "employee_id": emp.EmployeeID,
                                "employee_name": getattr(emp, 'Name', emp.EmployeeID),
                                "travel_minutes": int(tmin),
                                "violation_count": len(viols),
                            })
                        except Exception:
                            continue
                    # Build compact issues (reuse helper) and attach suggestions
                    issues = self._build_patient_issues(pid, day_iso, set(row.get('reasons') or []))
                    diag_ctx = {
                        "issues": issues,
                        "attempts": attempts_p,
                        "suggestions": {"potential_employees": potentials},
                    }
                    # Append-only log so weekly aggregator merges arrays
                    self.db_manager.log_unassigned('patient', pid, day_iso, [], diag_ctx)
                    enriched_patients += 1
                except Exception:
                    continue
        except Exception:
            pass
        try:
            # Employees
            employee_rows = self.db_manager.get_unassigned_employees_for_week(week_start_iso, week_end_iso)
            for row in employee_rows:
                try:
                    eid = row.get('employee_id')
                    day_iso = row.get('date')
                    emp = self.data_processor.get_employee_by_id(eid)
                    if not emp:
                        continue
                    # Always recompute full attempts set across all patients for this employee; travel fallback 0
                    ranked: List[Tuple[int, Patient]] = []
                    for pat in self.data_processor.patients:
                        try:
                            tmin = self._calc_travel_minutes(emp, pat)
                        except Exception:
                            tmin = 0
                        ranked.append((int(tmin) if isinstance(tmin, int) else 0, pat))
                    ranked.sort(key=lambda x: x[0])
                    attempts_e: List[Dict[str, Any]] = []
                    potentials: List[Dict[str, Any]] = []
                    subset = ranked if (top_k is None) else ranked[:max(1, int(top_k))]
                    for tmin, pat in subset:
                        try:
                            earliest, _latest = self._parse_shift(emp)
                            inferred_str = self._infer_service_type(pat)
                            try:
                                inferred_enum = ServiceType(inferred_str)
                            except Exception:
                                inferred_enum = ServiceType.PERSONAL_CARE
                            base_dt = datetime.combine(datetime.fromisoformat(f"{day_iso}T00:00:00").date(), earliest)
                            start_iso = (base_dt + timedelta(minutes=int(tmin))).replace(second=0, microsecond=0).isoformat()
                            default_minutes = self.data_processor.get_default_service_duration(inferred_enum)
                            end_iso = (datetime.fromisoformat(start_iso) + timedelta(minutes=int(default_minutes))).replace(second=0, microsecond=0).isoformat()
                            viols = self.validator.validate_with_details(
                                employee_id=eid,
                                patient_id=pat.PatientID,
                                service_type=inferred_enum,
                                start_iso=start_iso,
                                end_iso=end_iso,
                                duration_minutes=int(default_minutes),
                                allow_same_day_dup_for_meal_prep=(inferred_enum == ServiceType.MEAL_PREP),
                            )
                            attempts_e.append({
                                "employee_id": eid,
                                "employee_name": getattr(emp, 'Name', eid),
                                "patient_id": pat.PatientID,
                                "patient_name": getattr(pat, 'PatientName', pat.PatientID),
                                "service_type": inferred_enum.value,
                                "start_time": start_iso,
                                "end_time": end_iso,
                                "violations": list(viols),
                            })
                            potentials.append({
                                "patient_id": pat.PatientID,
                                "patient_name": getattr(pat, 'PatientName', pat.PatientID),
                                "travel_minutes": int(tmin),
                                "violation_count": len(viols),
                            })
                        except Exception:
                            continue
                    issues = self._build_employee_issues(eid, day_iso, row.get('reasons') or [])
                    diag_ctx = {
                        "issues": issues,
                        "attempts": attempts_e,
                        "suggestions": {"potential_patients": potentials},
                    }
                    self.db_manager.log_unassigned('employee', eid, day_iso, [], diag_ctx)
                    enriched_employees += 1
                except Exception:
                    continue
        except Exception:
            pass
        return {"enriched_patients": enriched_patients, "enriched_employees": enriched_employees}

