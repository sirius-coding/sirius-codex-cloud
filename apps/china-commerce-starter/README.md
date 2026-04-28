# China Commerce Starter

一个基于 **Spring Boot + Spring Security + MySQL + Redis** 的中国市场电商接单骨架项目，包含以下核心模块：

- 用户管理（注册）
- 商品管理（新增、列表）
- 购物车（加购、查询）
- 订单管理（从购物车创建订单）
- 支付接口（支付宝/微信支付下单链接 + 支付确认）

## 快速运行

```bash
cd apps/china-commerce-starter
mvn spring-boot:run
```

## 测试

```bash
cd apps/china-commerce-starter
mvn test
```

## 安全说明

- 密码使用 BCrypt 存储
- Spring Security 启用认证保护
- 接口参数通过 `jakarta.validation` 校验

> 生产环境请替换支付 mock 逻辑为支付宝/微信官方 SDK，并实现回调验签与幂等控制。
