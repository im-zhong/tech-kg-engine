package cn.techkg.common.utils;

import org.springframework.data.redis.core.RedisTemplate;

import java.util.concurrent.TimeUnit;

public class CacheUtil {

    private static RedisTemplate<String, Object> redisTemplate;

    private CacheUtil() {
    }

    public static void setRedisTemplate(RedisTemplate<String, Object> template) {
        redisTemplate = template;
    }

    public static void put(String key, Object value, long timeout, TimeUnit unit) {
        redisTemplate.opsForValue().set(key, value, timeout, unit);
    }

    public static Object get(String key) {
        return redisTemplate.opsForValue().get(key);
    }

    public static void evict(String key) {
        redisTemplate.delete(key);
    }
}
