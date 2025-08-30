package com.example.userservice;

import org.junit.jupiter.api.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.junit.jupiter.MockitoExtension;
import org.junit.jupiter.api.extension.ExtendWith;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
public class UserControllerUnitTest {

    @Mock
    private User user;

    @InjectMocks
    private UserController userController;

    @Test
    public void testGreetUser() {
        when(user.greet()).thenReturn("Hello, Mr./Ms. Alice");

        String response = userController.greetUser("Alice", 22);
        assertThat(response).isEqualTo("Hello, Mr./Ms. Alice");

        Mockito.verify(user).setName("Alice");
        Mockito.verify(user).setAge(22);
    }
}