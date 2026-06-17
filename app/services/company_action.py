import logging
from uuid import UUID

from app.models.company_action import ActionType
from app.models.company_member import CompanyMemberRole
from app.schemas.company_action import ActionsListResponse, ActionResponse

from app.utils.uow import UnitOfWork
from app.core.exceptions import (
    CompanyNotFoundException,
    UserNotFoundException,
    InvitationAlreadyExist,
    UserAlreadyMemberException,
    CannotInviteYourselfException,
    InvitationNotFoundException,
    RequestAlreadyExistException,
    CannotRequestYourselfException,
    RequestNotFoundException,
)
from app.services.utils import add_company_member

logger = logging.getLogger(__name__)


class CompanyActionService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def get_user_invitations(
        self, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> ActionsListResponse:
        async with self.uow:
            actions, total_count = await self.uow.company_actions.get_user_invitations(
                user_id, skip, limit
            )
            actions_list = [ActionResponse.model_validate(a) for a in actions]
            return ActionsListResponse(actions=actions_list, total_count=total_count)

    async def get_user_requests(
        self, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> ActionsListResponse:
        async with self.uow:
            requests, total_count = await self.uow.company_actions.get_user_requests(
                user_id, skip, limit
            )
            requests_list = [ActionResponse.model_validate(a) for a in requests]
            return ActionsListResponse(actions=requests_list, total_count=total_count)

    async def get_company_requests(
        self, company_id: UUID, skip: int = 0, limit: int = 100
    ) -> ActionsListResponse:
        async with self.uow:
            requests, total_count = await self.uow.company_actions.get_company_requests(
                company_id, skip, limit
            )
            requests_list = [ActionResponse.model_validate(a) for a in requests]
            return ActionsListResponse(actions=requests_list, total_count=total_count)

    async def get_company_invitations(
        self, company_id: UUID, skip: int = 0, limit: int = 100
    ) -> ActionsListResponse:
        async with self.uow:
            actions, total_count = (
                await self.uow.company_actions.get_company_invitations(
                    company_id, skip, limit
                )
            )
            actions_list = [ActionResponse.model_validate(a) for a in actions]
            return ActionsListResponse(actions=actions_list, total_count=total_count)

    async def send_invitation(
        self, company_id: UUID, invited_user_id: UUID, owner_id: UUID
    ) -> None:
        if owner_id == invited_user_id:
            raise CannotInviteYourselfException()

        async with self.uow:
            user = await self.uow.users.get_one(invited_user_id)
            if not user:
                raise UserNotFoundException()

            await self._check_user_is_not_member(company_id, invited_user_id)
            await self._check_action_does_not_exist(
                company_id, invited_user_id, ActionType.INVITATION
            )
            await self._check_action_does_not_exist(
                company_id, invited_user_id, ActionType.REQUEST
            )

            await self.uow.company_actions.create(
                {
                    "company_id": company_id,
                    "user_id": invited_user_id,
                    "action_type": ActionType.INVITATION,
                }
            )

    async def cancel_invitation(self, company_id: UUID, canceled_user_id: UUID) -> None:
        async with self.uow:
            await self._remove_action_in_db(
                company_id, canceled_user_id, ActionType.INVITATION
            )

    async def accept_invitation(self, user_id: UUID, company_id: UUID) -> None:
        async with self.uow:
            await self._approve_action_in_db(company_id, user_id, ActionType.INVITATION)

    async def decline_invitation(self, user_id: UUID, company_id: UUID) -> None:
        async with self.uow:
            await self._remove_action_in_db(company_id, user_id, ActionType.INVITATION)

    async def send_request(self, user_id: UUID, company_id: UUID) -> None:
        async with self.uow:
            company = await self.uow.companies.get_one(company_id)
            if not company:
                raise CompanyNotFoundException()

            if company.owner_id == user_id:
                raise CannotRequestYourselfException()

            await self._check_user_is_not_member(company_id, user_id)
            await self._check_action_does_not_exist(
                company_id, user_id, ActionType.INVITATION
            )
            await self._check_action_does_not_exist(
                company_id, user_id, ActionType.REQUEST
            )

            await self.uow.company_actions.create(
                {
                    "company_id": company_id,
                    "user_id": user_id,
                    "action_type": ActionType.REQUEST,
                }
            )

    async def cancel_request(self, user_id: UUID, company_id: UUID) -> None:
        async with self.uow:
            await self._remove_action_in_db(company_id, user_id, ActionType.REQUEST)

    async def accept_request(self, company_id: UUID, requester_id: UUID) -> None:
        async with self.uow:
            await self._approve_action_in_db(
                company_id, requester_id, ActionType.REQUEST
            )

    async def decline_request(self, company_id: UUID, requester_id: UUID) -> None:
        async with self.uow:
            await self._remove_action_in_db(
                company_id, requester_id, ActionType.REQUEST
            )

    async def _check_user_is_not_member(self, company_id: UUID, user_id: UUID) -> None:
        member = await self.uow.company_members.get_by_company_and_user(
            company_id, user_id
        )
        if member:
            raise UserAlreadyMemberException()

    async def _get_action_or_raise(
        self, company_id: UUID, user_id: UUID, action_type: ActionType
    ):
        action = await self.uow.company_actions.get_by_company_and_user(
            company_id, user_id, action_type
        )
        if not action:
            if action_type == ActionType.INVITATION:
                raise InvitationNotFoundException()
            raise RequestNotFoundException()
        return action

    async def _check_action_does_not_exist(
        self, company_id: UUID, user_id: UUID, action_type: ActionType
    ) -> None:
        action = await self.uow.company_actions.get_by_company_and_user(
            company_id, user_id, action_type
        )
        if action:
            if action_type == ActionType.INVITATION:
                raise InvitationAlreadyExist()
            raise RequestAlreadyExistException()

    async def _approve_action_in_db(
        self, company_id: UUID, user_id: UUID, action_type: ActionType
    ) -> None:
        action = await self._get_action_or_raise(company_id, user_id, action_type)
        await self._check_user_is_not_member(company_id, user_id)

        await self.uow.company_actions.delete(action)
        await add_company_member(
            self.uow, company_id, user_id, CompanyMemberRole.MEMBER
        )

    async def _remove_action_in_db(
        self, company_id: UUID, user_id: UUID, action_type: ActionType
    ) -> None:
        action = await self._get_action_or_raise(company_id, user_id, action_type)
        await self.uow.company_actions.delete(action)
