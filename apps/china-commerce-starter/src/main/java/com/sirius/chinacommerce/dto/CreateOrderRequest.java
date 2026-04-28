package com.sirius.chinacommerce.dto;

import jakarta.validation.constraints.NotNull;

public record CreateOrderRequest(@NotNull Long userId) {
}
