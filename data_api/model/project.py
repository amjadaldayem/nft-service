from typing import Any, Dict, Optional

from pydantic import BaseModel


class ProjectInfo(BaseModel):
    id: int
    project_name: str
    description: str
    contract_address: str
    slug: str
    project_id: str
    twitter_account_username: str
    icon_url: str
    website_url: Optional[str]
    blockchain_id: int
    curated: bool


@classmethod
def from_dict(cls, project_info_dict: Dict[str, Any]) -> ProjectInfo:
    return cls(
        id=project_info_dict["id"],
        project_name=project_info_dict["project_name"],
        description=project_info_dict["description"],
        contract_address=project_info_dict["contract_address"],
        slug=project_info_dict["slug"],
        project_id=project_info_dict["project_id"],
        twitter_account_username=project_info_dict["twitter_account_username"],
        icon_url=project_info_dict["icon_url"],
        website_url=project_info_dict.get("website_url", None),
        blockchain_id=project_info_dict["blockchain_id"],
        curated=project_info_dict["curated"],
    )
