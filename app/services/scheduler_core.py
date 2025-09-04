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

    def generate_weekly_rota(self, start_date: Optional[date] = None) -> Dict[str, int]:
        """Generate assignments for the next 7 days.

        Returns summary counts.
        """
        if start_date is None:
            start_date = self._next_monday(date.today())

        total_created = 0
        for day_offset in range(7):
            day_date = start_date + timedelta(days=day_offset)
            created = self._generate_daily_rota(day_date)
            total_created += created
            logger.info(f"SchedulerCore: created {created} assignments on {day_date.isoformat()}")

        return {"created": total_created}

    def _generate_daily_rota(self, day_date: date) -> int:
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
            except Exception:
                daily = self._estimate_patient_daily_minutes(patient)
            if daily > 0:
                patient_daily_minutes[patient.PatientID] = daily

        created_count = 0

        for employee in self.data_processor.employees:
            earliest, latest = self._parse_shift(employee)
            if earliest >= latest:
                continue

            current_time = datetime.combine(day_date, earliest)
            shift_end = datetime.combine(day_date, latest)
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
                default_minutes = self.data_processor.get_default_service_duration(inferred_enum)
                service_minutes = min(default_minutes, remaining)

                # Compute proposed times
                proposed_start = current_time + timedelta(minutes=travel_minutes)
                proposed_end = proposed_start + timedelta(minutes=service_minutes)

                # Ensure fit in shift; shrink if needed
                if proposed_end > shift_end:
                    # shrink to fit
                    fit_minutes = int((shift_end - proposed_start).total_seconds() // 60)
                    if fit_minutes < 15:
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

                # Skip if employee already served this patient today
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
        if "exercise" in supports:
            return "exercise"
        if "compan" in supports:
            return "companionship"
        if "personal" in supports or "care" in supports:
            return "personal_care"
        return "personal_care"

    def _next_monday(self, today: date) -> date:
        # Monday is 0; if today is Monday, use today
        days_ahead = (0 - today.weekday()) % 7
        return today + timedelta(days=days_ahead)


