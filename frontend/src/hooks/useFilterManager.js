import { useEffect, useCallback } from 'react';
import { useSearchParams, useNavigate, useLocation } from 'react-router-dom';
import useFilterStore from '../store/useFilterStore';

export const useFilterManager = (page) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams, setSearchParams] = useSearchParams();
  
  const {
    filters,
    suggestions,
    sortBy,
    sortOrder,
    pageSize,
    pageNumber,
    isLoading,
    error,
    loadFilterSuggestions,
    loadFilterConfig,
    saveFilterConfig,
    applyFilters,
    addFilter,
    updateFilter,
    removeFilter,
    clearFilters,
    setSortBy,
    setSortOrder,
    setPageSize,
    setPageNumber,
    syncWithURL,
    generateURLParams,
    clearError
  } = useFilterStore();

  // Load suggestions and config on mount
  useEffect(() => {
    const initializeFilters = async () => {
      await loadFilterSuggestions(page);
      await loadFilterConfig(page);
    };
    
    initializeFilters();
  }, [page, loadFilterSuggestions, loadFilterConfig]);

  // Sync with URL parameters
  useEffect(() => {
    syncWithURL(page, searchParams);
  }, [page, searchParams, syncWithURL]);

  // Update URL when filters change
  useEffect(() => {
    const params = generateURLParams(page);
    const newSearchParams = new URLSearchParams();
    
    // Copy existing params
    for (const [key, value] of searchParams.entries()) {
      if (!['filters', 'sortBy', 'sortOrder', 'pageSize', 'pageNumber'].includes(key)) {
        newSearchParams.set(key, value);
      }
    }
    
    // Add filter params
    for (const [key, value] of params.entries()) {
      newSearchParams.set(key, value);
    }
    
    setSearchParams(newSearchParams);
  }, [filters[page], sortBy[page], sortOrder[page], pageSize[page], pageNumber[page], page, generateURLParams, searchParams, setSearchParams]);

  // Handle filter changes
  const handleFiltersChange = useCallback((newFilters) => {
    // Update store
    useFilterStore.setState(state => ({
      filters: {
        ...state.filters,
        [page]: newFilters
      }
    }));
  }, [page]);

  // Handle clear filters
  const handleClearFilters = useCallback(() => {
    clearFilters(page);
  }, [page, clearFilters]);

  // Handle save filters
  const handleSaveFilters = useCallback(async (newFilters) => {
    await saveFilterConfig(page);
  }, [page, saveFilterConfig]);

  // Handle apply filters to data
  const handleApplyFiltersToData = useCallback(async (data) => {
    return await applyFilters(page, data);
  }, [page, applyFilters]);

  // Handle sorting
  const handleSortChange = useCallback((newSortBy, newSortOrder = 'asc') => {
    setSortBy(page, newSortBy);
    setSortOrder(page, newSortOrder);
  }, [page, setSortBy, setSortOrder]);

  // Handle pagination
  const handlePageSizeChange = useCallback((newPageSize) => {
    setPageSize(page, newPageSize);
    setPageNumber(page, 1); // Reset to first page
  }, [page, setPageSize, setPageNumber]);

  const handlePageNumberChange = useCallback((newPageNumber) => {
    setPageNumber(page, newPageNumber);
  }, [page, setPageNumber]);

  // Get current filter state
  const getCurrentFilters = useCallback(() => {
    return {
      filters: filters[page] || [],
      suggestions: suggestions[page] || [],
      sortBy: sortBy[page],
      sortOrder: sortOrder[page] || 'asc',
      pageSize: pageSize[page] || 50,
      pageNumber: pageNumber[page] || 1,
      isLoading,
      error
    };
  }, [page, filters, suggestions, sortBy, sortOrder, pageSize, pageNumber, isLoading, error]);

  // Clear error
  const handleClearError = useCallback(() => {
    clearError();
  }, [clearError]);

  return {
    // State
    ...getCurrentFilters(),
    
    // Actions
    handleFiltersChange,
    handleClearFilters,
    handleSaveFilters,
    handleApplyFiltersToData,
    handleSortChange,
    handlePageSizeChange,
    handlePageNumberChange,
    handleClearError,
    
    // Direct store actions
    addFilter: (filterGroup) => addFilter(page, filterGroup),
    updateFilter: (groupIndex, filterGroup) => updateFilter(page, groupIndex, filterGroup),
    removeFilter: (groupIndex) => removeFilter(page, groupIndex),
    
    // URL management
    searchParams,
    setSearchParams
  };
}; 