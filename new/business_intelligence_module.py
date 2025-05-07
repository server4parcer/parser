"""
Business Intelligence Module - Analyze and visualize YCLIENTS booking data.

This module provides functions for analyzing booking data and generating
visualizations for business intelligence purposes.
"""
import asyncio
import logging
import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
import numpy as np
from pathlib import Path

from src.database.db_manager import DatabaseManager
from config.settings import EXPORT_PATH


logger = logging.getLogger(__name__)


class BusinessIntelligence:
    """
    Business Intelligence module for analyzing booking data.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize the business intelligence module.
        
        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
        self.reports_dir = os.path.join(EXPORT_PATH, "reports")
        os.makedirs(self.reports_dir, exist_ok=True)
    
    async def generate_price_comparison_report(self, court_types: List[str] = None) -> str:
        """
        Generate a price comparison report for different court types.
        
        Args:
            court_types: List of court types to include (optional)
            
        Returns:
            str: Path to the generated report
        """
        try:
            logger.info("Generating price comparison report")
            
            # Get price ranges for court types
            query, params = self.db_manager.queries.BookingQueries.get_price_ranges_by_court_type()
            
            # Execute query
            async with self.db_manager.pool.acquire() as conn:
                rows = await conn.fetch(query, *params)
            
            # Convert to DataFrame
            df = pd.DataFrame([dict(row) for row in rows])
            
            # Filter court types if specified
            if court_types:
                df = df[df['court_type'].isin(court_types)]
            
            # Generate timestamp for the report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = os.path.join(self.reports_dir, f"price_comparison_{timestamp}")
            
            # Create report directory
            os.makedirs(report_path, exist_ok=True)
            
            # Save data as CSV
            csv_path = os.path.join(report_path, "price_comparison_data.csv")
            df.to_csv(csv_path, index=False)
            
            # Generate visualizations
            self._generate_price_comparison_charts(df, report_path)
            
            # Generate HTML report
            html_path = os.path.join(report_path, "price_comparison_report.html")
            self._generate_price_comparison_html(df, html_path)
            
            logger.info(f"Price comparison report generated at {report_path}")
            return report_path
        
        except Exception as e:
            logger.error(f"Error generating price comparison report: {str(e)}")
            return ""
    
    def _generate_price_comparison_charts(self, df: pd.DataFrame, report_path: str) -> None:
        """
        Generate price comparison charts.
        
        Args:
            df: DataFrame with price data
            report_path: Path to save the charts
        """
        try:
            # Set seaborn style
            sns.set(style="whitegrid")
            
            # 1. Bar chart for average prices by court type
            plt.figure(figsize=(12, 6))
            ax = sns.barplot(x="court_type", y="avg_price", data=df, palette="viridis")
            ax.set_title("Average Price by Court Type", fontsize=16)
            ax.set_xlabel("Court Type", fontsize=12)
            ax.set_ylabel("Average Price (₽)", fontsize=12)
            ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right")
            
            # Add price values on top of bars
            for i, p in enumerate(ax.patches):
                ax.annotate(f"{p.get_height():.0f} ₽", 
                            (p.get_x() + p.get_width() / 2., p.get_height()), 
                            ha='center', va='bottom', fontsize=10)
            
            plt.tight_layout()
            plt.savefig(os.path.join(report_path, "avg_price_by_court_type.png"), dpi=300)
            plt.close()
            
            # 2. Box plot for price ranges by court type
            plt.figure(figsize=(12, 6))
            
            # Create a melted dataframe for the box plot
            box_df = pd.DataFrame({
                'Court Type': np.repeat(df['court_type'].values, 3),
                'Price Type': np.tile(['Min', 'Avg', 'Max'], len(df)),
                'Price': np.concatenate([df['min_price'].values, df['avg_price'].values, df['max_price'].values])
            })
            
            ax = sns.boxplot(x="Court Type", y="Price", data=box_df, palette="Set2")
            ax.set_title("Price Ranges by Court Type", fontsize=16)
            ax.set_xlabel("Court Type", fontsize=12)
            ax.set_ylabel("Price Range (₽)", fontsize=12)
            ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right")
            
            plt.tight_layout()
            plt.savefig(os.path.join(report_path, "price_ranges_by_court_type.png"), dpi=300)
            plt.close()
            
            # 3. Venue count by court type
            plt.figure(figsize=(10, 6))
            ax = sns.barplot(x="court_type", y="venue_count", data=df, palette="coolwarm")
            ax.set_title("Number of Venues by Court Type", fontsize=16)
            ax.set_xlabel("Court Type", fontsize=12)
            ax.set_ylabel("Number of Venues", fontsize=12)
            ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right")
            
            # Add venue counts on top of bars
            for i, p in enumerate(ax.patches):
                ax.annotate(f"{int(p.get_height())}", 
                            (p.get_x() + p.get_width() / 2., p.get_height()), 
                            ha='center', va='bottom', fontsize=10)
            
            plt.tight_layout()
            plt.savefig(os.path.join(report_path, "venue_count_by_court_type.png"), dpi=300)
            plt.close()
        
        except Exception as e:
            logger.error(f"Error generating price comparison charts: {str(e)}")
    
    def _generate_price_comparison_html(self, df: pd.DataFrame, html_path: str) -> None:
        """
        Generate HTML report for price comparison.
        
        Args:
            df: DataFrame with price data
            html_path: Path to save the HTML report
        """
        try:
            # Calculate summary statistics
            avg_price = df['avg_price'].mean()
            max_price = df['max_price'].max()
            min_price = df['min_price'].min()
            most_expensive_court = df.loc[df['avg_price'].idxmax(), 'court_type']
            least_expensive_court = df.loc[df['avg_price'].idxmin(), 'court_type']
            most_common_court = df.loc[df['venue_count'].idxmax(), 'court_type']
            
            # Generate HTML content
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Court Price Comparison Report</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    h1, h2 {{ color: #2c3e50; }}
                    .report-container {{ max-width: 1200px; margin: 0 auto; }}
                    .summary-stats {{ display: flex; flex-wrap: wrap; margin-bottom: 20px; }}
                    .stat-box {{ background-color: #f8f9fa; border-radius: 5px; padding: 15px; margin: 10px; flex: 1; min-width: 200px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
                    .stat-box h3 {{ margin-top: 0; color: #3498db; }}
                    .charts {{ display: flex; flex-direction: column; gap: 20px; }}
                    .chart {{ background-color: #ffffff; border-radius: 5px; padding: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
                    table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                    th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
                    th {{ background-color: #3498db; color: white; }}
                    tr:nth-child(even) {{ background-color: #f8f9fa; }}
                </style>
            </head>
            <body>
                <div class="report-container">
                    <h1>Court Price Comparison Report</h1>
                    <p>Generated on {datetime.now().strftime("%Y-%m-%d at %H:%M")}</p>
                    
                    <h2>Summary Statistics</h2>
                    <div class="summary-stats">
                        <div class="stat-box">
                            <h3>Average Price</h3>
                            <p>{avg_price:.0f} ₽</p>
                        </div>
                        <div class="stat-box">
                            <h3>Price Range</h3>
                            <p>{min_price:.0f} ₽ - {max_price:.0f} ₽</p>
                        </div>
                        <div class="stat-box">
                            <h3>Most Expensive Court Type</h3>
                            <p>{most_expensive_court}</p>
                        </div>
                        <div class="stat-box">
                            <h3>Least Expensive Court Type</h3>
                            <p>{least_expensive_court}</p>
                        </div>
                        <div class="stat-box">
                            <h3>Most Common Court Type</h3>
                            <p>{most_common_court}</p>
                        </div>
                    </div>
                    
                    <h2>Price Analysis Charts</h2>
                    <div class="charts">
                        <div class="chart">
                            <h3>Average Price by Court Type</h3>
                            <img src="avg_price_by_court_type.png" alt="Average Price by Court Type" style="max-width: 100%;">
                        </div>
                        <div class="chart">
                            <h3>Price Ranges by Court Type</h3>
                            <img src="price_ranges_by_court_type.png" alt="Price Ranges by Court Type" style="max-width: 100%;">
                        </div>
                        <div class="chart">
                            <h3>Number of Venues by Court Type</h3>
                            <img src="venue_count_by_court_type.png" alt="Number of Venues by Court Type" style="max-width: 100%;">
                        </div>
                    </div>
                    
                    <h2>Detailed Data</h2>
                    <table>
                        <tr>
                            <th>Court Type</th>
                            <th>Min Price (₽)</th>
                            <th>Avg Price (₽)</th>
                            <th>Max Price (₽)</th>
                            <th>Venue Count</th>
                        </tr>
            """
            
            # Add table rows
            for _, row in df.iterrows():
                html_content += f"""
                        <tr>
                            <td>{row['court_type']}</td>
                            <td>{row['min_price']:.0f}</td>
                            <td>{row['avg_price']:.0f}</td>
                            <td>{row['max_price']:.0f}</td>
                            <td>{row['venue_count']}</td>
                        </tr>
                """
            
            # Complete HTML
            html_content += """
                    </table>
                </div>
            </body>
            </html>
            """
            
            # Write HTML content to file
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            
            logger.info(f"HTML report generated at {html_path}")
        
        except Exception as e:
            logger.error(f"Error generating HTML report: {str(e)}")
    
    async def generate_time_category_price_report(self) -> str:
        """
        Generate a price comparison report by time category.
        
        Returns:
            str: Path to the generated report
        """
        try:
            logger.info("Generating time category price report")
            
            # Get price comparison by time category
            query, params = self.db_manager.queries.BookingQueries.get_price_comparison_by_time_category()
            
            # Execute query
            async with self.db_manager.pool.acquire() as conn:
                rows = await conn.fetch(query, *params)
            
            # Convert to DataFrame
            df = pd.DataFrame([dict(row) for row in rows])
            
            # Generate timestamp for the report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = os.path.join(self.reports_dir, f"time_category_price_{timestamp}")
            
            # Create report directory
            os.makedirs(report_path, exist_ok=True)
            
            # Save data as CSV
            csv_path = os.path.join(report_path, "time_category_price_data.csv")
            df.to_csv(csv_path, index=False)
            
            # Generate visualizations
            self._generate_time_category_charts(df, report_path)
            
            # Generate HTML report
            html_path = os.path.join(report_path, "time_category_price_report.html")
            self._generate_time_category_html(df, html_path)
            
            logger.info(f"Time category price report generated at {report_path}")
            return report_path
        
        except Exception as e:
            logger.error(f"Error generating time category price report: {str(e)}")
            return ""
    
    def _generate_time_category_charts(self, df: pd.DataFrame, report_path: str) -> None:
        """
        Generate time category price charts.
        
        Args:
            df: DataFrame with time category price data
            report_path: Path to save the charts
        """
        try:
            # Set seaborn style
            sns.set(style="whitegrid")
            
            # 1. Grouped bar chart for average prices by court type and time category
            plt.figure(figsize=(14, 8))
            ax = sns.barplot(x="court_type", y="avg_price", hue="time_category", data=df, palette="viridis")
            ax.set_title("Average Price by Court Type and Time Category", fontsize=16)
            ax.set_xlabel("Court Type", fontsize=12)
            ax.set_ylabel("Average Price (₽)", fontsize=12)
            ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right")
            ax.legend(title="Time Category")
            
            plt.tight_layout()
            plt.savefig(os.path.join(report_path, "avg_price_by_court_time.png"), dpi=300)
            plt.close()
            
            # 2. Heatmap for price differences
            # Pivot the data for the heatmap
            pivot_df = df.pivot_table(index="court_type", columns="time_category", values="avg_price", fill_value=0)
            
            plt.figure(figsize=(12, 8))
            ax = sns.heatmap(pivot_df, annot=True, fmt=".0f", cmap="YlGnBu", linewidths=.5)
            ax.set_title("Average Price Heatmap by Court Type and Time Category", fontsize=16)
            
            plt.tight_layout()
            plt.savefig(os.path.join(report_path, "price_heatmap.png"), dpi=300)
            plt.close()
            
            # 3. Line plot showing price evolution by time category
            plt.figure(figsize=(14, 8))
            
            # Sort by court type for better visualization
            sorted_df = df.sort_values(by=['court_type', 'time_category'])
            
            ax = sns.lineplot(x="court_type", y="avg_price", hue="time_category", 
                             style="time_category", markers=True, dashes=False, data=sorted_df)
            
            ax.set_title("Price Trends by Time Category", fontsize=16)
            ax.set_xlabel("Court Type", fontsize=12)
            ax.set_ylabel("Average Price (₽)", fontsize=12)
            ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right")
            
            plt.tight_layout()
            plt.savefig(os.path.join(report_path, "price_trends.png"), dpi=300)
            plt.close()
            
            # 4. Slot count by time category and court type
            plt.figure(figsize=(14, 8))
            ax = sns.barplot(x="time_category", y="slot_count", hue="court_type", data=df, palette="Set2")
            ax.set_title("Slot Availability by Time Category and Court Type", fontsize=16)
            ax.set_xlabel("Time Category", fontsize=12)
            ax.set_ylabel("Available Slots", fontsize=12)
            
            plt.tight_layout()
            plt.savefig(os.path.join(report_path, "slot_availability.png"), dpi=300)
            plt.close()
        
        except Exception as e:
            logger.error(f"Error generating time category price charts: {str(e)}")
    
    def _generate_time_category_html(self, df: pd.DataFrame, html_path: str) -> None:
        """
        Generate HTML report for time category price comparison.
        
        Args:
            df: DataFrame with time category price data
            html_path: Path to save the HTML report
        """
        try:
            # Calculate summary statistics by time category
            time_summary = df.groupby('time_category').agg({
                'avg_price': ['mean', 'min', 'max'],
                'slot_count': 'sum'
            }).reset_index()
            
            time_summary.columns = ['time_category', 'mean_price', 'min_price', 'max_price', 'total_slots']
            
            # Find most expensive and cheapest time categories
            most_expensive_time = time_summary.loc[time_summary['mean_price'].idxmax(), 'time_category']
            cheapest_time = time_summary.loc[time_summary['mean_price'].idxmin(), 'time_category']
            
            # Calculate price premiums
            if len(time_summary) > 1:
                baseline_price = time_summary.loc[time_summary['time_category'] == 'DAY', 'mean_price'].values[0]
                time_summary['price_premium'] = ((time_summary['mean_price'] / baseline_price) - 1) * 100
            else:
                time_summary['price_premium'] = 0
            
            # Generate HTML content
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Time Category Price Analysis</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    h1, h2 {{ color: #2c3e50; }}
                    .report-container {{ max-width: 1200px; margin: 0 auto; }}
                    .summary-stats {{ display: flex; flex-wrap: wrap; margin-bottom: 20px; }}
                    .stat-box {{ background-color: #f8f9fa; border-radius: 5px; padding: 15px; margin: 10px; flex: 1; min-width: 200px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
                    .stat-box h3 {{ margin-top: 0; color: #3498db; }}
                    .charts {{ display: flex; flex-direction: column; gap: 20px; }}
                    .chart {{ background-color: #ffffff; border-radius: 5px; padding: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
                    table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                    th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
                    th {{ background-color: #3498db; color: white; }}
                    tr:nth-child(even) {{ background-color: #f8f9fa; }}
                    .premium-positive {{ color: #e74c3c; }}
                    .premium-negative {{ color: #2ecc71; }}
                </style>
            </head>
            <body>
                <div class="report-container">
                    <h1>Time Category Price Analysis</h1>
                    <p>Generated on {datetime.now().strftime("%Y-%m-%d at %H:%M")}</p>
                    
                    <h2>Summary by Time Category</h2>
                    <div class="summary-stats">
            """
            
            # Add summary stats for each time category
            for _, row in time_summary.iterrows():
                premium_class = "premium-positive" if row['price_premium'] > 0 else "premium-negative"
                premium_text = f"{row['price_premium']:.1f}%" if 'DAY' != row['time_category'] else "Baseline"
                
                html_content += f"""
                        <div class="stat-box">
                            <h3>{row['time_category']}</h3>
                            <p>Average Price: {row['mean_price']:.0f} ₽</p>
                            <p>Range: {row['min_price']:.0f} ₽ - {row['max_price']:.0f} ₽</p>
                            <p>Available Slots: {row['total_slots']}</p>
                            <p>Price Premium: <span class="{premium_class}">{premium_text}</span></p>
                        </div>
                """
            
            html_content += f"""
                    </div>
                    
                    <h2>Key Findings</h2>
                    <div class="stat-box">
                        <p>Most Expensive Time: <strong>{most_expensive_time}</strong></p>
                        <p>Cheapest Time: <strong>{cheapest_time}</strong></p>
                    </div>
                    
                    <h2>Price Analysis Charts</h2>
                    <div class="charts">
                        <div class="chart">
                            <h3>Average Price by Court Type and Time Category</h3>
                            <img src="avg_price_by_court_time.png" alt="Average Price by Court Type and Time Category" style="max-width: 100%;">
                            <p>This chart shows how prices vary across different court types and time categories.</p>
                        </div>
                        <div class="chart">
                            <h3>Price Heatmap</h3>
                            <img src="price_heatmap.png" alt="Price Heatmap" style="max-width: 100%;">
                            <p>This heatmap provides a visual representation of price variations across court types and time categories.</p>
                        </div>
                        <div class="chart">
                            <h3>Price Trends by Time Category</h3>
                            <img src="price_trends.png" alt="Price Trends by Time Category" style="max-width: 100%;">
                            <p>This line chart shows how prices trend across different court types for each time category.</p>
                        </div>
                        <div class="chart">
                            <h3>Slot Availability</h3>
                            <img src="slot_availability.png" alt="Slot Availability" style="max-width: 100%;">
                            <p>This chart shows the availability of slots for different time categories and court types.</p>
                        </div>
                    </div>
                    
                    <h2>Detailed Data by Court Type and Time Category</h2>
                    <table>
                        <tr>
                            <th>Court Type</th>
                            <th>Time Category</th>
                            <th>Average Price (₽)</th>
                            <th>Available Slots</th>
                        </tr>
            """
            
            # Add table rows
            for _, row in df.iterrows():
                html_content += f"""
                        <tr>
                            <td>{row['court_type']}</td>
                            <td>{row['time_category']}</td>
                            <td>{row['avg_price']:.0f}</td>
                            <td>{row['slot_count']}</td>
                        </tr>
                """
            
            # Complete HTML
            html_content += """
                    </table>
                    
                    <h2>Recommendations</h2>
                    <div class="stat-box">
                        <p>1. <strong>Price Optimization:</strong> Consider adjusting pricing based on demand patterns observed in different time categories. Higher prices during peak times and discounts during less popular times can optimize revenue.</p>
                        <p>2. <strong>Marketing Focus:</strong> Target marketing efforts towards promoting court types with lower utilization rates, especially during off-peak hours.</p>
                        <p>3. <strong>Competitive Positioning:</strong> Use the price comparison data to position your courts competitively in the market, highlighting value propositions based on court type and time availability.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Write HTML content to file
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            
            logger.info(f"HTML time category report generated at {html_path}")
        
        except Exception as e:
            logger.error(f"Error generating time category HTML report: {str(e)}")
    
    async def generate_availability_heatmap(self, days: int = 14) -> str:
        """
        Generate an availability heatmap showing booking patterns.
        
        Args:
            days: Number of days to include in the analysis
            
        Returns:
            str: Path to the generated report
        """
        try:
            logger.info(f"Generating availability heatmap for {days} days")
            
            # Get availability data
            query, params = self.db_manager.queries.BookingQueries.get_availability_by_location()
            
            # Execute query
            async with self.db_manager.pool.acquire() as conn:
                rows = await conn.fetch(query, *params)
            
            # Convert to DataFrame
            df = pd.DataFrame([dict(row) for row in rows])
            
            # Filter by date range if we have date column
            if 'date' in df.columns:
                today = datetime.now().date()
                cutoff_date = (today - timedelta(days=days)).isoformat()
                df = df[df['date'] >= cutoff_date]
            
            # Generate timestamp for the report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = os.path.join(self.reports_dir, f"availability_heatmap_{timestamp}")
            
            # Create report directory
            os.makedirs(report_path, exist_ok=True)
            
            # Save data as CSV
            csv_path = os.path.join(report_path, "availability_data.csv")
            df.to_csv(csv_path, index=False)
            
            # Generate visualizations
            self._generate_availability_charts(df, report_path)
            
            # Generate HTML report
            html_path = os.path.join(report_path, "availability_heatmap.html")
            self._generate_availability_html(df, html_path)
            
            logger.info(f"Availability heatmap generated at {report_path}")
            return report_path
        
        except Exception as e:
            logger.error(f"Error generating availability heatmap: {str(e)}")
            return ""
    
    def _generate_availability_charts(self, df: pd.DataFrame, report_path: str) -> None:
        """
        Generate availability charts.
        
        Args:
            df: DataFrame with availability data
            report_path: Path to save the charts
        """
        try:
            # Set seaborn style
            sns.set(style="whitegrid")
            
            # 1. Heatmap of availability by location and date
            # Pivot the data for the heatmap
            if 'location_name' in df.columns and 'date' in df.columns:
                pivot_df = df.pivot_table(index="location_name", columns="date", values="total_slots", fill_value=0)
                
                # Keep only the last 14 columns (days) to make the chart more readable
                if pivot_df.shape[1] > 14:
                    pivot_df = pivot_df.iloc[:, -14:]
                
                plt.figure(figsize=(16, 10))
                ax = sns.heatmap(pivot_df, annot=True, fmt="d", cmap="YlGnBu", linewidths=.5)
                ax.set_title("Available Slots by Location and Date", fontsize=16)
                ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right")
                
                plt.tight_layout()
                plt.savefig(os.path.join(report_path, "availability_heatmap.png"), dpi=300)
                plt.close()
                
                # 2. Line plot of availability trends
                plt.figure(figsize=(16, 8))
                
                # Convert date column to datetime for proper ordering
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date')
                
                ax = sns.lineplot(x="date", y="total_slots", hue="location_name", data=df, markers=True)
                ax.set_title("Availability Trends by Location", fontsize=16)
                ax.set_xlabel("Date", fontsize=12)
                ax.set_ylabel("Available Slots", fontsize=12)
                ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right")
                
                plt.tight_layout()
                plt.savefig(os.path.join(report_path, "availability_trends.png"), dpi=300)
                plt.close()
            
            # 3. Bar chart of total availability by location
            if 'location_name' in df.columns:
                location_total = df.groupby('location_name')['total_slots'].sum().reset_index()
                
                plt.figure(figsize=(14, 8))
                ax = sns.barplot(x="location_name", y="total_slots", data=location_total, palette="viridis")
                ax.set_title("Total Available Slots by Location", fontsize=16)
                ax.set_xlabel("Location", fontsize=12)
                ax.set_ylabel("Total Available Slots", fontsize=12)
                ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right")
                
                # Add values on top of bars
                for i, p in enumerate(ax.patches):
                    ax.annotate(f"{int(p.get_height())}", 
                                (p.get_x() + p.get_width() / 2., p.get_height()), 
                                ha='center', va='bottom', fontsize=10)
                
                plt.tight_layout()
                plt.savefig(os.path.join(report_path, "total_availability.png"), dpi=300)
                plt.close()
        
        except Exception as e:
            logger.error(f"Error generating availability charts: {str(e)}")
    
    def _generate_availability_html(self, df: pd.DataFrame, html_path: str) -> None:
        """
        Generate HTML report for availability analysis.
        
        Args:
            df: DataFrame with availability data
            html_path: Path to save the HTML report
        """
        try:
            # Calculate summary statistics
            total_slots = df['total_slots'].sum() if 'total_slots' in df.columns else 0
            
            if 'location_name' in df.columns:
                location_summary = df.groupby('location_name')['total_slots'].sum().reset_index()
                location_summary = location_summary.sort_values('total_slots', ascending=False)
                top_location = location_summary.iloc[0]['location_name'] if not location_summary.empty else "N/A"
                
                # Calculate busy days if we have date column
                busy_days = None
                if 'date' in df.columns:
                    date_summary = df.groupby('date')['total_slots'].sum().reset_index()
                    date_summary = date_summary.sort_values('total_slots', ascending=False)
                    busy_days = date_summary.head(3) if not date_summary.empty else None
            
            # Generate HTML content
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Venue Availability Analysis</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    h1, h2 {{ color: #2c3e50; }}
                    .report-container {{ max-width: 1200px; margin: 0 auto; }}
                    .summary-stats {{ display: flex; flex-wrap: wrap; margin-bottom: 20px; }}
                    .stat-box {{ background-color: #f8f9fa; border-radius: 5px; padding: 15px; margin: 10px; flex: 1; min-width: 200px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
                    .stat-box h3 {{ margin-top: 0; color: #3498db; }}
                    .charts {{ display: flex; flex-direction: column; gap: 20px; }}
                    .chart {{ background-color: #ffffff; border-radius: 5px; padding: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
                    table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                    th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
                    th {{ background-color: #3498db; color: white; }}
                    tr:nth-child(even) {{ background-color: #f8f9fa; }}
                </style>
            </head>
            <body>
                <div class="report-container">
                    <h1>Venue Availability Analysis</h1>
                    <p>Generated on {datetime.now().strftime("%Y-%m-%d at %H:%M")}</p>
                    
                    <h2>Summary Statistics</h2>
                    <div class="summary-stats">
                        <div class="stat-box">
                            <h3>Total Available Slots</h3>
                            <p>{total_slots}</p>
                        </div>
            """
            
            if 'location_name' in df.columns:
                html_content += f"""
                        <div class="stat-box">
                            <h3>Most Available Location</h3>
                            <p>{top_location}</p>
                        </div>
                """
            
            if busy_days is not None and not busy_days.empty:
                busiest_day = busy_days.iloc[0]['date']
                html_content += f"""
                        <div class="stat-box">
                            <h3>Busiest Day</h3>
                            <p>{busiest_day}</p>
                        </div>
                """
            
            html_content += """
                    </div>
                    
                    <h2>Availability Analysis</h2>
                    <div class="charts">
            """
            
            # Add charts if they were generated
            chart_files = [
                ("availability_heatmap.png", "Available Slots by Location and Date"),
                ("availability_trends.png", "Availability Trends by Location"),
                ("total_availability.png", "Total Available Slots by Location")
            ]
            
            for chart_file, chart_title in chart_files:
                chart_path = os.path.join(report_path, chart_file)
                if os.path.exists(chart_path):
                    html_content += f"""
                        <div class="chart">
                            <h3>{chart_title}</h3>
                            <img src="{chart_file}" alt="{chart_title}" style="max-width: 100%;">
                        </div>
                    """
            
            # Add top locations table
            if 'location_name' in df.columns:
                html_content += """
                    <h2>Location Availability Ranking</h2>
                    <table>
                        <tr>
                            <th>Location</th>
                            <th>Available Slots</th>
                        </tr>
                """
                
                for _, row in location_summary.iterrows():
                    html_content += f"""
                        <tr>
                            <td>{row['location_name']}</td>
                            <td>{int(row['total_slots'])}</td>
                        </tr>
                    """
                
                html_content += """
                    </table>
                """
            
            # Add busy days table
            if busy_days is not None and not busy_days.empty:
                html_content += """
                    <h2>Busiest Days</h2>
                    <table>
                        <tr>
                            <th>Date</th>
                            <th>Available Slots</th>
                        </tr>
                """
                
                for _, row in busy_days.iterrows():
                    html_content += f"""
                        <tr>
                            <td>{row['date']}</td>
                            <td>{int(row['total_slots'])}</td>
                        </tr>
                    """
                
                html_content += """
                    </table>
                """
            
            # Complete HTML
            html_content += """
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Write HTML content to file
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            
            logger.info(f"HTML availability report generated at {html_path}")
        
        except Exception as e:
            logger.error(f"Error generating availability HTML report: {str(e)}")
    
    async def detect_price_changes(self, days: int = 30) -> str:
        """
        Detect price changes over the specified period.
        
        Args:
            days: Number of days to check for price changes
            
        Returns:
            str: Path to the generated report
        """
        try:
            logger.info(f"Detecting price changes over the last {days} days")
            
            # Get price changes
            query, params = self.db_manager.queries.PriceHistoryQueries.get_price_changes(days)
            
            # Execute query
            async with self.db_manager.pool.acquire() as conn:
                rows = await conn.fetch(query, *params)
            
            # Convert to DataFrame
            df = pd.DataFrame([dict(row) for row in rows])
            
            # Generate timestamp for the report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = os.path.join(self.reports_dir, f"price_changes_{timestamp}")
            
            # Create report directory
            os.makedirs(report_path, exist_ok=True)
            
            # Save data as CSV if we have results
            if not df.empty:
                # Clean price columns
                if 'current_price' in df.columns:
                    df['current_price_clean'] = df['current_price'].apply(
                        lambda x: float(re.sub(r'[^\d.]', '', str(x))) if pd.notnull(x) else 0
                    )
                
                if 'historical_price' in df.columns:
                    df['historical_price_clean'] = df['historical_price'].apply(
                        lambda x: float(re.sub(r'[^\d.]', '', str(x))) if pd.notnull(x) else 0
                    )
                
                # Calculate price change percentage
                if 'current_price_clean' in df.columns and 'historical_price_clean' in df.columns:
                    df['price_change_pct'] = ((df['current_price_clean'] / df['historical_price_clean']) - 1) * 100
                
                # Save to CSV
                csv_path = os.path.join(report_path, "price_changes_data.csv")
                df.to_csv(csv_path, index=False)
                
                # Generate visualizations
                self._generate_price_changes_charts(df, report_path)
                
                # Generate HTML report
                html_path = os.path.join(report_path, "price_changes_report.html")
                self._generate_price_changes_html(df, html_path)
                
                logger.info(f"Price changes report generated at {report_path}")
            else:
                logger.info("No price changes detected in the specified period")
                
                # Create a simple HTML report for no changes
                html_path = os.path.join(report_path, "price_changes_report.html")
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>Price Changes Report</title>
                        <style>
                            body {{ font-family: Arial, sans-serif; margin: 20px; }}
                            h1 {{ color: #2c3e50; }}
                            .report-container {{ max-width: 800px; margin: 0 auto; }}
                            .message-box {{ background-color: #f8f9fa; border-radius: 5px; padding: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
                        </style>
                    </head>
                    <body>
                        <div class="report-container">
                            <h1>Price Changes Report</h1>
                            <p>Generated on {datetime.now().strftime("%Y-%m-%d at %H:%M")}</p>
                            
                            <div class="message-box">
                                <p>No price changes were detected in the last {days} days.</p>
                                <p>This could indicate stable pricing across all venues during this period.</p>
                            </div>
                        </div>
                    </body>
                    </html>
                    """)
            
            return report_path
        
        except Exception as e:
            logger.error(f"Error detecting price changes: {str(e)}")
            return ""
    
    def _generate_price_changes_charts(self, df: pd.DataFrame, report_path: str) -> None:
        """
        Generate price changes charts.
        
        Args:
            df: DataFrame with price changes data
            report_path: Path to save the charts
        """
        try:
            # Skip if DataFrame is empty
            if df.empty:
                logger.warning("Cannot generate price changes charts: DataFrame is empty")
                return
            
            # Ensure we have the required columns
            required_columns = ['court_type', 'price_change_pct', 'current_price_clean', 'historical_price_clean']
            if not all(col in df.columns for col in required_columns):
                logger.warning(f"Cannot generate price changes charts: Missing required columns {required_columns}")
                return
            
            # Set seaborn style
            sns.set(style="whitegrid")
            
            # 1. Bar chart of price changes by court type
            court_changes = df.groupby('court_type')['price_change_pct'].mean().reset_index()
            
            plt.figure(figsize=(14, 8))
            bars = sns.barplot(x="court_type", y="price_change_pct", data=court_changes, palette="coolwarm")
            
            # Color bars based on positive/negative changes
            for i, bar in enumerate(bars.patches):
                if court_changes.iloc[i]['price_change_pct'] > 0:
                    bar.set_facecolor('#e74c3c')  # Red for price increases
                else:
                    bar.set_facecolor('#2ecc71')  # Green for price decreases
            
            plt.axhline(y=0, color='black', linestyle='-', alpha=0.3)
            bars.set_title("Average Price Change by Court Type (%)", fontsize=16)
            bars.set_xlabel("Court Type", fontsize=12)
            bars.set_ylabel("Price Change (%)", fontsize=12)
            bars.set_xticklabels(bars.get_xticklabels(), rotation=45, ha="right")
            
            # Add values on top of bars
            for i, bar in enumerate(bars.patches):
                height = bar.get_height()
                sign = "+" if height > 0 else ""
                bars.annotate(f"{sign}{height:.1f}%", 
                            (bar.get_x() + bar.get_width() / 2., height), 
                            ha='center', va='bottom' if height > 0 else 'top', fontsize=10)
            
            plt.tight_layout()
            plt.savefig(os.path.join(report_path, "price_change_by_court.png"), dpi=300)
            plt.close()
            
            # 2. Scatter plot of old vs new prices
            plt.figure(figsize=(12, 8))
            scatter = sns.scatterplot(x="historical_price_clean", y="current_price_clean", 
                                     hue="court_type", size="price_change_pct", 
                                     sizes=(20, 200), data=df)
            
            # Add diagonal line (no change)
            x_min, x_max = plt.xlim()
            y_min, y_max = plt.ylim()
            max_val = max(x_max, y_max)
            plt.plot([0, max_val], [0, max_val], 'k--', alpha=0.5)
            
            scatter.set_title("Price Comparison: Historical vs Current", fontsize=16)
            scatter.set_xlabel("Historical Price (₽)", fontsize=12)
            scatter.set_ylabel("Current Price (₽)", fontsize=12)
            
            plt.tight_layout()
            plt.savefig(os.path.join(report_path, "price_comparison_scatter.png"), dpi=300)
            plt.close()
            
            # 3. Histogram of price change percentages
            plt.figure(figsize=(12, 6))
            hist = sns.histplot(df['price_change_pct'], bins=20, kde=True)
            
            # Add vertical line at 0%
            plt.axvline(x=0, color='red', linestyle='--')
            
            hist.set_title("Distribution of Price Changes", fontsize=16)
            hist.set_xlabel("Price Change (%)", fontsize=12)
            hist.set_ylabel("Count", fontsize=12)
            
            plt.tight_layout()
            plt.savefig(os.path.join(report_path, "price_change_distribution.png"), dpi=300)
            plt.close()
            
            # 4. Time series of prices if we have recorded_at column
            if 'recorded_at' in df.columns:
                # Convert to datetime
                df['recorded_at'] = pd.to_datetime(df['recorded_at'])
                
                # Sort by date
                df = df.sort_values('recorded_at')
                
                # Group by date and court type
                daily_prices = df.groupby([pd.Grouper(key='recorded_at', freq='D'), 'court_type'])['current_price_clean'].mean().reset_index()
                
                plt.figure(figsize=(14, 8))
                time_series = sns.lineplot(x="recorded_at", y="current_price_clean", hue="court_type", data=daily_prices)
                
                time_series.set_title("Price Trends Over Time", fontsize=16)
                time_series.set_xlabel("Date", fontsize=12)
                time_series.set_ylabel("Average Price (₽)", fontsize=12)
                
                plt.tight_layout()
                plt.savefig(os.path.join(report_path, "price_trends_over_time.png"), dpi=300)
                plt.close()
        
        except Exception as e:
            logger.error(f"Error generating price changes charts: {str(e)}")
    
    def _generate_price_changes_html(self, df: pd.DataFrame, html_path: str) -> None:
        """
        Generate HTML report for price changes analysis.
        
        Args:
            df: DataFrame with price changes data
            html_path: Path to save the HTML report
        """
        try:
            # Skip if DataFrame is empty
            if df.empty:
                logger.warning("Cannot generate price changes HTML report: DataFrame is empty")
                return
            
            # Calculate summary statistics
            avg_change_pct = df['price_change_pct'].mean() if 'price_change_pct' in df.columns else 0
            max_increase = df['price_change_pct'].max() if 'price_change_pct' in df.columns else 0
            max_decrease = df['price_change_pct'].min() if 'price_change_pct' in df.columns else 0
            
            increases_count = len(df[df['price_change_pct'] > 0]) if 'price_change_pct' in df.columns else 0
            decreases_count = len(df[df['price_change_pct'] < 0]) if 'price_change_pct' in df.columns else 0
            no_change_count = len(df[df['price_change_pct'] == 0]) if 'price_change_pct' in df.columns else 0
            
            # Generate court type summary if we have court_type column
            court_summary = None
            if 'court_type' in df.columns and 'price_change_pct' in df.columns:
                court_summary = df.groupby('court_type')['price_change_pct'].agg([
                    ('mean', 'mean'),
                    ('min', 'min'),
                    ('max', 'max'),
                    ('count', 'count')
                ]).reset_index()
            
            # Generate HTML content
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Price Changes Analysis</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    h1, h2 {{ color: #2c3e50; }}
                    .report-container {{ max-width: 1200px; margin: 0 auto; }}
                    .summary-stats {{ display: flex; flex-wrap: wrap; margin-bottom: 20px; }}
                    .stat-box {{ background-color: #f8f9fa; border-radius: 5px; padding: 15px; margin: 10px; flex: 1; min-width: 200px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
                    .stat-box h3 {{ margin-top: 0; color: #3498db; }}
                    .price-up {{ color: #e74c3c; }}
                    .price-down {{ color: #2ecc71; }}
                    .charts {{ display: flex; flex-direction: column; gap: 20px; }}
                    .chart {{ background-color: #ffffff; border-radius: 5px; padding: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
                    table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                    th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
                    th {{ background-color: #3498db; color: white; }}
                    tr:nth-child(even) {{ background-color: #f8f9fa; }}
                </style>
            </head>
            <body>
                <div class="report-container">
                    <h1>Price Changes Analysis</h1>
                    <p>Generated on {datetime.now().strftime("%Y-%m-%d at %H:%M")}</p>
                    
                    <h2>Summary Statistics</h2>
                    <div class="summary-stats">
                        <div class="stat-box">
                            <h3>Average Price Change</h3>
                            <p class="{("price-up" if avg_change_pct > 0 else "price-down") if avg_change_pct != 0 else ""}">
                                {'+' if avg_change_pct > 0 else ''}{avg_change_pct:.2f}%
                            </p>
                        </div>
                        <div class="stat-box">
                            <h3>Largest Price Increase</h3>
                            <p class="price-up">+{max_increase:.2f}%</p>
                        </div>
                        <div class="stat-box">
                            <h3>Largest Price Decrease</h3>
                            <p class="price-down">{max_decrease:.2f}%</p>
                        </div>
                        <div class="stat-box">
                            <h3>Price Changes Count</h3>
                            <p>{increases_count} increases, {decreases_count} decreases, {no_change_count} unchanged</p>
                        </div>
                    </div>
                    
                    <h2>Price Change Analysis</h2>
                    <div class="charts">
            """
            
            # Add charts if they were generated
            chart_files = [
                ("price_change_by_court.png", "Average Price Change by Court Type (%)"),
                ("price_comparison_scatter.png", "Price Comparison: Historical vs Current"),
                ("price_change_distribution.png", "Distribution of Price Changes"),
                ("price_trends_over_time.png", "Price Trends Over Time")
            ]
            
            for chart_file, chart_title in chart_files:
                chart_path = os.path.join(report_path, chart_file)
                if os.path.exists(chart_path):
                    html_content += f"""
                        <div class="chart">
                            <h3>{chart_title}</h3>
                            <img src="{chart_file}" alt="{chart_title}" style="max-width: 100%;">
                        </div>
                    """
            
            # Add court type summary table if available
            if court_summary is not None and not court_summary.empty:
                html_content += """
                    <h2>Price Changes by Court Type</h2>
                    <table>
                        <tr>
                            <th>Court Type</th>
                            <th>Average Change (%)</th>
                            <th>Min Change (%)</th>
                            <th>Max Change (%)</th>
                            <th>Number of Changes</th>
                        </tr>
                """
                
                for _, row in court_summary.iterrows():
                    avg_class = "price-up" if row['mean'] > 0 else "price-down" if row['mean'] < 0 else ""
                    min_class = "price-down" if row['min'] < 0 else ""
                    max_class = "price-up" if row['max'] > 0 else ""
                    
                    html_content += f"""
                        <tr>
                            <td>{row['court_type']}</td>
                            <td class="{avg_class}">{'+' if row['mean'] > 0 else ''}{row['mean']:.2f}%</td>
                            <td class="{min_class}">{row['min']:.2f}%</td>
                            <td class="{max_class}">{'+' if row['max'] > 0 else ''}{row['max']:.2f}%</td>
                            <td>{int(row['count'])}</td>
                        </tr>
                    """
                
                html_content += """
                    </table>
                """
            
            # Add detailed changes table
            html_content += """
                <h2>Detailed Price Changes</h2>
                <table>
                    <tr>
                        <th>Court Type</th>
                        <th>Historical Price</th>
                        <th>Current Price</th>
                        <th>Change (%)</th>
                    </tr>
            """
            
            # Add top 20 changes
            if 'price_change_pct' in df.columns:
                top_changes = df.sort_values('price_change_pct', ascending=False).head(20)
                
                for _, row in top_changes.iterrows():
                    change_class = "price-up" if row['price_change_pct'] > 0 else "price-down" if row['price_change_pct'] < 0 else ""
                    
                    html_content += f"""
                        <tr>
                            <td>{row['court_type'] if 'court_type' in row else 'N/A'}</td>
                            <td>{row['historical_price'] if 'historical_price' in row else row['historical_price_clean'] if 'historical_price_clean' in row else 'N/A'}</td>
                            <td>{row['current_price'] if 'current_price' in row else row['current_price_clean'] if 'current_price_clean' in row else 'N/A'}</td>
                            <td class="{change_class}">{'+' if row['price_change_pct'] > 0 else ''}{row['price_change_pct']:.2f}%</td>
                        </tr>
                    """
            
            # Complete HTML
            html_content += """
                    </table>
                    <p><em>Note: Showing top 20 price changes by percentage.</em></p>
                    
                    <h2>Market Insights</h2>
                    <div class="stat-box">
            """
            
            # Add insights based on the data
            if avg_change_pct > 5:
                html_content += """
                        <p><strong>Significant Price Inflation:</strong> The overall market is experiencing substantial price increases, which may indicate growing demand or increased operational costs across venues.</p>
                """
            elif avg_change_pct < -5:
                html_content += """
                        <p><strong>Market Price Correction:</strong> The significant price decreases suggest a market correction, possibly due to increased competition or efforts to attract more customers during periods of lower demand.</p>
                """
            elif abs(avg_change_pct) <= 2:
                html_content += """
                        <p><strong>Stable Pricing Environment:</strong> The market shows pricing stability, with only minor adjustments that are likely routine or seasonal in nature.</p>
                """
            else:
                html_content += """
                        <p><strong>Moderate Price Adjustments:</strong> The market is experiencing moderate price changes, which may reflect normal adjustments to demand or minor cost increases.</p>
                """
            
            if increases_count > decreases_count * 2:
                html_content += """
                        <p><strong>Widespread Price Increases:</strong> The large number of price increases compared to decreases suggests a market-wide trend toward higher pricing, which may present opportunities for competitive pricing strategies.</p>
                """
            elif decreases_count > increases_count * 2:
                html_content += """
                        <p><strong>Competitive Price Cutting:</strong> The prevalence of price decreases indicates a more competitive market where venues are adjusting prices downward to attract customers.</p>
                """
            
            # Complete HTML
            html_content += """
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Write HTML content to file
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            
            logger.info(f"HTML price changes report generated at {html_path}")
        
        except Exception as e:
            logger.error(f"Error generating price changes HTML report: {str(e)}")
