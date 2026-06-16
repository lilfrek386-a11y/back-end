from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status

from app.dependencies.auth import CurrentUser
from app.dependencies.company_actions import ActionService


async def require_company_owner(
    company_id: UUID,
    current_user: CurrentUser,
    service: ActionService,
):
    async with service.uow:
        company = await service.uow.companies.get_one(company_id)
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Company not found."
            )
        if company.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Not the company owner."
            )


type RequireCompanyOwner = Annotated[None, Depends(require_company_owner)]
