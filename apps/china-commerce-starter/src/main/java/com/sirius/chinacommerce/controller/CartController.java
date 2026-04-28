package com.sirius.chinacommerce.controller;

import com.sirius.chinacommerce.dto.AddCartItemRequest;
import com.sirius.chinacommerce.model.CartItem;
import com.sirius.chinacommerce.repository.AppUserRepository;
import com.sirius.chinacommerce.repository.CartItemRepository;
import com.sirius.chinacommerce.repository.ProductRepository;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/cart")
public class CartController {

    private final CartItemRepository cartItemRepository;
    private final AppUserRepository userRepository;
    private final ProductRepository productRepository;

    public CartController(CartItemRepository cartItemRepository,
                          AppUserRepository userRepository,
                          ProductRepository productRepository) {
        this.cartItemRepository = cartItemRepository;
        this.userRepository = userRepository;
        this.productRepository = productRepository;
    }

    @PostMapping("/items")
    public CartItem addItem(@Valid @RequestBody AddCartItemRequest request) {
        CartItem item = new CartItem();
        item.setUser(userRepository.findById(request.userId()).orElseThrow(() -> new IllegalArgumentException("用户不存在")));
        item.setProduct(productRepository.findById(request.productId()).orElseThrow(() -> new IllegalArgumentException("商品不存在")));
        item.setQuantity(request.quantity());
        return cartItemRepository.save(item);
    }

    @GetMapping("/{userId}")
    public List<CartItem> list(@PathVariable Long userId) {
        return cartItemRepository.findByUserId(userId);
    }
}
