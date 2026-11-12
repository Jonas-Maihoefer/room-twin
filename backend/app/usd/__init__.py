"""Read-only RoomPlan/OpenUSD foundation used by the replacement pipeline."""

from app.usd.catalog import AssetCatalog, CatalogError, CatalogMatch
from app.usd.scan_parser import RoomPlanScan, ScanParseError, load_roomplan_scan, parse_roomplan_scan
from app.usd.scene_reader import SceneInventory, SceneReadError, read_usdz_inventory
from app.usd.matcher import MatchingError, FurnitureMatch, ReplacementPlanItem, match_furniture, build_replacement_plan, normalize_uuid
from app.usd.replacement import ReplacementError, ReplacementResult, apply_replacements, process_roomplan
from app.usd.transforms import Fit, TransformError, fit_bounds
from app.usd.workspace import WorkspaceError, extract_usdz

__all__ = [
    "AssetCatalog", "CatalogError", "CatalogMatch", "RoomPlanScan", "ScanParseError",
    "SceneInventory", "SceneReadError", "load_roomplan_scan", "parse_roomplan_scan",
    "read_usdz_inventory",
    "MatchingError", "FurnitureMatch", "ReplacementPlanItem", "match_furniture", "normalize_uuid",
    "build_replacement_plan", "ReplacementError", "ReplacementResult", "apply_replacements", "process_roomplan",
    "Fit", "TransformError", "fit_bounds", "WorkspaceError", "extract_usdz",
]
