package com.example.userservice;

import org.springframework.stereotype.Component;

@Component
public class User {
    private String name;
    private int age;

    public User() {
        // Default constructor
    }

    public User(String name, int age) {
        this.name = name;
        this.age = age;
    }

    // Getters and setters
    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public int getAge() {
        return age;
    }

    public void setAge(int age) {
        this.age = age;
    }

    // Simple method to check if user is adult
    public boolean isAdult() {
        return age >= 18;
    }

    // Business logic: greet the user
    public String greet() {
        if (isAdult()) {
            return "Hello, Mr./Ms. " + name;
        } else {
            return "Hi, " + name;
        }
    }
}