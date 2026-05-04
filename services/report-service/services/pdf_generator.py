"""
PDF Report Generator
Uses ReportLab to generate PDF reports
"""
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
import io
import httpx
import logging
from datetime import datetime
from typing import Optional, Dict, Any

import sys
sys.path.append('/app')
from config.settings import get_settings

logger = logging.getLogger(__name__)


class PDFGenerator:
    """Generate PDF reports for players, teams, and matches"""

    def __init__(self):
        self.settings = get_settings()
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

    async def _get_json(self, url: str) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    payload = response.json()
                    if isinstance(payload, dict) and 'data' in payload:
                        return payload['data'] or {}
                    return payload if isinstance(payload, dict) else {}
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
        return {}

    async def fetch_player_data(self, player_id: str) -> Dict[str, Any]:
        data = await self._get_json(f"{self.settings.player_service_url}/api/v2/players/{player_id}")
        return data or {"player_id": player_id, "name": "Unknown Player"}

    async def fetch_player_stats(self, player_id: str) -> Dict[str, Any]:
        data = await self._get_json(f"{self.settings.statistics_service_url}/api/v2/statistics/player/{player_id}")
        if isinstance(data, dict) and 'stats' in data:
            return data['stats']
        return data or {}

    async def fetch_team_data(self, team_id: str) -> Dict[str, Any]:
        data = await self._get_json(f"{self.settings.team_service_url}/api/v2/teams/{team_id}")
        return data or {"team_id": team_id, "name": "Unknown Team"}

    async def fetch_team_stats(self, team_id: str) -> Dict[str, Any]:
        data = await self._get_json(f"{self.settings.statistics_service_url}/api/v2/statistics/team/{team_id}")
        if isinstance(data, dict) and 'stats' in data:
            return data['stats']
        return data or {}

    async def fetch_match_data(self, match_id: str) -> Dict[str, Any]:
        data = await self._get_json(f"{self.settings.match_service_url}/api/v2/matches/{match_id}")
        return data or {"match_id": match_id}

    def _table_style(self, header_color: str = '#1a237e') -> TableStyle:
        return TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(header_color)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ])

    def _build_pdf(self, elements) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        doc.build(elements)
        content = buffer.getvalue()
        buffer.close()
        return content

    async def generate_player_report(self, player_id: str, include_stats: bool = True, include_charts: bool = True) -> bytes:
        player = await self.fetch_player_data(player_id)
        stats = await self.fetch_player_stats(player_id) if include_stats else {}

        elements = []
        elements.append(Paragraph(f"Player Report: {player.get('name', 'Unknown')}", self.title_style))
        elements.append(Spacer(1, 12))

        meta = (
            f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}<br/>"
            f"<b>Player ID:</b> {player_id}<br/>"
            f"<b>Position:</b> {player.get('position') or 'N/A'}<br/>"
            f"<b>Team:</b> {player.get('club') or player.get('team_name') or player.get('teamName') or 'N/A'}<br/>"
            f"<b>Nationality:</b> {player.get('nationality') or 'N/A'}<br/>"
            f"<b>Age:</b> {player.get('age') or 'N/A'}"
        )
        elements.append(Paragraph(meta, self.styles['Normal']))
        elements.append(Spacer(1, 20))

        elements.append(Paragraph("Player Information", self.heading_style))
        info_rows = [
            ['Field', 'Value'],
            ['Name', str(player.get('name') or 'N/A')],
            ['Position', str(player.get('position') or 'N/A')],
            ['Detailed Position', str(player.get('detailed_position') or player.get('detailedPosition') or 'N/A')],
            ['Team', str(player.get('club') or player.get('team_name') or player.get('teamName') or 'N/A')],
            ['Nationality', str(player.get('nationality') or 'N/A')],
            ['Age', str(player.get('age') or 'N/A')],
            ['Height', str(player.get('height') or 'N/A')],
            ['Weight', str(player.get('weight') or 'N/A')],
            ['Preferred Foot', str(player.get('preferred_foot') or player.get('preferredFoot') or 'N/A')],
            ['Player ID', player_id],
        ]
        t = Table(info_rows, colWidths=[2.5 * inch, 4 * inch])
        t.setStyle(self._table_style('#616161'))
        elements.append(t)
        elements.append(Spacer(1, 20))

        if include_stats and stats:
            elements.append(Paragraph("Season Statistics", self.heading_style))
            stat_labels = {
                'goals': 'Goals', 'goal_assist': 'Assists', 'assists': 'Assists',
                'appearances': 'Appearances', 'games_played': 'Appearances',
                'minutes_played': 'Minutes Played', 'total_pass': 'Total Passes',
                'accurate_pass': 'Accurate Passes', 'pass_accuracy': 'Pass Accuracy (%)',
                'total_scoring_att': 'Total Shots', 'ontarget_scoring_att': 'Shots on Target',
                'yellow_card': 'Yellow Cards', 'red_card': 'Red Cards',
                'total_tackle': 'Tackles', 'interception': 'Interceptions',
            }
            stat_rows = [['Statistic', 'Value']]
            for key, label in stat_labels.items():
                val = stats.get(key)
                if val is not None:
                    stat_rows.append([label, str(val)])
            if len(stat_rows) > 1:
                t2 = Table(stat_rows, colWidths=[3 * inch, 3.5 * inch])
                t2.setStyle(self._table_style())
                elements.append(t2)
                elements.append(Spacer(1, 20))

        if include_stats and isinstance(player.get('statsbomb_enrichment') or player.get('statsbombEnrichment'), dict):
            sb = player.get('statsbomb_enrichment') or player.get('statsbombEnrichment')
            elements.append(Paragraph("Advanced Metrics (StatsBomb)", self.heading_style))
            adv_rows = [['Metric', 'Value']]
            for key, label in [('total_xg', 'Total xG'), ('total_obv', 'Total OBV'),
                                ('passes', 'Passes'), ('shots', 'Shots'), ('goals', 'Goals'),
                                ('avg_pass_success_prob', 'Avg Pass Success %')]:
                val = sb.get(key)
                if val is not None:
                    adv_rows.append([label, str(round(val, 3) if isinstance(val, float) else val)])
            if len(adv_rows) > 1:
                t3 = Table(adv_rows, colWidths=[3 * inch, 3.5 * inch])
                t3.setStyle(self._table_style('#37474f'))
                elements.append(t3)
                elements.append(Spacer(1, 20))

        elements.append(Spacer(1, 30))
        elements.append(Paragraph(f"<i>Generated by ScoutPro Report Service - {datetime.now().year}</i>", self.styles['Normal']))

        return self._build_pdf(elements)

    async def generate_team_report(self, team_id: str, include_players: bool = True, include_stats: bool = True) -> bytes:
        team = await self.fetch_team_data(team_id)
        stats = await self.fetch_team_stats(team_id) if include_stats else {}

        elements = []
        elements.append(Paragraph(f"Team Report: {team.get('name', team_id)}", self.title_style))
        elements.append(Spacer(1, 20))

        meta = (
            f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}<br/>"
            f"<b>Team ID:</b> {team_id}<br/>"
            f"<b>Country:</b> {team.get('country') or 'N/A'}<br/>"
            f"<b>Stadium:</b> {team.get('stadium') or 'N/A'}"
        )
        elements.append(Paragraph(meta, self.styles['Normal']))
        elements.append(Spacer(1, 20))

        elements.append(Paragraph("Team Information", self.heading_style))
        info_rows = [
            ['Field', 'Value'],
            ['Name', str(team.get('name') or 'N/A')],
            ['Short Name', str(team.get('short_name') or team.get('shortName') or 'N/A')],
            ['Country', str(team.get('country') or 'N/A')],
            ['Stadium', str(team.get('stadium') or 'N/A')],
            ['Manager', str(team.get('manager') or 'N/A')],
            ['Founded', str(team.get('founded') or 'N/A')],
        ]
        t = Table(info_rows, colWidths=[2.5 * inch, 4 * inch])
        t.setStyle(self._table_style('#616161'))
        elements.append(t)
        elements.append(Spacer(1, 20))

        if include_stats and stats:
            elements.append(Paragraph("Team Statistics", self.heading_style))
            stat_labels = {
                'goals': 'Goals Scored', 'goals_conceded': 'Goals Conceded',
                'wins': 'Wins', 'draws': 'Draws', 'losses': 'Losses',
                'matches_played': 'Matches Played', 'pass_accuracy': 'Pass Accuracy (%)',
                'total_pass': 'Total Passes', 'clean_sheets': 'Clean Sheets',
            }
            stat_rows = [['Statistic', 'Value']]
            for key, label in stat_labels.items():
                val = stats.get(key)
                if val is not None:
                    stat_rows.append([label, str(val)])
            if len(stat_rows) > 1:
                t2 = Table(stat_rows, colWidths=[3 * inch, 3.5 * inch])
                t2.setStyle(self._table_style())
                elements.append(t2)

        elements.append(Spacer(1, 30))
        elements.append(Paragraph(f"<i>Generated by ScoutPro Report Service - {datetime.now().year}</i>", self.styles['Normal']))

        return self._build_pdf(elements)

    async def generate_match_report(self, match_id: str, include_events: bool = True, include_stats: bool = True) -> bytes:
        match = await self.fetch_match_data(match_id)

        elements = []
        home = match.get('home_team_name') or match.get('homeTeamName') or match.get('home_team_id') or 'Home'
        away = match.get('away_team_name') or match.get('awayTeamName') or match.get('away_team_id') or 'Away'
        elements.append(Paragraph(f"Match Report: {home} vs {away}", self.title_style))
        elements.append(Spacer(1, 20))

        meta = f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        elements.append(Paragraph(meta, self.styles['Normal']))
        elements.append(Spacer(1, 20))

        elements.append(Paragraph("Match Information", self.heading_style))
        home_score = match.get('home_score', match.get('homeScore', 'N/A'))
        away_score = match.get('away_score', match.get('awayScore', 'N/A'))
        score = f"{home_score} - {away_score}" if home_score != 'N/A' else 'N/A'
        match_rows = [
            ['Field', 'Value'],
            ['Match ID', str(match_id)],
            ['Home Team', str(home)],
            ['Away Team', str(away)],
            ['Score', str(score)],
            ['Date', str(match.get('date') or 'N/A')],
            ['Competition', str(match.get('competition') or match.get('competitionID') or 'N/A')],
            ['Venue', str(match.get('venue') or 'N/A')],
            ['Status', str(match.get('status') or 'N/A')],
        ]
        t = Table(match_rows, colWidths=[3 * inch, 3.5 * inch])
        t.setStyle(self._table_style('#616161'))
        elements.append(t)
        elements.append(Spacer(1, 30))
        elements.append(Paragraph(f"<i>Generated by ScoutPro Report Service - {datetime.now().year}</i>", self.styles['Normal']))

        return self._build_pdf(elements)
