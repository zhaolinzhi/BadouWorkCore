"""Flow Engine - Data Models (Pydantic)"""

from __future__ import annotations
from typing import Optional, List
from pydantic import BaseModel, Field, model_validator
import sys
import uuid


class BusiDef(BaseModel):
    """业务定义"""
    code: str                                    # 业务编码（唯一）
    name: str                                    # 业务名称
    module_code: Optional[str] = None            # 关联模块 code
    instance_class: str = "com.badou.designer.module.design.base.ModuleEntityFlowWithNodeCode"


class HandlerDef(BaseModel):
    """环节处理人配置"""
    type: int = Field(..., ge=0, le=40)          # node_handler_type (0/1/20/40)
    value: str                                   # node_processor_value（完整格式）
    text: str                                    # node_processor_text（显示名称）

    @model_validator(mode="after")
    def validate_handler(self) -> "HandlerDef":
        # 校验 value 格式: {type}!@!{name}!@!{ref}
        parts = self.value.split("!@!")
        if len(parts) != 3:
            raise ValueError(f"processor_value 格式错误，需要 3 段: {self.value}")
        # 第一段需与 handler.type 一致
        if str(parts[0]) != str(self.type):
            raise ValueError(f"handler.type ({self.type}) 与 value 第一段 ({parts[0]}) 不一致")
        # 第二段需与 text 一致
        if parts[1] != self.text:
            raise ValueError(f"handler.text ('{self.text}') 与 value 第二段 ('{parts[1]}') 不一致")
        # ⚠️ type=1（抽象处理人）：第三段必须是 comm_handler_rule 的真实 ID，不是占位符
        if self.type == 1:
            ref = parts[2].strip()
            known_rules = {'3': '拟稿人/填报人', '2': '审批人', '6': '部门负责人',
                           '4': '主管领导', '5': '会签人'}
            if ref == '0':
                raise ValueError(
                    f"type=1（抽象处理人）的 processor_value 第三段不能为 '0'。\n"
                    f"  第三段必须是 comm_handler_rule 表中对应规则的 ID，不是占位符。\n"
                    f"  常用规则 ID: {', '.join(f'{k}={v}' for k, v in known_rules.items())}\n"
                    f"  首环节常用规则: 拟稿人/填报人 → ID=3  → value='1!@!{parts[1]}!@!3'"
                )
            if ref not in known_rules:
                print(
                    f"\033[93m⚠️  [提醒] type=1 抽象处理人 '{parts[1]}' 的规则 ID='{ref}' 不在常用列表中。\033[0m\n"
                    f"  请确认 '{ref}' 是 comm_handler_rule 表中真实存在的 ID。\n"
                    f"  常用规则 ID: {', '.join(f'{k}={v}' for k, v in known_rules.items())}",
                    file=sys.stderr
                )
        return self


class RouteDef(BaseModel):
    """环节路由"""
    code: str                                    # 路由编码
    menu_name: str                               # 按钮显示名称
    flg_attribute: str = "GOAHEAD"               # GOAHEAD / BACK
    target_node: str                             # 目标节点 code
    priority: int = 0                            # 排序（同一节点内）
    flg_multi_node: int = 0                      # 0=普通, 1=多目标, 2=多目标单向
    iz_need_opinion: int = 1                     # 是否需要意见
    flow_submit_form_no_valid: int = 1           # 路由保存校验（默认1）
    name: Optional[str] = None                   # 路由名称（默认用 menu_name）

    @model_validator(mode="after")
    def set_defaults(self) -> "RouteDef":
        if self.name is None:
            self.name = self.menu_name
        return self


class NodeDef(BaseModel):
    """流程环节"""
    code: str                                    # 节点编码（如 START, REVIEW_01）
    node_name: str                               # 节点名称
    flg_head: int = 0                            # 是否首环节（NOT NULL, 默认0, 第一个环节=1）
    flg_root: int = 0                            # 是否结束环节（NOT NULL, 默认0, 结束环节=1）
    handle_way: Optional[int] = None             # 处理方式 ID（1=串行...）
    handler: Optional[HandlerDef] = None         # 处理人配置
    routes: List[RouteDef] = []                  # 路由列表
    priority: Optional[int] = None               # 排序（自动分配时可为空）
    automatic_terminate: int = 0                 # 自动提交（不允许为空，默认0）
    flg_spread: int = 0                           # 环节是否需要传阅属性（NOT NULL, 默认0）
    flg_spread_allow: int = 1                     # 是否允许处理人发待阅（默认1）
    timelimit_relate_yq: int = 0                  # 时限：相对年季（默认0）
    timelimit_relate: int = 0                     # 时限：相对月份（默认0）
    timelimit_date: int = 0                       # 时限：日期（默认0）
    timelimit_flg_apply: int = 0                  # 时限：应用（默认0）
    timellimt_house: int = 0                      # 时限：收到待办小时（默认0）
    memo: Optional[str] = None                   # 备注


class FlowDefinition(BaseModel):
    """流程定义（顶层模型）"""
    code: str                                    # 流程编码（唯一）
    flow_name: str                               # 流程名称
    busi: BusiDef                                # 绑定的业务
    nodes: List[NodeDef]                         # 节点列表
    memo: Optional[str] = None                   # 备注
    org_id: str = "ROOT"                         # 组织ID
    priority: Optional[int] = None               # 流程排序
    flg_allow_modify: int = 1                    # 允许修改

    @staticmethod
    def gen_uuid() -> str:
        return uuid.uuid4().hex

    @model_validator(mode="after")
    def validate_flow(self) -> "FlowDefinition":
        # 至少有一个节点
        if not self.nodes:
            raise ValueError("流程至少需要一个节点")

        # 校验起始节点唯一性
        heads = [n for n in self.nodes if n.flg_head == 1]
        if len(heads) != 1:
            raise ValueError(f"流程必须有且仅有一个起始节点（当前 {len(heads)} 个）")

        # 校验节点 code 唯一性
        codes = [n.code for n in self.nodes]
        if len(codes) != len(set(codes)):
            raise ValueError(f"节点编码重复: {[c for c in codes if codes.count(c) > 1]}")

        # 校验路由 target_node 存在性
        node_codes = set(codes)
        for node in self.nodes:
            for route in node.routes:
                if route.target_node not in node_codes and route.target_node != "end":
                    raise ValueError(f"节点 '{node.code}' 的路由 target_node='{route.target_node}' 不存在")

        # 自动分配 priority（如果为空）
        for i, node in enumerate(self.nodes):
            if node.priority is None:
                node.priority = i

        return self

    def get_node(self, code: str) -> Optional[NodeDef]:
        """按 code 查找节点"""
        for n in self.nodes:
            if n.code == code:
                return n
        return None

    def is_end_node(self, code: str) -> bool:
        return code == "end"
