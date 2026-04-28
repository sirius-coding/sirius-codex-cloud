package com.sirius.chinacommerce.service;

import com.sirius.chinacommerce.dto.RegisterRequest;
import com.sirius.chinacommerce.model.AppUser;
import com.sirius.chinacommerce.repository.AppUserRepository;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

@Service
public class UserService {

    private final AppUserRepository userRepository;
    private final PasswordEncoder passwordEncoder;

    public UserService(AppUserRepository userRepository, PasswordEncoder passwordEncoder) {
        this.userRepository = userRepository;
        this.passwordEncoder = passwordEncoder;
    }

    public AppUser register(RegisterRequest request) {
        userRepository.findByPhone(request.phone()).ifPresent(u -> {
            throw new IllegalArgumentException("手机号已注册");
        });
        AppUser user = new AppUser();
        user.setPhone(request.phone());
        user.setPasswordHash(passwordEncoder.encode(request.password()));
        user.setDisplayName(request.displayName());
        user.setRole("ROLE_USER");
        return userRepository.save(user);
    }
}
