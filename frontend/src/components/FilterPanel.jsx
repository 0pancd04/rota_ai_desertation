import { useState, useEffect } from 'react';
import { 
  FunnelIcon, 
  XMarkIcon, 
  PlusIcon,
  ChevronDownIcon,
  ChevronUpIcon,
  TrashIcon,
  CheckIcon
} from '@heroicons/react/24/outline';

const FilterPanel = ({ 
  page, 
  suggestions, 
  filters, 
  onFiltersChange, 
  onClearFilters,
  onSaveFilters,
  isLoading 
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [localFilters, setLocalFilters] = useState(filters || []);
  const [activeGroup, setActiveGroup] = useState(null);

  useEffect(() => {
    setLocalFilters(filters || []);
  }, [filters]);

  const handleAddFilter = () => {
    const newGroup = {
      group_id: `group_${Date.now()}`,
      conditions: [],
      operator: "AND"
    };
    setLocalFilters([...localFilters, newGroup]);
    setActiveGroup(newGroup.group_id);
  };

  const handleRemoveFilter = (groupIndex) => {
    const newFilters = localFilters.filter((_, index) => index !== groupIndex);
    setLocalFilters(newFilters);
    onFiltersChange(newFilters);
  };

  const handleAddCondition = (groupIndex) => {
    const newFilters = [...localFilters];
    newFilters[groupIndex].conditions.push({
      field: '',
      operator: 'equals',
      value: '',
      value2: ''
    });
    setLocalFilters(newFilters);
  };

  const handleRemoveCondition = (groupIndex, conditionIndex) => {
    const newFilters = [...localFilters];
    newFilters[groupIndex].conditions.splice(conditionIndex, 1);
    setLocalFilters(newFilters);
  };

  const handleConditionChange = (groupIndex, conditionIndex, field, value) => {
    const newFilters = [...localFilters];
    newFilters[groupIndex].conditions[conditionIndex][field] = value;
    setLocalFilters(newFilters);
  };

  const handleGroupOperatorChange = (groupIndex, operator) => {
    const newFilters = [...localFilters];
    newFilters[groupIndex].operator = operator;
    setLocalFilters(newFilters);
  };

  const handleApplyFilters = () => {
    onFiltersChange(localFilters);
    setIsOpen(false);
  };

  const handleClearFilters = () => {
    setLocalFilters([]);
    onClearFilters();
    setIsOpen(false);
  };

  const handleSaveFilters = () => {
    onSaveFilters(localFilters);
    setIsOpen(false);
  };

  const getOperatorOptions = () => [
    { value: 'equals', label: 'Equals' },
    { value: 'not_equals', label: 'Not Equals' },
    { value: 'contains', label: 'Contains' },
    { value: 'not_contains', label: 'Not Contains' },
    { value: 'greater_than', label: 'Greater Than' },
    { value: 'less_than', label: 'Less Than' },
    { value: 'greater_than_equal', label: 'Greater Than or Equal' },
    { value: 'less_than_equal', label: 'Less Than or Equal' },
    { value: 'in', label: 'In' },
    { value: 'not_in', label: 'Not In' },
    { value: 'between', label: 'Between' },
    { value: 'is_null', label: 'Is Null' },
    { value: 'is_not_null', label: 'Is Not Null' }
  ];

  const getSuggestionByField = (field) => {
    return suggestions.find(s => s.field === field);
  };

  const renderValueInput = (condition, suggestion, groupIndex, conditionIndex) => {
    if (condition.operator === 'is_null' || condition.operator === 'is_not_null') {
      return null;
    }

    if (suggestion?.type === 'select') {
      return (
        <select
          value={condition.value || ''}
          onChange={(e) => handleConditionChange(groupIndex, conditionIndex, 'value', e.target.value)}
          className="block w-full px-2 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 text-sm"
        >
          <option value="">Select {suggestion.label}</option>
          {suggestion.options?.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      );
    }

    if (suggestion?.type === 'number') {
      return (
        <input
          type="number"
          min={suggestion.min_value}
          max={suggestion.max_value}
          placeholder={suggestion.placeholder}
          value={condition.value || ''}
          onChange={(e) => handleConditionChange(groupIndex, conditionIndex, 'value', e.target.value)}
          className="block w-full px-2 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 text-sm"
        />
      );
    }

    if (suggestion?.type === 'date') {
      return (
        <input
          type="date"
          placeholder={suggestion.placeholder}
          value={condition.value || ''}
          onChange={(e) => handleConditionChange(groupIndex, conditionIndex, 'value', e.target.value)}
          className="block w-full px-2 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 text-sm"
        />
      );
    }

    return (
      <input
        type="text"
        placeholder={suggestion?.placeholder || 'Enter value'}
        value={condition.value || ''}
        onChange={(e) => handleConditionChange(groupIndex, conditionIndex, 'value', e.target.value)}
        className="block w-full px-2 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 text-sm"
      />
    );
  };

  const renderBetweenInput = (condition, suggestion, groupIndex, conditionIndex) => {
    if (condition.operator !== 'between') return null;

    return (
      <div className="flex space-x-1">
        <input
          type={suggestion?.type === 'number' ? 'number' : 'text'}
          placeholder="From"
          value={condition.value || ''}
          onChange={(e) => handleConditionChange(groupIndex, conditionIndex, 'value', e.target.value)}
          className="block w-full px-2 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 text-sm"
        />
        <input
          type={suggestion?.type === 'number' ? 'number' : 'text'}
          placeholder="To"
          value={condition.value2 || ''}
          onChange={(e) => handleConditionChange(groupIndex, conditionIndex, 'value2', e.target.value)}
          className="block w-full px-2 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 text-sm"
        />
      </div>
    );
  };

  return (
    <div className="relative">
      {/* Filter Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
      >
        <FunnelIcon className="w-4 h-4 mr-2" />
        Filters
        {filters && filters.length > 0 && (
          <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
            {filters.length}
          </span>
        )}
      </button>

      {/* Filter Panel */}
      {isOpen && (
        <>
          {/* Backdrop */}
          <div 
            className="fixed inset-0 z-40" 
            onClick={() => setIsOpen(false)}
          />
          
          {/* Panel */}
          <div className="absolute right-0 mt-2 w-[600px] max-w-[90vw] bg-white rounded-lg shadow-lg border border-gray-200 z-50">
            <div className="p-4 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium text-gray-900">Filters</h3>
                <button
                  onClick={() => setIsOpen(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XMarkIcon className="w-5 h-5" />
                </button>
              </div>
            </div>

            <div className="p-4 max-h-[70vh] overflow-y-auto">
              {localFilters.length === 0 ? (
                <div className="text-center py-8">
                  <FunnelIcon className="mx-auto w-8 h-8 text-gray-400 mb-2" />
                  <p className="text-gray-500 text-sm">No filters applied</p>
                  <button
                    onClick={handleAddFilter}
                    className="mt-2 inline-flex items-center px-3 py-1 border border-transparent text-sm font-medium rounded-md text-blue-700 bg-blue-100 hover:bg-blue-200"
                  >
                    <PlusIcon className="w-4 h-4 mr-1" />
                    Add Filter
                  </button>
                </div>
              ) : (
                <div className="space-y-4">
                  {localFilters.map((group, groupIndex) => (
                    <div key={group.group_id} className="border border-gray-200 rounded-lg p-3">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center space-x-3">
                          <div className="relative">
                            <select
                              value={group.operator}
                              onChange={(e) => handleGroupOperatorChange(groupIndex, e.target.value)}
                              className="text-sm border border-gray-300 rounded px-3 py-2 pr-8 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 min-w-[80px]"
                            >
                              <option value="AND">AND</option>
                              <option value="OR">OR</option>
                            </select>
                          </div>
                          <span className="text-sm text-gray-600 font-medium">Group {groupIndex + 1}</span>
                        </div>
                        <button
                          onClick={() => handleRemoveFilter(groupIndex)}
                          className="text-red-400 hover:text-red-600"
                        >
                          <TrashIcon className="w-4 h-4" />
                        </button>
                      </div>

                      <div className="space-y-3">
                        {group.conditions.map((condition, conditionIndex) => (
                          <div key={conditionIndex} className="grid grid-cols-1 md:grid-cols-12 gap-3 items-center">
                            <div className="md:col-span-3">
                              <select
                                value={condition.field}
                                onChange={(e) => handleConditionChange(groupIndex, conditionIndex, 'field', e.target.value)}
                                className="w-full text-sm border border-gray-300 rounded px-2 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                              >
                                <option value="">Select field</option>
                                {suggestions.map((suggestion) => (
                                  <option key={suggestion.field} value={suggestion.field}>
                                    {suggestion.label}
                                  </option>
                                ))}
                              </select>
                            </div>

                            <div className="md:col-span-3">
                              <select
                                value={condition.operator}
                                onChange={(e) => handleConditionChange(groupIndex, conditionIndex, 'operator', e.target.value)}
                                className="w-full text-sm border border-gray-300 rounded px-2 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                              >
                                {getOperatorOptions().map((option) => (
                                  <option key={option.value} value={option.value}>
                                    {option.label}
                                  </option>
                                ))}
                              </select>
                            </div>

                            <div className="md:col-span-5">
                              {condition.field && (
                                <>
                                  {renderValueInput(condition, getSuggestionByField(condition.field), groupIndex, conditionIndex)}
                                  {renderBetweenInput(condition, getSuggestionByField(condition.field), groupIndex, conditionIndex)}
                                </>
                              )}
                            </div>

                            <div className="md:col-span-1 flex justify-center">
                              <button
                                onClick={() => handleRemoveCondition(groupIndex, conditionIndex)}
                                className="text-red-400 hover:text-red-600 p-1 rounded hover:bg-red-50 transition-colors"
                                title="Remove condition"
                              >
                                <XMarkIcon className="w-4 h-4" />
                              </button>
                            </div>
                          </div>
                        ))}

                        <button
                          onClick={() => handleAddCondition(groupIndex)}
                          className="w-full inline-flex items-center justify-center px-3 py-1 border border-gray-300 rounded-md text-sm text-gray-700 bg-white hover:bg-gray-50"
                        >
                          <PlusIcon className="w-4 h-4 mr-1" />
                          Add Condition
                        </button>
                      </div>
                    </div>
                  ))}

                  <button
                    onClick={handleAddFilter}
                    className="w-full inline-flex items-center justify-center px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                  >
                    <PlusIcon className="w-4 h-4 mr-2" />
                    Add Filter Group
                  </button>
                </div>
              )}
            </div>

            {/* Actions */}
            {localFilters.length > 0 && (
              <div className="p-4 border-t border-gray-200 bg-gray-50 rounded-b-lg">
                <div className="flex space-x-2">
                  <button
                    onClick={handleApplyFilters}
                    disabled={isLoading}
                    className="flex-1 inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
                  >
                    {isLoading ? 'Applying...' : 'Apply Filters'}
                  </button>
                  <button
                    onClick={handleSaveFilters}
                    className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                  >
                    <CheckIcon className="w-4 h-4 mr-1" />
                    Save
                  </button>
                  <button
                    onClick={handleClearFilters}
                    className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                  >
                    Clear
                  </button>
                </div>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
};

export default FilterPanel; 