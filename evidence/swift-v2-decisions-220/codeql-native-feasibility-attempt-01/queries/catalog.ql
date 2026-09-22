/**
 * @name Shipped Swift model catalog enumeration
 * @description Non-scored structural enumeration; declares no benchmark model.
 * @kind table
 * @id dfb/swift-v2-shipped-catalog
 */
import swift
import codeql.swift.dataflow.ExternalFlow
import codeql.swift.security.CommandInjectionQuery

from string role, string row
where
  exists(SourceModelCsv model | model.row(row)) and role = "source"
  or exists(SinkModelCsv model | model.row(row)) and role = "sink"
  or exists(SummaryModelCsv model | model.row(row)) and role = "summary"
select role, row
