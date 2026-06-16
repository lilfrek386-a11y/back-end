from uuid import UUID
from fastapi import APIRouter, Depends, status
from app.dependencies.pagination import SkipQuery, LimitQuery
from app.schemas.company_action import ActionsListResponse
from app.dependencies.auth import CurrentUser
from app.dependencies.company_actions import ActionService
from app.dependencies.company_owner import require_company_owner

router = APIRouter(
    prefix="/companies/{company_id}",
    tags=["Company Actions – Owner"],
    dependencies=[Depends(require_company_owner)],
)


@router.get("/invitations", response_model=ActionsListResponse)
async def get_company_invitations(
    company_id: UUID,
    current_user: CurrentUser,
    service: ActionService,
    skip: SkipQuery = 0,
    limit: LimitQuery = 100,
):
    return await service.get_company_invitations(
        owner_id=current_user.id, company_id=company_id, skip=skip, limit=limit
    )


@router.get("/requests", response_model=ActionsListResponse)
async def get_company_requests(
    company_id: UUID,
    current_user: CurrentUser,
    service: ActionService,
    skip: SkipQuery = 0,
    limit: LimitQuery = 100,
):
    return await service.get_company_requests(
        owner_id=current_user.id, company_id=company_id, skip=skip, limit=limit
    )


@router.post("/invitations/{user_id}", status_code=status.HTTP_201_CREATED)
async def send_invitation(
    company_id: UUID, user_id: UUID, current_user: CurrentUser, service: ActionService
):
    await service.send_invitation(
        owner_id=current_user.id, company_id=company_id, invited_user_id=user_id
    )
    return {"detail": "Invitation sent successfully."}


@router.delete("/invitations/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_invitation(
    company_id: UUID, user_id: UUID, current_user: CurrentUser, service: ActionService
):
    await service.cancel_invitation(
        owner_id=current_user.id, company_id=company_id, canceled_user_id=user_id
    )


@router.post("/requests/{user_id}/accept", status_code=status.HTTP_200_OK)
async def accept_request(
    company_id: UUID, user_id: UUID, current_user: CurrentUser, service: ActionService
):
    await service.accept_request(
        owner_id=current_user.id, company_id=company_id, requester_id=user_id
    )
    return {"detail": "Request accepted. User is now a member."}


@router.post("/requests/{user_id}/decline", status_code=status.HTTP_200_OK)
async def decline_request(
    company_id: UUID, user_id: UUID, current_user: CurrentUser, service: ActionService
):
    await service.decline_request(
        owner_id=current_user.id, company_id=company_id, requester_id=user_id
    )
    return {"detail": "Request declined."}
