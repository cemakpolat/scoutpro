"""
PDF Report Generator
Uses ReportLab to generate PDF reports
"""
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import io
import httpx
import logging
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class PDFGenerator:
    """Generate PDF reports for players, teams, and matches"""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a237e'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#283593'),
            spaceAfter=12
        )

    async def fetch_player_data(self, player_id: str) -> Dict[str, Any]:
        """Fetch player data from Player Service"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"http://player-service:8000/api/v2/players/{player_id}",
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error fetching player data: {e}")
            # Return mock data for now
            return {
                "player_id": player_id,
                "name": "Sample Player",
                "position": "Forward",
                "team": "Sample Team"
            }

    async def generate_player_report(
        self,
        player_id: str,
        include_stats: bool = True,
        include_charts: bool = True
    ) -> bytes:
        """
        Generate a PDF report for a player

        Args:
            player_id: Player ID
            include_stats: Include statistics section
            include_charts: Include charts and visualizations

        Returns:
            PDF content as bytes
        """
        try:
            # Fetch player data
            player_data = await self.fetch_player_data(player_id)

            # Create PDF buffer
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )

            # Container for the 'Flowable' objects
            elements = []

            # Title
            title = Paragraph(
                f"Player Report: {player_data.get('name', 'Unknown')}",
                self.title_style
            )
            elements.append(title)
            elements.append(Spacer(1, 12))

            # Metadata
            metadata_text = f"""
            <b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}<br/>
            <b>Player ID:</b> {player_id}<br/>
            <b>Position:</b> {player_data.get('position', 'N/A')}<br/>
            <b>Team:</b> {player_data.get('team', 'N/A')}
            """
            metadata = Paragraph(metadata_text, self.styles['Normal'])
            elements.append(metadata)
            elements.append(Spacer(1, 20))

            # Player information section
            elements.append(Paragraph("Player Information", self.heading_style))
            player_info_data = [
                ['Field', 'Value'],
                ['Name', player_data.get('name', 'N/A')],
                ['Position', player_data.get('position', 'N/A')],
                ['Team', player_data.get('team', 'N/A')],
                ['Player ID', player_id],
            ]
            player_info_table = Table(player_info_data, colWidths=[2.5*inch, 4*inch])
            player_info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            elements.append(player_info_table)
            elements.append(Spacer(1, 20))

            # Statistics section
            if include_stats:
                elements.append(Paragraph("Season Statistics", self.heading_style))
                stats_data = [
                    ['Statistic', 'Value'],
                    ['Appearances', '25'],
                    ['Goals', '12'],
                    ['Assists', '8'],
                    ['Pass Accuracy', '85%'],
                    ['Minutes Played', '2,100'],
                ]
                stats_table = Table(stats_data, colWidths=[3*inch, 3.5*inch])
                stats_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
                ]))
                elements.append(stats_table)
                elements.append(Spacer(1, 20))

            # Footer
            elements.append(Spacer(1, 30))
            footer_text = f"<i>Generated by ScoutPro Report Service - {datetime.now().year}</i>"
            footer = Paragraph(footer_text, self.styles['Normal'])
            elements.append(footer)

            # Build PDF
            doc.build(elements)

            # Get PDF content
            pdf_content = buffer.getvalue()
            buffer.close()

            return pdf_content

        except Exception as e:
            logger.error(f"Error generating player PDF report: {e}")
            raise

    async def generate_team_report(
        self,
        team_id: str,
        include_players: bool = True,
        include_stats: bool = True
    ) -> bytes:
        """Generate a PDF report for a team"""
        try:
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            elements = []

            # Title
            title = Paragraph(f"Team Report: {team_id}", self.title_style)
            elements.append(title)
            elements.append(Spacer(1, 20))

            # Metadata
            metadata_text = f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            elements.append(Paragraph(metadata_text, self.styles['Normal']))
            elements.append(Spacer(1, 20))

            # Team statistics
            if include_stats:
                elements.append(Paragraph("Team Statistics", self.heading_style))
                stats_data = [
                    ['Statistic', 'Value'],
                    ['Matches Played', '30'],
                    ['Wins', '18'],
                    ['Draws', '7'],
                    ['Losses', '5'],
                    ['Goals Scored', '56'],
                    ['Goals Conceded', '28'],
                ]
                stats_table = Table(stats_data, colWidths=[3*inch, 3.5*inch])
                stats_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
                ]))
                elements.append(stats_table)

            # Build PDF
            doc.build(elements)
            pdf_content = buffer.getvalue()
            buffer.close()

            return pdf_content

        except Exception as e:
            logger.error(f"Error generating team PDF report: {e}")
            raise

    async def generate_match_report(
        self,
        match_id: str,
        include_events: bool = True,
        include_stats: bool = True
    ) -> bytes:
        """Generate a PDF report for a match"""
        try:
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            elements = []

            # Title
            title = Paragraph(f"Match Report: {match_id}", self.title_style)
            elements.append(title)
            elements.append(Spacer(1, 20))

            # Metadata
            metadata_text = f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            elements.append(Paragraph(metadata_text, self.styles['Normal']))
            elements.append(Spacer(1, 20))

            # Match info
            elements.append(Paragraph("Match Information", self.heading_style))
            match_data = [
                ['Field', 'Value'],
                ['Match ID', match_id],
                ['Date', '2024-03-15'],
                ['Competition', 'Premier League'],
                ['Status', 'Completed'],
            ]
            match_table = Table(match_data, colWidths=[3*inch, 3.5*inch])
            match_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ]))
            elements.append(match_table)

            # Build PDF
            doc.build(elements)
            pdf_content = buffer.getvalue()
            buffer.close()

            return pdf_content

        except Exception as e:
            logger.error(f"Error generating match PDF report: {e}")
            raise
