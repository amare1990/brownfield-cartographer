# Brownfield Cartographer - State Schema

## Node Types
- ModuleNode: path, language, purpose_statement, domain_cluster, complexity_score, change_velocity_30d, is_dead_code_candidate, last_modified
- DatasetNode: name, storage_type, schema_snapshot, freshness_sla, owner, is_source_of_truth
- FunctionNode: qualified_name, parent_module, signature, purpose_statement, call_count_within_repo, is_public_api
- TransformationNode: source_datasets, target_datasets, transformation_type, source_file, line_range, sql_query_if_applicable

## Edge Types
- IMPORTS: source_module → target_module
- CALLS: function → function
- PRODUCES: transformation → dataset
- CONSUMES: transformation → dataset
- CONFIGURES: config_file → module/pipeline
