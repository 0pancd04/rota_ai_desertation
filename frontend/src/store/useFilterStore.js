import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const useFilterStore = create(
  subscribeWithSelector((set, get) => ({
    // State
    filters: {},
    suggestions: {},
    appliedFilters: {},
    sortBy: {},
    sortOrder: {},
    pageSize: {},
    pageNumber: {},
    isLoading: false,
    error: null,

    // Actions
    setLoading: (loading) => set({ isLoading: loading }),
    setError: (error) => set({ error }),

    // Load filter suggestions for a page
    loadFilterSuggestions: async (page) => {
      set({ isLoading: true, error: null });
      try {
        const response = await axios.get(`${API_BASE_URL}/filters/suggestions/${page}`);
        set(state => ({
          suggestions: {
            ...state.suggestions,
            [page]: response.data.suggestions
          },
          isLoading: false
        }));
        return response.data.suggestions;
      } catch (error) {
        set({ 
          error: error.response?.data?.detail || 'Failed to load filter suggestions',
          isLoading: false 
        });
        return [];
      }
    },

    // Load saved filter configuration
    loadFilterConfig: async (page) => {
      set({ isLoading: true, error: null });
      try {
        const response = await axios.get(`${API_BASE_URL}/filters/config/${page}`);
        const config = response.data;
        
        set(state => ({
          filters: {
            ...state.filters,
            [page]: config.filters || []
          },
          sortBy: {
            ...state.sortBy,
            [page]: config.sort_by
          },
          sortOrder: {
            ...state.sortOrder,
            [page]: config.sort_order || 'asc'
          },
          pageSize: {
            ...state.pageSize,
            [page]: config.page_size || 50
          },
          pageNumber: {
            ...state.pageNumber,
            [page]: config.page_number || 1
          },
          isLoading: false
        }));
        
        return config;
      } catch (error) {
        set({ 
          error: error.response?.data?.detail || 'Failed to load filter config',
          isLoading: false 
        });
        return null;
      }
    },

    // Save filter configuration
    saveFilterConfig: async (page) => {
      const state = get();
      const config = {
        page,
        filters: state.filters[page] || [],
        sort_by: state.sortBy[page],
        sort_order: state.sortOrder[page] || 'asc',
        page_size: state.pageSize[page] || 50,
        page_number: state.pageNumber[page] || 1
      };

      try {
        await axios.post(`${API_BASE_URL}/filters/config/${page}`, config);
        return true;
      } catch (error) {
        set({ 
          error: error.response?.data?.detail || 'Failed to save filter config'
        });
        return false;
      }
    },

    // Apply filters to data
    applyFilters: async (page, data) => {
      const state = get();
      const filters = state.filters[page] || [];
      
      if (filters.length === 0) {
        return data;
      }

      try {
        const response = await axios.post(`${API_BASE_URL}/filters/apply/${page}`, filters);
        return response.data.data;
      } catch (error) {
        set({ 
          error: error.response?.data?.detail || 'Failed to apply filters'
        });
        return data;
      }
    },

    // Filter management
    addFilter: (page, filterGroup) => {
      set(state => ({
        filters: {
          ...state.filters,
          [page]: [...(state.filters[page] || []), filterGroup]
        }
      }));
    },

    updateFilter: (page, groupIndex, filterGroup) => {
      set(state => ({
        filters: {
          ...state.filters,
          [page]: state.filters[page].map((group, index) => 
            index === groupIndex ? filterGroup : group
          )
        }
      }));
    },

    removeFilter: (page, groupIndex) => {
      set(state => ({
        filters: {
          ...state.filters,
          [page]: state.filters[page].filter((_, index) => index !== groupIndex)
        }
      }));
    },

    clearFilters: (page) => {
      set(state => ({
        filters: {
          ...state.filters,
          [page]: []
        }
      }));
    },

    // Sorting
    setSortBy: (page, sortBy) => {
      set(state => ({
        sortBy: {
          ...state.sortBy,
          [page]: sortBy
        }
      }));
    },

    setSortOrder: (page, sortOrder) => {
      set(state => ({
        sortOrder: {
          ...state.sortOrder,
          [page]: sortOrder
        }
      }));
    },

    // Pagination
    setPageSize: (page, pageSize) => {
      set(state => ({
        pageSize: {
          ...state.pageSize,
          [page]: pageSize
        }
      }));
    },

    setPageNumber: (page, pageNumber) => {
      set(state => ({
        pageNumber: {
          ...state.pageNumber,
          [page]: pageNumber
        }
      }));
    },

    // URL synchronization
    syncWithURL: (page, searchParams) => {
      const filtersParam = searchParams.get('filters');
      const sortByParam = searchParams.get('sortBy');
      const sortOrderParam = searchParams.get('sortOrder');
      const pageSizeParam = searchParams.get('pageSize');
      const pageNumberParam = searchParams.get('pageNumber');

      if (filtersParam) {
        try {
          const filters = JSON.parse(decodeURIComponent(filtersParam));
          set(state => ({
            filters: {
              ...state.filters,
              [page]: filters
            }
          }));
        } catch (error) {
          console.error('Failed to parse filters from URL:', error);
        }
      }

      if (sortByParam) {
        set(state => ({
          sortBy: {
            ...state.sortBy,
            [page]: sortByParam
          }
        }));
      }

      if (sortOrderParam) {
        set(state => ({
          sortOrder: {
            ...state.sortOrder,
            [page]: sortOrderParam
          }
        }));
      }

      if (pageSizeParam) {
        set(state => ({
          pageSize: {
            ...state.pageSize,
            [page]: parseInt(pageSizeParam)
          }
        }));
      }

      if (pageNumberParam) {
        set(state => ({
          pageNumber: {
            ...state.pageNumber,
            [page]: parseInt(pageNumberParam)
          }
        }));
      }
    },

    // Generate URL parameters
    generateURLParams: (page) => {
      const state = get();
      const params = new URLSearchParams();

      const filters = state.filters[page] || [];
      if (filters.length > 0) {
        params.set('filters', encodeURIComponent(JSON.stringify(filters)));
      }

      const sortBy = state.sortBy[page];
      if (sortBy) {
        params.set('sortBy', sortBy);
      }

      const sortOrder = state.sortOrder[page];
      if (sortOrder) {
        params.set('sortOrder', sortOrder);
      }

      const pageSize = state.pageSize[page];
      if (pageSize) {
        params.set('pageSize', pageSize.toString());
      }

      const pageNumber = state.pageNumber[page];
      if (pageNumber) {
        params.set('pageNumber', pageNumber.toString());
      }

      return params;
    },

    // Clear error
    clearError: () => set({ error: null })
  }))
);

export default useFilterStore; 