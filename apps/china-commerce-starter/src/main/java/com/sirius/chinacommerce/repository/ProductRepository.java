package com.sirius.chinacommerce.repository;

import com.sirius.chinacommerce.model.Product;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ProductRepository extends JpaRepository<Product, Long> {
}
