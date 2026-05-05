"""
Report Service API Endpoints
Generates PDF and Excel reports for players, teams, and matches
"""
from fastapi import APIRouter, HTTPException, Query, Path, BackgroundTasks
from fastapi.responses import StreamingResponse, FileResponse
from typing import Optional, List
from pydantic import BaseModel
from enum import Enum
import sys
import logging
import io

sys.path.append('/app')

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v2/reports", tags=["reports"])


class ReportFormat(str, Enum):
    PDF = "pdf"
    EXCEL = "excel"
    HTML = "html"


class ReportType(str, Enum):
    PLAYER = "player"
    TEAM = "team"
    MATCH = "match"
    COMPARISON = "comparison"
    SCOUTING = "scouting"


class ReportRequest(BaseModel):
    report_type: ReportType
    format: ReportFormat
    entity_ids: List[str]  # Player IDs, Team IDs, or Match IDs
    include_stats: bool = True
    include_charts: bool = True
    season: Optional[str] = None
    competition: Optional[str] = None


class ReportStatus(BaseModel):
    report_id: str
    status: str  # "pending", "processing", "completed", "failed"
    download_url: Optional[str] = None
    created_at: str
    expires_at: Optional[str] = None


# ============ Report Generation Endpoints ============

@router.post("/generate", summary="Generate a new report")
async def generate_report(
    request: ReportRequest,
    background_tasks: BackgroundTasks
):
    """
    Generate a new report (async)

    Returns a report_id that can be used to check status and download
    """
    try:
        # Import here to avoid circular imports
        from services.report_generator import ReportGenerator

        generator = ReportGenerator()
        report_id = await generator.create_report_job(request)

        # Process report in background
        background_tasks.add_task(
            generator.process_report,
            report_id,
            request
        )

        return {
            "report_id": report_id,
            "status": "pending",
            "message": "Report generation started",
            "status_url": f"/api/v2/reports/{report_id}/status"
        }

    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{report_id}/status", summary="Check report generation status")
async def get_report_status(
    report_id: str = Path(..., description="Report ID")
) -> ReportStatus:
    """
    Check the status of a report generation job
    """
    try:
        from services.report_generator import ReportGenerator

        generator = ReportGenerator()
        status = await generator.get_report_status(report_id)

        if not status:
            raise HTTPException(status_code=404, detail="Report not found")

        return status

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking report status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{report_id}/download", summary="Download generated report")
async def download_report(
    report_id: str = Path(..., description="Report ID")
):
    """
    Download a generated report
    """
    try:
        from services.report_generator import ReportGenerator

        generator = ReportGenerator()
        report_data = await generator.download_report(report_id)

        if not report_data:
            raise HTTPException(status_code=404, detail="Report not found or expired")

        return StreamingResponse(
            io.BytesIO(report_data['content']),
            media_type=report_data['content_type'],
            headers={
                "Content-Disposition": f"attachment; filename={report_data['filename']}"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ Quick Report Endpoints (Synchronous) ============

@router.get("/player/{player_id}", summary="Generate player report (quick)")
async def generate_player_report(
    player_id: str = Path(..., description="Player ID"),
    format: ReportFormat = Query(ReportFormat.PDF, description="Report format"),
    include_stats: bool = Query(True, description="Include statistics"),
    include_charts: bool = Query(True, description="Include charts")
):
    """
    Generate and immediately return a player report (synchronous)

    For quick reports without background processing
    """
    try:
        from services.pdf_generator import PDFGenerator
        from services.excel_generator import ExcelGenerator

        if format == ReportFormat.PDF:
            generator = PDFGenerator()
            content = await generator.generate_player_report(
                player_id,
                include_stats=include_stats,
                include_charts=include_charts
            )
            media_type = "application/pdf"
            filename = f"player_{player_id}_report.pdf"
        else:
            generator = ExcelGenerator()
            content = await generator.generate_player_report(
                player_id,
                include_stats=include_stats
            )
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            filename = f"player_{player_id}_report.xlsx"

        return StreamingResponse(
            io.BytesIO(content),
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except Exception as e:
        logger.error(f"Error generating player report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/team/{team_id}", summary="Generate team report (quick)")
async def generate_team_report(
    team_id: str = Path(..., description="Team ID"),
    format: ReportFormat = Query(ReportFormat.PDF, description="Report format"),
    include_players: bool = Query(True, description="Include player list"),
    include_stats: bool = Query(True, description="Include statistics")
):
    """
    Generate and immediately return a team report (synchronous)
    """
    try:
        from services.pdf_generator import PDFGenerator
        from services.excel_generator import ExcelGenerator

        if format == ReportFormat.PDF:
            generator = PDFGenerator()
            content = await generator.generate_team_report(
                team_id,
                include_players=include_players,
                include_stats=include_stats
            )
            media_type = "application/pdf"
            filename = f"team_{team_id}_report.pdf"
        else:
            generator = ExcelGenerator()
            content = await generator.generate_team_report(
                team_id,
                include_players=include_players,
                include_stats=include_stats
            )
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            filename = f"team_{team_id}_report.xlsx"

        return StreamingResponse(
            io.BytesIO(content),
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except Exception as e:
        logger.error(f"Error generating team report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/match/{match_id}", summary="Generate match report (quick)")
async def generate_match_report(
    match_id: str = Path(..., description="Match ID"),
    format: ReportFormat = Query(ReportFormat.PDF, description="Report format"),
    include_events: bool = Query(True, description="Include match events"),
    include_stats: bool = Query(True, description="Include statistics")
):
    """
    Generate and immediately return a match report (synchronous)
    """
    try:
        from services.pdf_generator import PDFGenerator
        from services.excel_generator import ExcelGenerator

        if format == ReportFormat.PDF:
            generator = PDFGenerator()
            content = await generator.generate_match_report(
                match_id,
                include_events=include_events,
                include_stats=include_stats
            )
            media_type = "application/pdf"
            filename = f"match_{match_id}_report.pdf"
        else:
            generator = ExcelGenerator()
            content = await generator.generate_match_report(
                match_id,
                include_events=include_events,
                include_stats=include_stats
            )
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            filename = f"match_{match_id}_report.xlsx"

        return StreamingResponse(
            io.BytesIO(content),
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except Exception as e:
        logger.error(f"Error generating match report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ Scouting-Style Report Endpoints ============

@router.get("/scouting/player/{player_id}", summary="Generate professional player scouting report")
async def generate_scouting_player_report(
    player_id: str = Path(..., description="Player ID"),
    include_stats: bool = Query(True, description="Include full statistics"),
):
    """
    Generate a professional scouting report for a player, mirroring the style
    used by human scouts (profile, season performance, statistical breakdown,
    advanced metrics, and analytical narrative).
    """
    try:
        from services.pdf_generator import PDFGenerator
        generator = PDFGenerator()
        content = await generator.generate_player_report(player_id, include_stats=include_stats)
        return StreamingResponse(
            io.BytesIO(content),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=scouting_player_{player_id}.pdf"}
        )
    except Exception as e:
        logger.error(f"Error generating player scouting report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scouting/team/{team_id}", summary="Generate professional team tactical report")
async def generate_scouting_team_report(
    team_id: str = Path(..., description="Team ID"),
    include_players: bool = Query(True, description="Include squad list"),
    include_stats: bool = Query(True, description="Include team statistics"),
):
    """
    Generate a professional tactical report for a team, covering club profile,
    squad overview, statistical analysis, and playing-style narrative.
    """
    try:
        from services.pdf_generator import PDFGenerator
        generator = PDFGenerator()
        content = await generator.generate_team_report(team_id, include_players=include_players, include_stats=include_stats)
        return StreamingResponse(
            io.BytesIO(content),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=tactical_team_{team_id}.pdf"}
        )
    except Exception as e:
        logger.error(f"Error generating team tactical report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scouting/match/{match_id}", summary="Generate professional match analysis report")
async def generate_scouting_match_report(
    match_id: str = Path(..., description="Match ID"),
    include_events: bool = Query(True, description="Include event-level analysis"),
    include_stats: bool = Query(True, description="Include team statistics comparison"),
):
    """
    Generate a detailed match analysis report covering the scoreline, event timeline,
    team statistics comparison, disciplinary records, and narrative summary.
    """
    try:
        from services.pdf_generator import PDFGenerator
        generator = PDFGenerator()
        content = await generator.generate_match_report(match_id, include_events=include_events, include_stats=include_stats)
        return StreamingResponse(
            io.BytesIO(content),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=match_analysis_{match_id}.pdf"}
        )
    except Exception as e:
        logger.error(f"Error generating match analysis report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ Report Management Endpoints ============

@router.get("/list", summary="List all reports")
async def list_reports(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100, description="Maximum results")
):
    """
    List all generated reports
    """
    try:
        from services.report_generator import ReportGenerator

        generator = ReportGenerator()
        reports = await generator.list_reports(status=status, limit=limit)

        return {
            "reports": reports,
            "total": len(reports)
        }

    except Exception as e:
        logger.error(f"Error listing reports: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{report_id}", summary="Delete a report")
async def delete_report(
    report_id: str = Path(..., description="Report ID")
):
    """
    Delete a generated report
    """
    try:
        from services.report_generator import ReportGenerator

        generator = ReportGenerator()
        success = await generator.delete_report(report_id)

        if not success:
            raise HTTPException(status_code=404, detail="Report not found")

        return {
            "message": "Report deleted successfully",
            "report_id": report_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting report: {e}")
        raise HTTPException(status_code=500, detail=str(e))
