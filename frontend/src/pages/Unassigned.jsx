import React, { useEffect, useMemo, useState } from 'react';
import { fetchUnassignedWeek, summarizeUnassignedEntity, fetchPatientDetails, fetchEmployeeDetails } from '../services/scheduleService';

function startOfWeek(date) {
  const d = new Date(date);
  const day = d.getDay();
  const diff = (day === 0 ? -6 : 1) - day; // to Monday
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

export default function Unassigned() {
  const DAY_COL_PX = 220;
  const ENTITY_COL_PX = 220;
  const [weekStart, setWeekStart] = useState(() => startOfWeek(new Date()));
  const weekEnd = useMemo(() => endOfWeek(weekStart), [weekStart]);
  const [view, setView] = useState('patients'); // 'patients' | 'employees'
  const [data, setData] = useState({ patients: [], employees: [] });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [hoverSummary, setHoverSummary] = useState({ key: null, text: '', loading: false, error: null });
  const [cellDetail, setCellDetail] = useState(null); // { entityType, entityId, date, reasons, context }
  const [entityDetail, setEntityDetail] = useState(null); // { entityType, entityId, data }
  const [entityNames, setEntityNames] = useState(new Map()); // entityId -> display name
  const [headerSummary, setHeaderSummary] = useState(null); // { entityType, entityId, weekStart, weekEnd, text, loading, error }

  const moveWeek = (delta) => {
    const d = new Date(weekStart);
    d.setDate(d.getDate() + delta * 7);
    setWeekStart(startOfWeek(d));
  };

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await fetchUnassignedWeek(formatISODate(weekStart), formatISODate(weekEnd), false);
        setData({ patients: res.patients || [], employees: res.employees || [] });
      } catch (e) {
        setError(e.message || 'Failed to load unassigned data');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [weekStart, weekEnd]);

  const days = useMemo(() => Array.from({ length: 7 }, (_, i) => {
    const d = new Date(weekStart);
    d.setDate(weekStart.getDate() + i);
    return d;
  }), [weekStart]);

  const items = view === 'patients' ? data.patients : data.employees;

  const entityIdKey = view === 'patients' ? 'patient_id' : 'employee_id';

  // Build grid map and entity meta map
  const { grid, entities } = useMemo(() => {
    const m = new Map(); // dateISO -> Map(entityId -> row)
    const meta = new Map(); // entityId -> { name, basic }
    for (const row of items) {
      const date = row.date;
      if (!m.has(date)) m.set(date, new Map());
      m.get(date).set(row[entityIdKey], row);
      // Build some basic inline info if available in context
      const eid = row[entityIdKey];
      if (!meta.has(eid)) {
        const ctx = row.context || {};
        if (view === 'patients') {
          meta.set(eid, {
            title: ctx.patient_name || eid,
            subtitle: `Pref: ${ctx.preference_of_carer ?? '-'} | RCS: ${ctx.required_carer_support ?? '-'}`
          });
        } else {
          meta.set(eid, {
            title: ctx.employee_name || eid,
            subtitle: `${ctx.role_level ?? ''} ${ctx.transport_mode ? `• ${ctx.transport_mode}` : ''}`.trim()
          });
        }
      }
    }
    return { grid: m, entities: meta };
  }, [items, entityIdKey, view]);

  const entityKeys = useMemo(() => Array.from(entities.keys()), [entities]);

  // Prefetch names to show under IDs by default
  useEffect(() => {
    const ids = Array.from(new Set(items.map(it => it[entityIdKey])));
    ids.forEach(async (eid) => {
      if (entityNames.has(eid)) return;
      try {
        if (view === 'patients') {
          const pat = await fetchPatientDetails(eid);
          const name = pat?.PatientName || '';
          if (name) setEntityNames(prev => new Map(prev).set(eid, name));
        } else {
          const emp = await fetchEmployeeDetails(eid);
          const name = emp?.Name || '';
          if (name) setEntityNames(prev => new Map(prev).set(eid, name));
        }
      } catch {}
    });
  }, [items, entityIdKey, view, entityNames]);

  const onEntityHeaderClick = async (entityId) => {
    try {
      if (view === 'patients') {
        const pat = await fetchPatientDetails(entityId);
        setEntityDetail({ entityType: view, entityId, data: pat });
      } else {
        const emp = await fetchEmployeeDetails(entityId);
        setEntityDetail({ entityType: view, entityId, data: emp });
      }
    } catch (e) {
      setEntityDetail({ entityType: view, entityId, data: { error: e.message || 'Failed to load details' } });
    }
  };

  // Remove hover summary

  const openHeaderSummary = async (entityId) => {
    setHeaderSummary({ entityType: view, entityId, weekStart: formatISODate(weekStart), weekEnd: formatISODate(weekEnd), text: '', loading: true, error: null });
    try {
      const res = await summarizeUnassignedEntity(view === 'patients' ? 'patient' : 'employee', entityId, formatISODate(weekStart), formatISODate(weekEnd));
      setHeaderSummary({ entityType: view, entityId, weekStart: formatISODate(weekStart), weekEnd: formatISODate(weekEnd), text: res.summary || '', loading: false, error: null, cached: res.cached });
    } catch (e) {
      setHeaderSummary({ entityType: view, entityId, weekStart: formatISODate(weekStart), weekEnd: formatISODate(weekEnd), text: '', loading: false, error: e.message || 'Failed to load summary' });
    }
  };

  const regenerateHeaderSummary = async () => {
    if (!headerSummary) return;
    setHeaderSummary({ ...headerSummary, loading: true, error: null });
    try {
      // Force regeneration
      const res = await summarizeUnassignedEntity(headerSummary.entityType === 'patients' ? 'patient' : 'employee', headerSummary.entityId, headerSummary.weekStart, headerSummary.weekEnd + '', true);
      setHeaderSummary({ ...headerSummary, text: res.summary || '', loading: false, error: null, cached: false });
    } catch (e) {
      setHeaderSummary({ ...headerSummary, loading: false, error: e.message || 'Failed to regenerate summary' });
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <button className="px-3 py-1.5 rounded border border-gray-300 text-gray-700" onClick={() => moveWeek(-1)}>Prev</button>
          <div className="text-sm text-gray-600">Week: {formatISODate(weekStart)} → {formatISODate(weekEnd)}</div>
          <button className="px-3 py-1.5 rounded border border-gray-300 text-gray-700" onClick={() => moveWeek(1)}>Next</button>
        </div>
        <div className="flex items-center gap-2">
          <button className={`px-3 py-1.5 rounded ${view==='patients'?'bg-blue-600 text-white':'border border-gray-300 text-gray-700'}`} onClick={() => setView('patients')}>Patients</button>
          <button className={`px-3 py-1.5 rounded ${view==='employees'?'bg-blue-600 text-white':'border border-gray-300 text-gray-700'}`} onClick={() => setView('employees')}>Employees</button>
        </div>
      </div>

      {loading && <div className="text-gray-600">Loading unassigned data...</div>}
      {error && <div className="text-red-600">{error}</div>}

      {!loading && !error && (
        <div className="bg-white border rounded-lg overflow-x-auto">
          {/* CSS Grid: one consistent column template across header and all rows */}
          <div className="min-w-[960px]">
            {/* Header row */}
            <div className="grid border-b sticky top-0 bg-white z-10" style={{ gridTemplateColumns: `${DAY_COL_PX}px repeat(${entityKeys.length}, ${ENTITY_COL_PX}px)` }}>
              <div className="box-border p-2 text-sm font-medium text-gray-700 border-r">Day</div>
              {entityKeys.map((eid) => (
                <div key={eid} className="box-border p-2 text-sm font-medium text-gray-700 border-r">
                  <button className="w-full text-left" title={`${view === 'patients' ? 'Patient' : 'Employee'} ${eid}`} onClick={() => onEntityHeaderClick(eid)}>
                    <div className="truncate font-medium">{eid}</div>
                    <div className="text-[11px] text-gray-700 truncate">{entityNames.get(eid) || entities.get(eid)?.title || ''}</div>
                    <div className="text-[11px] text-gray-500 truncate">{entities.get(eid)?.subtitle || ''}</div>
                  </button>
                  <div className="mt-1">
                    <button className="text-[11px] text-blue-600 hover:underline" onClick={() => openHeaderSummary(eid)}>Open Summary</button>
                  </div>
                </div>
              ))}
            </div>

            {/* Body rows */}
            {days.map((d, idx) => {
              const dayISO = d.toISOString().slice(0,10);
              const mapForDay = grid.get(dayISO) || new Map();
              return (
                <div key={idx} className="grid border-b" style={{ gridTemplateColumns: `${DAY_COL_PX}px repeat(${entityKeys.length}, ${ENTITY_COL_PX}px)` }}>
                  <div className="box-border p-2 text-sm text-gray-700 border-r bg-gray-50">
                    {d.toLocaleDateString(undefined, { weekday: 'short', day: 'numeric', month: 'short' })}
                  </div>
                  {entityKeys.map((eid) => {
                    const cell = mapForDay.get(eid);
                    return (
                      <div key={`${dayISO}-${eid}`} className="box-border p-2 border-r">
                        {cell ? (
                          <button className="w-full text-left bg-red-50 border border-red-200 rounded p-2 hover:bg-red-100"
                                  onClick={() => setCellDetail({ entityType: view, entityId: eid, date: dayISO, reasons: cell.reasons || [], context: cell.context || {} })}>
                            <div className="text-xs font-medium text-red-700">Unassigned</div>
                            <div className="text-[11px] text-red-600 truncate" title={(cell.reasons || []).join(', ')}>
                              {(cell.reasons || []).slice(0,2).join(' • ')}{(cell.reasons || []).length > 2 ? '…' : ''}
                            </div>
                          </button>
                        ) : (
                          <div className="text-xs text-gray-400">—</div>
                        )}
                      </div>
                    );
                  })}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Cell detail modal */}
      {cellDetail && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="fixed inset-0 bg-black/40" onClick={() => setCellDetail(null)}></div>
          <div className="relative bg-white rounded-lg shadow-lg max-w-2xl w-full mx-4">
            <div className="px-4 py-3 border-b flex items-center justify-between">
              <div className="text-lg font-semibold text-gray-900">{cellDetail.entityType === 'patients' ? 'Patient' : 'Employee'} {cellDetail.entityId} — {cellDetail.date}</div>
              <button className="text-gray-500 hover:text-gray-700" onClick={() => setCellDetail(null)}>✕</button>
            </div>
            <div className="p-4 space-y-3">
              {cellDetail.context && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm text-gray-700">
                  {Object.entries(cellDetail.context).map(([k,v]) => (
                    <div key={k}><span className="text-gray-500">{k}:</span> {String(v)}</div>
                  ))}
                </div>
              )}
              {Array.isArray(cellDetail.reasons) && cellDetail.reasons.length > 0 && (
                <div>
                  <div className="text-sm font-medium text-gray-800 mb-1">Reasons</div>
                  <ul className="list-disc list-inside text-sm text-gray-700">
                    {cellDetail.reasons.map((r,i) => (<li key={i}>{r}</li>))}
                  </ul>
                </div>
              )}
            </div>
            <div className="px-4 py-3 border-t flex justify-end">
              <button className="px-3 py-1.5 rounded border border-gray-300 text-gray-700" onClick={() => setCellDetail(null)}>Close</button>
            </div>
          </div>
        </div>
      )}

      {/* Header summary modal */}
      {headerSummary && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="fixed inset-0 bg-black/40" onClick={() => setHeaderSummary(null)}></div>
          <div className="relative bg-white rounded-lg shadow-lg max-w-2xl w-full mx-4">
            <div className="px-4 py-3 border-b flex items-center justify-between">
              <div className="text-lg font-semibold text-gray-900">{headerSummary.entityType === 'patients' ? 'Patient' : 'Employee'} {headerSummary.entityId} — Summary</div>
              <button className="text-gray-500 hover:text-gray-700" onClick={() => setHeaderSummary(null)}>✕</button>
            </div>
            <div className="p-4 space-y-3">
              {headerSummary.loading && <div className="text-gray-600 text-sm">Generating summary…</div>}
              {headerSummary.error && <div className="text-red-600 text-sm">{headerSummary.error}</div>}
              {!headerSummary.loading && !headerSummary.error && (
                <div className="text-sm text-gray-800 whitespace-pre-wrap">{headerSummary.text || 'No summary available.'}</div>
              )}
            </div>
            <div className="px-4 py-3 border-t flex justify-between items-center">
              <div className="text-xs text-gray-500">Week: {headerSummary.weekStart} → {headerSummary.weekEnd} {headerSummary.cached ? '(cached)' : ''}</div>
              <div className="space-x-2">
                <button className="px-3 py-1.5 rounded border border-gray-300 text-gray-700" onClick={() => setHeaderSummary(null)}>Close</button>
                <button className="px-3 py-1.5 rounded bg-blue-600 text-white disabled:opacity-50" disabled={headerSummary.loading} onClick={regenerateHeaderSummary}>Regenerate summary</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Entity detail modal */}
      {entityDetail && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="fixed inset-0 bg-black/40" onClick={() => setEntityDetail(null)}></div>
          <div className="relative bg-white rounded-lg shadow-lg max-w-3xl w-full mx-4">
            <div className="px-4 py-3 border-b flex items-center justify-between">
              <div className="text-lg font-semibold text-gray-900">{entityDetail.entityType === 'patients' ? 'Patient' : 'Employee'} {entityDetail.entityId} — Details</div>
              <button className="text-gray-500 hover:text-gray-700" onClick={() => setEntityDetail(null)}>✕</button>
            </div>
            <div className="p-4">
              {entityDetail.data?.error ? (
                <div className="text-red-600 text-sm">{entityDetail.data.error}</div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-gray-800">
                  {entityDetail.entityType === 'patients' ? (
                    <>
                      <div className="bg-white rounded-lg border p-4">
                        <div className="text-lg font-semibold text-gray-900 mb-2">{entityDetail.data.PatientName}</div>
                        <div className="text-sm text-gray-600">ID: {entityDetail.data.PatientID}</div>
                        <div className="text-sm text-gray-600">Gender: {entityDetail.data.Gender}</div>
                        <div className="text-sm text-gray-600">Language: {entityDetail.data.LanguagePreference}</div>
                        <div className="text-sm text-gray-600">Address: {entityDetail.data.Address}, {entityDetail.data.PostCode}</div>
                      </div>
                      <div className="bg-white rounded-lg border p-4">
                        <div className="text-sm text-gray-800 font-medium mb-2">Care Requirements</div>
                        <div className="text-sm text-gray-600">Required Support: {entityDetail.data.RequiredSupport}</div>
                        <div className="text-sm text-gray-600">Hours/Week: {entityDetail.data.RequiredHoursOfSupport}</div>
                        <div className="text-sm text-gray-600">DaysOfSupport: {entityDetail.data.DaysOfSupport}</div>
                        <div className="text-sm text-gray-600">Weekend Support: {entityDetail.data.SatSunSupport}</div>
                        <div className="text-sm text-gray-600">Preference Of Carer: {entityDetail.data.PreferenceOfCarer}</div>
                        <div className="text-sm text-gray-600">Required Carer Support: {entityDetail.data.RequiredCarerSupport}</div>
                        <div className="text-sm text-gray-600">Meal Prep: {String(entityDetail.data.MealPrepRequired)}</div>
                      </div>
                    </>
                  ) : (
                    <>
                      <div className="bg-white rounded-lg border p-4">
                        <div className="text-lg font-semibold text-gray-900 mb-2">{entityDetail.data.Name}</div>
                        <div className="text-sm text-gray-600">EmployeeID: {entityDetail.data.EmployeeID}</div>
                        <div className="text-sm text-gray-600">RoleLevel: {entityDetail.data.RoleLevel}</div>
                        <div className="text-sm text-gray-600">Qualification: {entityDetail.data.Qualification}</div>
                        <div className="text-sm text-gray-600">Languages: {entityDetail.data.LanguageSpoken}</div>
                        <div className="text-sm text-gray-600">Transport: {entityDetail.data.TransportMode}</div>
                      </div>
                      <div className="bg-white rounded-lg border p-4">
                        <div className="text-sm text-gray-800 font-medium mb-2">Availability & Address</div>
                        <div className="text-sm text-gray-600">Availability: {entityDetail.data.EarliestStart} - {entityDetail.data.LatestEnd}</div>
                        {entityDetail.data.weekly_capacity_minutes != null && (
                          <div className="text-sm text-gray-600">Weekly Capacity: {entityDetail.data.weekly_capacity_minutes}m</div>
                        )}
                        <div className="text-sm text-gray-600">Address: {entityDetail.data.Address}, {entityDetail.data.PostCode}</div>
                      </div>
                    </>
                  )}
                </div>
              )}
            </div>
            <div className="px-4 py-3 border-t flex justify-end">
              <button className="px-3 py-1.5 rounded border border-gray-300 text-gray-700" onClick={() => setEntityDetail(null)}>Close</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}


