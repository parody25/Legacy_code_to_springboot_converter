package com.example.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Entity
@Table(name = "batch_cheques")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class BatchCheque {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "account_number", nullable = false)
    private String accountNumber;

    @Column(name = "cheque_number", nullable = false)
    private String chequeNumber;

    @Column(name = "currency", nullable = false)
    private String currency;

    @Column(name = "amount", nullable = false)
    private Double amount;

    @Column(name = "signature", nullable = false)
    private String signature;
}