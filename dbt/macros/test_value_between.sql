{#
    A reusable data test: every non-empty value of the column lies between min_value and max_value (inclusive).
    Rows where the column is empty pass (a share with nothing to divide is empty, not wrong).
    Use in a .yml file:  data_tests: [{value_between: {arguments: {min_value: 0, max_value: 1}}}]
#}
{% test value_between(model, column_name, min_value, max_value) %}

select {{ column_name }}
from {{ model }}
where {{ column_name }} is not null
  and ({{ column_name }} < {{ min_value }} or {{ column_name }} > {{ max_value }})

{% endtest %}
