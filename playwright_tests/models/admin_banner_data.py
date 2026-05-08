from dataclasses import dataclass
from typing import Optional, List


@dataclass
class AdminBannerData:
    content: str
    start_display_date: Optional[str] = None
    start_display_time: Optional[str] = None
    stop_display_date: Optional[str] = None
    stop_display_time: Optional[str] = None
    target_groups: Optional[List[str]] = None
    target_locale: Optional[str] = None
    target_platforms: Optional[List[str]] = None
    target_product: Optional[str] = None
