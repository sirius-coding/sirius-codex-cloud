package com.sirius.chinacommerce.service;

import com.sirius.chinacommerce.model.*;
import com.sirius.chinacommerce.repository.AppUserRepository;
import com.sirius.chinacommerce.repository.CartItemRepository;
import com.sirius.chinacommerce.repository.OrderRepository;
import com.sirius.chinacommerce.repository.ProductRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.List;

@Service
public class OrderService {

    private final AppUserRepository userRepository;
    private final CartItemRepository cartRepository;
    private final ProductRepository productRepository;
    private final OrderRepository orderRepository;

    public OrderService(AppUserRepository userRepository,
                        CartItemRepository cartRepository,
                        ProductRepository productRepository,
                        OrderRepository orderRepository) {
        this.userRepository = userRepository;
        this.cartRepository = cartRepository;
        this.productRepository = productRepository;
        this.orderRepository = orderRepository;
    }

    @Transactional
    public OrderEntity createOrderFromCart(Long userId) {
        AppUser user = userRepository.findById(userId)
                .orElseThrow(() -> new IllegalArgumentException("用户不存在"));
        List<CartItem> cartItems = cartRepository.findByUserId(userId);
        if (cartItems.isEmpty()) {
            throw new IllegalStateException("购物车为空");
        }

        BigDecimal total = BigDecimal.ZERO;
        OrderEntity order = new OrderEntity();
        order.setUser(user);
        order.setStatus(OrderStatus.CREATED);
        order.setCreatedAt(OffsetDateTime.now());

        for (CartItem cartItem : cartItems) {
            Product product = cartItem.getProduct();
            if (product.getStock() < cartItem.getQuantity()) {
                throw new IllegalStateException("库存不足: " + product.getName());
            }
            product.setStock(product.getStock() - cartItem.getQuantity());
            productRepository.save(product);

            OrderItem orderItem = new OrderItem();
            orderItem.setOrder(order);
            orderItem.setProduct(product);
            orderItem.setQuantity(cartItem.getQuantity());
            orderItem.setSnapshotPriceCny(product.getPriceCny());
            order.getItems().add(orderItem);

            total = total.add(product.getPriceCny().multiply(BigDecimal.valueOf(cartItem.getQuantity())));
        }

        order.setTotalAmountCny(total);
        OrderEntity saved = orderRepository.save(order);
        cartRepository.deleteByUserId(userId);
        return saved;
    }

    @Transactional
    public OrderEntity markPaid(Long orderId) {
        OrderEntity order = orderRepository.findById(orderId)
                .orElseThrow(() -> new IllegalArgumentException("订单不存在"));
        if (order.getStatus() != OrderStatus.CREATED) {
            throw new IllegalStateException("当前订单状态不可支付");
        }
        order.setStatus(OrderStatus.PAID);
        return orderRepository.save(order);
    }
}
