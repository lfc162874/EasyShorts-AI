from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.constants import MenuType, NewsSourceType, PlatformAuthStatus, UserStatus
from app.core.security import get_password_hash
from app.db.models.business import NewsSource
from app.db.models.rbac import Menu, Role, User
from app.db.models.system import PlatformAccount, SystemConfig

DEFAULT_MENU_SEED = [
    {
        "name": "dashboard",
        "title": "工作台",
        "path": "/dashboard",
        "component": "dashboard/index",
        "icon": "dashboard",
        "menu_type": MenuType.MENU.value,
        "permission_code": "dashboard:view",
        "sort_order": 1,
        "hidden": False,
        "parent": None,
    },
    {
        "name": "system",
        "title": "系统管理",
        "path": "/system",
        "component": "Layout",
        "icon": "system",
        "menu_type": MenuType.DIRECTORY.value,
        "permission_code": None,
        "sort_order": 100,
        "hidden": False,
        "parent": None,
    },
    {
        "name": "system_users",
        "title": "用户管理",
        "path": "/system/users",
        "component": "system/users/index",
        "icon": "user",
        "menu_type": MenuType.MENU.value,
        "permission_code": "system:user:view",
        "sort_order": 101,
        "hidden": False,
        "parent": "system",
    },
    {
        "name": "system_roles",
        "title": "角色管理",
        "path": "/system/roles",
        "component": "system/roles/index",
        "icon": "roles",
        "menu_type": MenuType.MENU.value,
        "permission_code": "system:role:view",
        "sort_order": 102,
        "hidden": False,
        "parent": "system",
    },
    {
        "name": "system_menus",
        "title": "菜单管理",
        "path": "/system/menus",
        "component": "system/menus/index",
        "icon": "menu",
        "menu_type": MenuType.MENU.value,
        "permission_code": "system:menu:view",
        "sort_order": 103,
        "hidden": False,
        "parent": "system",
    },
    {
        "name": "system_configs",
        "title": "配置中心",
        "path": "/system/configs",
        "component": "system/configs/index",
        "icon": "configs",
        "menu_type": MenuType.MENU.value,
        "permission_code": "system:config:view",
        "sort_order": 104,
        "hidden": False,
        "parent": "system",
    },
    {
        "name": "system_files",
        "title": "文件中心",
        "path": "/assets/files",
        "component": "assets/files/index",
        "icon": "files",
        "menu_type": MenuType.MENU.value,
        "permission_code": "system:file:view",
        "sort_order": 105,
        "hidden": False,
        "parent": "system",
    },
    {
        "name": "system_logs",
        "title": "日志中心",
        "path": "/system/logs",
        "component": "system/logs/index",
        "icon": "logs",
        "menu_type": MenuType.MENU.value,
        "permission_code": "system:log:view",
        "sort_order": 106,
        "hidden": False,
        "parent": "system",
    },
    {
        "name": "system_tasks",
        "title": "任务中心",
        "path": "/system/tasks",
        "component": "system/tasks/index",
        "icon": "tasks",
        "menu_type": MenuType.MENU.value,
        "permission_code": "system:task:view",
        "sort_order": 107,
        "hidden": False,
        "parent": "system",
    },
    {
        "name": "system_menu_list_perm",
        "title": "菜单列表权限",
        "path": None,
        "component": None,
        "icon": None,
        "menu_type": MenuType.BUTTON.value,
        "permission_code": "system:menu:list",
        "sort_order": 110,
        "hidden": True,
        "parent": "system",
    },
    {
        "name": "system_user_list_perm",
        "title": "用户列表权限",
        "path": None,
        "component": None,
        "icon": None,
        "menu_type": MenuType.BUTTON.value,
        "permission_code": "system:user:list",
        "sort_order": 111,
        "hidden": True,
        "parent": "system",
    },
    {
        "name": "system_user_create_perm",
        "title": "用户新增权限",
        "path": None,
        "component": None,
        "icon": None,
        "menu_type": MenuType.BUTTON.value,
        "permission_code": "system:user:create",
        "sort_order": 112,
        "hidden": True,
        "parent": "system",
    },
    {
        "name": "system_user_update_perm",
        "title": "用户更新权限",
        "path": None,
        "component": None,
        "icon": None,
        "menu_type": MenuType.BUTTON.value,
        "permission_code": "system:user:update",
        "sort_order": 113,
        "hidden": True,
        "parent": "system",
    },
    {
        "name": "system_role_list_perm",
        "title": "角色列表权限",
        "path": None,
        "component": None,
        "icon": None,
        "menu_type": MenuType.BUTTON.value,
        "permission_code": "system:role:list",
        "sort_order": 114,
        "hidden": True,
        "parent": "system",
    },
    {
        "name": "system_role_update_perm",
        "title": "角色更新权限",
        "path": None,
        "component": None,
        "icon": None,
        "menu_type": MenuType.BUTTON.value,
        "permission_code": "system:role:update",
        "sort_order": 115,
        "hidden": True,
        "parent": "system",
    },
    {
        "name": "system_menu_update_perm",
        "title": "菜单更新权限",
        "path": None,
        "component": None,
        "icon": None,
        "menu_type": MenuType.BUTTON.value,
        "permission_code": "system:menu:update",
        "sort_order": 116,
        "hidden": True,
        "parent": "system",
    },
    {
        "name": "system_config_list_perm",
        "title": "配置列表权限",
        "path": None,
        "component": None,
        "icon": None,
        "menu_type": MenuType.BUTTON.value,
        "permission_code": "system:config:list",
        "sort_order": 117,
        "hidden": True,
        "parent": "system",
    },
    {
        "name": "system_config_update_perm",
        "title": "配置更新权限",
        "path": None,
        "component": None,
        "icon": None,
        "menu_type": MenuType.BUTTON.value,
        "permission_code": "system:config:update",
        "sort_order": 118,
        "hidden": True,
        "parent": "system",
    },
    {
        "name": "system_file_upload_perm",
        "title": "文件上传权限",
        "path": None,
        "component": None,
        "icon": None,
        "menu_type": MenuType.BUTTON.value,
        "permission_code": "system:file:upload",
        "sort_order": 119,
        "hidden": True,
        "parent": "system",
    },
    {
        "name": "system_log_list_perm",
        "title": "日志列表权限",
        "path": None,
        "component": None,
        "icon": None,
        "menu_type": MenuType.BUTTON.value,
        "permission_code": "system:log:list",
        "sort_order": 120,
        "hidden": True,
        "parent": "system",
    },
    {
        "name": "system_task_list_perm",
        "title": "任务列表权限",
        "path": None,
        "component": None,
        "icon": None,
        "menu_type": MenuType.BUTTON.value,
        "permission_code": "system:task:list",
        "sort_order": 121,
        "hidden": True,
        "parent": "system",
    },
    {
        "name": "system_platform_account_list_perm",
        "title": "平台账号列表权限",
        "path": None,
        "component": None,
        "icon": None,
        "menu_type": MenuType.BUTTON.value,
        "permission_code": "system:platform-account:list",
        "sort_order": 122,
        "hidden": True,
        "parent": "system",
    },
    {
        "name": "system_platform_account_update_perm",
        "title": "平台账号更新权限",
        "path": None,
        "component": None,
        "icon": None,
        "menu_type": MenuType.BUTTON.value,
        "permission_code": "system:platform-account:update",
        "sort_order": 123,
        "hidden": True,
        "parent": "system",
    },
    {
        "name": "content",
        "title": "内容中心",
        "path": "/news",
        "component": "Layout",
        "icon": "collection",
        "menu_type": MenuType.DIRECTORY.value,
        "permission_code": None,
        "sort_order": 200,
        "hidden": False,
        "parent": None,
    },
    {
        "name": "news_articles",
        "title": "新闻管理",
        "path": "/news/list",
        "component": "news/list/index",
        "icon": "collection",
        "menu_type": MenuType.MENU.value,
        "permission_code": "news:list",
        "sort_order": 201,
        "hidden": False,
        "parent": "content",
    },
    {
        "name": "news_sources",
        "title": "新闻源管理",
        "path": "/news/sources",
        "component": "news/sources/index",
        "icon": "link",
        "menu_type": MenuType.MENU.value,
        "permission_code": "news:source:list",
        "sort_order": 202,
        "hidden": False,
        "parent": "content",
    },
    {
        "name": "news_fetch_records",
        "title": "抓取记录",
        "path": "/news/records",
        "component": "news/records/index",
        "icon": "document",
        "menu_type": MenuType.MENU.value,
        "permission_code": "news:fetch-record:list",
        "sort_order": 203,
        "hidden": False,
        "parent": "content",
    },
    {
        "name": "news_list_perm",
        "title": "新闻列表权限",
        "path": None,
        "component": None,
        "icon": None,
        "menu_type": MenuType.BUTTON.value,
        "permission_code": "news:list",
        "sort_order": 210,
        "hidden": True,
        "parent": "content",
    },
    {
        "name": "news_generate_perm",
        "title": "新闻生成权限",
        "path": None,
        "component": None,
        "icon": None,
        "menu_type": MenuType.BUTTON.value,
        "permission_code": "news:generate",
        "sort_order": 211,
        "hidden": True,
        "parent": "content",
    },
    {
        "name": "news_process_perm",
        "title": "新闻处理权限",
        "path": None,
        "component": None,
        "icon": None,
        "menu_type": MenuType.BUTTON.value,
        "permission_code": "news:process",
        "sort_order": 212,
        "hidden": True,
        "parent": "content",
    },
    {
        "name": "news_source_list_perm",
        "title": "新闻源列表权限",
        "path": None,
        "component": None,
        "icon": None,
        "menu_type": MenuType.BUTTON.value,
        "permission_code": "news:source:list",
        "sort_order": 212,
        "hidden": True,
        "parent": "content",
    },
    {
        "name": "news_source_create_perm",
        "title": "新闻源新增权限",
        "path": None,
        "component": None,
        "icon": None,
        "menu_type": MenuType.BUTTON.value,
        "permission_code": "news:source:create",
        "sort_order": 213,
        "hidden": True,
        "parent": "content",
    },
    {
        "name": "news_source_update_perm",
        "title": "新闻源更新权限",
        "path": None,
        "component": None,
        "icon": None,
        "menu_type": MenuType.BUTTON.value,
        "permission_code": "news:source:update",
        "sort_order": 214,
        "hidden": True,
        "parent": "content",
    },
    {
        "name": "news_source_sync_perm",
        "title": "新闻源同步权限",
        "path": None,
        "component": None,
        "icon": None,
        "menu_type": MenuType.BUTTON.value,
        "permission_code": "news:source:sync",
        "sort_order": 215,
        "hidden": True,
        "parent": "content",
    },
    {
        "name": "news_fetch_record_list_perm",
        "title": "抓取记录列表权限",
        "path": None,
        "component": None,
        "icon": None,
        "menu_type": MenuType.BUTTON.value,
        "permission_code": "news:fetch-record:list",
        "sort_order": 216,
        "hidden": True,
        "parent": "content",
    },
    {
        "name": "agent",
        "title": "智能处理",
        "path": "/agent",
        "component": "Layout",
        "icon": "cpu",
        "menu_type": MenuType.DIRECTORY.value,
        "permission_code": None,
        "sort_order": 300,
        "hidden": False,
        "parent": None,
    },
    {
        "name": "agent_runs",
        "title": "Agent运行",
        "path": "/agent/runs",
        "component": "agent/runs/index",
        "icon": "connection",
        "menu_type": MenuType.MENU.value,
        "permission_code": "agent:run:list",
        "sort_order": 301,
        "hidden": False,
        "parent": "agent",
    },
    {
        "name": "agent_hot_topics",
        "title": "热点池",
        "path": "/agent/hot-topics",
        "component": "agent/hot-topics/index",
        "icon": "trend-charts",
        "menu_type": MenuType.MENU.value,
        "permission_code": "agent:hot-topic:list",
        "sort_order": 302,
        "hidden": False,
        "parent": "agent",
    },
    {
        "name": "agent_push_plans",
        "title": "推送计划",
        "path": "/agent/push-plans",
        "component": "agent/push-plans/index",
        "icon": "position",
        "menu_type": MenuType.MENU.value,
        "permission_code": "agent:push-plan:list",
        "sort_order": 303,
        "hidden": False,
        "parent": "agent",
    },
    {
        "name": "agent_models",
        "title": "模型配置",
        "path": "/agent/config",
        "component": "agent/config/index",
        "icon": "setting",
        "menu_type": MenuType.MENU.value,
        "permission_code": "agent:config:list",
        "sort_order": 304,
        "hidden": False,
        "parent": "agent",
    },
    {
        "name": "agent_run_create_perm",
        "title": "Agent创建权限",
        "path": None,
        "component": None,
        "icon": None,
        "menu_type": MenuType.BUTTON.value,
        "permission_code": "agent:run:create",
        "sort_order": 310,
        "hidden": True,
        "parent": "agent",
    },
    {
        "name": "agent_run_retry_perm",
        "title": "Agent重试权限",
        "path": None,
        "component": None,
        "icon": None,
        "menu_type": MenuType.BUTTON.value,
        "permission_code": "agent:run:retry",
        "sort_order": 311,
        "hidden": True,
        "parent": "agent",
    },
    {
        "name": "agent_run_step_retry_perm",
        "title": "Agent步骤重试权限",
        "path": None,
        "component": None,
        "icon": None,
        "menu_type": MenuType.BUTTON.value,
        "permission_code": "agent:run:step:retry",
        "sort_order": 312,
        "hidden": True,
        "parent": "agent",
    },
    {
        "name": "agent_config_list_perm",
        "title": "Agent配置列表权限",
        "path": None,
        "component": None,
        "icon": None,
        "menu_type": MenuType.BUTTON.value,
        "permission_code": "agent:config:list",
        "sort_order": 313,
        "hidden": True,
        "parent": "agent",
    },
    {
        "name": "agent_config_update_perm",
        "title": "Agent配置更新权限",
        "path": None,
        "component": None,
        "icon": None,
        "menu_type": MenuType.BUTTON.value,
        "permission_code": "agent:config:update",
        "sort_order": 314,
        "hidden": True,
        "parent": "agent",
    },
    {
        "name": "agent_model_list_perm",
        "title": "Agent模型列表权限",
        "path": None,
        "component": None,
        "icon": None,
        "menu_type": MenuType.BUTTON.value,
        "permission_code": "agent:model:list",
        "sort_order": 315,
        "hidden": True,
        "parent": "agent",
    },
    {
        "name": "agent_hot_topic_list_perm",
        "title": "Agent热点列表权限",
        "path": None,
        "component": None,
        "icon": None,
        "menu_type": MenuType.BUTTON.value,
        "permission_code": "agent:hot-topic:list",
        "sort_order": 316,
        "hidden": True,
        "parent": "agent",
    },
    {
        "name": "agent_push_plan_list_perm",
        "title": "Agent推送列表权限",
        "path": None,
        "component": None,
        "icon": None,
        "menu_type": MenuType.BUTTON.value,
        "permission_code": "agent:push-plan:list",
        "sort_order": 317,
        "hidden": True,
        "parent": "agent",
    },
    {
        "name": "agent_push_plan_execute_perm",
        "title": "Agent推送执行权限",
        "path": None,
        "component": None,
        "icon": None,
        "menu_type": MenuType.BUTTON.value,
        "permission_code": "agent:push-plan:execute",
        "sort_order": 318,
        "hidden": True,
        "parent": "agent",
    },
    {
        "name": "agent_digest_run_perm",
        "title": "Agent简报创建权限",
        "path": None,
        "component": None,
        "icon": None,
        "menu_type": MenuType.BUTTON.value,
        "permission_code": "agent:run:digest:create",
        "sort_order": 319,
        "hidden": True,
        "parent": "agent",
    },
    {
        "name": "agent_digest_list_perm",
        "title": "Agent简报列表权限",
        "path": None,
        "component": None,
        "icon": None,
        "menu_type": MenuType.BUTTON.value,
        "permission_code": "agent:digest:list",
        "sort_order": 320,
        "hidden": True,
        "parent": "agent",
    },
    {
        "name": "agent_digest_push_perm",
        "title": "Agent简报推送权限",
        "path": None,
        "component": None,
        "icon": None,
        "menu_type": MenuType.BUTTON.value,
        "permission_code": "agent:digest:push",
        "sort_order": 321,
        "hidden": True,
        "parent": "agent",
    },
    {
        "name": "agent_push_record_list_perm",
        "title": "Agent推送记录权限",
        "path": None,
        "component": None,
        "icon": None,
        "menu_type": MenuType.BUTTON.value,
        "permission_code": "agent:push-record:list",
        "sort_order": 322,
        "hidden": True,
        "parent": "agent",
    },
    {
        "name": "agent_hot_topic_reprocess_perm",
        "title": "Agent热点重处理权限",
        "path": None,
        "component": None,
        "icon": None,
        "menu_type": MenuType.BUTTON.value,
        "permission_code": "agent:hot-topic:reprocess",
        "sort_order": 323,
        "hidden": True,
        "parent": "agent",
    },
]

DEFAULT_ROLE_SEEDS = [
    {
        "code": "SUPER_ADMIN",
        "name": "超级管理员",
        "description": "系统内置超级管理员，拥有全部基础设施权限。",
        "is_system": True,
        "menu_names": [item["name"] for item in DEFAULT_MENU_SEED],
    },
    {
        "code": "OPERATOR",
        "name": "运营",
        "description": "负责日常后台查看、内容管理、配置维护和文件上传。",
        "is_system": False,
        "menu_names": [
            "dashboard",
            "system",
            "content",
            "system_configs",
            "system_files",
            "system_logs",
            "system_tasks",
            "system_menu_list_perm",
            "system_config_list_perm",
            "system_file_upload_perm",
            "system_log_list_perm",
            "system_task_list_perm",
            "system_platform_account_list_perm",
            "system_platform_account_update_perm",
            "news_articles",
            "news_sources",
            "news_fetch_records",
            "news_list_perm",
            "news_generate_perm",
            "news_process_perm",
            "news_source_list_perm",
            "news_source_create_perm",
            "news_source_update_perm",
            "news_source_sync_perm",
            "news_fetch_record_list_perm",
            "agent_runs",
            "agent_hot_topics",
            "agent_push_plans",
            "agent_models",
            "agent_run_create_perm",
            "agent_run_retry_perm",
            "agent_run_step_retry_perm",
            "agent_config_list_perm",
            "agent_config_update_perm",
            "agent_model_list_perm",
            "agent_hot_topic_list_perm",
            "agent_push_plan_list_perm",
            "agent_push_plan_execute_perm",
            "agent_digest_run_perm",
            "agent_digest_list_perm",
            "agent_digest_push_perm",
            "agent_push_record_list_perm",
            "agent_hot_topic_reprocess_perm",
        ],
    },
]

DEFAULT_USER_SEEDS = [
    {
        "username": settings.bootstrap_admin_username,
        "email": settings.bootstrap_admin_email,
        "nickname": settings.bootstrap_admin_nickname,
        "password": settings.bootstrap_admin_password,
        "status": UserStatus.ACTIVE.value,
        "is_superuser": True,
        "role_codes": ["SUPER_ADMIN"],
    },
    {
        "username": "operator",
        "email": "operator@easyshorts.local",
        "nickname": "运营同学",
        "password": "Operator@123456",
        "status": UserStatus.ACTIVE.value,
        "is_superuser": False,
        "role_codes": ["OPERATOR"],
    },
]

DEFAULT_SYSTEM_CONFIGS = [
    {
        "category": "prompt",
        "config_key": "script_style_default",
        "config_value": "专业快讯",
        "value_type": "STRING",
        "description": "默认文案风格",
        "is_secret": False,
        "is_enabled": True,
    },
    {
        "category": "prompt",
        "config_key": "title_prompt",
        "config_value": "生成 18 字以内、信息密度高、适合短视频封面的标题。",
        "value_type": "STRING",
        "description": "标题生成提示词",
        "is_secret": False,
        "is_enabled": True,
    },
    {
        "category": "prompt",
        "config_key": "video_summary_prompt",
        "config_value": "请用简洁中文总结下面内容，突出事件、结论和适合短视频表达的亮点。",
        "value_type": "STRING",
        "description": "视频摘要提示词",
        "is_secret": False,
        "is_enabled": True,
    },
    {
        "category": "prompt",
        "config_key": "news_summary_prompt",
        "config_value": "请根据下面新闻内容生成中文摘要，突出核心结论和关键信息。",
        "value_type": "STRING",
        "description": "新闻摘要提示词",
        "is_secret": False,
        "is_enabled": True,
    },
    {
        "category": "prompt",
        "config_key": "news_title_prompt",
        "config_value": "请为下面这条新闻生成一个适合短视频封面的中文标题。",
        "value_type": "STRING",
        "description": "新闻标题提示词",
        "is_secret": False,
        "is_enabled": True,
    },
    {
        "category": "prompt",
        "config_key": "news_script_prompt",
        "config_value": "请根据下面新闻内容生成适合短视频口播的中文脚本。",
        "value_type": "STRING",
        "description": "新闻脚本提示词",
        "is_secret": False,
        "is_enabled": True,
    },
    {
        "category": "prompt",
        "config_key": "news_tags_prompt",
        "config_value": "请为下面新闻生成 3 到 5 个适合短视频传播的话题标签。",
        "value_type": "STRING",
        "description": "新闻标签提示词",
        "is_secret": False,
        "is_enabled": True,
    },
    {
        "category": "parameter",
        "config_key": "news_block_keywords",
        "config_value": "赌博,色情,诈骗,暴力,违法",
        "value_type": "STRING",
        "description": "新闻敏感词过滤列表",
        "is_secret": False,
        "is_enabled": True,
    },
    {
        "category": "parameter",
        "config_key": "news_hot_threshold",
        "config_value": "35",
        "value_type": "INTEGER",
        "description": "新闻热度阈值",
        "is_secret": False,
        "is_enabled": True,
    },
    {
        "category": "parameter",
        "config_key": "news_hot_keywords",
        "config_value": "openai,google,anthropic,meta,deepseek,huggingface,arxiv",
        "value_type": "STRING",
        "description": "新闻热度关键词",
        "is_secret": False,
        "is_enabled": True,
    },
    {
        "category": "agent",
        "config_key": "default_model_name",
        "config_value": "qwen3.5-plus",
        "value_type": "STRING",
        "description": "Agent 默认模型名称",
        "is_secret": False,
        "is_enabled": True,
    },
    {
        "category": "agent",
        "config_key": "supported_models",
        "config_value": "[\"qwen3.5-plus\", \"qwen-max\", \"deepseek-v3\"]",
        "value_type": "JSON",
        "description": "Agent 支持的模型列表",
        "is_secret": False,
        "is_enabled": True,
    },
    {
        "category": "agent",
        "config_key": "default_provider",
        "config_value": "dashscope",
        "value_type": "STRING",
        "description": "Agent 默认提供方",
        "is_secret": False,
        "is_enabled": True,
    },
    {
        "category": "agent",
        "config_key": "prompt_version",
        "config_value": "v1",
        "value_type": "STRING",
        "description": "Agent 提示词版本",
        "is_secret": False,
        "is_enabled": True,
    },
    {
        "category": "agent",
        "config_key": "push_channels",
        "config_value": "[\"email\", \"feishu\"]",
        "value_type": "JSON",
        "description": "Agent 默认推送渠道",
        "is_secret": False,
        "is_enabled": True,
    },
    {
        "category": "push",
        "config_key": "delivery_retry_count",
        "config_value": "3",
        "value_type": "INTEGER",
        "description": "推送失败重试次数",
        "is_secret": False,
        "is_enabled": True,
    },
    {
        "category": "push",
        "config_key": "delivery_timeout_seconds",
        "config_value": "10",
        "value_type": "INTEGER",
        "description": "推送请求超时时间（秒）",
        "is_secret": False,
        "is_enabled": True,
    },
    {
        "category": "push",
        "config_key": "webhook_url",
        "config_value": "",
        "value_type": "STRING",
        "description": "通用 Webhook 地址",
        "is_secret": True,
        "is_enabled": True,
    },
    {
        "category": "push",
        "config_key": "webhook_headers",
        "config_value": "{}",
        "value_type": "JSON",
        "description": "Webhook 请求头扩展",
        "is_secret": False,
        "is_enabled": True,
    },
    {
        "category": "push",
        "config_key": "email_smtp_host",
        "config_value": "",
        "value_type": "STRING",
        "description": "邮件 SMTP 主机",
        "is_secret": False,
        "is_enabled": True,
    },
    {
        "category": "push",
        "config_key": "email_smtp_port",
        "config_value": "587",
        "value_type": "INTEGER",
        "description": "邮件 SMTP 端口",
        "is_secret": False,
        "is_enabled": True,
    },
    {
        "category": "push",
        "config_key": "email_from",
        "config_value": "",
        "value_type": "STRING",
        "description": "邮件发件人",
        "is_secret": False,
        "is_enabled": True,
    },
    {
        "category": "push",
        "config_key": "email_to",
        "config_value": "[]",
        "value_type": "JSON",
        "description": "邮件收件人列表",
        "is_secret": False,
        "is_enabled": True,
    },
    {
        "category": "push",
        "config_key": "email_username",
        "config_value": "",
        "value_type": "STRING",
        "description": "邮件账号用户名",
        "is_secret": True,
        "is_enabled": True,
    },
    {
        "category": "push",
        "config_key": "email_password",
        "config_value": "",
        "value_type": "SECRET",
        "description": "邮件账号密码或授权码",
        "is_secret": True,
        "is_enabled": True,
    },
    {
        "category": "push",
        "config_key": "email_use_tls",
        "config_value": "true",
        "value_type": "BOOLEAN",
        "description": "邮件是否启用 TLS",
        "is_secret": False,
        "is_enabled": True,
    },
    {
        "category": "push",
        "config_key": "email_use_ssl",
        "config_value": "false",
        "value_type": "BOOLEAN",
        "description": "邮件是否启用 SSL",
        "is_secret": False,
        "is_enabled": True,
    },
    {
        "category": "push",
        "config_key": "email_subject_prefix",
        "config_value": "[EasyShorts]",
        "value_type": "STRING",
        "description": "邮件主题前缀",
        "is_secret": False,
        "is_enabled": True,
    },
    {
        "category": "prompt",
        "config_key": "agent_hotspot_prompt",
        "config_value": "判断输入内容是否属于高价值 AI 热点，输出结构化 JSON。",
        "value_type": "STRING",
        "description": "Agent 热点判断提示词",
        "is_secret": False,
        "is_enabled": True,
    },
    {
        "category": "prompt",
        "config_key": "agent_classification_prompt",
        "config_value": "根据输入内容输出主分类、标签和关键词，要求只输出 JSON。",
        "value_type": "STRING",
        "description": "Agent 分类提示词",
        "is_secret": False,
        "is_enabled": True,
    },
    {
        "category": "prompt",
        "config_key": "agent_summary_prompt",
        "config_value": "根据输入内容生成优化标题、一句话摘要和核心要点，要求只输出 JSON。",
        "value_type": "STRING",
        "description": "Agent 摘要提示词",
        "is_secret": False,
        "is_enabled": True,
    },
    {
        "category": "prompt",
        "config_key": "agent_enrichment_prompt",
        "config_value": "根据输入内容补充背景说明、行业影响、技术解读和应用场景，要求只输出 JSON。",
        "value_type": "STRING",
        "description": "Agent 内容扩展提示词",
        "is_secret": False,
        "is_enabled": True,
    },
    {
        "category": "prompt",
        "config_key": "agent_push_planner_prompt",
        "config_value": "根据输入内容输出推送决策，要求只输出 JSON。",
        "value_type": "STRING",
        "description": "Agent 推送计划提示词",
        "is_secret": False,
        "is_enabled": True,
    },
    {
        "category": "prompt",
        "config_key": "agent_digest_prompt",
        "config_value": "聚合多条热点内容，输出 AI 热点简报，要求只输出 JSON。",
        "value_type": "STRING",
        "description": "Agent 简报提示词",
        "is_secret": False,
        "is_enabled": True,
    },
    {
        "category": "platform",
        "config_key": "douyin_main",
        "config_value": "已授权 / token 剩余 6 天",
        "value_type": "STRING",
        "description": "抖音主账号占位配置",
        "is_secret": False,
        "is_enabled": True,
    },
    {
        "category": "parameter",
        "config_key": "upload_max_size_mb",
        "config_value": "500",
        "value_type": "INTEGER",
        "description": "统一上传大小上限，单位 MB",
        "is_secret": False,
        "is_enabled": True,
    },
]

DEFAULT_NEWS_SOURCES = [
    {
        "source_key": "modelscope_community",
        "name": "魔搭社区",
        "source_type": NewsSourceType.WEB.value,
        "url": "https://community.modelscope.cn/",
        "category": "国内社区",
        "language": "zh",
        "fetch_interval_minutes": 180,
        "is_enabled": True,
        "extra": {
            "mode": "list",
            "weight": 22,
            "max_items": 5,
            "article_urls": [
                "https://modelscope.csdn.net/69df3a2854b52172bc69c95e.html",
                "https://modelscope.csdn.net/69def6260a2f6a37c59fc8d1.html",
                "https://modelscope.csdn.net/69dc50730a2f6a37c59f202b.html",
                "https://modelscope.csdn.net/69dc4d9254b52172bc690de0.html",
                "https://modelscope.csdn.net/69d852a90a2f6a37c59e2e5d.html",
            ],
        },
    },
    {
        "source_key": "zhihu_ai_hot",
        "name": "知乎",
        "source_type": NewsSourceType.WEB.value,
        "url": "https://www.zhihu.com/",
        "category": "中文社区",
        "language": "zh",
        "fetch_interval_minutes": 180,
        "is_enabled": True,
        "extra": {
            "mode": "list",
            "weight": 20,
            "max_items": 5,
            "requires_auth": True,
            "cookie": "",
            "article_urls": [
                "https://zhuanlan.zhihu.com/p/706129671",
                "https://zhuanlan.zhihu.com/p/2011841127288938794",
                "https://zhuanlan.zhihu.com/p/1954137743031502336",
                "https://zhuanlan.zhihu.com/p/1973698835604840668",
                "https://zhuanlan.zhihu.com/p/1969826532110366202",
            ],
        },
    },
    {
        "source_key": "openai_blog",
        "name": "OpenAI Blog",
        "source_type": NewsSourceType.RSS.value,
        "url": "https://openai.com/blog/rss.xml",
        "category": "模型发布",
        "language": "en",
        "fetch_interval_minutes": 360,
        "is_enabled": True,
        "extra": {"weight": 25, "product": "openai"},
    },
    {
        "source_key": "huggingface_blog",
        "name": "HuggingFace Blog",
        "source_type": NewsSourceType.RSS.value,
        "url": "https://huggingface.co/blog/feed.xml",
        "category": "开源生态",
        "language": "en",
        "fetch_interval_minutes": 360,
        "is_enabled": True,
        "extra": {"weight": 20, "product": "huggingface"},
    },
]

DEFAULT_PLATFORM_ACCOUNTS = [
    {
        "platform": "douyin",
        "display_name": "抖音主账号",
        "account_id": "douyin_main",
        "auth_status": PlatformAuthStatus.AUTHORIZED.value,
        "access_token": None,
        "refresh_token": None,
        "expires_at": None,
        "extra": {"nickname": "EasyShorts"},
        "is_enabled": True,
    }
]


def _ensure_menu(
    *,
    db: Session,
    menu_lookup: dict[str, Menu],
    item: dict,
) -> Menu:
    parent_name = item.get("parent")
    parent = menu_lookup.get(parent_name) if parent_name else None
    menu = menu_lookup.get(item["name"])
    if menu is None:
        menu = Menu(
            name=item["name"],
            title=item["title"],
            path=item.get("path"),
            component=item.get("component"),
            icon=item.get("icon"),
            permission_code=item.get("permission_code"),
            menu_type=item["menu_type"],
            sort_order=item.get("sort_order", 0),
            hidden=item.get("hidden", False),
            parent_id=parent.id if parent else None,
        )
        db.add(menu)
        db.flush()
        menu_lookup[menu.name] = menu
        return menu

    menu.title = item["title"]
    menu.path = item.get("path")
    menu.component = item.get("component")
    menu.icon = item.get("icon")
    menu.permission_code = item.get("permission_code")
    menu.menu_type = item["menu_type"]
    menu.sort_order = item.get("sort_order", 0)
    menu.hidden = item.get("hidden", False)
    menu.parent_id = parent.id if parent else None
    db.add(menu)
    return menu


def _ensure_role(
    *,
    db: Session,
    role_lookup: dict[str, Role],
    item: dict,
    menu_lookup: dict[str, Menu],
) -> Role:
    role = role_lookup.get(item["code"])
    if role is None:
        role = Role(
            name=item["name"],
            code=item["code"],
            description=item.get("description"),
            is_system=item.get("is_system", False),
        )
        db.add(role)
        db.flush()
        role_lookup[role.code] = role
    else:
        role.name = item["name"]
        role.description = item.get("description")
        role.is_system = item.get("is_system", False)
        db.add(role)

    existing_menu_ids = {menu.id for menu in role.menus}
    missing_menus = [menu_lookup[name] for name in item.get("menu_names", []) if name in menu_lookup and menu_lookup[name].id not in existing_menu_ids]
    if missing_menus:
        role.menus = list(role.menus) + missing_menus

    return role


def _ensure_user(
    *,
    db: Session,
    role_lookup: dict[str, Role],
    item: dict,
) -> User:
    user = db.scalar(select(User).where(User.username == item["username"]))
    if user is None:
        user = User(
            username=item["username"],
            email=item.get("email"),
            nickname=item.get("nickname"),
            hashed_password=get_password_hash(item["password"]),
            status=item.get("status", UserStatus.ACTIVE.value),
            is_superuser=item.get("is_superuser", False),
        )
        db.add(user)
        db.flush()
    else:
        user.email = item.get("email")
        user.nickname = item.get("nickname")
        user.status = item.get("status", UserStatus.ACTIVE.value)
        user.is_superuser = item.get("is_superuser", False)
        db.add(user)

    seed_roles = [role_lookup[code] for code in item.get("role_codes", []) if code in role_lookup]
    current_role_ids = {role.id for role in user.roles}
    missing_roles = [role for role in seed_roles if role.id not in current_role_ids]
    if missing_roles:
        user.roles = list(user.roles) + missing_roles
    return user


def _ensure_system_config(db: Session, item: dict) -> SystemConfig:
    config = db.scalar(
        select(SystemConfig).where(
            SystemConfig.category == item["category"],
            SystemConfig.config_key == item["config_key"],
        )
    )
    if config is None:
        config = SystemConfig(**item)
        db.add(config)
        return config

    config.config_value = item["config_value"]
    config.value_type = item["value_type"]
    config.description = item.get("description")
    config.is_secret = item.get("is_secret", False)
    config.is_enabled = item.get("is_enabled", True)
    db.add(config)
    return config


def _ensure_news_source(db: Session, item: dict) -> NewsSource:
    source = db.scalar(
        select(NewsSource).where(NewsSource.source_key == item["source_key"])
    )
    if source is None:
        source = NewsSource(**item)
        db.add(source)
        return source

    source.name = item["name"]
    source.source_type = item.get("source_type", NewsSourceType.RSS.value)
    source.url = item["url"]
    source.category = item.get("category")
    source.language = item.get("language", "en")
    source.fetch_interval_minutes = item.get("fetch_interval_minutes", 360)
    source.is_enabled = item.get("is_enabled", True)
    source.extra = item.get("extra")
    db.add(source)
    return source


def _ensure_platform_account(db: Session, item: dict) -> PlatformAccount:
    account = db.scalar(
        select(PlatformAccount).where(
            PlatformAccount.platform == item["platform"],
            PlatformAccount.account_id == item["account_id"],
        )
    )
    if account is None:
        account = PlatformAccount(**item)
        db.add(account)
        return account

    account.display_name = item["display_name"]
    account.auth_status = item.get("auth_status", PlatformAuthStatus.UNAUTHORIZED.value)
    account.access_token = item.get("access_token")
    account.refresh_token = item.get("refresh_token")
    account.expires_at = item.get("expires_at")
    account.extra = item.get("extra")
    account.is_enabled = item.get("is_enabled", True)
    db.add(account)
    return account


def bootstrap_default_data(db: Session) -> None:
    menu_lookup: dict[str, Menu] = {
        menu.name: menu
        for menu in db.scalars(select(Menu).order_by(Menu.sort_order.asc(), Menu.id.asc())).all()
    }
    role_lookup: dict[str, Role] = {
        role.code: role
        for role in db.scalars(select(Role).order_by(Role.id.asc())).all()
    }

    for item in DEFAULT_MENU_SEED:
        _ensure_menu(db=db, menu_lookup=menu_lookup, item=item)

    for item in DEFAULT_ROLE_SEEDS:
        _ensure_role(db=db, role_lookup=role_lookup, item=item, menu_lookup=menu_lookup)

    for item in DEFAULT_USER_SEEDS:
        _ensure_user(db=db, role_lookup=role_lookup, item=item)

    for item in DEFAULT_SYSTEM_CONFIGS:
        _ensure_system_config(db=db, item=item)

    for item in DEFAULT_NEWS_SOURCES:
        _ensure_news_source(db=db, item=item)

    for item in DEFAULT_PLATFORM_ACCOUNTS:
        _ensure_platform_account(db=db, item=item)

    db.commit()
