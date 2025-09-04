import { useEffect, useMemo, useState } from 'react';
import useStore from '../store/useStore';

function StatCard({ title, value, subtitle }) {
  return (
    <div className="bg-white border rounded-lg p-4">
      <div className="text-sm text-gray-500">{title}</div>
      <div className="text-2xl font-semibold text-gray-900">{value}</div>
      {subtitle && <div className="text-xs text-gray-500 mt-1">{subtitle}</div>}
    </div>
  );
}

export default function Stats() {
  const { stats, fetchStats, loading, error } = useStore();
  const [selectedDays, setSelectedDays] = useState([]); // 0=Mon..6=Sun
  const [rangeStart, setRangeStart] = useState('');
  const [rangeEnd, setRangeEnd] = useState('');

  useEffect(() => { fetchStats(false, {}); }, [fetchStats]);

  const toggleDay = (d) => {
    setSelectedDays(prev => prev.includes(d) ? prev.filter(x => x !== d) : [...prev, d]);
  };
  const applyFilters = () => fetchStats(false, { days: selectedDays, startDate: rangeStart || null, endDate: rangeEnd || null });
  const clearFilters = () => { setSelectedDays([]); setRangeStart(''); setRangeEnd(''); fetchStats(false, {}); };

  const metrics = stats?.metrics || {};
  const counts = metrics.counts || {};
  const time = metrics.time || {};
  const workload = metrics.workload || {};
  const future = metrics.future || {};

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <h1 className="text-2xl font-bold text-gray-900">Optimization Stats</h1>
          <p className="text-gray-600">Insights, savings and resource outlook</p>
        </div>
        <div className="flex items-center space-x-3">
          <button onClick={applyFilters} disabled={loading} className="px-3 py-2 rounded border bg-white">Apply Filters</button>
          <button onClick={clearFilters} disabled={loading} className="px-3 py-2 rounded border bg-white">Clear Filters</button>
          <button onClick={() => fetchStats(false, {})} disabled={loading} className="px-3 py-2 rounded border bg-white">Refresh</button>
          <button onClick={() => fetchStats(true, {})} disabled={loading} className="px-3 py-2 rounded bg-blue-600 text-white">Regenerate</button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white border rounded-lg p-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
          <div>
            <div className="text-sm text-gray-600 mb-2">Weekdays</div>
            <div className="grid grid-cols-7 gap-1">
              {['Mon','Tue','Wed','Thu','Fri','Sat','Sun'].map((label, idx) => (
                <button
                  key={label}
                  onClick={() => toggleDay(idx)}
                  className={`px-2 py-1 rounded text-sm ${selectedDays.includes(idx) ? 'bg-blue-600 text-white' : 'bg-gray-100'}`}
                >{label}</button>
              ))}
            </div>
          </div>
          <div>
            <label className="block text-sm text-gray-600 mb-1">Start Date</label>
            <input type="date" value={rangeStart} onChange={(e) => setRangeStart(e.target.value)} className="w-full border rounded px-3 py-2" />
          </div>
          <div>
            <label className="block text-sm text-gray-600 mb-1">End Date</label>
            <input type="date" value={rangeEnd} onChange={(e) => setRangeEnd(e.target.value)} className="w-full border rounded px-3 py-2" />
          </div>
        </div>
      </div>

      {loading && <div className="text-gray-500">Loading...</div>}
      {error && <div className="text-red-600">{String(error)}</div>}

      {stats && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard title="Assignments" value={counts.assignments || 0} />
            <StatCard title="Employees" value={counts.employees || 0} />
            <StatCard title="Patients" value={counts.patients || 0} />
            <StatCard title="Unassigned Patients" value={counts.unassigned_patients || 0} />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <StatCard title="Total Service Time" value={`${time.total_service_minutes || 0} min`} />
            <StatCard title="Total Travel Time" value={`${time.total_travel_minutes || 0} min`} />
            <StatCard title="Travel Time Saved" value={`${time.travel_time_saved_minutes || 0} min`} subtitle="vs baseline 20 min/assignment" />
            <StatCard title="Avg Service" value={`${time.avg_service_minutes || 0} min`} />
            <StatCard title="Avg Travel" value={`${time.avg_travel_minutes || 0} min`} />
            <StatCard title="Future Demand" value={`${future.estimated_future_minutes || 0} min`} subtitle="Est. minutes needed for unassigned" />
          </div>

          {/* Workload table */}
          <div className="bg-white border rounded-lg p-4">
            <div className="text-lg font-semibold text-gray-900 mb-2">Workload by Employee</div>
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="text-left text-gray-500">
                    <th className="px-4 py-2">Employee ID</th>
                    <th className="px-4 py-2">Assignments</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(workload).map(([eid, num]) => (
                    <tr key={eid} className="border-t">
                      <td className="px-4 py-2">{eid}</td>
                      <td className="px-4 py-2">{num}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* AI Summary and Ideas */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-white border rounded-lg p-4">
              <div className="text-lg font-semibold text-gray-900 mb-2">AI Summary</div>
              <div className="text-gray-700 whitespace-pre-wrap text-sm">{stats.ai_summary || '—'}</div>
            </div>
            <div className="bg-white border rounded-lg p-4">
              <div className="text-lg font-semibold text-gray-900 mb-2">AI Ideas</div>
              <div className="text-gray-700 whitespace-pre-wrap text-sm">{stats.ai_ideas || '—'}</div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}


