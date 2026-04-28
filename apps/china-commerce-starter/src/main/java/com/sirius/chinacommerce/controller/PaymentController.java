package com.sirius.chinacommerce.controller;

import com.sirius.chinacommerce.model.OrderEntity;
import com.sirius.chinacommerce.service.OrderService;
import com.sirius.chinacommerce.service.PaymentService;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/payments")
public class PaymentController {

    private final PaymentService paymentService;
    private final OrderService orderService;

    public PaymentController(PaymentService paymentService, OrderService orderService) {
        this.paymentService = paymentService;
        this.orderService = orderService;
    }

    @PostMapping("/{orderId}/alipay")
    public Map<String, String> alipay(@PathVariable Long orderId) {
        return paymentService.createAlipayPayment(orderId);
    }

    @PostMapping("/{orderId}/wechat")
    public Map<String, String> wechat(@PathVariable Long orderId) {
        return paymentService.createWechatPayment(orderId);
    }

    @PostMapping("/{orderId}/confirm")
    public OrderEntity confirmPaid(@PathVariable Long orderId) {
        return orderService.markPaid(orderId);
    }
}
