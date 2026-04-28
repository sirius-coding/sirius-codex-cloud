package com.sirius.chinacommerce.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

public record RegisterRequest(
        @Pattern(regexp = "^1\\d{10}$", message = "手机号格式不正确") String phone,
        @Size(min = 8, max = 64) String password,
        @NotBlank String displayName
) {
}
