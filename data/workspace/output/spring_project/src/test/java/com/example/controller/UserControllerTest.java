package com.example.controller;

import com.example.dto.UserDTO;
import com.example.entity.User;
import com.example.service.UserService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.http.ResponseEntity;

import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class UserControllerTest {

    @Mock
    private UserService userService;

    @InjectMocks
    private UserController userController;

    private User user;

    @BeforeEach
    void setUp() {
        user = new User(1L, "testuser", "encodedpassword", "USER");
    }

    @Test
    void testRegisterUser_Success() {
        UserDTO userDTO = new UserDTO();
        userDTO.setUsername("testuser");
        userDTO.setPassword("password");
        userDTO.setRole("USER");

        when(userService.registerUser("testuser", "password", "USER")).thenReturn(user);

        ResponseEntity<User> response = userController.registerUser(userDTO);

        assertNotNull(response);
        assertEquals(200, response.getStatusCodeValue());
        assertEquals("testuser", response.getBody().getUsername());
    }

    @Test
    void testRegisterUser_ValidationFailure() {
        UserDTO userDTO = new UserDTO();
        userDTO.setUsername(""); // Invalid username
        userDTO.setPassword("password");
        userDTO.setRole("USER");

        assertThrows(Exception.class, () -> userController.registerUser(userDTO));
    }

    @Test
    void testGetUserByUsername_Success() {
        when(userService.findByUsername("testuser")).thenReturn(Optional.of(user));

        ResponseEntity<User> response = userController.getUserByUsername("testuser");

        assertNotNull(response);
        assertEquals(200, response.getStatusCodeValue());
        assertEquals("testuser", response.getBody().getUsername());
    }

    @Test
    void testGetUserByUsername_NotFound() {
        when(userService.findByUsername("unknownuser")).thenReturn(Optional.empty());

        ResponseEntity<User> response = userController.getUserByUsername("unknownuser");

        assertNotNull(response);
        assertEquals(404, response.getStatusCodeValue());
    }

    @Test
    void testRegisterUser_NullRequestBody() {
        assertThrows(NullPointerException.class, () -> userController.registerUser(null));
    }
}