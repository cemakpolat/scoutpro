"""
Export Service API Endpoints
Exports data in CSV, JSON, and Excel formats
"""
from fastapi import APIRouter, HTTPException, Query, Path, Body
from fastapi.responses import StreamingResponse
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from enum import Enum
import sys
import logging
import io
import json

sys.path.append('/app')

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v2/exports", tags=["exports"])


class ExportFormat(str, Enum):
    CSV = "csv"
    JSON = "json"
    EXCEL = "excel"


class ExportRequest(BaseModel):
    entity_type: str  # "players", "teams", "matches", "statistics"
    entity_ids: Optional[List[str]] = None  # If None, export all
    fields: Optional[List[str]] = None  # If None, export all fields
    format: ExportFormat = ExportFormat.CSV
    filters: Optional[Dict[str, Any]] = None


# ============ Direct Export Endpoints ============

@router.get("/players", summary="Export players data")
async def export_players(
    format: ExportFormat = Query(ExportFormat.CSV, description="Export format"),
    team: Optional[str] = Query(None, description="Filter by team"),
    position: Optional[str] = Query(None, description="Filter by position"),
    limit: int = Query(1000, ge=1, le=100000, description="Maximum rows")
):
    """
    Export players data in specified format
    """
    try:
        from services.export_handler import ExportHandler

        handler = ExportHandler()

        # Build filters
        filters = {}
        if team:
            filters['team'] = team
        if position:
            filters['position'] = position

        # Get data
        data = await handler.get_players_data(filters=filters, limit=limit)

        # Export based on format
        if format == ExportFormat.CSV:
            content = handler.to_csv(data)
            media_type = "text/csv"
            filename = "players_export.csv"
        elif format == ExportFormat.JSON:
            content = handler.to_json(data)
            media_type = "application/json"
            filename = "players_export.json"
        else:  # Excel
            content = handler.to_excel(data, sheet_name="Players")
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            filename = "players_export.xlsx"

        return StreamingResponse(
            io.BytesIO(content),
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except Exception as e:
        logger.error(f"Error exporting players: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/teams", summary="Export teams data")
async def export_teams(
    format: ExportFormat = Query(ExportFormat.CSV, description="Export format"),
    competition: Optional[str] = Query(None, description="Filter by competition"),
    limit: int = Query(1000, ge=1, le=100000, description="Maximum rows")
):
    """
    Export teams data in specified format
    """
    try:
        from services.export_handler import ExportHandler

        handler = ExportHandler()

        filters = {}
        if competition:
            filters['competition'] = competition

        data = await handler.get_teams_data(filters=filters, limit=limit)

        if format == ExportFormat.CSV:
            content = handler.to_csv(data)
            media_type = "text/csv"
            filename = "teams_export.csv"
        elif format == ExportFormat.JSON:
            content = handler.to_json(data)
            media_type = "application/json"
            filename = "teams_export.json"
        else:
            content = handler.to_excel(data, sheet_name="Teams")
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            filename = "teams_export.xlsx"

        return StreamingResponse(
            io.BytesIO(content),
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except Exception as e:
        logger.error(f"Error exporting teams: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/matches", summary="Export matches data")
async def export_matches(
    format: ExportFormat = Query(ExportFormat.CSV, description="Export format"),
    team: Optional[str] = Query(None, description="Filter by team"),
    competition: Optional[str] = Query(None, description="Filter by competition"),
    date_from: Optional[str] = Query(None, description="Filter from date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter to date (YYYY-MM-DD)"),
    limit: int = Query(1000, ge=1, le=100000, description="Maximum rows")
):
    """
    Export matches data in specified format
    """
    try:
        from services.export_handler import ExportHandler

        handler = ExportHandler()

        filters = {}
        if team:
            filters['team'] = team
        if competition:
            filters['competition'] = competition
        if date_from:
            filters['date_from'] = date_from
        if date_to:
            filters['date_to'] = date_to

        data = await handler.get_matches_data(filters=filters, limit=limit)

        if format == ExportFormat.CSV:
            content = handler.to_csv(data)
            media_type = "text/csv"
            filename = "matches_export.csv"
        elif format == ExportFormat.JSON:
            content = handler.to_json(data)
            media_type = "application/json"
            filename = "matches_export.json"
        else:
            content = handler.to_excel(data, sheet_name="Matches")
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            filename = "matches_export.xlsx"

        return StreamingResponse(
            io.BytesIO(content),
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except Exception as e:
        logger.error(f"Error exporting matches: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics", summary="Export statistics data")
async def export_statistics(
    format: ExportFormat = Query(ExportFormat.CSV, description="Export format"),
    entity_type: str = Query(..., description="Entity type (player, team, match)"),
    entity_id: Optional[str] = Query(None, description="Filter by entity ID"),
    stat_type: Optional[str] = Query(None, description="Filter by stat type"),
    limit: int = Query(1000, ge=1, le=100000, description="Maximum rows")
):
    """
    Export statistics data in specified format
    """
    try:
        from services.export_handler import ExportHandler

        handler = ExportHandler()

        filters = {
            'entity_type': entity_type
        }
        if entity_id:
            filters['entity_id'] = entity_id
        if stat_type:
            filters['stat_type'] = stat_type

        data = await handler.get_statistics_data(filters=filters, limit=limit)

        if format == ExportFormat.CSV:
            content = handler.to_csv(data)
            media_type = "text/csv"
            filename = "statistics_export.csv"
        elif format == ExportFormat.JSON:
            content = handler.to_json(data)
            media_type = "application/json"
            filename = "statistics_export.json"
        else:
            content = handler.to_excel(data, sheet_name="Statistics")
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            filename = "statistics_export.xlsx"

        return StreamingResponse(
            io.BytesIO(content),
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except Exception as e:
        logger.error(f"Error exporting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ Custom Export Endpoint ============

@router.post("/custom", summary="Custom export with filters")
async def custom_export(request: ExportRequest = Body(...)):
    """
    Custom export with advanced filtering

    Allows exporting any entity type with custom filters and field selection
    """
    try:
        from services.export_handler import ExportHandler

        handler = ExportHandler()

        # Get data based on entity type
        if request.entity_type == "players":
            data = await handler.get_players_data(
                entity_ids=request.entity_ids,
                filters=request.filters,
                fields=request.fields
            )
        elif request.entity_type == "teams":
            data = await handler.get_teams_data(
                entity_ids=request.entity_ids,
                filters=request.filters,
                fields=request.fields
            )
        elif request.entity_type == "matches":
            data = await handler.get_matches_data(
                entity_ids=request.entity_ids,
                filters=request.filters,
                fields=request.fields
            )
        elif request.entity_type == "statistics":
            data = await handler.get_statistics_data(
                filters=request.filters,
                fields=request.fields
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown entity type: {request.entity_type}"
            )

        # Export based on format
        if request.format == ExportFormat.CSV:
            content = handler.to_csv(data)
            media_type = "text/csv"
            extension = "csv"
        elif request.format == ExportFormat.JSON:
            content = handler.to_json(data)
            media_type = "application/json"
            extension = "json"
        else:
            content = handler.to_excel(data, sheet_name=request.entity_type.title())
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            extension = "xlsx"

        filename = f"{request.entity_type}_export.{extension}"

        return StreamingResponse(
            io.BytesIO(content),
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in custom export: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ Template Endpoints ============

@router.get("/templates/players", summary="Get player export template")
async def get_player_template(
    format: ExportFormat = Query(ExportFormat.CSV, description="Template format")
):
    """
    Get an empty template for player data export

    Useful for understanding the export structure
    """
    try:
        from services.export_handler import ExportHandler

        handler = ExportHandler()

        # Create empty template with headers
        template_data = [{
            "player_id": "",
            "name": "",
            "position": "",
            "team": "",
            "age": "",
            "nationality": ""
        }]

        if format == ExportFormat.CSV:
            content = handler.to_csv(template_data)
            media_type = "text/csv"
            filename = "player_template.csv"
        elif format == ExportFormat.JSON:
            content = handler.to_json(template_data)
            media_type = "application/json"
            filename = "player_template.json"
        else:
            content = handler.to_excel(template_data, sheet_name="Template")
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            filename = "player_template.xlsx"

        return StreamingResponse(
            io.BytesIO(content),
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except Exception as e:
        logger.error(f"Error generating template: {e}")
        raise HTTPException(status_code=500, detail=str(e))
