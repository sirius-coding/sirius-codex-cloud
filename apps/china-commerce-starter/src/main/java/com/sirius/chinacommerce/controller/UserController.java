package com.sirius.chinacommerce.controller;

import com.sirius.chinacommerce.dto.RegisterRequest;
import com.sirius.chinacommerce.model.AppUser;
import com.sirius.chinacommerce.service.UserService;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/auth")
public class UserController {

    private final UserService userService;

    public UserController(UserService userService) {
        this.userService = userService;
    }

    @PostMapping("/register")
    public AppUser register(@Valid @RequestBody RegisterRequest request) {
        return userService.register(request);
    }
}
