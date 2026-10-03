import React from 'react';

export interface PaginationControlsProps {
  page: number;
  pageSize: number;
  totalCount: number;
  totalPages: number;
  onPageChange: (newPage: number) => void;
  onPageSizeChange: (newSize: number) => void;
  itemLabel?: string;
}

export const PaginationControls: React.FC<PaginationControlsProps> = ({
  page,
  pageSize,
  totalCount,
  totalPages,
  onPageChange,
  onPageSizeChange,
  itemLabel = 'items',
}) => {
  if (totalCount === 0) return null;

  const startIdx = (page - 1) * pageSize + 1;
  const endIdx = Math.min(page * pageSize, totalCount);

  // Generate page numbers to show
  const pageNumbers: number[] = [];
  const maxButtons = 5;
  let startPage = Math.max(1, page - Math.floor(maxButtons / 2));
  let endPage = Math.min(totalPages, startPage + maxButtons - 1);
  if (endPage - startPage + 1 < maxButtons) {
    startPage = Math.max(1, endPage - maxButtons + 1);
  }
  for (let i = startPage; i <= endPage; i++) {
    pageNumbers.push(i);
  }

  return (
    <div className="pagination-bar">
      <div className="pagination-info">
        <span>
          Showing <strong>{startIdx}</strong> to <strong>{endIdx}</strong> of <strong>{totalCount}</strong> {itemLabel}
        </span>
        <div className="page-size-selector">
          <label>Rows per page:</label>
          <select
            className="filter-select page-size-select"
            value={pageSize}
            onChange={(e) => onPageSizeChange(Number(e.target.value))}
          >
            <option value={10}>10</option>
            <option value={25}>25</option>
            <option value={50}>50</option>
            <option value={100}>100</option>
          </select>
        </div>
      </div>

      <div className="pagination-nav">
        <button
          type="button"
          className="page-nav-btn"
          onClick={() => onPageChange(page - 1)}
          disabled={page <= 1}
          title="Previous Page"
        >
          ‹ Prev
        </button>

        {pageNumbers.map((p) => (
          <button
            key={p}
            type="button"
            className={`page-num-btn ${p === page ? 'active' : ''}`}
            onClick={() => onPageChange(p)}
          >
            {p}
          </button>
        ))}

        <button
          type="button"
          className="page-nav-btn"
          onClick={() => onPageChange(page + 1)}
          disabled={page >= totalPages}
          title="Next Page"
        >
          Next ›
        </button>
      </div>
    </div>
  );
};
