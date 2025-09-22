import React, { useEffect, useMemo, useRef, useState } from 'react';
import Modal from '../components/Modal';
import { 
  fetchWeekAssignments, 
  fetchEmployeesWeeklySummary, 
  fetchEmployeeDetails, 
  fetchPatientDetails 
} from '../services/scheduleService';

function startOfWeek(date) {
  const d = new Date(date);
  const day = d.getDay(); // 0=Sun..6=Sat
  const diff = (day === 0 ? -6 : 1) - day; // adjust to Monday
  d.setDate(d.getDate() + diff);
  d.setHours(0,0,0,0);
  return d;
}

function formatISODate(d) {
  const dd = new Date(d);
  dd.setHours(0,0,0,0);
  return dd.toISOString().slice(0,10);
}

function endOfWeek(monday) {
  const d = new Date(monday);
  d.setDate(d.getDate() + 6);
  d.setHours(23,59,0,0);
  return d;
}

const transportBadge = (mode) => {
  const map = { 'Car': 'bg-blue-50 text-blue-700', 'Public Transport': 'bg-purple-50 text-purple-700', 'Bicycle': 'bg-emerald-50 text-emerald-700', 'Walking': 'bg-orange-50 text-orange-700' };
  return map[mode] || 'bg-gray-50 text-gray-700';
};

export default function Timeline() {
  const [view, setView] = useState('employees'); // 'employees' | 'patients'
  const [weekStart, setWeekStart] = useState(() => startOfWeek(new Date()));
  const [assignments, setAssignments] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selEmployee, setSelEmployee] = useState(null);
  const [selPatient, setSelPatient] = useState(null);
  const [detail, setDetail] = useState(null);
  const [hScroll, setHScroll] = useState(0);
  const [empRowHeights, setEmpRowHeights] = useState([]);
  const [patRowHeights, setPatRowHeights] = useState([]);

  // Refs for synchronized scrolling
  const bodyXRef = useRef(null);
  const leftYRef = useRef(null);
  const rightYRef = useRef(null);
  const leftYRefPatients = useRef(null);
  const rightYRefPatients = useRef(null);
  const syncingY = useRef(false);

  // Day column width; will adapt to container width to fill screen without shrinking below a minimum
  const containerRef = useRef(null);
  const [dayColPx, setDayColPx] = useState(240);

  // Resize observer to fill available width (without overlapping sidebar)
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const ro = new ResizeObserver(() => {
      try {
        const w = el.clientWidth;
        const minPx = 180; // keep cards readable
        const target = Math.max(minPx, Math.floor(w / 7));
        setDayColPx(target);
      } catch {}
    });
    ro.observe(el);
    return () => {
      try { ro.disconnect(); } catch {}
    };
  }, []);

  const weekEnd = useMemo(() => endOfWeek(weekStart), [weekStart]);
  const days = useMemo(() => Array.from({ length: 7 }, (_, i) => {
    const d = new Date(weekStart);
    d.setDate(weekStart.getDate() + i);
    return d;
  }), [weekStart]);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const [{ assignments: weekRows }, { employees: emps }] = await Promise.all([
          fetchWeekAssignments(formatISODate(weekStart), formatISODate(weekEnd)),
          fetchEmployeesWeeklySummary(formatISODate(weekStart), formatISODate(weekEnd)),
        ]);
        setAssignments(weekRows || []);
        setEmployees(emps || []);
      } catch (e) {
        setError(e.message || 'Failed to load');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [weekStart, weekEnd]);

  // Measure row heights for employees grid -> align left pane rows
  useEffect(() => {
    if (!rightYRef.current) return;
    const nodes = rightYRef.current.querySelectorAll('[data-emp-row="true"]');
    const heights = Array.from(nodes).map(n => n.offsetHeight);
    setEmpRowHeights(heights);
  }, [assignments, employees, view]);

  // Measure row heights for patients grid -> align left pane rows
  useEffect(() => {
    if (!rightYRefPatients.current) return;
    const nodes = rightYRefPatients.current.querySelectorAll('[data-pat-row="true"]');
    const heights = Array.from(nodes).map(n => n.offsetHeight);
    setPatRowHeights(heights);
  }, [assignments, view]);

  const byEmployee = useMemo(() => {
    const map = new Map();
    for (const row of assignments) {
      const key = row.employee_id;
      if (!map.has(key)) map.set(key, []);
      map.get(key).push(row);
    }
    for (const list of map.values()) list.sort((a,b) => (a.start_time || '').localeCompare(b.start_time || ''));
    return map;
  }, [assignments]);

  const byPatient = useMemo(() => {
    const map = new Map();
    for (const row of assignments) {
      const key = row.patient_id;
      if (!map.has(key)) map.set(key, []);
      map.get(key).push(row);
    }
    for (const list of map.values()) list.sort((a,b) => (a.start_time || '').localeCompare(b.start_time || ''));
    return map;
  }, [assignments]);

  const dayKey = (iso) => (iso || '').slice(0,10);

  const onCardClick = async (row) => {
    try {
      const pat = await fetchPatientDetails(row.patient_id);
      setDetail({ type: 'patient', data: pat, assignment: row });
    } catch {
      setDetail({ type: 'assignment', data: row });
    }
  };

  const onEmployeeClick = async (employeeId) => {
    try {
      const emp = await fetchEmployeeDetails(employeeId);
      const meta = employees.find(e => e.employee_id === employeeId) || {};
      setSelEmployee({ ...emp, remaining_minutes: meta.remaining_minutes, used_minutes: meta.used_minutes, weekly_capacity_minutes: meta.weekly_capacity_minutes });
    } catch {}
  };

  const onPatientHeaderClick = async (patientId) => {
    try {
      const pat = await fetchPatientDetails(patientId);
      setSelPatient(pat);
    } catch {}
  };

  const scrollXRef = React.useRef(null);
  const scrollYRef = React.useRef(null);

  const moveWeek = (delta) => {
    const d = new Date(weekStart);
    d.setDate(d.getDate() + delta * 7);
    setWeekStart(startOfWeek(d));
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <button className="px-3 py-1.5 rounded border border-gray-300 text-gray-700" onClick={() => moveWeek(-1)}>Prev</button>
          <div className="text-sm text-gray-600">
            Week: {formatISODate(weekStart)} → {formatISODate(weekEnd)}
          </div>
          <button className="px-3 py-1.5 rounded border border-gray-300 text-gray-700" onClick={() => moveWeek(1)}>Next</button>
        </div>
        <div className="flex items-center gap-2">
          <button className={`px-3 py-1.5 rounded ${view==='employees'?'bg-blue-600 text-white':'border border-gray-300 text-gray-700'}`} onClick={() => setView('employees')}>Employees view</button>
          <button className={`px-3 py-1.5 rounded ${view==='patients'?'bg-blue-600 text-white':'border border-gray-300 text-gray-700'}`} onClick={() => setView('patients')}>Patients view</button>
        </div>
      </div>

      {loading && <div className="text-gray-600">Loading weekly schedule...</div>}
      {error && <div className="text-red-600">{error}</div>}

      {!loading && view === 'employees' && (
        <div className="border rounded-lg overflow-hidden" ref={containerRef}>
          {/* Body: left (employees list) and right (week grid) with synchronized vertical scroll; right handles horizontal scroll */}
          <div className="flex">
            {/* Left pane (vertical scroll) */}
            <div className="w-64 flex-shrink-0">
              <div className="max-h-[70vh] overflow-y-auto" ref={leftYRef} onScroll={(e) => {
                if (syncingY.current) return; syncingY.current = true; if (rightYRef.current) rightYRef.current.scrollTop = e.currentTarget.scrollTop; syncingY.current = false;
              }}>
                {employees.map((emp, idx) => (
                  <div key={emp.employee_id} className="px-3 py-2 border-b hover:bg-gray-50 cursor-pointer" onClick={() => onEmployeeClick(emp.employee_id)} style={{ height: empRowHeights[idx] ? `${empRowHeights[idx]}px` : undefined }}>
                    <div className="font-medium text-gray-900 truncate" title={emp.name}>{emp.name}</div>
                    <div className="text-xs text-gray-600 truncate">{emp.qualification || emp.role_level}</div>
                    <div className="text-xs">
                      <span className={`px-2 py-0.5 rounded-full ${transportBadge(emp.transport_mode)}`}>{emp.transport_mode || 'N/A'}</span>
                    </div>
                    <div className="text-[11px] text-gray-600">Remaining: {emp.remaining_minutes}m</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Right pane: horizontal + vertical scroll */}
            <div className="flex-1">
              <div className="overflow-x-auto" ref={bodyXRef}>
                <div className="min-w-[980px]" style={{ width: `${dayColPx * 7}px` }}>
                  {/* Header row inside the same horizontal scroller */}
                  <div className="flex border-b bg-white">
                    {days.map((d, idx) => (
                      <div key={idx} className="px-3 py-2 text-sm font-medium text-gray-700 border-l shrink-0" style={{ width: `${dayColPx}px` }}>
                        {d.toLocaleDateString(undefined, { weekday: 'short', day: 'numeric', month: 'short' })}
                      </div>
                    ))}
                  </div>
                  {/* Grid rows with vertical scroll */}
                  <div className="max-h-[70vh] overflow-y-auto" ref={rightYRef} onScroll={(e) => {
                    if (syncingY.current) return; syncingY.current = true; if (leftYRef.current) leftYRef.current.scrollTop = e.currentTarget.scrollTop; syncingY.current = false;
                  }}>
                    {employees.map((emp, idx) => (
                      <div key={emp.employee_id} className="flex border-b bg-white" data-emp-row="true">
                        {days.map((d, idx) => {
                          const key = d.toISOString().slice(0,10);
                          const rows = (byEmployee.get(emp.employee_id) || []).filter(r => dayKey(r.start_time) === key);
                          return (
                            <div key={idx} className="border-l px-2 py-2 space-y-2 min-h-[96px] shrink-0" style={{ width: `${dayColPx}px` }}>
                              {rows.map(r => (
                                <div key={r.id || `${r.employee_id}-${r.start_time}-${r.patient_id}`}
                                     className="bg-white border rounded shadow-sm p-2 hover:shadow cursor-pointer"
                                     onClick={() => onCardClick(r)}>
                                  <div className="text-sm font-medium text-gray-900 truncate" title={r.patient_name}>{r.patient_name}</div>
                                  <div className="text-xs text-gray-600 flex items-center justify-between">
                                    <span>{(r.service_type || '').replace(/_/g,' ')}</span>
                                    <span>{(r.start_time||'').slice(11,16)}–{(r.end_time||'').slice(11,16)}</span>
                                  </div>
                                  {r.assignment_reason && (
                                    <div className="text-[11px] text-gray-500 truncate" title={r.assignment_reason}>{r.assignment_reason}</div>
                                  )}
                                  <div className="mt-1 text-[11px] text-gray-500 truncate">
                                    Pref: {r.preference_of_carer || '-'} | RCS: {r.required_carer_support || '-'}
                                  </div>
                                </div>
                              ))}
                            </div>
                          );
                        })}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {!loading && view === 'patients' && (
        <div className="border rounded-lg overflow-hidden" ref={containerRef}>
          {/* Body panes */}
          <div className="flex">
            {/* Left pane (patients list) */}
            <div className="w-64 flex-shrink-0">
              <div className="max-h-[70vh] overflow-y-auto" ref={leftYRefPatients} onScroll={(e) => {
                if (syncingY.current) return; syncingY.current = true; if (rightYRefPatients.current) rightYRefPatients.current.scrollTop = e.currentTarget.scrollTop; syncingY.current = false;
              }}>
                {[...byPatient.keys()].map((pid, idx) => {
                  const first = (byPatient.get(pid) || [])[0] || {};
                  return (
                    <div key={pid} className="px-3 py-2 border-b hover:bg-gray-50 cursor-pointer" onClick={() => onPatientHeaderClick(pid)} style={{ height: patRowHeights[idx] ? `${patRowHeights[idx]}px` : undefined }}>
                      <div className="font-medium text-gray-900 truncate" title={first.patient_name}>{first.patient_name || pid}</div>
                      <div className="text-xs text-gray-600 truncate">{first.patient_id}</div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Right pane: horizontal + vertical scroll */}
            <div className="flex-1">
              <div className="overflow-x-auto">
                <div className="min-w-[980px]" style={{ width: `${dayColPx * 7}px` }}>
                  {/* Header row inside the same horizontal scroller */}
                  <div className="flex border-b bg-white">
                    {days.map((d, idx) => (
                      <div key={idx} className="px-3 py-2 text-sm font-medium text-gray-700 border-l shrink-0" style={{ width: `${dayColPx}px` }}>
                        {d.toLocaleDateString(undefined, { weekday: 'short', day: 'numeric', month: 'short' })}
                      </div>
                    ))}
                  </div>
                  <div className="max-h-[70vh] overflow-y-auto" ref={rightYRefPatients} onScroll={(e) => {
                    if (syncingY.current) return; syncingY.current = true; if (leftYRefPatients.current) leftYRefPatients.current.scrollTop = e.currentTarget.scrollTop; syncingY.current = false;
                  }}>
                    {[...byPatient.keys()].map((pid, idx) => (
                      <div key={pid} className="flex border-b bg-white" data-pat-row="true">
                        {days.map((d, idx) => {
                          const key = d.toISOString().slice(0,10);
                          const rows = (byPatient.get(pid) || []).filter(r => dayKey(r.start_time) === key);
                          return (
                            <div key={idx} className="border-l px-2 py-2 space-y-2 min-h-[96px] shrink-0" style={{ width: `${dayColPx}px` }}>
                              {rows.map(r => (
                                <div key={r.id || `${r.employee_id}-${r.start_time}-${r.patient_id}`}
                                     className="bg-white border rounded shadow-sm p-2 hover:shadow cursor-pointer"
                                     onClick={() => onCardClick(r)}>
                                  <div className="text-sm font-medium text-gray-900 truncate" title={r.employee_name}>{r.employee_name}</div>
                                  <div className="text-xs text-gray-600 flex items-center justify-between">
                                    <span>{(r.service_type || '').replace(/_/g,' ')}</span>
                                    <span>{(r.start_time||'').slice(11,16)}–{(r.end_time||'').slice(11,16)}</span>
                                  </div>
                                  {r.assignment_reason && (
                                    <div className="text-[11px] text-gray-500 truncate" title={r.assignment_reason}>{r.assignment_reason}</div>
                                  )}
                                  {/* Additional patient info inline for quick glance */}
                                  <div className="mt-1 text-[11px] text-gray-500 truncate">
                                    Pref: {r.preference_of_carer || '-'} | RCS: {r.required_carer_support || '-'}
                                  </div>
                                </div>
                              ))}
                            </div>
                          );
                        })}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Employee detail modal */}
      <Modal open={!!selEmployee} title="Employee details" onClose={() => setSelEmployee(null)}>
        {selEmployee && (
          <div className="space-y-2 text-sm">
            <div className="text-lg font-semibold">{selEmployee.Name || selEmployee.name}</div>
            <div>EmployeeID: {selEmployee.EmployeeID || selEmployee.employee_id}</div>
            <div>RoleLevel: {selEmployee.RoleLevel || selEmployee.role_level}</div>
            <div>Qualification: {selEmployee.Qualification || selEmployee.qualification}</div>
            <div>Languages: {selEmployee.LanguageSpoken || selEmployee.languages}</div>
            <div>Transport: {selEmployee.TransportMode || selEmployee.transport_mode}</div>
            <div>Availability: {selEmployee.EarliestStart} - {selEmployee.LatestEnd}</div>
            <div>Weekly Capacity: {selEmployee.weekly_capacity_minutes}m</div>
            <div>Used: {selEmployee.used_minutes}m</div>
            <div>Remaining: {selEmployee.remaining_minutes}m</div>
            <div>Address: {selEmployee.Address}, {selEmployee.PostCode}</div>
          </div>
        )}
      </Modal>

      {/* Patient/assignment detail modal */}
      <Modal open={!!detail} title={detail?.type === 'patient' ? 'Patient details' : 'Assignment details'} onClose={() => setDetail(null)}>
        {detail?.type === 'patient' && (
          <div className="p-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-white rounded-lg border p-4">
                <div className="text-lg font-semibold text-gray-900 mb-2">{detail.data.PatientName}</div>
                <div className="text-sm text-gray-600">ID: {detail.data.PatientID}</div>
                <div className="text-sm text-gray-600">Gender: {detail.data.Gender}</div>
                <div className="text-sm text-gray-600">Language: {detail.data.LanguagePreference}</div>
                <div className="text-sm text-gray-600">Address: {detail.data.Address}, {detail.data.PostCode}</div>
              </div>
              <div className="bg-white rounded-lg border p-4">
                <div className="text-sm text-gray-800 font-medium mb-2">Care Requirements</div>
                <div className="text-sm text-gray-600">Required Support: {detail.data.RequiredSupport}</div>
                <div className="text-sm text-gray-600">Hours/Week: {detail.data.RequiredHoursOfSupport}</div>
                <div className="text-sm text-gray-600">DaysOfSupport: {detail.data.DaysOfSupport}</div>
                <div className="text-sm text-gray-600">Weekend Support: {detail.data.SatSunSupport}</div>
                <div className="text-sm text-gray-600">Preference Of Carer: {detail.data.PreferenceOfCarer}</div>
                <div className="text-sm text-gray-600">Required Carer Support: {detail.data.RequiredCarerSupport}</div>
                <div className="text-sm text-gray-600">Meal Prep: {String(detail.data.MealPrepRequired)}</div>
              </div>
              {detail.assignment && (
                <div className="md:col-span-2 bg-white rounded-lg border p-4">
                  <div className="text-sm text-gray-800 font-medium mb-2">Selected Assignment</div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-sm text-gray-700">
                    <div>Employee: <span className="font-medium">{detail.assignment.employee_name}</span> ({detail.assignment.employee_id})</div>
                    <div>Service: <span className="font-medium">{detail.assignment.service_type}</span></div>
                    <div>Start: {detail.assignment.start_time}</div>
                    <div>End: {detail.assignment.end_time}</div>
                    <div>Duration: {detail.assignment.estimated_duration}m</div>
                    <div>Travel: {detail.assignment.travel_time}m</div>
                    {detail.assignment.assignment_reason && (
                      <div className="sm:col-span-2">Reason: {detail.assignment.assignment_reason}</div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
        {detail?.type === 'assignment' && (
          <div className="p-4">
            <div className="bg-white rounded-lg border p-4">
              <div className="text-lg font-semibold text-gray-900 mb-2">{detail.data.patient_name}</div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-sm text-gray-700">
                <div>Employee: <span className="font-medium">{detail.data.employee_name}</span></div>
                <div>Service: <span className="font-medium">{detail.data.service_type}</span></div>
                <div>Start: {detail.data.start_time}</div>
                <div>End: {detail.data.end_time}</div>
                <div>Duration: {detail.data.estimated_duration}m</div>
                <div>Travel: {detail.data.travel_time}m</div>
                {detail.data.assignment_reason && (
                  <div className="sm:col-span-2">Reason: {detail.data.assignment_reason}</div>
                )}
              </div>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}


