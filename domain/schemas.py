from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, HttpUrl


class EntryKind(str, Enum):
    book = "book"
    article = "article"


class EntryStatus(str, Enum):
    planned = "planned"
    in_progress = "in_progress"
    finished = "finished"


class EntryBase(BaseModel):
    title: str
    kind: EntryKind
    link: Optional[HttpUrl] = None
    status: EntryStatus = EntryStatus.planned


class EntryCreate(EntryBase):
    pass


class EntryUpdate(BaseModel):
    title: Optional[str] = None
    kind: Optional[EntryKind] = None
    link: Optional[HttpUrl] = None
    status: Optional[EntryStatus] = None


class EntryInDB(EntryBase):
    id: int
    owner_id: int
    model_config = ConfigDict(from_attributes=True)


class UserListItem(BaseModel):
    id: int
    email: EmailStr
    model_config = ConfigDict(from_attributes=True, extra="forbid")
