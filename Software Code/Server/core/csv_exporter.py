"""
CSV Export Module for Analytics Data
Exports tracking and behavior data to CSV, JSON, and Excel formats
Location: Software Code/Server/core/csv_exporter.py
"""

import csv
import json
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from core.config import DATA_DIR, CSV_COLUMNS, REPORTS_DIR


class DataExporter:
    """
    Handles export of analytics data to various formats
    """
    
    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or (DATA_DIR / "csv")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir = REPORTS_DIR
        self.reports_dir.mkdir(parents=True, exist_ok=True)
    
    def export_to_csv(
        self, 
        analyzed_tracks: List[Dict], 
        filename: str = None,
        include_summary: bool = True
    ) -> str:
        """
        Export analyzed tracks to CSV file
        
        Args:
            analyzed_tracks: List of analyzed track dictionaries
            filename: Output filename (auto-generated if None)
            include_summary: Include summary statistics
            
        Returns:
            Path to created CSV file
        """
        if not analyzed_tracks:
            print("⚠️ No data to export")
            return None
        
        # Generate filename if not provided
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"analytics_{timestamp}.csv"
        
        filepath = self.output_dir / filename
        
        # Prepare data rows
        rows = []
        for track in analyzed_tracks:
            row = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "person_id": track.get("uuid", track.get("track_id", "unknown")),
                "entry_time": self._format_time(track.get("entry_time")),
                "exit_time": self._format_time(track.get("exit_time")),
                "duration_seconds": round(track.get("duration", 0), 2),
                "behavior": track.get("behavior", "unknown"),
                "visited_zones": ", ".join(track.get("zones_visited", [])),
                "made_purchase": "Yes" if track.get("made_purchase", False) else "No",
                "confidence": round(track.get("confidence", 0), 2),
                "movement_distance": round(track.get("movement_distance", 0), 2),
                "details": track.get("details", "")
            }
            rows.append(row)
        
        # Write CSV
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                "timestamp", "person_id", "entry_time", "exit_time", 
                "duration_seconds", "behavior", "visited_zones", 
                "made_purchase", "confidence", "movement_distance", "details"
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            writer.writerows(rows)
        
        print(f"✅ CSV exported: {filepath}")
        print(f"📊 Total records: {len(rows)}")
        
        # Create summary file if requested
        if include_summary:
            self._create_summary_file(analyzed_tracks, filename)
        
        return str(filepath)
    
    def export_to_json(
        self, 
        analyzed_tracks: List[Dict],
        summary: Dict = None,
        filename: str = None
    ) -> str:
        """
        Export data to JSON format
        
        Args:
            analyzed_tracks: List of analyzed tracks
            summary: Summary statistics dictionary
            filename: Output filename
            
        Returns:
            Path to created JSON file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"analytics_{timestamp}.json"
        
        filepath = self.output_dir / filename
        
        # Prepare export data
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "total_tracks": len(analyzed_tracks),
            "summary": summary or {},
            "tracks": analyzed_tracks
        }
        
        # Write JSON
        with open(filepath, 'w', encoding='utf-8') as jsonfile:
            json.dump(export_data, jsonfile, indent=2, default=str)
        
        print(f"✅ JSON exported: {filepath}")
        return str(filepath)
    
    def export_to_excel(
        self,
        analyzed_tracks: List[Dict],
        summary: Dict = None,
        filename: str = None
    ) -> str:
        """
        Export data to Excel format with multiple sheets
        
        Args:
            analyzed_tracks: List of analyzed tracks
            summary: Summary statistics
            filename: Output filename
            
        Returns:
            Path to created Excel file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"analytics_{timestamp}.xlsx"
        
        filepath = self.output_dir / filename
        
        # Create Excel writer
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            
            # Sheet 1: Individual tracks
            if analyzed_tracks:
                df_tracks = pd.DataFrame(analyzed_tracks)
                
                # Format columns
                if 'entry_time' in df_tracks.columns:
                    df_tracks['entry_time'] = df_tracks['entry_time'].apply(self._format_time)
                if 'exit_time' in df_tracks.columns:
                    df_tracks['exit_time'] = df_tracks['exit_time'].apply(self._format_time)
                if 'zones_visited' in df_tracks.columns:
                    df_tracks['zones_visited'] = df_tracks['zones_visited'].apply(
                        lambda x: ", ".join(x) if isinstance(x, list) else x
                    )
                
                df_tracks.to_excel(writer, sheet_name='Individual Tracks', index=False)
            
            # Sheet 2: Summary statistics
            if summary:
                df_summary = pd.DataFrame([summary]).T
                df_summary.columns = ['Value']
                df_summary.to_excel(writer, sheet_name='Summary')
            
            # Sheet 3: Behavior breakdown
            if analyzed_tracks:
                behavior_counts = {}
                for track in analyzed_tracks:
                    behavior = track.get('behavior', 'unknown')
                    behavior_counts[behavior] = behavior_counts.get(behavior, 0) + 1
                
                df_behavior = pd.DataFrame(list(behavior_counts.items()), 
                                          columns=['Behavior', 'Count'])
                df_behavior = df_behavior.sort_values('Count', ascending=False)
                df_behavior.to_excel(writer, sheet_name='Behavior Breakdown', index=False)
        
        print(f"✅ Excel exported: {filepath}")
        return str(filepath)
    
    def _create_summary_file(self, analyzed_tracks: List[Dict], data_filename: str):
        """Create a summary statistics file"""
        from core.behavior_analyzer import BehaviorAnalyzer
        
        # Calculate summary (need frame dimensions, using defaults)
        analyzer = BehaviorAnalyzer(1920, 1080)
        summary = analyzer.generate_summary(analyzed_tracks)
        
        # Create summary filename
        summary_filename = data_filename.replace('.csv', '_summary.txt')
        summary_filepath = self.reports_dir / summary_filename
        
        # Write summary
        with open(summary_filepath, 'w', encoding='utf-8') as f:
            f.write("="*60 + "\n")
            f.write("EYEORA ANALYTICS SUMMARY REPORT\n")
            f.write("="*60 + "\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Data File: {data_filename}\n\n")
            
            f.write("VISITOR STATISTICS\n")
            f.write("-"*60 + "\n")
            f.write(f"Total Visitors: {summary['total_visitors']}\n")
            f.write(f"Total Customers (Purchased): {summary['purchasers']}\n")
            f.write(f"Window Shoppers: {summary['window_shoppers']}\n")
            f.write(f"Browsers: {summary['browsers']}\n")
            f.write(f"Passing Through: {summary['passing_through']}\n")
            f.write(f"Idle: {summary['idle']}\n\n")
            
            f.write("KEY METRICS\n")
            f.write("-"*60 + "\n")
            f.write(f"Conversion Rate: {summary['conversion_rate']}%\n")
            f.write(f"Average Visit Duration: {summary['avg_visit_duration']}s\n")
            f.write(f"Checkout Area Visitors: {summary['total_checkout_visitors']}\n\n")
            
            f.write("="*60 + "\n")
        
        print(f"📄 Summary report: {summary_filepath}")
    
    def _format_time(self, timestamp: float) -> str:
        """Format timestamp to readable time"""
        if timestamp is None:
            return "N/A"
        try:
            return datetime.fromtimestamp(timestamp).strftime('%H:%M:%S')
        except:
            return str(timestamp)
    
    def create_daily_report(
        self,
        analyzed_tracks: List[Dict],
        video_info: Dict = None
    ) -> Dict[str, str]:
        """
        Create comprehensive daily report in all formats
        
        Args:
            analyzed_tracks: List of analyzed tracks
            video_info: Video metadata
            
        Returns:
            Dictionary with paths to all created files
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"daily_report_{timestamp}"
        
        # Calculate summary
        from core.behavior_analyzer import BehaviorAnalyzer
        analyzer = BehaviorAnalyzer(
            video_info.get('width', 1920) if video_info else 1920,
            video_info.get('height', 1080) if video_info else 1080
        )
        summary = analyzer.generate_summary(analyzed_tracks)
        
        # Export to all formats
        created_files = {}
        
        # CSV
        csv_file = self.export_to_csv(
            analyzed_tracks, 
            f"{base_filename}.csv",
            include_summary=True
        )
        created_files['csv'] = csv_file
        
        # JSON
        json_file = self.export_to_json(
            analyzed_tracks,
            summary,
            f"{base_filename}.json"
        )
        created_files['json'] = json_file
        
        # Excel
        try:
            excel_file = self.export_to_excel(
                analyzed_tracks,
                summary,
                f"{base_filename}.xlsx"
            )
            created_files['excel'] = excel_file
        except Exception as e:
            print(f"⚠️ Excel export failed: {e}")
            created_files['excel'] = None
        
        print(f"\n✅ Daily report created: {base_filename}")
        print(f"📁 Files location: {self.output_dir}")
        
        return created_files


def generate_sample_data():
    """Generate sample data for testing"""
    sample_tracks = [
        {
            "uuid": "abc123",
            "track_id": 1,
            "entry_time": datetime.now().timestamp(),
            "exit_time": datetime.now().timestamp() + 120,
            "duration": 120.0,
            "behavior": "purchasing",
            "zones_visited": ["entry", "main_area", "checkout", "exit"],
            "made_purchase": True,
            "confidence": 0.9,
            "movement_distance": 450.5,
            "details": "Customer visited checkout area"
        },
        {
            "uuid": "def456",
            "track_id": 2,
            "entry_time": datetime.now().timestamp(),
            "exit_time": datetime.now().timestamp() + 45,
            "duration": 45.0,
            "behavior": "window_shopping",
            "zones_visited": ["entry", "main_area", "exit"],
            "made_purchase": False,
            "confidence": 0.8,
            "movement_distance": 150.3,
            "details": "Brief visit, possibly window shopping"
        }
    ]
    return sample_tracks


if __name__ == "__main__":
    print("✅ Data Exporter Module Ready")
    print("📊 Supported formats: CSV, JSON, Excel")
    print("\n🧪 Testing with sample data...")
    
    exporter = DataExporter()
    sample_data = generate_sample_data()
    
    # Test exports
    exporter.create_daily_report(sample_data)
    print("\n✅ Test completed successfully!")