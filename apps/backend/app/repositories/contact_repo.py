from typing import List, Optional
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contact import Contact
from app.repositories.base import BaseRepository


class ContactRepository(BaseRepository[Contact]):
    def __init__(self, session: AsyncSession):
        super().__init__(Contact, session)

    async def get_by_email(self, workspace_id: str, email: str) -> Optional[Contact]:
        query = select(Contact).where(
            and_(
                Contact.workspace_id == workspace_id,
                Contact.email == email.strip().lower(),
            )
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def list_by_company(self, workspace_id: str, company_id: str) -> List[Contact]:
        query = select(Contact).where(
            and_(
                Contact.workspace_id == workspace_id,
                Contact.company_id == company_id,
            )
        ).order_by(Contact.created_at.asc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def list_contacts(
        self,
        workspace_id: str,
        company_id: Optional[str] = None,
        is_suppressed: Optional[bool] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Contact]:
        filters = [Contact.workspace_id == workspace_id]
        if company_id:
            filters.append(Contact.company_id == company_id)
        if is_suppressed is not None:
            filters.append(Contact.is_suppressed == is_suppressed)

        query = (
            select(Contact)
            .where(and_(*filters))
            .order_by(Contact.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_contacts(
        self,
        workspace_id: str,
        company_id: Optional[str] = None,
        is_suppressed: Optional[bool] = None,
    ) -> int:
        filters = [Contact.workspace_id == workspace_id]
        if company_id:
            filters.append(Contact.company_id == company_id)
        if is_suppressed is not None:
            filters.append(Contact.is_suppressed == is_suppressed)

        query = select(func.count(Contact.id)).where(and_(*filters))
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def upsert_contact(
        self,
        workspace_id: str,
        company_id: str,
        email: str,
        first_name: str,
        last_name: str = "",
        title: Optional[str] = None,
        phone: Optional[str] = None,
        linkedin_url: Optional[str] = None,
        provenance_url: Optional[str] = None,
        permission_status: str = "LEGITIMATE_INTEREST",
    ) -> Contact:
        normalized_email = email.strip().lower()
        existing = await self.get_by_email(workspace_id, normalized_email)
        if existing:
            if not existing.title and title:
                existing.title = title
            if not existing.phone and phone:
                existing.phone = phone
            if not existing.linkedin_url and linkedin_url:
                existing.linkedin_url = linkedin_url
            await self.session.flush()
            return existing

        contact = Contact(
            workspace_id=workspace_id,
            company_id=company_id,
            email=normalized_email,
            first_name=first_name,
            last_name=last_name,
            title=title,
            phone=phone,
            linkedin_url=linkedin_url,
            provenance_url=provenance_url,
            permission_status=permission_status,
        )
        self.session.add(contact)
        await self.session.flush()
        return contact
