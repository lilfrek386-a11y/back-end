from uuid import UUID

from fastapi import APIRouter, status

from app.dependencies.auth import CurrentUser
from app.dependencies.pagination import SkipQuery, LimitQuery
from app.schemas.company_member import MembersListResponse
from app.dependencies.company_members import MemberService

router = APIRouter(prefix="/companies", tags=["Company Members"])


@router.get(
    "/{company_id}/members",
    response_model=MembersListResponse,
    status_code=status.HTTP_200_OK,
)
async def get_company_members(
    company_id: UUID,
    service: MemberService,
    skip: SkipQuery = 0,
    limit: LimitQuery = 100,
):
    return await service.get_company_members(
        company_id=company_id, skip=skip, limit=limit
    )


@router.delete(
    "/{company_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def kick_user(
    company_id: UUID,
    user_id: UUID,
    current_user: CurrentUser,
    service: MemberService,
):
    await service.kick_user(
        owner_id=current_user.id, company_id=company_id, user_id=user_id
    )


@router.delete(
    "/{company_id}/leave",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def leave_company(
    company_id: UUID,
    current_user: CurrentUser,
    service: MemberService,
):
    await service.leave_company(user_id=current_user.id, company_id=company_id)
