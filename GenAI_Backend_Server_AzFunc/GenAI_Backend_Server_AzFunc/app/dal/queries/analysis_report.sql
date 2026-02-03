select 
    TestCaseExpected,
    TestCaseActual,
    BReportExpected,
    BReportUpperBound,
    BReportLowerBound,
    BReportActual,
    BReportFixed,
    TestCaseExpectedTotal,
    TestCaseActualTotal,
    BReportExpectedTotal,
    BReportActualTotal,
    BReportFixedTotal,
    BReportOutstanding
from [bug-management_dm_11].[vw_bug_report_by_testplan]
WHERE date IS NOT NULL
  AND date BETWEEN :start_date AND :end_date
  AND redmine_infra = :redmine_infra
  AND redmine_server = :redmine_server
  AND redmine_instance = :redmine_instance
  AND project_identifier IN (:project_identifier_list)
  AND filter1 IN (:filter1_list)
  AND filter2 IN (:filter2_list)
  AND filter3 IN (:filter3_list)
  AND filter4 IN (:filter4_list)
  AND filter5 IN (:filter5_list)