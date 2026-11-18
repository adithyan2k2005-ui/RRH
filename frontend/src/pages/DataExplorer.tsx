import React, { useEffect, useState } from 'react';
import {
  Database,
  Download,
  Search,
  ChevronLeft,
  ChevronRight,
  Layers,
  ArrowUpDown,
  Info,
  AlertCircle,
  RefreshCw,
} from 'lucide-react';
import { api, DatasetMeta, DatasetRecordsResponse } from '../services/api';
import { formatInt } from '../utils/format';

export const DataExplorer: React.FC = () => {
  const [datasets, setDatasets] = useState<DatasetMeta[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>('competitions');
  const [loadingDatasets, setLoadingDatasets] = useState(true);
  const [datasetsError, setDatasetsError] = useState<string | null>(null);

  // Table State
  const [recordsData, setRecordsData] = useState<DatasetRecordsResponse | null>(null);
  const [loadingRecords, setLoadingRecords] = useState(false);
  const [recordsError, setRecordsError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [search, setSearch] = useState('');
  const [sortBy, setSortBy] = useState<string>('');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');

  // Load dataset catalog
  const loadCatalog = async () => {
    try {
      setLoadingDatasets(true);
      setDatasetsError(null);
      const data = await api.getDatasets();
      setDatasets(data);
      if (data.length > 0 && !selectedDatasetId) {
        setSelectedDatasetId(data[0].dataset_id);
      }
    } catch (err: any) {
      console.error('Failed to load datasets:', err);
      setDatasetsError(err?.message || 'Failed to load dataset catalog.');
    } finally {
      setLoadingDatasets(false);
    }
  };

  useEffect(() => {
    loadCatalog();
  }, []);

  // Load records on parameter changes
  const loadRecords = async () => {
    if (!selectedDatasetId) return;
    try {
      setLoadingRecords(true);
      setRecordsError(null);
      const data = await api.getDatasetRecords(
        selectedDatasetId,
        page,
        pageSize,
        search || undefined,
        sortBy || undefined,
        sortOrder
      );
      setRecordsData(data);
    } catch (err: any) {
      console.error('Failed to load records:', err);
      setRecordsError(err?.message || 'Failed to load dataset records.');
    } finally {
      setLoadingRecords(false);
    }
  };

  useEffect(() => {
    loadRecords();
  }, [selectedDatasetId, page, pageSize, search, sortBy, sortOrder]);

  const selectedMeta = datasets.find((d) => d.dataset_id === selectedDatasetId);

  const handleDatasetChange = (newId: string) => {
    setSelectedDatasetId(newId);
    setPage(1);
    setSearch('');
    setSortBy('');
  };

  const handleSort = (col: string) => {
    if (sortBy === col) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(col);
      setSortOrder('asc');
    }
  };

  // Derive column names safely from selectedMeta.columns (handles both strings and {name, type} objects)
  const metaColumns: string[] = Array.isArray(selectedMeta?.columns)
    ? selectedMeta.columns.map((c: any) => (typeof c === 'string' ? c : c?.name || String(c)))
    : [];

  // Derive records columns safely from recordsData
  const displayColumns: string[] =
    recordsData?.columns && recordsData.columns.length > 0
      ? recordsData.columns
      : recordsData?.records && recordsData.records.length > 0
      ? Object.keys(recordsData.records[0])
      : metaColumns;

  const totalRowCount = selectedMeta?.rows_count ?? selectedMeta?.row_count ?? 0;
  const totalColCount = selectedMeta?.columns_count ?? selectedMeta?.column_count ?? metaColumns.length;
  const fileSizeBytes = selectedMeta?.file_size_bytes ?? selectedMeta?.size_bytes ?? 0;

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header & Selector */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 rounded-3xl bg-[#120817] border border-[#400A2D] shadow-rr-card">
        <div>
          <h2 className="text-xl sm:text-2xl font-extrabold text-white flex items-center gap-2">
            <Database className="text-[#C21868]" size={24} />
            Data Explorer & Schema Inspector
          </h2>
          <p className="text-xs text-[#BFA8BA] mt-1">
            Query and inspect all 10 verified data artifacts across the complete cricket analytics pipeline.
          </p>
        </div>

        {/* Dataset Selector Dropdown */}
        <div className="flex items-center gap-3">
          <label htmlFor="dataset-select" className="text-xs text-[#BFA8BA] font-medium whitespace-nowrap">
            Artifact:
          </label>
          <select
            id="dataset-select"
            value={selectedDatasetId}
            onChange={(e) => handleDatasetChange(e.target.value)}
            disabled={loadingDatasets}
            className="px-4 py-2 rounded-xl bg-[#20091F] border border-[#400A2D] text-white text-xs font-semibold focus:outline-none focus:border-[#C21868] transition-colors"
          >
            {datasets.map((d) => {
              const rCount = d.rows_count ?? d.row_count ?? 0;
              return (
                <option key={d.dataset_id} value={d.dataset_id}>
                  {d.name} ({rCount.toLocaleString()} rows)
                </option>
              );
            })}
          </select>

          {/* Export CSV Button */}
          <a
            href={api.getDatasetExportUrl(selectedDatasetId)}
            download
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-gradient-to-r from-[#C21868] to-[#8F2455] text-white text-xs font-bold hover:shadow-rr-glow transition-all"
          >
            <Download size={14} />
            Export CSV
          </a>
        </div>
      </div>

      {/* Dataset Metadata Dossier */}
      {selectedMeta && (
        <div className="p-5 rounded-2xl bg-[#20091F]/60 border border-[#400A2D] space-y-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <span className="text-xs font-mono font-bold text-[#C21868] uppercase">
                {selectedMeta.format || 'Data'} Artifact
              </span>
              <h3 className="text-base font-bold text-white">{selectedMeta.name}</h3>
              <p className="text-xs text-[#BFA8BA] mt-0.5">{selectedMeta.description}</p>
            </div>
            <div className="flex items-center gap-3 text-xs font-mono">
              <div className="px-3 py-1.5 rounded-lg bg-[#080510] border border-[#400A2D] text-white">
                <span className="text-[#BFA8BA]">Rows: </span>
                <span className="font-bold text-[#D4AF37]">{totalRowCount.toLocaleString()}</span>
              </div>
              <div className="px-3 py-1.5 rounded-lg bg-[#080510] border border-[#400A2D] text-white">
                <span className="text-[#BFA8BA]">Cols: </span>
                <span className="font-bold text-[#F5EAF2]">{totalColCount}</span>
              </div>
              <div className="px-3 py-1.5 rounded-lg bg-[#080510] border border-[#400A2D] text-white">
                <span className="text-[#BFA8BA]">Size: </span>
                <span>{(fileSizeBytes / 1024).toFixed(1)} KB</span>
              </div>
            </div>
          </div>

          {/* Column Tags */}
          {metaColumns.length > 0 && (
            <div className="pt-2 border-t border-[#400A2D]/50 flex flex-wrap gap-1.5">
              <span className="text-[11px] text-[#BFA8BA] font-medium mr-1 py-0.5 flex items-center gap-1">
                <Layers size={11} /> Columns:
              </span>
              {metaColumns.map((col) => (
                <span
                  key={col}
                  onClick={() => handleSort(col)}
                  className={`text-[11px] px-2 py-0.5 rounded-md font-mono cursor-pointer transition-colors ${
                    sortBy === col
                      ? 'bg-[#C21868] text-white font-bold'
                      : 'bg-[#120817] border border-[#400A2D] text-[#BFA8BA] hover:text-white hover:border-[#C21868]/50'
                  }`}
                >
                  {col} {sortBy === col && (sortOrder === 'asc' ? '↑' : '↓')}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Filter & Controls Toolbar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="relative flex-1 max-w-md">
          <Search size={16} className="absolute left-3 top-2.5 text-[#BFA8BA]" />
          <input
            type="text"
            placeholder="Search within records..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            className="w-full pl-9 pr-4 py-2 rounded-xl bg-[#120817] border border-[#400A2D] text-white text-xs placeholder-[#826D7D] focus:outline-none focus:border-[#C21868]"
          />
        </div>

        <div className="flex items-center gap-3">
          <span className="text-xs text-[#BFA8BA]">Per page:</span>
          <select
            value={pageSize}
            onChange={(e) => {
              setPageSize(Number(e.target.value));
              setPage(1);
            }}
            className="px-2.5 py-1.5 rounded-lg bg-[#120817] border border-[#400A2D] text-white text-xs focus:outline-none"
          >
            <option value={10}>10</option>
            <option value={20}>20</option>
            <option value={50}>50</option>
            <option value={100}>100</option>
          </select>
        </div>
      </div>

      {/* Paginated Data Table Container */}
      <div className="rounded-3xl bg-[#120817] border border-[#400A2D] overflow-hidden shadow-rr-card">
        {loadingRecords ? (
          <div className="p-12 text-center space-y-2">
            <div className="w-8 h-8 border-3 border-[#C21868] border-t-transparent rounded-full animate-spin mx-auto"></div>
            <p className="text-xs text-[#BFA8BA]">Querying datastore...</p>
          </div>
        ) : recordsError ? (
          <div className="p-8 text-center space-y-3">
            <AlertCircle size={32} className="text-[#C21868] mx-auto" />
            <div className="text-sm font-bold text-white">Error Querying Artifact</div>
            <p className="text-xs text-[#BFA8BA] max-w-md mx-auto">{recordsError}</p>
            <button
              onClick={loadRecords}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-[#20091F] border border-[#C21868] text-[#C21868] hover:text-white text-xs font-bold transition-colors"
            >
              <RefreshCw size={13} /> Try Again
            </button>
          </div>
        ) : recordsData && recordsData.records.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-[#20091F] border-b border-[#400A2D] text-[#BFA8BA] font-semibold">
                  <th className="py-3 px-4 font-mono w-12 text-center text-[#826D7D]">#</th>
                  {displayColumns.map((col) => (
                    <th
                      key={col}
                      onClick={() => handleSort(col)}
                      className="py-3 px-4 cursor-pointer hover:text-white whitespace-nowrap transition-colors"
                    >
                      <div className="flex items-center gap-1.5">
                        <span>{col}</span>
                        <ArrowUpDown size={11} className={sortBy === col ? 'text-[#C21868]' : 'text-[#826D7D]'} />
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-[#400A2D]/40">
                {recordsData.records.map((row, idx) => {
                  const rowNumber = (page - 1) * pageSize + idx + 1;
                  return (
                    <tr
                      key={idx}
                      className="hover:bg-[#20091F]/60 transition-colors font-mono"
                    >
                      <td className="py-2.5 px-4 text-center text-[#826D7D] text-[11px]">
                        {rowNumber}
                      </td>
                      {displayColumns.map((col) => {
                        const val = row[col];
                        const displayVal =
                          val === null || val === undefined
                            ? '—'
                            : typeof val === 'number'
                            ? Number.isInteger(val)
                              ? val.toLocaleString()
                              : val.toFixed(2)
                            : String(val);
                        return (
                          <td
                            key={col}
                            className={`py-2.5 px-4 whitespace-nowrap ${
                              col.includes('name') || col === 'stage' || col === 'result'
                                ? 'font-sans font-medium text-white'
                                : col.includes('score') || col.includes('rate') || col.includes('impact')
                                ? 'text-[#D4AF37]'
                                : col === 'rank'
                                ? 'text-[#C21868] font-bold'
                                : 'text-[#F5EAF2]'
                            }`}
                          >
                            {displayVal}
                          </td>
                        );
                      })}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-12 text-center space-y-2">
            <Info size={28} className="text-[#BFA8BA] mx-auto" />
            <p className="text-sm font-semibold text-white">No records found</p>
            <p className="text-xs text-[#BFA8BA]">Try adjusting your search filter or selecting a different artifact.</p>
          </div>
        )}

        {/* Pagination Footer */}
        {recordsData && recordsData.total_records > 0 && (
          <div className="p-4 bg-[#20091F]/60 border-t border-[#400A2D] flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
            <span className="text-[#BFA8BA]">
              Showing{' '}
              <span className="text-white font-mono">
                {(page - 1) * pageSize + 1}–{Math.min(page * pageSize, recordsData.total_records)}
              </span>{' '}
              of <span className="text-white font-mono">{recordsData.total_records.toLocaleString()}</span> entries
            </span>

            <div className="flex items-center space-x-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="p-1.5 rounded-lg bg-[#120817] border border-[#400A2D] text-white disabled:opacity-40 disabled:cursor-not-allowed hover:bg-[#20091F]"
                aria-label="Previous page"
              >
                <ChevronLeft size={16} />
              </button>

              <span className="font-mono text-white px-2">
                Page {page} of {recordsData.total_pages || 1}
              </span>

              <button
                onClick={() => setPage((p) => Math.min(recordsData.total_pages, p + 1))}
                disabled={page >= recordsData.total_pages}
                className="p-1.5 rounded-lg bg-[#120817] border border-[#400A2D] text-white disabled:opacity-40 disabled:cursor-not-allowed hover:bg-[#20091F]"
                aria-label="Next page"
              >
                <ChevronRight size={16} />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
