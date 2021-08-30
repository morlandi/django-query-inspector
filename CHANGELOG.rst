.. :changelog:

History
=======

v1.1.6
------
* Fix: remove duplicates from extract_named_parameters()

v1.1.5
------
* Fix readme

v1.1.4
------
* qsdump2() helper added
* Query: persist parameters and duplicate

v1.1.3
------
* fix preview styles again

v1.1.2
------
* fix styles

v1.1.1
------
* Query preview: add horizontal scrolling to results table

v1.1.0
------
* SQL query preview from admin
* fix format_datetime() for naive datetimes

v1.0.9
------
* added "params" and "reindend" parameters to prettyprint_query()
* added "reindend" to prettyprint_queryset()

v1.0.8
------
* [fix] remove division by zero when computing average for and empty list of rows

v1.0.7
------
* QueryCountMiddleware can be used as standalone

v1.0.6
------

* optionally Transpose rendered tables
* slugify "field-..." class in rendered HTML tables
* support "field1__field2" syntax to span relationships

v1.0.5
------
* "dump_local_data" management command now supports sqlite and Windows platform

v1.0.4
------
* fix syntax error due to wrong indentation

v1.0.3
------
* render_value_as_text() optionally preserves numeric formats

v1.0.2
------
* use apply_autofit() in export_any_queryset()

v1.0.1
------
* fix unprettified duplicate_queries dump

v1.0.0
------
* fix format_datetime

v0.0.6
------
* normalized_export_filename() helper
* improved documentation

v0.0.5
------
* Tracing queries in real-time
* Inspecting queries in a unit test
* Helper management commands

v0.0.4
------
* render_queryset_as_data added for greated control of the final rendering
* qsdump supports tabulate
* download the queryset as a spreadsheet

v0.0.3
------
* querycounter middleware
* query_debugger decorator
* tracing helpers
* templetags helpers
* export a Queryset to a spreadsheet

v0.0.2
------
* unit tests reorganized

v0.0.1
------
* Initial setup
