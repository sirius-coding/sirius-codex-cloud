package com.sirius.chinacommerce.service;

import com.sirius.chinacommerce.model.*;
import com.sirius.chinacommerce.repository.AppUserRepository;
import com.sirius.chinacommerce.repository.CartItemRepository;
import com.sirius.chinacommerce.repository.ProductRepository;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;

import java.math.BigDecimal;

@SpringBootTest
@ActiveProfiles("test")
class OrderServiceTest {

    @Autowired
    private OrderService orderService;
    @Autowired
    private AppUserRepository userRepository;
    @Autowired
    private ProductRepository productRepository;
    @Autowired
    private CartItemRepository cartItemRepository;

    @Test
    void shouldCreateOrderFromCartAndReduceStock() {
        AppUser user = new AppUser();
        user.setPhone("13800000000");
        user.setPasswordHash("$2a$10$test");
        user.setRole("ROLE_USER");
        user.setDisplayName("测试用户");
        user = userRepository.save(user);

        Product product = new Product();
        product.setName("机械键盘");
        product.setPriceCny(new BigDecimal("299.00"));
        product.setStock(10);
        product = productRepository.save(product);

        CartItem item = new CartItem();
        item.setUser(user);
        item.setProduct(product);
        item.setQuantity(2);
        cartItemRepository.save(item);

        OrderEntity order = orderService.createOrderFromCart(user.getId());

        Assertions.assertEquals(OrderStatus.CREATED, order.getStatus());
        Assertions.assertEquals(new BigDecimal("598.00"), order.getTotalAmountCny());

        Product updated = productRepository.findById(product.getId()).orElseThrow();
        Assertions.assertEquals(8, updated.getStock());
        Assertions.assertTrue(cartItemRepository.findByUserId(user.getId()).isEmpty());
    }
}
