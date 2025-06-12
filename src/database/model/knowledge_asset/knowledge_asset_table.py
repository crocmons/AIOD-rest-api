from sqlmodel import Field, SQLModel

from database.model.field_length import IDENTIFIER_LENGTH


class KnowledgeAssetTable(SQLModel, table=True):  # type: ignore [call-arg]
    __tablename__ = "knowledge_asset"
    identifier: str = Field(max_length=IDENTIFIER_LENGTH, default=None, primary_key=True)
    type: str = Field(
        description="The name of the table of the knowledge asset. E.g. 'publication'"
    )
