package com.sirius.chinacommerce.controller;

import com.sirius.chinacommerce.dto.CreateOrderRequest;
import com.sirius.chinacommerce.model.OrderEntity;
import com.sirius.chinacommerce.repository.OrderRepository;
import com.sirius.chinacommerce.service.OrderService;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/orders")
public class OrderController {

    private final OrderService orderService;
    private final OrderRepository orderRepository;

    public OrderController(OrderService orderService, OrderRepository orderRepository) {
        this.orderService = orderService;
        this.orderRepository = orderRepository;
    }

    @PostMapping
    public OrderEntity create(@Valid @RequestBody CreateOrderRequest request) {
        return orderService.createOrderFromCart(request.userId());
    }

    @GetMapping("/user/{userId}")
    public List<OrderEntity> userOrders(@PathVariable Long userId) {
        return orderRepository.findByUserId(userId);
    }
}
