"""
PDF Report Generator
Uses ReportLab to generate professional scouting-style PDF reports for players, teams, and matches.
"""
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
    HRFlowable, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import io
import httpx
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

import sys
sys.path.append('/app')
from config.settings import get_settings

logger = logging.getLogger(__name__)

# ─── Brand colours ────────────────────────────────────────────────────────────
NAVY     = colors.HexColor('#1a237e')
DARK_BLUE = colors.HexColor('#283593')
MID_BLUE = colors.HexColor('#3949ab')
LIGHT_BLUE = colors.HexColor('#e8eaf6')
DARK_GREY = colors.HexColor('#37474f')
MID_GREY  = colors.HexColor('#607d8b')
LIGHT_GREY = colors.HexColor('#eceff1')
GREEN    = colors.HexColor('#2e7d32')
AMBER    = colors.HexColor('#e65100')
WHITE    = colors.white
BLACK    = colors.black


class PDFGenerator:
    """Generate professional scouting-style PDF reports for players, teams, and matches."""

    def __init__(self):
        self.settings = get_settings()
        self._build_styles()

    def _build_styles(self):
        base = getSampleStyleSheet()

        self.styles = base

        self.cover_title = ParagraphStyle(
            'CoverTitle', parent=base['Normal'],
            fontSize=22, textColor=WHITE, fontName='Helvetica-Bold',
            spaceAfter=4, leading=26, alignment=TA_LEFT
        )
        self.cover_sub = ParagraphStyle(
            'CoverSub', parent=base['Normal'],
            fontSize=12, textColor=colors.HexColor('#b0bec5'), fontName='Helvetica',
            spaceAfter=2, alignment=TA_LEFT
        )
        self.section_heading = ParagraphStyle(
            'SectionHeading', parent=base['Normal'],
            fontSize=13, textColor=NAVY, fontName='Helvetica-Bold',
            spaceBefore=14, spaceAfter=6, leading=16
        )
        self.sub_heading = ParagraphStyle(
            'SubHeading', parent=base['Normal'],
            fontSize=11, textColor=DARK_BLUE, fontName='Helvetica-Bold',
            spaceBefore=8, spaceAfter=4, leading=14
        )
        self.body_text = ParagraphStyle(
            'BodyText2', parent=base['Normal'],
            fontSize=9, textColor=DARK_GREY, fontName='Helvetica',
            spaceAfter=4, leading=13
        )
        self.label_text = ParagraphStyle(
            'LabelText', parent=base['Normal'],
            fontSize=8, textColor=MID_GREY, fontName='Helvetica-Bold',
            spaceAfter=2
        )
        self.footer_text = ParagraphStyle(
            'FooterText', parent=base['Normal'],
            fontSize=8, textColor=MID_GREY, fontName='Helvetica',
            alignment=TA_CENTER
        )
        self.kpi_value = ParagraphStyle(
            'KpiValue', parent=base['Normal'],
            fontSize=20, textColor=NAVY, fontName='Helvetica-Bold',
            alignment=TA_CENTER, spaceAfter=0
        )
        self.kpi_label = ParagraphStyle(
            'KpiLabel', parent=base['Normal'],
            fontSize=8, textColor=MID_GREY, fontName='Helvetica',
            alignment=TA_CENTER
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

    # ─── Data fetching helpers ─────────────────────────────────────────────────

    async def _get_json(self, url: str) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=12.0) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    payload = response.json()
                    if isinstance(payload, dict) and 'data' in payload:
                        return payload['data'] or {}
                    return payload if isinstance(payload, dict) else {}
        except Exception as e:
            logger.warning(f"Fetch failed {url}: {e}")
        return {}

    async def _get_list(self, url: str) -> List[Dict[str, Any]]:
        try:
            async with httpx.AsyncClient(timeout=12.0) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    payload = response.json()
                    if isinstance(payload, dict) and 'data' in payload:
                        d = payload['data']
                        return d if isinstance(d, list) else []
                    return payload if isinstance(payload, list) else []
        except Exception as e:
            logger.warning(f"List fetch failed {url}: {e}")
        return []

    async def fetch_player_data(self, player_id: str) -> Dict[str, Any]:
        data = await self._get_json(f"{self.settings.player_service_url}/api/v2/players/{player_id}")
        return data or {"player_id": player_id, "name": "Unknown Player"}

    async def fetch_player_stats(self, player_id: str) -> Dict[str, Any]:
        data = await self._get_json(
            f"{self.settings.statistics_service_url}/api/v2/statistics/player/{player_id}"
        )
        if isinstance(data, dict) and 'stats' in data:
            return data['stats']
        return data or {}

    async def fetch_player_matches(self, player_id: str) -> List[Dict[str, Any]]:
        return await self._get_list(
            f"{self.settings.player_service_url}/api/v2/players/{player_id}/matches"
        )

    async def fetch_player_events(self, player_id: str, limit: int = 200) -> List[Dict[str, Any]]:
        return await self._get_list(
            f"{self.settings.player_service_url}/api/v2/players/{player_id}/events?limit={limit}"
        )

    async def fetch_team_data(self, team_id: str) -> Dict[str, Any]:
        data = await self._get_json(f"{self.settings.team_service_url}/api/v2/teams/{team_id}")
        return data or {"team_id": team_id, "name": "Unknown Team"}

    async def fetch_team_stats(self, team_id: str) -> Dict[str, Any]:
        data = await self._get_json(
            f"{self.settings.statistics_service_url}/api/v2/statistics/team/{team_id}"
        )
        if isinstance(data, dict) and 'stats' in data:
            return data['stats']
        return data or {}

    async def fetch_team_players(self, team_id: str) -> List[Dict[str, Any]]:
        return await self._get_list(
            f"{self.settings.player_service_url}/api/v2/players?club={team_id}&limit=50"
        )

    async def fetch_match_data(self, match_id: str) -> Dict[str, Any]:
        data = await self._get_json(f"{self.settings.match_service_url}/api/v2/matches/{match_id}")
        return data or {"match_id": match_id}

    async def fetch_match_events(self, match_id: str) -> List[Dict[str, Any]]:
        return await self._get_list(
            f"{self.settings.match_service_url}/api/v2/matches/{match_id}/events?limit=500"
        )

    async def fetch_match_stats(self, match_id: str) -> Dict[str, Any]:
        return await self._get_json(
            f"{self.settings.statistics_service_url}/api/v2/statistics/match/{match_id}"
        )

    # ─── Formatting helpers ────────────────────────────────────────────────────

    @staticmethod
    def _safe(val, fallback: str = 'N/A') -> str:
        if val is None or val == '':
            return fallback
        return str(val)

    @staticmethod
    def _fmt_float(val, decimals: int = 1, fallback: str = 'N/A') -> str:
        if val is None:
            return fallback
        try:
            return f"{float(val):.{decimals}f}"
        except (TypeError, ValueError):
            return str(val)

    @staticmethod
    def _pct(numerator, denominator, fallback: str = 'N/A') -> str:
        try:
            n, d = float(numerator), float(denominator)
            if d == 0:
                return fallback
            return f"{n / d * 100:.1f}%"
        except (TypeError, ValueError):
            return fallback

    def _table_style(self, header_color: str = '#1a237e') -> TableStyle:
        return TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(header_color)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdbdbd')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, LIGHT_GREY]),
        ])

    def _two_col_style(self) -> TableStyle:
        return TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), LIGHT_BLUE),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdbdbd')),
        ])

    def _section_divider(self, title: str) -> list:
        """Returns a list of flowables forming a coloured section header."""
        return [
            Spacer(1, 8),
            HRFlowable(width="100%", thickness=2, color=NAVY, spaceAfter=4),
            Paragraph(title, self.section_heading),
        ]

    def _cover_banner(self, title: str, subtitle: str, tag: str = '') -> list:
        """Dark navy banner used as the cover / title area."""
        data = [[
            Paragraph(title, self.cover_title),
            Paragraph(subtitle, self.cover_sub),
        ]]
        t = Table(data, colWidths=[5.5 * inch, 2.0 * inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), NAVY),
            ('TEXTCOLOR', (0, 0), (-1, -1), WHITE),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
            ('TOPPADDING', (0, 0), (-1, -1), 18),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 18),
            ('LEFTPADDING', (0, 0), (-1, -1), 14),
            ('RIGHTPADDING', (0, 0), (-1, -1), 14),
            ('ROUNDEDCORNERS', [4, 4, 4, 4]),
        ]))
        return [t, Spacer(1, 16)]

    def _kpi_row(self, items: List[tuple]) -> Table:
        """Render a row of KPI boxes: [(label, value), ...]"""
        col_w = (7.5 * inch) / len(items)
        data = [[Paragraph(str(v), self.kpi_value) for _, v in items],
                [Paragraph(str(l), self.kpi_label) for l, _ in items]]
        t = Table(data, colWidths=[col_w] * len(items))
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BLUE),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('BOX', (0, 0), (-1, -1), 1, DARK_BLUE),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, DARK_BLUE),
        ]))
        return t

    def _analysis_paragraph(self, text: str) -> Paragraph:
        return Paragraph(text, self.body_text)

    def _footer(self) -> list:
        return [
            Spacer(1, 20),
            HRFlowable(width="100%", thickness=0.5, color=MID_GREY, spaceAfter=4),
            Paragraph(
                f"Confidential — Generated by ScoutPro Intelligence Platform · {datetime.now().strftime('%d %B %Y')}",
                self.footer_text
            ),
        ]

    def _build_pdf(self, elements) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=A4,
            rightMargin=0.75 * inch, leftMargin=0.75 * inch,
            topMargin=0.75 * inch, bottomMargin=0.5 * inch
        )
        doc.build(elements)
        content = buffer.getvalue()
        buffer.close()
        return content

    # ─── Stat-derived narrative helpers ───────────────────────────────────────

    @staticmethod
    def _player_attacking_profile(stats: Dict[str, Any], sb: Dict[str, Any]) -> str:
        goals = stats.get('goals') or sb.get('goals') or 0
        assists = stats.get('goal_assist') or stats.get('assists') or 0
        shots = stats.get('total_scoring_att') or stats.get('total_shots') or sb.get('shots') or 0
        sot = stats.get('ontarget_scoring_att') or stats.get('shots_on_target') or 0
        xg = sb.get('total_xg')
        obv = sb.get('total_obv')

        lines = []
        if goals:
            conv = PDFGenerator._pct(goals, shots) if shots else 'N/A'
            lines.append(
                f"The player has recorded <b>{goals} goal(s)</b> with a conversion rate of {conv}, "
                f"demonstrating {'clinical' if conv != 'N/A' and float(conv.rstrip('%')) > 20 else 'developing'} finishing."
            )
        if shots and sot:
            sot_pct = PDFGenerator._pct(sot, shots)
            lines.append(
                f"Of {shots} shot attempts, {sot} were on target ({sot_pct}), "
                f"indicating {'accurate' if sot_pct != 'N/A' and float(sot_pct.rstrip('%')) > 40 else 'improving'} shot placement."
            )
        if xg is not None:
            lines.append(
                f"Expected Goals (xG) of <b>{float(xg):.2f}</b> "
                f"{'exceeds' if goals and float(xg) < float(goals) else 'aligns with'} actual output, "
                f"suggesting {'clinical finishing above expectation' if goals and float(xg) < float(goals) else 'expected goal conversion'}."
            )
        if obv is not None:
            quality = 'positive' if float(obv) > 0 else 'negative'
            lines.append(f"On-Ball Value (OBV) is <b>{float(obv):.3f}</b> — a {quality} net contribution to team goal probability.")
        if assists:
            lines.append(f"<b>{assists} assist(s)</b> highlight a willingness to create for teammates.")
        return ' '.join(lines) if lines else 'Attacking statistics are not available for this period.'

    @staticmethod
    def _player_passing_profile(stats: Dict[str, Any], sb: Dict[str, Any]) -> str:
        total_pass = stats.get('total_pass') or stats.get('passes_total') or sb.get('passes') or 0
        accurate = stats.get('accurate_pass') or stats.get('passes_successful') or 0
        pass_acc = stats.get('pass_accuracy') or stats.get('pass_success_rate')
        if not pass_acc and total_pass:
            try:
                pass_acc = round(float(accurate) / float(total_pass) * 100, 1)
            except Exception:
                pass_acc = None
        long = stats.get('long_passes') or stats.get('total_long_balls') or 0
        through = stats.get('through_ball') or 0
        crosses = stats.get('total_crosses') or 0

        lines = []
        if total_pass:
            acc_str = f"{pass_acc:.1f}%" if pass_acc is not None else 'N/A'
            quality = (
                'elite ball distributor' if pass_acc and float(pass_acc) >= 88
                else 'reliable passer' if pass_acc and float(pass_acc) >= 80
                else 'developing passer'
            )
            lines.append(
                f"The player has attempted <b>{total_pass} passes</b> with an accuracy of <b>{acc_str}</b>, "
                f"profiling as a {quality}."
            )
        if long:
            lines.append(f"<b>{long} long balls</b> indicate an ability to switch play and bypass the press.")
        if through:
            lines.append(f"<b>{through} through ball(s)</b> demonstrate progressive passing intent and vision.")
        if crosses:
            lines.append(f"<b>{crosses} cross(es)</b> from wide positions contribute to chance creation in the final third.")
        sb_passes = sb.get('passes') or 0
        sb_pass_prob = sb.get('avg_pass_success_prob')
        if sb_pass_prob is not None:
            lines.append(
                f"StatsBomb model estimates an average pass success probability of <b>{float(sb_pass_prob):.1%}</b>."
            )
        return ' '.join(lines) if lines else 'Passing statistics are not available for this period.'

    @staticmethod
    def _player_defensive_profile(stats: Dict[str, Any]) -> str:
        tackles = stats.get('total_tackle') or stats.get('total_tackles') or 0
        succ_tackles = stats.get('total_successful_tackles') or 0
        interceptions = stats.get('interception') or stats.get('total_interceptions') or 0
        clearances = stats.get('total_clearance') or stats.get('total_clearances') or 0
        duels_won = stats.get('duel_won') or stats.get('successful_duels') or 0
        duels_total = stats.get('duel_total') or stats.get('total_duels') or 0
        aerial_won = stats.get('aerial_won') or 0
        yellow = stats.get('yellow_card') or 0
        red = stats.get('red_card') or 0

        lines = []
        if tackles:
            t_pct = PDFGenerator._pct(succ_tackles, tackles) if succ_tackles else 'N/A'
            lines.append(
                f"<b>{tackles} tackle(s)</b> attempted "
                f"({'success rate ' + t_pct if t_pct != 'N/A' else ''}) reflect active defensive engagement."
            )
        if interceptions:
            lines.append(f"<b>{interceptions} interception(s)</b> show strong anticipation and positional reading.")
        if clearances:
            lines.append(f"<b>{clearances} clearance(s)</b> confirm a defensive contribution in and around the penalty area.")
        if duels_total:
            d_pct = PDFGenerator._pct(duels_won, duels_total)
            lines.append(f"Ground duel success rate: <b>{d_pct}</b> ({duels_won}/{duels_total} won).")
        if aerial_won:
            lines.append(f"<b>{aerial_won} aerial duel(s) won</b> — relevant for set-piece situations.")
        if yellow or red:
            lines.append(
                f"Disciplinary record: <b>{yellow} yellow card(s)</b>"
                f"{', <b>' + str(red) + ' red card(s)</b>' if red else ''}."
            )
        return ' '.join(lines) if lines else 'Defensive statistics are not available for this period.'

    @staticmethod
    def _player_assessment(player: Dict[str, Any], stats: Dict[str, Any], sb: Dict[str, Any]) -> str:
        position = player.get('position') or 'Unknown'
        name = player.get('name') or 'The player'
        goals = float(stats.get('goals') or sb.get('goals') or 0)
        assists = float(stats.get('goal_assist') or stats.get('assists') or 0)
        pass_acc = stats.get('pass_accuracy') or stats.get('pass_success_rate') or 0
        try:
            pass_acc = float(pass_acc)
        except Exception:
            pass_acc = 0
        tackles = float(stats.get('total_tackle') or stats.get('total_tackles') or 0)
        xg = float(sb.get('total_xg') or 0)
        obv = float(sb.get('total_obv') or 0)

        strengths = []
        concerns = []

        if pass_acc >= 85:
            strengths.append("elite-level passing accuracy")
        elif pass_acc >= 78:
            strengths.append("reliable ball distribution")
        else:
            concerns.append("passing accuracy needs improvement")

        if goals + assists > 5:
            strengths.append(f"strong direct output ({int(goals)}G/{int(assists)}A)")
        if xg > 0 and goals > xg:
            strengths.append("clinical finishing above expected value")
        if tackles > 30:
            strengths.append("proactive defensive work-rate")
        if obv > 0.5:
            strengths.append("positive on-ball value contribution")
        if obv < -0.5:
            concerns.append("negative on-ball value — decision-making under review")

        strengths_text = (
            f"{name} demonstrates notable strengths: {', '.join(strengths)}."
            if strengths else ""
        )
        concerns_text = (
            f" Key areas for development include: {', '.join(concerns)}."
            if concerns else " No significant concerns flagged by the data model."
        )
        closing = (
            f" As a {position}, this player profiles as a "
            f"{'high-impact' if len(strengths) >= 2 else 'developing'} asset "
            f"that warrants {'priority' if len(strengths) >= 3 else 'continued'} monitoring."
        )
        return strengths_text + concerns_text + closing

    @staticmethod
    def _match_narrative(match: Dict[str, Any], events: List[Dict[str, Any]]) -> str:
        home = match.get('home_team_name') or match.get('homeTeamName') or 'Home'
        away = match.get('away_team_name') or match.get('awayTeamName') or 'Away'
        hs = match.get('home_score', match.get('homeScore', 0)) or 0
        aws = match.get('away_score', match.get('awayScore', 0)) or 0
        result = (
            f"{home} won" if hs > aws
            else f"{away} won" if aws > hs
            else "The match ended in a draw"
        )
        goal_events = [e for e in events if (e.get('type_id') or e.get('typeID') or e.get('type_name', '')) in (16, '16', 'Goal')]
        goals_narrative = ""
        if goal_events:
            times = sorted([str(e.get('min') or e.get('minute') or '?') for e in goal_events])
            goals_narrative = f" Goals were recorded in minutes: {', '.join(times)}."
        return (
            f"{result} {hs}–{aws}.{goals_narrative} "
            f"A total of {len(events)} tracked events provide the analytical basis for this report."
        )

    @staticmethod
    def _team_tactical_narrative(team: Dict[str, Any], stats: Dict[str, Any], players: List[Dict[str, Any]]) -> str:
        name = team.get('name') or 'The team'
        pass_acc = stats.get('pass_accuracy') or stats.get('pass_success_rate') or 0
        try:
            pass_acc = float(pass_acc)
        except Exception:
            pass_acc = 0
        goals = stats.get('goals') or 0
        conceded = stats.get('goals_conceded') or 0
        matches = stats.get('matches_played') or stats.get('appearances') or 1
        try:
            gpg = round(float(goals) / float(matches), 2) if matches else 0
            cpg = round(float(conceded) / float(matches), 2) if matches else 0
        except Exception:
            gpg = cpg = 0

        style = (
            "possession-oriented, preferring short pass combinations to advance"
            if pass_acc >= 82
            else "transitional, relying on direct play and quick vertical passes"
            if pass_acc < 75
            else "balanced, combining possession play with direct transition"
        )
        attack_desc = (
            "a high-scoring outfit" if gpg >= 2
            else "a consistent scoring threat" if gpg >= 1.5
            else "a defensively stable unit"
        )
        def_desc = (
            "an extremely solid defensive structure" if cpg < 0.8
            else "a respectable defensive record" if cpg < 1.3
            else "a defensive line requiring attention"
        )
        positions = {}
        for p in players[:20]:
            pos = (p.get('position') or 'Unknown').strip()
            positions.setdefault(pos, []).append(p.get('name') or 'Unknown')
        gk_list = ', '.join(positions.get('Goalkeeper', [])[:2]) or 'N/A'
        def_list = ', '.join(positions.get('Defender', [])[:3]) or 'N/A'
        mid_list = ', '.join(positions.get('Midfielder', [])[:3]) or 'N/A'
        fwd_list = ', '.join(positions.get('Forward', [])[:3]) or 'N/A'

        return (
            f"{name} operates a {style} playing system, scoring {gpg:.2f} goals per match — {attack_desc}. "
            f"Defensively, they concede {cpg:.2f} goals per match, indicative of {def_desc}. "
            f"Key squad members identified: GK: {gk_list} · DEF: {def_list} · MID: {mid_list} · FWD: {fwd_list}."
        )

    # ─── Public report generators ─────────────────────────────────────────────

    async def generate_player_report(
        self,
        player_id: str,
        include_stats: bool = True,
        include_charts: bool = True
    ) -> bytes:
        """Generate a professional player scouting report."""
        player, stats, matches = await _gather(
            self.fetch_player_data(player_id),
            self.fetch_player_stats(player_id) if include_stats else {},
            self.fetch_player_matches(player_id)
        )
        sb: Dict[str, Any] = player.get('statsbomb_enrichment') or player.get('statsbombEnrichment') or {}
        if not isinstance(sb, dict):
            sb = {}

        name  = player.get('name') or 'Unknown Player'
        club  = player.get('club') or player.get('team_name') or player.get('teamName') or 'N/A'
        pos   = player.get('position') or 'N/A'
        nat   = player.get('nationality') or 'N/A'
        age   = self._safe(player.get('age'))
        dob   = player.get('birth_date') or player.get('birthDate') or 'N/A'
        height = self._safe(player.get('height') or player.get('height_cm'))
        weight = self._safe(player.get('weight') or player.get('weight_kg'))
        foot  = player.get('preferred_foot') or player.get('preferredFoot') or player.get('foot') or 'N/A'
        det_pos = player.get('detailed_position') or player.get('detailedPosition') or pos
        shirt = self._safe(player.get('shirt_number') or player.get('shirtNumber'))
        contract = player.get('contract_until') or 'N/A'
        mkt_val = player.get('market_value')
        mkt_str = f"€{int(mkt_val):,}" if mkt_val else 'N/A'

        # ── Core metrics from stats / StatsBomb ────────────────────────────────
        goals   = stats.get('goals') or sb.get('goals') or 0
        assists = stats.get('goal_assist') or stats.get('assists') or 0
        apps    = stats.get('appearances') or stats.get('games_played') or 0
        mins    = stats.get('minutes_played') or 0
        shots   = stats.get('total_scoring_att') or stats.get('total_shots') or sb.get('shots') or 0
        sot     = stats.get('ontarget_scoring_att') or stats.get('shots_on_target') or 0
        total_pass = stats.get('total_pass') or stats.get('passes_total') or sb.get('passes') or 0
        acc_pass   = stats.get('accurate_pass') or stats.get('passes_successful') or 0
        pass_pct   = stats.get('pass_accuracy') or stats.get('pass_success_rate') or ''
        if not pass_pct and total_pass:
            try:
                pass_pct = f"{float(acc_pass) / float(total_pass) * 100:.1f}%"
            except Exception:
                pass_pct = 'N/A'
        else:
            pass_pct = f"{float(pass_pct):.1f}%" if pass_pct else 'N/A'
        tackles = stats.get('total_tackle') or stats.get('total_tackles') or 0
        intercept = stats.get('interception') or stats.get('total_interceptions') or 0
        xg  = sb.get('total_xg')
        obv = sb.get('total_obv')

        elements = []

        # ── Cover banner ───────────────────────────────────────────────────────
        elements += self._cover_banner(
            f"PLAYER SCOUTING REPORT: {name.upper()}",
            f"{club}  ·  {pos}  ·  {nat}",
            "ScoutPro Intelligence"
        )

        # ── KPI row ────────────────────────────────────────────────────────────
        kpi_items = [
            ("Goals", int(goals) if goals else 0),
            ("Assists", int(assists) if assists else 0),
            ("Appearances", int(apps) if apps else 0),
            ("Pass Acc.", pass_pct),
        ]
        if xg is not None:
            kpi_items.append(("xG", self._fmt_float(xg, 2)))
        if obv is not None:
            kpi_items.append(("OBV", self._fmt_float(obv, 3)))
        elements.append(self._kpi_row(kpi_items[:6]))
        elements.append(Spacer(1, 10))

        # ── Section A: Player Profile ──────────────────────────────────────────
        elements += self._section_divider("A. Player Profile")

        profile_data = [
            ["Full Name", name,            "Position", pos],
            ["Detailed Position", det_pos, "Club", club],
            ["Nationality", nat,           "Age", age],
            ["Date of Birth", str(dob),    "Height", height],
            ["Weight", weight,             "Preferred Foot", foot],
            ["Shirt Number", shirt,        "Contract Until", str(contract)],
            ["Market Value", mkt_str,      "Player ID", player_id],
        ]
        col_w = [1.4 * inch, 2.2 * inch, 1.4 * inch, 2.2 * inch]
        t = Table(profile_data, colWidths=col_w)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), LIGHT_BLUE),
            ('BACKGROUND', (2, 0), (2, -1), LIGHT_BLUE),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdbdbd')),
        ]))
        elements.append(t)

        # ── Season Performance ─────────────────────────────────────────────────
        if matches:
            elements += self._section_divider("B. Recent Match Appearances")
            match_rows = [["Date", "Home Team", "Score", "Away Team", "Competition"]]
            for m in matches[:8]:
                hname = m.get('home_team_name') or m.get('homeTeamName') or m.get('home_team_id') or '-'
                aname = m.get('away_team_name') or m.get('awayTeamName') or m.get('away_team_id') or '-'
                hs_v = m.get('home_score', m.get('homeScore', '-'))
                as_v = m.get('away_score', m.get('awayScore', '-'))
                score_str = f"{hs_v} – {as_v}"
                comp = m.get('competition') or m.get('competitionID') or m.get('competition_id') or '-'
                date_str = str(m.get('date') or '-')[:10]
                match_rows.append([date_str, hname, score_str, aname, str(comp)])
            mt = Table(match_rows, colWidths=[1.0 * inch, 2.0 * inch, 0.8 * inch, 2.0 * inch, 1.5 * inch])
            mt.setStyle(self._table_style())
            elements.append(mt)
        else:
            elements += self._section_divider("B. Season Performance")
            perf_rows = [["Season", "League / Division", "Club", "Apps", "Goals", "Assists"]]
            season_apps = stats.get('appearances') or stats.get('games_played') or '-'
            perf_rows.append(['Current', 'N/A', club, str(season_apps), str(goals), str(assists)])
            pt = Table(perf_rows, colWidths=[0.9 * inch, 2.2 * inch, 1.5 * inch, 0.8 * inch, 0.8 * inch, 0.8 * inch])
            pt.setStyle(self._table_style())
            elements.append(pt)

        # ── Section C: Performance Statistics ─────────────────────────────────
        elements += self._section_divider("C. Performance Statistics")

        stat_groups = [
            ("Attacking", [
                ("Goals", str(int(goals) if goals else 0)),
                ("Assists", str(int(assists) if assists else 0)),
                ("Total Shots", str(int(shots) if shots else 0)),
                ("Shots on Target", str(int(sot) if sot else 0)),
                ("Shot Accuracy", self._pct(sot, shots)),
                ("Minutes Played", str(int(mins) if mins else 0)),
            ]),
            ("Passing", [
                ("Total Passes", str(int(total_pass) if total_pass else 0)),
                ("Accurate Passes", str(int(acc_pass) if acc_pass else 0)),
                ("Pass Accuracy", pass_pct),
                ("Long Balls", str(stats.get('long_passes') or stats.get('total_long_balls') or 0)),
                ("Through Balls", str(stats.get('through_ball') or 0)),
                ("Crosses", str(stats.get('total_crosses') or 0)),
            ]),
            ("Defensive", [
                ("Tackles", str(int(tackles) if tackles else 0)),
                ("Interceptions", str(int(intercept) if intercept else 0)),
                ("Clearances", str(stats.get('total_clearance') or stats.get('total_clearances') or 0)),
                ("Ground Duels Won", str(stats.get('duel_won') or stats.get('successful_duels') or 0)),
                ("Aerial Duels Won", str(stats.get('aerial_won') or 0)),
                ("Yellow Cards", str(stats.get('yellow_card') or 0)),
            ]),
        ]

        for group_title, rows in stat_groups:
            elements.append(Paragraph(group_title, self.sub_heading))
            tbl_data = [["Metric", "Value"]] + rows
            tbl = Table(tbl_data, colWidths=[3.5 * inch, 4.0 * inch])
            tbl.setStyle(self._table_style('#283593'))
            elements.append(tbl)
            elements.append(Spacer(1, 6))

        # ── Section D: Advanced Metrics ────────────────────────────────────────
        if sb:
            elements += self._section_divider("D. Advanced Metrics (StatsBomb)")
            adv_rows = [["Metric", "Value", "Interpretation"]]
            if xg is not None:
                interp = "Above average" if float(xg) > 0.3 else "Average" if float(xg) > 0.1 else "Low"
                adv_rows.append(["Total xG", self._fmt_float(xg, 3), interp])
            if obv is not None:
                interp = "Positive net impact" if float(obv) > 0 else "Net negative impact"
                adv_rows.append(["On-Ball Value (OBV)", self._fmt_float(obv, 4), interp])
            sb_passes = sb.get('passes')
            sb_prob = sb.get('avg_pass_success_prob')
            if sb_passes is not None:
                adv_rows.append(["Pass Attempts (SB)", str(int(sb_passes)), "—"])
            if sb_prob is not None:
                adv_rows.append(["Avg Pass Success Prob", f"{float(sb_prob):.1%}", "Model estimated"])
            if len(adv_rows) > 1:
                at = Table(adv_rows, colWidths=[2.5 * inch, 1.5 * inch, 3.5 * inch])
                at.setStyle(self._table_style('#37474f'))
                elements.append(at)

        # ── Section E: Analytical Narrative ───────────────────────────────────
        elements += self._section_divider("E. Analytical Report")

        elements.append(Paragraph("Attacking Profile", self.sub_heading))
        elements.append(self._analysis_paragraph(self._player_attacking_profile(stats, sb)))

        elements.append(Paragraph("Passing & Build-Up", self.sub_heading))
        elements.append(self._analysis_paragraph(self._player_passing_profile(stats, sb)))

        elements.append(Paragraph("Defensive Contribution", self.sub_heading))
        elements.append(self._analysis_paragraph(self._player_defensive_profile(stats)))

        # ── Section F: Assessment ──────────────────────────────────────────────
        elements += self._section_divider("F. Scout Assessment")
        elements.append(self._analysis_paragraph(self._player_assessment(player, stats, sb)))

        elements += self._footer()
        return self._build_pdf(elements)

    async def generate_team_report(
        self,
        team_id: str,
        include_players: bool = True,
        include_stats: bool = True
    ) -> bytes:
        """Generate a professional team tactical report."""
        team, stats, players = await _gather(
            self.fetch_team_data(team_id),
            self.fetch_team_stats(team_id) if include_stats else {},
            self.fetch_team_players(team_id) if include_players else []
        )

        name = team.get('name') or team_id
        country = self._safe(team.get('country'))
        stadium = self._safe(team.get('stadium'))
        manager = self._safe(team.get('manager'))
        founded = self._safe(team.get('founded'))
        capacity = self._safe(team.get('capacity'))

        goals = stats.get('goals') or 0
        conceded = stats.get('goals_conceded') or 0
        wins = stats.get('wins') or 0
        draws = stats.get('draws') or 0
        losses = stats.get('losses') or 0
        matches = stats.get('matches_played') or (int(wins) + int(draws) + int(losses)) or 1
        pass_acc = stats.get('pass_accuracy') or stats.get('pass_success_rate') or 'N/A'
        clean_sheets = stats.get('clean_sheets') or 0

        elements = []
        elements += self._cover_banner(
            f"TEAM TACTICAL REPORT: {name.upper()}",
            f"{country}  ·  {stadium}",
        )

        kpi_items = [
            ("Goals Scored", int(goals) if goals else 0),
            ("Goals Conceded", int(conceded) if conceded else 0),
            ("Wins", int(wins) if wins else 0),
            ("Draws", int(draws) if draws else 0),
            ("Losses", int(losses) if losses else 0),
            ("Clean Sheets", int(clean_sheets) if clean_sheets else 0),
        ]
        elements.append(self._kpi_row(kpi_items))
        elements.append(Spacer(1, 10))

        # ── A: Club Information ────────────────────────────────────────────────
        elements += self._section_divider("A. Club Information")
        info_data = [
            ["Club Name", name,       "Country", country],
            ["Stadium", stadium,      "Capacity", capacity],
            ["Manager", manager,      "Founded", founded],
            ["Team ID", team_id,      "Matches Played", str(matches)],
        ]
        t = Table(info_data, colWidths=[1.4 * inch, 2.2 * inch, 1.4 * inch, 2.2 * inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), LIGHT_BLUE),
            ('BACKGROUND', (2, 0), (2, -1), LIGHT_BLUE),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdbdbd')),
        ]))
        elements.append(t)

        # ── B: Team Statistics ─────────────────────────────────────────────────
        elements += self._section_divider("B. Team Statistics")
        stat_groups = [
            ("Results Summary", [
                ("Matches Played", str(int(matches))),
                ("Wins", str(int(wins) if wins else 0)),
                ("Draws", str(int(draws) if draws else 0)),
                ("Losses", str(int(losses) if losses else 0)),
                ("Clean Sheets", str(int(clean_sheets) if clean_sheets else 0)),
            ]),
            ("Attacking", [
                ("Goals Scored", str(int(goals) if goals else 0)),
                ("Goals per Match", self._fmt_float(float(goals) / float(matches) if matches else 0)),
                ("Total Shots", str(stats.get('total_shots') or stats.get('total_scoring_att') or 'N/A')),
                ("Shots on Target", str(stats.get('shots_on_target') or stats.get('ontarget_scoring_att') or 'N/A')),
            ]),
            ("Defending", [
                ("Goals Conceded", str(int(conceded) if conceded else 0)),
                ("Goals Conceded per Match", self._fmt_float(float(conceded) / float(matches) if matches else 0)),
                ("Clean Sheets", str(int(clean_sheets) if clean_sheets else 0)),
            ]),
            ("Passing", [
                ("Pass Accuracy", f"{float(pass_acc):.1f}%" if pass_acc not in ('N/A', None, '') else 'N/A'),
                ("Total Passes", str(stats.get('total_pass') or 'N/A')),
            ]),
        ]
        for group_title, rows in stat_groups:
            elements.append(Paragraph(group_title, self.sub_heading))
            tbl_data = [["Metric", "Value"]] + rows
            tbl = Table(tbl_data, colWidths=[3.5 * inch, 4.0 * inch])
            tbl.setStyle(self._table_style('#283593'))
            elements.append(tbl)
            elements.append(Spacer(1, 6))

        # ── C: Squad Overview ──────────────────────────────────────────────────
        if players:
            elements += self._section_divider("C. Squad Overview")
            squad_rows = [["Name", "Position", "Nationality", "Age"]]
            for p in sorted(players, key=lambda x: x.get('position') or '')[:25]:
                squad_rows.append([
                    p.get('name') or 'N/A',
                    p.get('position') or 'N/A',
                    p.get('nationality') or 'N/A',
                    str(p.get('age') or 'N/A'),
                ])
            st = Table(squad_rows, colWidths=[2.5 * inch, 1.5 * inch, 2.0 * inch, 1.5 * inch])
            st.setStyle(self._table_style())
            elements.append(st)

        # ── D: Tactical Narrative ──────────────────────────────────────────────
        elements += self._section_divider("D. Tactical Analysis")
        elements.append(self._analysis_paragraph(
            self._team_tactical_narrative(team, stats, players)
        ))

        elements += self._footer()
        return self._build_pdf(elements)

    async def generate_match_report(
        self,
        match_id: str,
        include_events: bool = True,
        include_stats: bool = True
    ) -> bytes:
        """Generate a detailed match analysis report."""
        match, events, match_stats = await _gather(
            self.fetch_match_data(match_id),
            self.fetch_match_events(match_id) if include_events else [],
            self.fetch_match_stats(match_id) if include_stats else {}
        )

        home = match.get('home_team_name') or match.get('homeTeamName') or 'Home'
        away = match.get('away_team_name') or match.get('awayTeamName') or 'Away'
        hs = match.get('home_score', match.get('homeScore', 0)) or 0
        aws = match.get('away_score', match.get('awayScore', 0)) or 0
        comp = match.get('competition') or match.get('competitionID') or match.get('competition_id') or 'N/A'
        date_str = str(match.get('date') or 'N/A')[:10]
        venue = match.get('venue') or 'N/A'
        status = match.get('status') or 'N/A'
        match_day = match.get('match_day') or match.get('matchDay') or 'N/A'

        elements = []
        elements += self._cover_banner(
            f"MATCH ANALYSIS REPORT",
            f"{home.upper()} vs {away.upper()}",
        )

        # ── Score banner ───────────────────────────────────────────────────────
        score_data = [
            [
                Paragraph(home, self.cover_sub),
                Paragraph(f"{hs}  —  {aws}", ParagraphStyle(
                    'Score', parent=self.styles['Normal'],
                    fontSize=28, textColor=WHITE, fontName='Helvetica-Bold', alignment=TA_CENTER
                )),
                Paragraph(away, self.cover_sub),
            ]
        ]
        score_tbl = Table(score_data, colWidths=[2.5 * inch, 2.5 * inch, 2.5 * inch])
        score_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), DARK_BLUE),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 14),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 14),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ]))
        elements.append(score_tbl)
        elements.append(Spacer(1, 12))

        # ── A: Match Overview ──────────────────────────────────────────────────
        elements += self._section_divider("A. Match Overview")
        overview_data = [
            ["Date", date_str,       "Competition", str(comp)],
            ["Venue", venue,         "Match Day", str(match_day)],
            ["Status", status,       "Match ID", match_id],
        ]
        t = Table(overview_data, colWidths=[1.0 * inch, 2.6 * inch, 1.2 * inch, 2.6 * inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), LIGHT_BLUE),
            ('BACKGROUND', (2, 0), (2, -1), LIGHT_BLUE),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdbdbd')),
        ]))
        elements.append(t)

        # ── B: Team Statistics Comparison ─────────────────────────────────────
        if match_stats:
            elements += self._section_divider("B. Team Statistics Comparison")
            home_s = match_stats.get('home_team') or match_stats.get('home') or {}
            away_s = match_stats.get('away_team') or match_stats.get('away') or {}
            if not (home_s or away_s):
                home_s = {k: v for k, v in match_stats.items() if 'home' in k.lower()}
                away_s = {k: v for k, v in match_stats.items() if 'away' in k.lower()}

            comparison_metrics = [
                ('Goals', 'goals'),
                ('Shots Total', 'total_shots'),
                ('Shots on Target', 'shots_on_target'),
                ('Pass Accuracy (%)', 'pass_accuracy'),
                ('Total Passes', 'total_pass'),
                ('Tackles', 'total_tackles'),
                ('Corners', 'corners'),
                ('Yellow Cards', 'yellow_cards'),
                ('Red Cards', 'red_cards'),
            ]
            comp_rows = [["Metric", home, away]]
            for label, key in comparison_metrics:
                hv = home_s.get(key, '—')
                av = away_s.get(key, '—')
                if hv != '—' or av != '—':
                    comp_rows.append([label, str(hv), str(av)])
            if len(comp_rows) > 1:
                ct = Table(comp_rows, colWidths=[3.0 * inch, 2.25 * inch, 2.25 * inch])
                ct.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), NAVY),
                    ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, LIGHT_GREY]),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdbdbd')),
                    ('TOPPADDING', (0, 0), (-1, -1), 5),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ]))
                elements.append(ct)

        # ── C: Key Events ──────────────────────────────────────────────────────
        if events:
            elements += self._section_divider("C. Key Match Events")

            # Goals
            goal_evts = [
                e for e in events
                if str(e.get('type_id') or e.get('typeID') or '') in ('16', '15')
                or str(e.get('type_name') or '').lower() in ('goal', 'attempt saved')
            ]
            # Cards
            card_evts = [
                e for e in events
                if str(e.get('type_id') or e.get('typeID') or '') in ('17', '19')
                or str(e.get('type_name') or '').lower() in ('yellow card', 'red card', 'card')
            ]

            if goal_evts:
                elements.append(Paragraph("Goals & Decisive Moments", self.sub_heading))
                goal_rows = [["Minute", "Team", "Player", "Event Type", "Outcome"]]
                for e in sorted(goal_evts, key=lambda x: int(x.get('min') or x.get('minute') or 0))[:20]:
                    tid = str(e.get('team_id') or e.get('teamID') or '-')
                    team_str = home if tid == str(match.get('home_team_id') or match.get('homeTeamID') or '') else away
                    goal_rows.append([
                        str(e.get('min') or e.get('minute') or '—'),
                        team_str,
                        str(e.get('player_name') or e.get('playerName') or e.get('player_id') or '—'),
                        str(e.get('type_name') or e.get('type_id') or '—'),
                        str(e.get('outcome') or '—'),
                    ])
                gt = Table(goal_rows, colWidths=[0.6 * inch, 1.5 * inch, 2.2 * inch, 1.6 * inch, 1.5 * inch])
                gt.setStyle(self._table_style('#2e7d32'))
                elements.append(gt)
                elements.append(Spacer(1, 6))

            if card_evts:
                elements.append(Paragraph("Disciplinary Events", self.sub_heading))
                card_rows = [["Minute", "Team", "Player", "Card Type"]]
                for e in sorted(card_evts, key=lambda x: int(x.get('min') or x.get('minute') or 0)):
                    tid = str(e.get('team_id') or e.get('teamID') or '-')
                    team_str = home if tid == str(match.get('home_team_id') or match.get('homeTeamID') or '') else away
                    card_rows.append([
                        str(e.get('min') or e.get('minute') or '—'),
                        team_str,
                        str(e.get('player_name') or e.get('playerName') or e.get('player_id') or '—'),
                        str(e.get('type_name') or ('Yellow Card' if str(e.get('type_id') or '') == '17' else 'Red Card')),
                    ])
                card_t = Table(card_rows, colWidths=[0.6 * inch, 1.8 * inch, 3.0 * inch, 2.0 * inch])
                card_t.setStyle(self._table_style('#e65100'))
                elements.append(card_t)
                elements.append(Spacer(1, 6))

            # Event type summary
            elements += self._section_divider("D. Event Summary by Type")
            type_counts: Dict[str, int] = {}
            for e in events:
                etype = str(e.get('type_name') or e.get('type_id') or 'Unknown')
                type_counts[etype] = type_counts.get(etype, 0) + 1
            top_types = sorted(type_counts.items(), key=lambda x: -x[1])[:20]
            evt_rows = [["Event Type", "Count"]]
            for et, cnt in top_types:
                evt_rows.append([et, str(cnt)])
            et_table = Table(evt_rows, colWidths=[5.0 * inch, 2.5 * inch])
            et_table.setStyle(self._table_style())
            elements.append(et_table)

        # ── E: Match Narrative ─────────────────────────────────────────────────
        elements += self._section_divider("E. Match Analysis")
        elements.append(self._analysis_paragraph(self._match_narrative(match, events)))
        if events:
            players_involved = len({
                e.get('player_id') or e.get('playerID') or e.get('player_name')
                for e in events
                if (e.get('player_id') or e.get('playerID') or e.get('player_name'))
            })
            if players_involved:
                elements.append(self._analysis_paragraph(
                    f"<b>{players_involved} distinct players</b> were involved in tracked events, "
                    f"providing a comprehensive view of both squads' participation."
                ))

        elements += self._footer()
        return self._build_pdf(elements)


# ─── async helper ──────────────────────────────────────────────────────────────

import asyncio

async def _gather(*coros):
    """Run multiple coroutines concurrently and return their results."""
    return await asyncio.gather(*coros)
