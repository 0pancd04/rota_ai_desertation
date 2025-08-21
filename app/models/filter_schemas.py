from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime

class FilterOperator(Enum):
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_THAN_EQUAL = "greater_than_equal"
    LESS_THAN_EQUAL = "less_than_equal"
    IN = "in"
    NOT_IN = "not_in"
    BETWEEN = "between"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"

class FilterCondition(BaseModel):
    field: str
    operator: FilterOperator
    value: Any = None
    value2: Any = None  # For BETWEEN operations

class FilterGroup(BaseModel):
    conditions: List[FilterCondition]
    operator: str = "AND"  # AND or OR
    group_id: Optional[str] = None

class FilterConfig(BaseModel):
    page: str  # assignments, employees, patients
    filters: List[FilterGroup]
    sort_by: Optional[str] = None
    sort_order: str = "asc"  # asc or desc
    page_size: int = 50
    page_number: int = 1
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class FilterSuggestion(BaseModel):
    field: str
    label: str
    type: str  # text, number, date, select, multi_select
    options: Optional[List[Dict[str, Any]]] = None
    min_value: Optional[Any] = None
    max_value: Optional[Any] = None
    placeholder: Optional[str] = None

class FilterPageConfig(BaseModel):
    page: str
    suggestions: List[FilterSuggestion]
    default_filters: Optional[List[FilterGroup]] = None 