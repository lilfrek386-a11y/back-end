from uuid import UUID
from fastapi import APIRouter, status
from app.dependencies.pagination import SkipQuery, LimitQuery
from app.schemas.company_action import ActionsListResponse
from app.dependencies.auth import CurrentUser
from app.dependencies.company_actions import ActionService

router = APIRouter(tags=["Company Actions – User"])


@router.get("/users/me/invitations", response_model=ActionsListResponse)
async def get_my_invitations(
    current_user: CurrentUser,
    service: ActionService,
    skip: SkipQuery = 0,
    limit: LimitQuery = 100,
):
    return await service.get_user_invitations(
        user_id=current_user.id, skip=skip, limit=limit
    )


@router.get("/users/me/requests", response_model=ActionsListResponse)
async def get_my_requests(
    current_user: CurrentUser,
    service: ActionService,
    skip: SkipQuery = 0,
    limit: LimitQuery = 100,
):
    return await service.get_user_requests(
        user_id=current_user.id, skip=skip, limit=limit
    )


@router.post("/companies/{company_id}/requests", status_code=status.HTTP_201_CREATED)
async def send_request_to_join(
    company_id: UUID, current_user: CurrentUser, service: ActionService
):
    await service.send_request(user_id=current_user.id, company_id=company_id)
    return {"detail": "Membership request sent successfully."}


@router.delete(
    "/companies/{company_id}/requests", status_code=status.HTTP_204_NO_CONTENT
)
async def cancel_my_request(
    company_id: UUID, current_user: CurrentUser, service: ActionService
):
    await service.cancel_request(user_id=current_user.id, company_id=company_id)


@router.post(
    "/companies/{company_id}/invitations/accept", status_code=status.HTTP_200_OK
)
async def accept_invitation(
    company_id: UUID, current_user: CurrentUser, service: ActionService
):
    await service.accept_invitation(user_id=current_user.id, company_id=company_id)
    return {"detail": "Invitation accepted. You are now a member."}


@router.post(
    "/companies/{company_id}/invitations/decline", status_code=status.HTTP_200_OK
)
async def decline_invitation(
    company_id: UUID, current_user: CurrentUser, service: ActionService
):
    await service.decline_invitation(user_id=current_user.id, company_id=company_id)
    return {"detail": "Invitation declined."}
