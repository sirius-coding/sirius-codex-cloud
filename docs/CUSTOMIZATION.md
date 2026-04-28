# 定制指南（私活常用）

下面是最常见的私活改造路径，你可以按顺序做：

## 路径 A：改成小型 CRM

1. 为 `Client` 增加字段：`source`、`level`、`follow_up_at`。
2. 新增 `FollowUp` 表记录跟进日志。
3. 新增“近 7 天待跟进”接口。

## 路径 B：改成项目交付管理

1. 新增 `Task` 表（任务拆分）。
2. 新增 `Worklog` 表（工时记录）。
3. 新增“项目利润率”统计接口。

## 路径 C：改成订单/预约管理

1. 新增 `Order` / `Booking` 表。
2. 对接短信、邮件通知。
3. 增加状态机（待确认/已确认/已完成/已取消）。

## 推荐改造顺序

1. 先补充数据模型。
2. 再补充 CRUD 接口。
3. 最后做权限 + 报表。

## 代码位置建议

- 数据模型：`backend/app/models.py`
- 请求/响应：`backend/app/schemas.py`
- 路由层：`backend/app/routes/`
- 配置层：`backend/app/config.py`

