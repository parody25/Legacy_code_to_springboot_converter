package com.example.service;

import com.example.entity.User;
import com.example.repository.UserRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.crypto.password.PasswordEncoder;

import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class UserServiceTest {

    @Mock
    private UserRepository userRepository;

    @Mock
    private PasswordEncoder passwordEncoder;

    @InjectMocks
    private UserService userService;

    private User user;

    @BeforeEach
    void setUp() {
        user = new User(1L, "testuser", "encodedpassword", "USER");
    }

    @Test
    void testRegisterUser_Success() {
        when(passwordEncoder.encode("password")).thenReturn("encodedpassword");
        when(userRepository.save(any(User.class))).thenReturn(user);

        User result = userService.registerUser("testuser", "password", "USER");

        assertNotNull(result);
        assertEquals("testuser", result.getUsername());
        assertEquals("encodedpassword", result.getPassword());
        assertEquals("USER", result.getRole());

        verify(userRepository, times(1)).save(any(User.class));
    }

    @Test
    void testRegisterUser_NullUsername() {
        assertThrows(IllegalArgumentException.class, () -> userService.registerUser(null, "password", "USER"));
    }

    @Test
    void testFindByUsername_Success() {
        when(userRepository.findByUsername("testuser")).thenReturn(user);

        Optional<User> result = userService.findByUsername("testuser");

        assertTrue(result.isPresent());
        assertEquals("testuser", result.get().getUsername());
    }

    @Test
    void testFindByUsername_NotFound() {
        when(userRepository.findByUsername("unknownuser")).thenReturn(null);

        Optional<User> result = userService.findByUsername("unknownuser");

        assertFalse(result.isPresent());
    }

    @Test
    void testRegisterUser_EmptyPassword() {
        assertThrows(IllegalArgumentException.class, () -> userService.registerUser("testuser", "", "USER"));
    }
}