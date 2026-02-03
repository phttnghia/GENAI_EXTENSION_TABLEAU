from app.dal.base import BaseDAL


class AnalysisDAL(BaseDAL):

    def fetch_all(self):
        return self.execute("SELECT 1 as sample_column")
    
    def fetch_analysis_report(
        self,
        start_date: str,
        end_date: str,
        redmine_infra: str,
        redmine_server: str,
        redmine_instance: str,
        project_identifier_list: list,
        filter1_list: list,
        filter2_list: list,
        filter3_list: list,
        filter4_list: list,
        filter5_list: list,
    ):
        return self.execute_query(
            sql_file="analysis_report.sql",
            params={
                "start_date": start_date,
                "end_date": end_date,
                "redmine_infra": redmine_infra,
                "redmine_server": redmine_server,
                "redmine_instance": redmine_instance,
                "project_identifier_list": project_identifier_list,
                "filter1_list": filter1_list,
                "filter2_list": filter2_list,
                "filter3_list": filter3_list,
                "filter4_list": filter4_list,
                "filter5_list": filter5_list,
            },
        )
