package cn.techkg.auth.controller;

import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/auth")
public class AuthController {

    @PostMapping("/login")
    public Object login() {
        // TODO: implement login
        return null;
    }

    @PostMapping("/logout")
    public Object logout() {
        // TODO: implement logout
        return null;
    }

    @PostMapping("/refresh")
    public Object refreshToken() {
        // TODO: implement token refresh
        return null;
    }
}
