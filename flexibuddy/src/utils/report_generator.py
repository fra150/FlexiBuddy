import os
import pandas as pd
import matplotlib.pyplot as plt
from weasyprint import HTML
from datetime import datetime

def generate_pdf_report(report_data, output_file, include_plots=True):
    """
    Generates a PDF report using WeasyPrint
    Args:
        report_data (dict): Data to include in the report
        output_file (str): Output file path
        include_plots (bool): Whether to include plots in the report  
    Returns:
        str: Path of the generated report file
    """
    # I create directory for temporary images if needed
    temp_dir = os.path.dirname(output_file)
    plots_dir = os.path.join(temp_dir, 'temp_plots')
    if include_plots and not os.path.exists(plots_dir):
        os.makedirs(plots_dir)

    # I generate plots if requested
    plot_files = []
    if include_plots:
        plot_files = _generate_report_plots(report_data, plots_dir)
    
    # I create the HTML content for the report
    html_content = _generate_report_html(report_data, plot_files)
    
    # I generate PDF from HTML
    HTML(string=html_content).write_pdf(output_file)
    
    # I remove temporary plot files
    for plot_file in plot_files:
        if os.path.exists(plot_file):
            os.remove(plot_file)
    
    return output_file

def _generate_report_plots(report_data, output_dir):
    """
    Generates plots for the report
    Args:
        report_data (dict): Data for the plots
        output_dir (str): Output directory for images  
    Returns:
        list: List of generated image paths
    """
    plot_files = []
    
    # I create plot for completed activities
    if report_data["completed_activities"]:
        # I convert to DataFrame for analysis
        activities_df = pd.DataFrame(report_data["completed_activities"])
        
        # I count activities
        activity_counts = activities_df["activity"].value_counts()
        
        # I create pie chart
        plt.figure(figsize=(8, 6))
        plt.pie(activity_counts, labels=activity_counts.index, autopct='%1.1f%%', startangle=90)
        plt.title('Completed Activities')
        plt.axis('equal')
        
        # I save the plot
        pie_chart_file = os.path.join(output_dir, 'activities_pie.png')
        plt.savefig(pie_chart_file)
        plt.close()
        plot_files.append(pie_chart_file)
        
        # I create plot for average attention duration per activity
        if report_data["attention_spans"]:
            attention_df = pd.DataFrame(report_data["attention_spans"])
            
            # I calculate average attention duration per activity
            avg_attention = attention_df.groupby("activity")["attention_duration"].mean()
            
            # I create bar chart
            plt.figure(figsize=(10, 6))
            avg_attention.plot(kind='bar')
            plt.title('Average Attention Duration per Activity')
            plt.ylabel('Duration (seconds)')
            plt.xlabel('Activity')
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # I save the plot
            bar_chart_file = os.path.join(output_dir, 'attention_bar.png')
            plt.savefig(bar_chart_file)
            plt.close()
            plot_files.append(bar_chart_file)
    
    return plot_files

def _generate_report_html(report_data, plot_files):
    """
    Generates HTML content for the report
    Args:
        report_data (dict): Data to include in the report
        plot_files (list): Paths of plot files
    Returns:
        str: HTML content of the report
    """
    # I define base CSS for the report
    css = """
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            margin: 20px;
        }
        h1, h2, h3 {
            color: #2c3e50;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }
        .section {
            margin-bottom: 30px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }
        th, td {
            padding: 10px;
            border: 1px solid #ddd;
            text-align: left;
        }
        th {
            background-color: #f2f2f2;
        }
        .chart {
            max-width: 100%;
            margin: 20px 0;
            text-align: center;
        }
        .chart img {
            max-width: 100%;
            height: auto;
        }
        .footer {
            text-align: center;
            margin-top: 40px;
            font-size: 0.8em;
            color: #7f8c8d;
        }
    </style>
    """
    
    # I create HTML content for the report
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>FlexiBuddy Report - {report_data["user_name"]}</title>
        {css}
    </head>
    <body>
        <div class="header">
            <h1>FlexiBuddy Report</h1>
            <p>User: {report_data["user_name"]} | Date: {report_data["date"]} | Session: {report_data["session_id"]}</p>
        </div>
        
        <div class="section">
            <h2>Session Summary</h2>
            <table>
                <tr>
                    <th>Completed Activities</th>
                    <th>Average Attention Duration</th>
                    <th>Frustration Moments</th>
                </tr>
                <tr>
                    <td>{report_data["total_activities"]}</td>
                    <td>{report_data["avg_attention_span"]:.2f} seconds</td>
                    <td>{report_data["frustration_moments"]}</td>
                </tr>
            </table>
        </div>
    """
    
    # I add plots if available
    if plot_files:
        html += '<div class="section"><h2>Charts</h2>'
        for i, plot_file in enumerate(plot_files):
            html += f'<div class="chart"><img src="{plot_file}" alt="Chart {i+1}"></div>'
        html += '</div>'
    
    # I add preferred activities
    if report_data["preferred_activities"]:
        html += """
        <div class="section">
            <h2>Preferred Activities</h2>
            <table>
                <tr>
                    <th>Activity</th>
                    <th>Completion Rate</th>
                    <th>Average Duration</th>
                    <th>Average Attention</th>
                </tr>
        """
        
        for activity in report_data["preferred_activities"]:
            html += f"""
                <tr>
                    <td>{activity["activity"]}</td>
                    <td>{float(activity["completion_rate"])*100:.1f}%</td>
                    <td>{float(activity["avg_duration"]):.1f} seconds</td>
                    <td>{float(activity["avg_attention"]):.1f} seconds</td>
                </tr>
            """
        
        html += """
            </table>
        </div>
        """
    
    # I add completed activities details
    if report_data["completed_activities"]:
        html += """
        <div class="section">
            <h2>Completed Activities Details</h2>
            <table>
                <tr>
                    <th>Time</th>
                    <th>Activity</th>
                    <th>Duration</th>
                    <th>Completed</th>
                </tr>
        """
        
        for activity in report_data["completed_activities"]:
            success = "Yes" if activity.get("success") == "1" else "No"
            html += f"""
                <tr>
                    <td>{activity.get("timestamp", "")}</td>
                    <td>{activity.get("activity", "")}</td>
                    <td>{float(activity.get("duration", 0)):.1f} seconds</td>
                    <td>{success}</td>
                </tr>
            """
        
        html += """
            </table>
        </div>
        """
    
    # I add frustration moments
    if report_data["frustration_events"]:
        html += """
        <div class="section">
            <h2>Frustration Moments</h2>
            <table>
                <tr>
                    <th>Time</th>
                    <th>Activity</th>
                    <th>Level</th>
                </tr>
        """
        
        for event in report_data["frustration_events"]:
            html += f"""
                <tr>
                    <td>{event.get("timestamp", "")}</td>
                    <td>{event.get("activity", "")}</td>
                    <td>{event.get("frustration_level", "")}</td>
                </tr>
            """
        
        html += """
            </table>
        </div>
        """
    
    # I add footer
    html += f"""
        <div class="footer">
            <p>Report generated by FlexiBuddy on {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}</p>
            <p>This report is confidential and contains information protected by privacy regulations.</p>
        </div>
    </body>
    </html>
    """
    return html