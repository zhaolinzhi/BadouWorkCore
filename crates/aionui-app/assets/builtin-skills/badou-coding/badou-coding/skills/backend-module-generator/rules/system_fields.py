"""CRUD Generator - Rule Engine: system standard fields"""
from common.generator_shared.models import FieldDef, FormConfig, SearchBox


def get_system_fields() -> list[FieldDef]:
    return [
        FieldDef.model_construct(field_name="id", entity_name="id", comment="主键ID", display_type="varchar",
                 primary_key=True, unique=True, nullable=False, length=64,
                 form=FormConfig.model_construct(show_in_grid=False, show_type="text", list_width="100px",
                                 sortable=True, show_in_page=False, editable=False, searchable=False)),
        FieldDef.model_construct(field_name="create_time", entity_name="createTime", comment="创建时间", display_type="datetime",
                 nullable=False, form=FormConfig.model_construct(show_in_grid=True, show_type="dateTime", list_width="160px",
                 sortable=True, show_in_page=True, editable=False, searchable=True,
                 search_box=SearchBox.model_construct(id="createTime", name="创建时间", defaultText="选择日期",
                                      isExtended=True, queryType="date-query"))),
        FieldDef.model_construct(field_name="update_time", entity_name="updateTime", comment="更新时间", display_type="datetime",
                 nullable=True, form=FormConfig.model_construct(show_in_grid=False, show_type="text", list_width="160px",
                 sortable=True, show_in_page=True, editable=False, searchable=False)),
        FieldDef.model_construct(field_name="flg_deleted", entity_name="flgDeleted", comment="逻辑删除", display_type="int",
                 nullable=True, default_value="0", form=FormConfig.model_construct(show_in_grid=False, show_in_page=False,
                 editable=False, searchable=False)),
        FieldDef.model_construct(field_name="creator", entity_name="creator", comment="创建人ID", display_type="varchar",
                 nullable=True, length=64, form=FormConfig.model_construct(show_in_grid=False, show_in_page=False,
                 editable=False, searchable=False)),
        FieldDef.model_construct(field_name="creator_name", entity_name="creatorName", comment="创建人", display_type="varchar",
                 nullable=True, length=255, form=FormConfig.model_construct(show_in_grid=True, show_type="text", list_width="120px",
                 show_in_page=True, editable=False, searchable=True,
                 search_box=SearchBox.model_construct(id="creatorName", name="创建人", queryType="like-query"))),
        FieldDef.model_construct(field_name="updator", entity_name="updator", comment="更新人ID", display_type="varchar",
                 nullable=True, length=64, form=FormConfig.model_construct(show_in_grid=False, show_in_page=False,
                 editable=False, searchable=False)),
        FieldDef.model_construct(field_name="updator_name", entity_name="updatorName", comment="更新人", display_type="varchar",
                 nullable=True, length=255, form=FormConfig.model_construct(show_in_grid=False, show_in_page=False,
                 editable=False, searchable=False)),
    ]
