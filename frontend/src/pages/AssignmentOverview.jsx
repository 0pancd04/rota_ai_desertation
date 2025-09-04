import { useEffect, useMemo, useState } from 'react';
import useStore from '../store/useStore';

function startOfWeek(date) {
  const d = new Date(date);
  const day = d.getDay(); // 0=Sun..6=Sat
  const diff = (day === 0 ? -6 : 1) - day; // shift to Monday
  d.setDate(d.getDate() + diff);
  d.setHours(0,0,0,0);
  return d;
}

function addDays(date, days) {
  const d = new Date(date);
  d.setDate(d.getDate() + days);
  return d;
}

function toIsoDate(date) {
  const d = new Date(date);
  return d.toISOString().slice(0,10);
}

function formatTime(ts) {
  try {
    return new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  } catch { return ts; }
}

export default function AssignmentOverview() {
  const { employees, fetchEmployees, fetchEmployeeWeekAssignments, loading, error } = useStore();
  const [selectedEmployeeId, setSelectedEmployeeId] = useState('');
  const [weekStart, setWeekStart] = useState(startOfWeek(new Date()));
  const [dayIndex, setDayIndex] = useState(0); // 0..6
  const [weekAssignments, setWeekAssignments] = useState([]);

  const weekDays = useMemo(() => (
    Array.from({ length: 7 }, (_, i) => addDays(weekStart, i))
  ), [weekStart]);

  useEffect(() => { fetchEmployees(); }, [fetchEmployees]);

  useEffect(() => {
    async function loadWeek() {
      if (!selectedEmployeeId) return;
      const startIso = toIsoDate(weekDays[0]);
      const endIso = toIsoDate(weekDays[6]);
      const data = await fetchEmployeeWeekAssignments(selectedEmployeeId, startIso, endIso);
      setWeekAssignments(data || []);
    }
    loadWeek();
  }, [selectedEmployeeId, weekDays, fetchEmployeeWeekAssignments]);

  const dayAssignments = useMemo(() => {
    const dayDateIso = toIsoDate(weekDays[dayIndex]);
    return weekAssignments
      .filter(a => (a.start_time || '').slice(0,10) === dayDateIso)
      .sort((a,b) => new Date(a.start_time) - new Date(b.start_time));
  }, [weekAssignments, weekDays, dayIndex]);

  const handlePrevWeek = () => setWeekStart(addDays(weekStart, -7));
  const handleNextWeek = () => setWeekStart(addDays(weekStart, 7));

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <h1 className="text-2xl font-bold text-gray-900">Assignment Overview</h1>
          <p className="text-gray-600">Inspect a single employee's week, by day and time</p>
        </div>
        <div className="flex items-center space-x-3">
          <button onClick={handlePrevWeek} className="px-3 py-2 rounded border bg-white">Prev Week</button>
          <div className="px-3 py-2 rounded bg-gray-100 text-gray-700">
            {toIsoDate(weekDays[0])} - {toIsoDate(weekDays[6])}
          </div>
          <button onClick={handleNextWeek} className="px-3 py-2 rounded border bg-white">Next Week</button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="md:col-span-1 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Employee</label>
            <select
              value={selectedEmployeeId}
              onChange={(e) => setSelectedEmployeeId(e.target.value)}
              className="w-full border rounded px-3 py-2"
            >
              <option value="">Select employee</option>
              {employees.map(e => (
                <option key={e.EmployeeID || e.employee_id} value={e.EmployeeID || e.employee_id}>
                  {(e.Name || e.name) + ' (' + (e.EmployeeID || e.employee_id) + ')'}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Day</label>
            <div className="grid grid-cols-7 gap-1">
              {weekDays.map((d, i) => (
                <button
                  key={i}
                  onClick={() => setDayIndex(i)}
                  className={`px-2 py-2 rounded text-sm ${i === dayIndex ? 'bg-blue-600 text-white' : 'bg-white border'}`}
                >
                  {d.toLocaleDateString(undefined, { weekday: 'short' })}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Filters</label>
            {/* Placeholder for additional filters (service type, min duration, etc.) */}
            <div className="flex items-center space-x-2 text-sm text-gray-500">
              <span>Use global filters on Assignments page if needed.</span>
            </div>
          </div>
        </div>

        <div className="md:col-span-2">
          <div className="bg-white border rounded-lg p-4">
            {loading && <div className="text-gray-500">Loading...</div>}
            {error && <div className="text-red-600">{String(error)}</div>}
            {!loading && dayAssignments.length === 0 && (
              <div className="text-gray-500">No assignments for the selected day.</div>
            )}
            {!loading && dayAssignments.length > 0 && (
              <div className="space-y-3">
                {dayAssignments.map((a, idx) => (
                  <div key={a.id || idx} className="">
                    <div className="p-3 rounded border">
                      <div className="text-sm text-gray-500">{formatTime(a.start_time)} → {formatTime(a.end_time)} ({a.duration || a.estimated_duration} min)</div>
                      <div className="text-gray-900 font-medium">{a.patient_name} ({a.patient_id})</div>
                      <div className="text-gray-600 text-sm">{String(a.service_type).replace('_',' ')}</div>
                    </div>
                    {idx < dayAssignments.length - 1 && (
                      <div className="flex items-center justify-center">
                        <div className="mt-2 mb-2 px-3 py-1 rounded-full bg-blue-50 text-blue-700 text-sm border">
                          Travel: {a.travel_time || 0} min
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}


