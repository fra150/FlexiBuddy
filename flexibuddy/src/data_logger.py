import os
import json
import csv
import time
import pandas as pd
from datetime import datetime
from src.utils.config import APP_CONFIG
from src.utils.report_generator import generate_pdf_report

class DataLogger:
    """
    It manages the recording of interaction data and the generation of reports for parents, teachers and health workers.
    """
    
    def __init__(self):
        # Create directories for data if they do not exist
        self.base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
        self.logs_dir = os.path.join(self.base_dir, 'logs')
        self.reports_dir = os.path.join(self.base_dir, 'reports')

        for directory in [self.base_dir, self.logs_dir, self.reports_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)
        
        # File log
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.activity_log = os.path.join(self.logs_dir, f"activity_log_{self.session_id}.csv")
        self.attention_log = os.path.join(self.logs_dir, f"attention_log_{self.session_id}.csv")
        self.frustration_log = os.path.join(self.logs_dir, f"frustration_log_{self.session_id}.csv")
        
        # start log
        self._init_log_files()
        
        # For report
        self.auto_share_reports = APP_CONFIG.get("auto_share_reports", False)
        self.share_with_parents = APP_CONFIG.get("share_with_parents", True)
        self.share_with_teachers = APP_CONFIG.get("share_with_teachers", False)
        self.share_with_healthcare = APP_CONFIG.get("share_with_healthcare", False)
    
    def _init_log_files(self):
        """Initialize log files with column headers"""
        with open(self.activity_log, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "activity", "duration", "success"])
        
        # Attention log
        with open(self.attention_log, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "activity", "attention_duration"])
        
        # Frustration log
        with open(self.frustration_log, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "activity", "frustration_level"])
    
    def log_activity_completion(self, activity, duration, success=True):
        """
        Records the completion of an activity
        Args:
            activity (str): Name of the activity
            duration (float): Duration of the activity in seconds
            success (bool): Whether the activity was completed successfully
        """
        with open(self.activity_log, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                activity,
                f"{duration:.2f}",
                "1" if success else "0"
            ])
    
    def log_attention_span(self, activity, duration):
        """
        Records the attention duration for an activity
        Args:
            activity (str): Name of the activity
            duration (float): Duration of attention in seconds
        """
        with open(self.attention_log, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                activity,
                f"{duration:.2f}"
            ])
    
    def log_frustration_moment(self, activity="unknown", level=1):
        """
        Records a moment of frustration
        Args:
            activity (str): Name of the activity during frustration
            level (int): Frustration level (1-10)
        """
        with open(self.frustration_log, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                activity,
                str(level)
            ])
    
    def generate_session_report(self, user_name="User", include_plots=True):
        """
        Generates a complete report of the current session
        Args:
            user_name (str): Name of the user
            include_plots (bool): Whether to include plots in the report  
        Returns:
            str: Path of the generated report file
        """
        # Load data from CSV files
        activity_data = pd.read_csv(self.activity_log) if os.path.exists(self.activity_log) else pd.DataFrame()
        attention_data = pd.read_csv(self.attention_log) if os.path.exists(self.attention_log) else pd.DataFrame()
        frustration_data = pd.read_csv(self.frustration_log) if os.path.exists(self.frustration_log) else pd.DataFrame()
        
        # Prepare data for the report
        report_data = {
            "user_name": user_name,
            "session_id": self.session_id,
            "date": datetime.now().strftime("%d/%m/%Y"),
            "total_activities": len(activity_data) if not activity_data.empty else 0,
            "avg_attention_span": attention_data["attention_duration"].mean() if not attention_data.empty else 0,
            "frustration_moments": len(frustration_data) if not frustration_data.empty else 0,
            "completed_activities": activity_data.to_dict('records') if not activity_data.empty else [],
            "attention_spans": attention_data.to_dict('records') if not attention_data.empty else [],
            "frustration_events": frustration_data.to_dict('records') if not frustration_data.empty else [],
            "preferred_activities": self._get_preferred_activities(activity_data, attention_data)
        }
        
        # Generate PDF report
        report_file = os.path.join(self.reports_dir, f"report_{self.session_id}.pdf")
        generate_pdf_report(report_data, report_file, include_plots)
        
        # Share report if configured
        if self.auto_share_reports:
            self._share_report(report_file)
        
        return report_file
    
    def _get_preferred_activities(self, activity_data, attention_data):
        """
        Analyzes data to determine preferred activities
        Args:
            activity_data (DataFrame): Activity data
            attention_data (DataFrame): Attention data    
        Returns:
            list: List of preferred activities with statistics
        """
        preferred = []
        

        if not activity_data.empty and not attention_data.empty:
            activities = activity_data["activity"].unique()
            
            for activity in activities:
                # Filter data for this activity
                activity_rows = activity_data[activity_data["activity"] == activity]
                attention_rows = attention_data[attention_data["activity"] == activity]
                
                # Calculate statistics
                completion_rate = activity_rows["success"].mean() if not activity_rows.empty else 0
                avg_duration = activity_rows["duration"].mean() if not activity_rows.empty else 0
                avg_attention = attention_rows["attention_duration"].mean() if not attention_rows.empty else 0
                
                preferred.append({
                    "activity": activity,
                    "completion_rate": f"{completion_rate:.2f}",
                    "avg_duration": f"{avg_duration:.2f}",
                    "avg_attention": f"{avg_attention:.2f}",
                    "engagement_score": (avg_attention / avg_duration) * completion_rate if avg_duration > 0 else 0
                })
            preferred.sort(key=lambda x: float(x["engagement_score"]), reverse=True)
        
        return preferred
    
    def _share_report(self, report_file):
        """
        Shares the report with configured stakeholders
        Args:
            report_file (str): Path of the report file
        """
        if self.share_with_parents:
            try:
                # TODO: Implement email sending logic here
                # Example: send_email(parent_email_address, "FlexiBuddy Report", "Attached is the session report.", report_file)
                print(f"Attempting to share report with parents: {report_file}")
                print("Parent sharing logic executed (implement actual sending).")
            except Exception as e:
                print(f"Error sharing report with parents: {e}")

        if self.share_with_teachers:
            try:
                # TODO: 
                # Example: upload_to_drive(teacher_folder_id, report_file)
                print(f"Attempting to share report with teachers: {report_file}")
                print("Teacher sharing logic executed (implement actual upload/sending).")
            except Exception as e:
                print(f"Error sharing report with teachers: {e}")
