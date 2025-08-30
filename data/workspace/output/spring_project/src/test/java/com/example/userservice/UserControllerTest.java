package com.example.userservice;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.http.ResponseEntity;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
public class UserControllerTest {

    @Autowired
    private TestRestTemplate restTemplate;

    @Test
    public void testGreetUser() {
        String name = "Alice";
        int age = 22;
        ResponseEntity<String> response = restTemplate.getForEntity("/users/greet?name=" + name + "&age=" + age, String.class);
        assertThat(response.getBody()).isEqualTo("Hello, Mr./Ms. Alice");

        name = "Bob";
        age = 15;
        response = restTemplate.getForEntity("/users/greet?name=" + name + "&age=" + age, String.class);
        assertThat(response.getBody()).isEqualTo("Hi, Bob");
    }
}