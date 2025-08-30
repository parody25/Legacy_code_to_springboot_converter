package com.example.userservice;

import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;

import static org.assertj.core.api.Assertions.assertThat;

public class UserTest {

    @ParameterizedTest
    @CsvSource({
        "Alice, 22, true",
        "Bob, 15, false"
    })
    public void testIsAdult(String name, int age, boolean expectedIsAdult) {
        User user = new User(name, age);
        assertThat(user.isAdult()).isEqualTo(expectedIsAdult);
    }

    @ParameterizedTest
    @CsvSource({
        "Alice, 22, Hello, Mr./Ms. Alice",
        "Bob, 15, Hi, Bob"
    })
    public void testGreet(String name, int age, String expectedGreeting) {
        User user = new User(name, age);
        assertThat(user.greet()).isEqualTo(expectedGreeting);
    }
}