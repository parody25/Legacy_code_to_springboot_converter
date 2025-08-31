package com.example.repository;

import com.example.entity.User;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.test.context.junit.jupiter.SpringExtension;

import static org.junit.jupiter.api.Assertions.*;

@ExtendWith(SpringExtension.class)
@DataJpaTest
class UserRepositoryTest {

    @Autowired
    private UserRepository userRepository;

    @Test
    void testFindByUsername_Success() {
        User user = new User(null, "testuser", "password", "USER");
        userRepository.save(user);

        User foundUser = userRepository.findByUsername("testuser");

        assertNotNull(foundUser);
        assertEquals("testuser", foundUser.getUsername());
    }

    @Test
    void testFindByUsername_NotFound() {
        User foundUser = userRepository.findByUsername("unknownuser");

        assertNull(foundUser);
    }

    @Test
    void testSaveUser_Success() {
        User user = new User(null, "newuser", "password", "USER");

        User savedUser = userRepository.save(user);

        assertNotNull(savedUser);
        assertNotNull(savedUser.getId());
        assertEquals("newuser", savedUser.getUsername());
    }

    @Test
    void testSaveUser_NullUsername() {
        User user = new User(null, null, "password", "USER");

        assertThrows(Exception.class, () -> userRepository.save(user));
    }

    @Test
    void testSaveUser_DuplicateUsername() {
        User user1 = new User(null, "duplicateuser", "password", "USER");
        userRepository.save(user1);

        User user2 = new User(null, "duplicateuser", "password", "USER");

        assertThrows(Exception.class, () -> userRepository.save(user2));
    }
}