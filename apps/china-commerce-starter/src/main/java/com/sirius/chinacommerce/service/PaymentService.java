package com.sirius.chinacommerce.service;

import org.springframework.stereotype.Service;

import java.util.Map;

@Service
public class PaymentService {

    public Map<String, String> createAlipayPayment(Long orderId) {
        return Map.of(
                "provider", "ALIPAY",
                "orderId", String.valueOf(orderId),
                "payUrl", "https://openapi.alipay.com/gateway.do?out_trade_no=" + orderId
        );
    }

    public Map<String, String> createWechatPayment(Long orderId) {
        return Map.of(
                "provider", "WECHAT_PAY",
                "orderId", String.valueOf(orderId),
                "payUrl", "weixin://wxpay/bizpayurl?pr=" + orderId
        );
    }
}
