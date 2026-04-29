# China Commerce Starter

一个基于 **Spring Boot + Spring Security + MySQL + Redis** 的中国市场电商接单骨架项目，已经补齐交付基线，适合作为首版交付或二次开发起点。

- 用户管理（注册）
- 商品管理（新增、列表）
- 购物车（加购、查询）
- 订单管理（从购物车创建订单）
- 支付接口（支付宝/微信支付下单链接 + 支付确认）
- Actuator 健康检查：`/actuator/health`

## 快速运行

```bash
cd apps/china-commerce-starter
mvn spring-boot:run
```

默认端口：`8080`

## 测试

```bash
cd apps/china-commerce-starter
mvn test
```

## Docker 构建

```bash
cd apps/china-commerce-starter
docker build -t china-commerce-starter:local .
docker run --rm -p 8080:8080 china-commerce-starter:local
```

## 关键环境变量

- `SERVER_PORT`
- `SPRING_DATASOURCE_URL`
- `SPRING_DATASOURCE_USERNAME`
- `SPRING_DATASOURCE_PASSWORD`
- `SPRING_DATA_REDIS_HOST`
- `SPRING_DATA_REDIS_PORT`

## 安全说明

- 密码使用 BCrypt 存储
- Spring Security 启用认证保护
- 接口参数通过 `jakarta.validation` 校验
- `/api/auth/**` 与 `/actuator/health` 允许匿名访问，其余接口默认需要认证

> 生产环境请替换支付 mock 逻辑为支付宝/微信官方 SDK，并实现回调验签与幂等控制。
